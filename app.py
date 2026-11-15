"""Racetrack Weather: the Streamlit entry point. The logic lives in the weather_app package."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import city_comparison, city_trend, compare_track_history, daily_range, feels_like_gap, rank_by_temperature, track_rain_history
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.dashboard import chance_of_rain, direction_label, interval_text, provider_table, session_message, session_window_rows
from weather_app.fetching import fetch_and_log, fetch_forecasts_and_log, fetch_many, fetch_radar_url, find_city
from weather_app.forecast_stats import combine_forecasts
from weather_app.sessions import session_times
from weather_app.storage import append_track, load_all_readings, load_all_tracks, load_circuits, load_tracks
from weather_app.tracks import check_new_track

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")
st.title("Racetrack Weather")
selected_track = None

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

# Weekend overview (card 7): the weather now and the next 5 days at the selected track.


def forecast_chart(combined, column, title, unit_label, sessions):
    """One line chart: the providers' average, and the low and high ends of its 95% interval."""
    # Readable names for the legend, instead of "temperature_low" and so on.
    chart_table = combined.rename(columns={
        column + "_low": "Low (95%)",
        column: "Average",
        column + "_high": "High (95%)",
    })
    fig = px.line(
        chart_table,
        x="time_utc",
        y=["Low (95%)", "Average", "High (95%)"],
        title=title,
        labels={"time_utc": "Time (UTC)", "value": unit_label, "variable": ""},
        markers=True,
    )
    # A dashed line at every session inside the forecast's 5 days.
    first = combined["time_utc"].min()
    last = combined["time_utc"].max()
    for session in sessions:
        if first <= session["start_utc"] <= last:
            fig.add_vline(x=session["start_utc"], line_dash="dash", line_color="grey")
    return fig


def show_radar(track):
    """A map around the track with the newest rain radar image laid over it."""
    try:
        radar_url = fetch_radar_url()
    except ValueError as error:
        st.warning(f"No rain radar right now: {error}")
        return
    # One row with the track's coordinates, so the map has a point to centre on.
    track_point = pd.DataFrame([track])
    fig = px.scatter_map(
        track_point,
        lat="latitude",
        lon="longitude",
        hover_name="location",
        # Centre on the track every time, so the map moves when another track is picked.
        center={"lat": track["latitude"], "lon": track["longitude"]},
        zoom=6,
        map_style="carto-positron",
        title="Rain radar now",
    )
    # The radar is a picture made of map tiles; the map fills in {z}/{x}/{y} itself.
    # RainViewer's free images stop at their zoom 7. The map asks for one zoom level more detail
    # than it shows, so from map zoom 6.5 it would get grey "not supported" tiles: hide the radar there.
    fig.update_layout(map_layers=[{"sourcetype": "raster", "source": [radar_url], "maxzoom": 6.5}])
    st.plotly_chart(fig)
    st.caption("The map opens at the most detailed free radar there is (about 1 km per pixel). Zoom in further and the radar hides, since RainViewer has no finer images.")


def show_weekend_overview(track):
    """The main page: the weather now and the next 5 days at the track picked in the sidebar."""
    if track is None:
        st.info("Pick a track in the sidebar.")
        return
    st.header(f"Weekend overview: {track['location']}")

    # The weather now needs the OpenWeatherMap key; the forecast below works without it.
    st.subheader("Weather now")
    if not API_KEY:
        st.warning(SETUP_MESSAGE)
    else:
        try:
            reading = fetch_and_log(track)
        except ValueError as error:
            st.warning(f"Could not load the weather now: {error}")
        else:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Temperature", f"{reading.temperature:.1f} °C")
            col2.metric("Feels like", f"{reading.feels_like:.1f} °C")
            col3.metric("Wind", f"{reading.wind_kmh:.0f} km/h")
            col4.metric("Conditions", reading.conditions)
    show_radar(track)

    # Every provider for this track. One that fails is skipped and named here.
    with st.spinner("Fetching the forecasts"):
        table, failures = fetch_forecasts_and_log(track)
    for failure in failures:
        st.warning(f"Skipped {failure}")
    if len(table) == 0:
        st.info("No forecast could be loaded. Try again in a few minutes.")
        return
    combined = combine_forecasts(table)

    # Rain and wind for the 3-hour window we are in now.
    now = datetime.now(timezone.utc)
    now_window = session_window_rows(combined, now)
    if len(now_window) == 0:
        st.info("No forecast for the current 3 hours yet.")
    else:
        window = now_window.iloc[0]
        st.subheader(f"This 3-hour window (from {window['time_utc']:%H:%M} UTC)")
        direction = direction_label(session_window_rows(table, now))
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Rain", f"{window['rain']:.1f} mm")
        col2.metric("Chance of rain", f"{chance_of_rain(window):.0f}%")
        col3.metric("Wind", f"{window['wind_kmh']:.0f} km/h")
        col4.metric("Wind from", direction)

    st.subheader("Next 5 days")
    sessions = session_times()
    st.plotly_chart(forecast_chart(combined, "temperature", "Temperature", "Temperature (°C)", sessions))
    st.plotly_chart(forecast_chart(combined, "rain", "Rain", "Rain (mm per 3 hours)", sessions))
    st.plotly_chart(forecast_chart(combined, "wind_kmh", "Wind", "Wind (km/h)", sessions))
    st.caption(
        "Average: the mean of the providers. Low and high: the 95% confidence interval. "
        "Dashed lines: the session times. MET Norway forecasts only about 2.5 days ahead, "
        "so later windows average fewer providers and their interval is wider."
    )


