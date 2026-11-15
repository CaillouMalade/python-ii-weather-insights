"""Racetrack Weather: the Streamlit entry point. The logic lives in the weather_app package."""

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import compare_track_history, rank_by_temperature, track_rain_history
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.fetching import fetch_many, find_city
from weather_app.storage import load_all_readings, load_circuits

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")
st.title("Racetrack Weather")

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
    history = load_all_readings()
    if len(history) == 0 or "location_id" not in history.columns:
        st.info("No collected track history yet.")
    else:
        tracks = history[history["location_id"].notna()][["location_id", "location"]].drop_duplicates()
        track_ids = list(tracks["location_id"])
        track_names = dict(zip(tracks["location_id"], tracks["location"]))
        if len(track_ids) == 0:
            st.info("No collected track history yet.")
        else:
            st.subheader("Track history")
            track_id = st.selectbox("Track", track_ids, format_func=lambda value: track_names[value])
            daily = track_rain_history(history, track_id)
            rain_fig = px.line(daily, x="day", y="rain_mm", markers=True, title=f"{track_names[track_id]}: daily rain")
            rain_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Rain (mm)")
            st.plotly_chart(rain_fig)
            temp_fig = px.line(daily, x="day", y=["temperature_min_c", "temperature_max_c"], markers=True, title=f"{track_names[track_id]}: daily temperature range")
            temp_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature (°C)", legend_title_text="")
            st.plotly_chart(temp_fig)
            variation_fig = px.line(daily, x="day", y="temperature_range_c", markers=True, title="Daily temperature variability")
            variation_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature range (°C)")
            st.plotly_chart(variation_fig)

            st.subheader("Compare two tracks")
            if len(track_ids) < 2:
                st.info("Track comparison needs history for at least two tracks.")
            else:
                col1, col2 = st.columns(2)
                first_id = col1.selectbox("First track", track_ids, index=0, format_func=lambda value: track_names[value])
                second_options = [value for value in track_ids if value != first_id]
                second_id = col2.selectbox("Second track", second_options, format_func=lambda value: track_names[value])
                first_rows = history[history["location_id"] == first_id]
                second_rows = history[history["location_id"] == second_id]
                start = max(first_rows["timestamp_utc"].min(), second_rows["timestamp_utc"].min())
                end = min(first_rows["timestamp_utc"].max(), second_rows["timestamp_utc"].max())
                if start > end:
                    st.info("These tracks do not have history over the same period.")
                else:
                    shared = history[(history["location_id"].isin([first_id, second_id])) & (history["timestamp_utc"] >= start) & (history["timestamp_utc"] <= end)].copy()
                    summaries = compare_track_history(shared, [first_id, second_id])
                    for summary in summaries:
                        st.caption(f"{summary['location']}: average {summary['average_temperature_c']:.1f} °C, {summary['rain_days']} rain days, {summary['total_rain_mm']:.1f} mm total rain over {summary['days_logged']} logged days.")
                    shared["day"] = shared["timestamp_utc"].dt.date
                    daily_compare = shared.groupby(["location", "day"]).agg(temperature_c=("temperature", "mean")).reset_index()
                    rain_compare = shared.groupby(["location", "day"])["rain"].sum(min_count=1).reset_index(name="rain_mm")
                    daily_compare = daily_compare.merge(rain_compare, on=["location", "day"])
                    temp_fig = px.line(daily_compare, x="day", y="temperature_c", color="location", markers=True, title="Average daily temperature comparison")
                    temp_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature (°C)")
                    st.plotly_chart(temp_fig)
                    rain_fig = px.line(daily_compare, x="day", y="rain_mm", color="location", markers=True, title="Daily rain comparison")
                    rain_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Rain (mm)")
                    st.plotly_chart(rain_fig)
