"""Racetrack Weather: the Streamlit entry point. The logic lives in the weather_app package."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import city_comparison, city_trend, daily_range, feels_like_gap, rank_by_temperature
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.fetching import fetch_many, find_city
from weather_app.sessions import session_times
from weather_app.storage import append_track, load_all_readings, load_all_tracks, load_circuits, load_tracks
from weather_app.tracks import check_new_track

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")
st.title("Racetrack Weather")

# Sidebar (card 4): pick a track, see the session times, add a track.


def add_track():
    """Runs when Add track is pressed: check the three inputs, then save the track."""
    try:
        track = check_new_track(
            st.session_state["new_track_name"],
            st.session_state["new_track_latitude"],
            st.session_state["new_track_longitude"],
            load_all_tracks(),
            load_tracks(),
        )
        append_track(track)
    except ValueError as error:
        st.session_state["track_message"] = ("warning", str(error))
        return
    # 加成功后直接选中新赛道，并清空输入框
    st.session_state["track"] = track["location"]
    st.session_state["track_message"] = ("ok", f"Added {track['location']}.")
    st.session_state["new_track_name"] = ""
    st.session_state["new_track_latitude"] = ""
    st.session_state["new_track_longitude"] = ""


def show_sidebar():
    """Draw the track part of the sidebar and return the chosen track as a location dictionary."""
    tracks = load_all_tracks()
    track_names = [track["location"] for track in tracks]

    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH))
        st.header("Track")
        st.selectbox("Pick a track", track_names, key="track")

        st.subheader("Sessions (UTC)")
        for session in session_times():
            st.markdown(f"**{session['session']}**: {session['start_utc']:%a %d %b, %H:%M}")

        st.subheader("Add a track")
        st.caption("Accepted only within 3 km of an FIA Grade 1 circuit.")
        st.text_input("Name", key="new_track_name", placeholder="e.g. Monza Parabolica")
        st.text_input("Latitude", key="new_track_latitude", placeholder="e.g. 45.615")
        st.text_input("Longitude", key="new_track_longitude", placeholder="e.g. 9.29")
        st.button("Add track", on_click=add_track)
        if "track_message" in st.session_state:
            kind, text = st.session_state.pop("track_message")
            if kind == "warning":
                st.warning(text)
            else:
                st.caption(text)

    for track in tracks:
        if track["location"] == st.session_state["track"]:
            return track


# 选中的赛道，后面 Weekend overview / Session dashboard (cards 7, 8) 会用到
selected_track = show_sidebar()


# The fixed list from data/circuits.csv, plus any place added this session.
if "places" not in st.session_state:
    st.session_state["places"] = load_circuits()
places = st.session_state["places"]
names = [city["location"] for city in places]


# Sidebar: choose circuits, or add a place.


def add_city():
    """Runs when the Add button is pressed, before the page reruns."""
    try:
        city = find_city(st.session_state["new_city"])
    except ValueError as error:
        st.session_state["add_message"] = str(error)
        return
    if city["location"] in names:
        st.session_state["add_message"] = f"{city['location']} is already in the list."
    else:
        places.append(city)
        st.session_state["chosen"] = st.session_state["chosen"] + [city["location"]]
        st.session_state["add_message"] = f"Added {city['location']}."
    st.session_state["new_city"] = ""


with st.sidebar:
    st.header("Circuits")
    if "chosen" not in st.session_state:
        st.session_state["chosen"] = names[:5]
    st.multiselect("Circuits to compare", names, key="chosen")

    if API_KEY:
        st.text_input("Add a place near another track (town name)", key="new_city", placeholder="e.g. Zandvoort")
        st.button("Add", on_click=add_city)
        if "add_message" in st.session_state:
            st.caption(st.session_state.pop("add_message"))

chosen = []
for city in places:
    if city["location"] in st.session_state["chosen"]:
        chosen.append(city)

live_tab, analytics_tab = st.tabs(["Live conditions", "Analytics"])


# View 1: live conditions at the chosen circuits.

with live_tab:
    if not API_KEY:
        st.warning(SETUP_MESSAGE)
    elif len(chosen) == 0:
        st.info("Pick at least one circuit in the sidebar.")
    else:
        with st.spinner("Fetching current weather"):
            readings, failures = fetch_many(chosen)
        for failure in failures:
            st.warning(f"Skipped {failure}")

        if len(readings) > 0:
            ranked = rank_by_temperature(readings)
            warmest = ranked[0]
            coldest = ranked[-1]
            columns = st.columns(2)
            columns[0].metric(f"Warmest now: {warmest.location}", f"{warmest.temperature:.1f} °C")
            columns[1].metric(f"Coldest now: {coldest.location}", f"{coldest.temperature:.1f} °C")

            rows = []
            for reading in ranked:
                rows.append(
                    {
                        "Circuit": reading.location,
                        "Temperature (°C)": round(reading.temperature, 1),
                        "Feels like (°C)": round(reading.feels_like, 1),
                        "Humidity (%)": reading.humidity,
                        "Wind (km/h)": round(reading.wind_kmh, 1),
                        "Conditions": reading.conditions,
                    }
                )
            table = pd.DataFrame(rows)

            fig = px.bar(table, x="Circuit", y="Temperature (°C)", title="Current temperature by circuit")
            st.plotly_chart(fig)
            st.dataframe(table, hide_index=True)
            st.caption("Each successful fetch is added to data/weather_log.csv. Readings refresh every 10 minutes.")


# View 2: analytics on our own collected history. Works without a key.

with analytics_tab:
    log = load_all_readings()
    if len(log) == 0:
        st.info("No collected history yet.")
    else:
        first = log["timestamp_utc"].min().strftime("%d %b %Y")
        last = log["timestamp_utc"].max().strftime("%d %b %Y")
        st.caption(f"{len(log)} collected readings from {first} to {last} (UTC): the collector's history plus the app's own log.")

        st.subheader("Trend over time")
        # The city with the most readings is shown first, because its trend says the most.
        logged_places = list(log["location"].value_counts().index)
        city = st.selectbox("Circuit", logged_places)
        trend = city_trend(log, city)
        if len(trend) < 2:
            st.info(f"Only one reading for {city} so far. The trend appears from the second one.")
        else:
            trend = trend.rename(columns={"timestamp_utc": "Time (UTC)", "temperature": "Temperature", "feels_like": "Feels like"})
            fig = px.line(trend, x="Time (UTC)", y=["Temperature", "Feels like"], markers=True, title=f"{city}: logged temperature")
            fig.update_layout(yaxis_title="°C", legend_title_text="")
            st.plotly_chart(fig)

        st.subheader("Compare circuits")
        comparison = city_comparison(log)
        fig = px.bar(comparison, x="location", y="average", error_y=comparison["highest"] - comparison["average"], error_y_minus=comparison["average"] - comparison["lowest"], title="Average logged temperature, with lowest and highest")
        fig.update_layout(xaxis_title="Circuit", yaxis_title="°C")
        st.plotly_chart(fig)
        st.dataframe(comparison.round(1), hide_index=True)

        st.subheader("Derived metrics")
        columns = st.columns(2)
        with columns[0]:
            st.markdown("**Average daily range** (highest minus lowest reading in a day, °C)")
            ranges = daily_range(log)
            if len(ranges) == 0:
                st.info("Needs two readings of one circuit on the same day.")
            else:
                average_range = ranges.groupby("location")["range"].mean().reset_index().sort_values("range", ascending=False)
                st.dataframe(average_range.round(1), hide_index=True)
        with columns[1]:
            st.markdown("**Feels-like gap** (average feels-like minus real temperature, °C)")
            st.dataframe(feels_like_gap(log).round(1), hide_index=True)