# Session dashboard (card 8): one session at a time, per provider and combined.


def previous_session():
    """Runs when Previous is pressed, before the page reruns."""
    st.session_state["session_index"] = st.session_state["session_index"] - 1


def next_session():
    """Runs when Next is pressed, before the page reruns."""
    st.session_state["session_index"] = st.session_state["session_index"] + 1


def session_chart(table, window, session_name):
    """Bar chart: each provider's temperature, and the combined one with its 95% interval."""
    chart_rows = []
    for _, row in table.iterrows():
        chart_rows.append({"Forecast": row["Provider"], "Temperature (°C)": row["Temperature (°C)"], "Margin": 0})
    # The error bar on the combined bar goes from the low to the high end of the interval.
    chart_rows.append({
        "Forecast": "Combined",
        "Temperature (°C)": window["temperature"],
        "Margin": window["temperature_high"] - window["temperature"],
    })
    fig = px.bar(
        pd.DataFrame(chart_rows),
        x="Forecast",
        y="Temperature (°C)",
        error_y="Margin",
        title=f"{session_name}: temperature by provider",
    )
    return fig


def show_session_dashboard(track):
    """One session at a time: what each provider forecasts for it, and the combined forecast."""
    if track is None:
        st.info("Pick a track in the sidebar.")
        return

    sessions = session_times()
    # A button is only "pressed" on the run right after the click, so the session
    # shown is remembered in session_state, like the track in the sidebar.
    if "session_index" not in st.session_state:
        st.session_state["session_index"] = 0
    index = st.session_state["session_index"]
    session = sessions[index]

    col1, col2, col3 = st.columns([1, 4, 1])
    col1.button("◀ Previous", on_click=previous_session, disabled=index == 0)
    col2.subheader(f"{session['session']}: {session['start_utc']:%a %d %b, %H:%M} UTC ({index + 1} of {len(sessions)})")
    col3.button("Next ▶", on_click=next_session, disabled=index == len(sessions) - 1)

    # The same cached call as the Weekend overview, so nothing is downloaded or logged twice.
    with st.spinner("Fetching the forecasts"):
        table, failures = fetch_forecasts_and_log(track)
    for failure in failures:
        st.warning(f"Skipped {failure}")

    now = datetime.now(timezone.utc)
    rows = session_window_rows(table, session["start_utc"])
    message = session_message(session["start_utc"], now, rows)
    if message is not None:
        st.info(message)
        return

    # Combine only this session's window: one row with the means and their 95% interval.
    window = combine_forecasts(rows).iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temperature", f"{window['temperature']:.1f} °C")
    col1.caption(interval_text(window, "temperature", "°C"))
    col2.metric("Chance of rain", f"{chance_of_rain(window):.0f}%")
    col2.caption(f"{window['rain_providers']} of {window['providers']} providers predict rain")
    col3.metric("Wind", f"{window['wind_kmh']:.0f} km/h")
    col3.caption(interval_text(window, "wind_kmh", "km/h"))
    col4.metric("Wind from", direction_label(rows))

    table = provider_table(rows)
    left, right = st.columns(2)
    with left:
        st.markdown("**Per provider**")
        st.dataframe(table.round(1), hide_index=True)
        st.caption(f"Combined from {window['providers']} providers. MET Norway only forecasts about 2.5 days ahead.")
    with right:
        st.plotly_chart(session_chart(table, window, session["session"]))


weekend_tab, session_tab, live_tab, analytics_tab = st.tabs(["Weekend overview", "Session dashboard", "Live conditions", "Analytics"])

with weekend_tab:
    show_weekend_overview(selected_track)

with session_tab:
    show_session_dashboard(selected_track)


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


def show_track_history(history, selected_track):
    """Show history for the sidebar track and compare two tracks over shared dates."""
    st.subheader("Track history")
    if selected_track is None:
        st.info("Pick a track in the sidebar to see its logged history.")
        return

    track_id = selected_track.get("id", selected_track.get("location_id"))
    track_name = selected_track["location"]
    if track_id is None:
        matching_tracks = history[history["location"] == track_name]
        if len(matching_tracks) > 0 and "location_id" in matching_tracks.columns:
            track_id = matching_tracks["location_id"].iloc[0]
    if track_id is None or "location_id" not in history.columns or len(history[history["location_id"] == track_id]) == 0:
        st.info("No logged history for this track yet.")
        return

    tracks = history[history["location_id"].notna()][["location_id", "location"]].drop_duplicates()
    track_ids = list(tracks["location_id"])
    track_names = dict(zip(tracks["location_id"], tracks["location"]))
    daily = track_rain_history(history, track_id)
    rain_fig = px.line(daily, x="day", y="rain_mm", markers=True, title=f"{track_name}: daily rain")
    rain_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Rain (mm)")
    st.plotly_chart(rain_fig)
    temperature = daily.rename(columns={"temperature_min_c": "Lowest", "temperature_max_c": "Highest"})
    temp_fig = px.line(temperature, x="day", y=["Lowest", "Highest"], markers=True, title=f"{track_name}: daily temperature range")
    temp_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature (°C)", legend_title_text="")
    st.plotly_chart(temp_fig)
    variation_fig = px.line(daily, x="day", y="temperature_range_c", markers=True, title="Daily temperature variability")
    variation_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature range (°C)")
    st.plotly_chart(variation_fig)

    st.subheader("Compare two tracks")
    if len(track_ids) < 2:
        st.info("Track comparison needs history for at least two tracks.")
        return
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
        return
    shared = history[(history["location_id"].isin([first_id, second_id])) & (history["timestamp_utc"] >= start) & (history["timestamp_utc"] <= end)].copy()
    summaries = compare_track_history(shared, [first_id, second_id])
    for summary in summaries:
        st.caption(str(summary))
    shared["day"] = shared["timestamp_utc"].dt.date
    daily_compare = shared.groupby(["location", "day"]).agg(temperature_c=("temperature", "mean")).reset_index()
    shared["rain"] = shared["rain"].fillna(0)
    rain_compare = (shared.groupby(["location", "day"])["rain"].mean() * 24).reset_index(name="rain_mm")
    daily_compare = daily_compare.merge(rain_compare, on=["location", "day"])
    temp_fig = px.line(daily_compare, x="day", y="temperature_c", color="location", markers=True, title="Average daily temperature comparison")
    temp_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature (°C)")
    st.plotly_chart(temp_fig)
    rain_fig = px.line(daily_compare, x="day", y="rain_mm", color="location", markers=True, title="Daily rain comparison")
    rain_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Rain (mm)")
    st.plotly_chart(rain_fig)


# View 2: existing weather analytics, followed by card 5's selected-track page.

with analytics_tab:
    history = load_all_readings()
    if len(history) == 0:
        st.info("No collected history yet.")
    else:
        first = history["timestamp_utc"].min().strftime("%d %b %Y")
        last = history["timestamp_utc"].max().strftime("%d %b %Y")
        st.caption(f"{len(history)} collected readings from {first} to {last} (UTC): the collector's history plus the app's own log.")

        st.subheader("Trend over time")
        logged_places = list(history["location"].value_counts().index)
        city = st.selectbox("Circuit", logged_places)
        trend = city_trend(history, city)
        if len(trend) < 2:
            st.info(f"Only one reading for {city} so far. The trend appears from the second one.")
        else:
            trend = trend.rename(columns={"timestamp_utc": "Time (UTC)", "temperature": "Temperature", "feels_like": "Feels like"})
            fig = px.line(trend, x="Time (UTC)", y=["Temperature", "Feels like"], markers=True, title=f"{city}: logged temperature")
            fig.update_layout(yaxis_title="°C", legend_title_text="")
            st.plotly_chart(fig)

        st.subheader("Compare circuits")
        comparison = city_comparison(history)
        fig = px.bar(comparison, x="location", y="average", error_y=comparison["highest"] - comparison["average"], error_y_minus=comparison["average"] - comparison["lowest"], title="Average logged temperature, with lowest and highest")
        fig.update_layout(xaxis_title="Circuit", yaxis_title="°C")
        st.plotly_chart(fig)
        st.dataframe(comparison.round(1), hide_index=True)

        st.subheader("Derived metrics")
        columns = st.columns(2)
        with columns[0]:
            st.markdown("**Average daily range** (highest minus lowest reading in a day, °C)")
            ranges = daily_range(history)
            if len(ranges) == 0:
                st.info("Needs two readings of one circuit on the same day.")
            else:
                average_range = ranges.groupby("location")["range"].mean().reset_index().sort_values("range", ascending=False)
                st.dataframe(average_range.round(1), hide_index=True)
        with columns[1]:
            st.markdown("**Feels-like gap** (average feels-like minus real temperature, °C)")
            st.dataframe(feels_like_gap(history).round(1), hide_index=True)

        history_track = selected_track
        if history_track is None:
            history_track = st.session_state.get("selected_track")
        if history_track is None and len(chosen) > 0:
            history_track = chosen[0]
        show_track_history(history, history_track)
