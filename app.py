"""Racetrack Weather: the Streamlit entry point. The logic lives in the weather_app package."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import compare_track_history, track_rain_history
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.dashboard import chance_of_rain, direction_votes, interval_text, provider_table, session_message, session_window_rows
from weather_app.fetching import fetch_and_log, fetch_forecasts_and_log, fetch_radar_frames
from weather_app.forecast_stats import combine_forecasts
from weather_app.sessions import session_times, weekend_start
from weather_app.storage import append_track, load_all_tracks, load_history, load_tracks
from weather_app.tracks import check_new_track

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")
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
    # Once added, select the new track straight away and empty the inputs.
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
        # The app's name sits in the sidebar, so the page area starts straight with the open page.
        st.title("Racetrack Weather")
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH))
        st.header("Track")
        st.selectbox("Pick a track", track_names, key="track")

        st.subheader("Sessions (UTC)")
        for session in session_times():
            st.markdown(f"**{session['session']}**: {session['start_utc']:%a %d %b, %H:%M}")

        # Folded by default: picking a track is what most visitors do, adding one is rarer.
        with st.expander("Add a track"):
            st.caption("Accepted only within 3 km of an FIA Grade 1 circuit.")
            st.text_input("Name", key="new_track_name", placeholder="e.g. Monza Parabolica")
            st.text_input("Latitude", key="new_track_latitude", placeholder="e.g. 45.615")
            st.text_input("Longitude", key="new_track_longitude", placeholder="e.g. 9.29")
            st.button("Add track", on_click=add_track)
        # Outside the expander, so the result of a click is seen even when it is folded.
        if "track_message" in st.session_state:
            kind, text = st.session_state.pop("track_message")
            if kind == "warning":
                st.warning(text)
            else:
                st.caption(text)

    for track in tracks:
        if track["location"] == st.session_state["track"]:
            return track


# The selected track, used below by the Weekend overview and Session dashboard (cards 7, 8).
selected_track = show_sidebar()

# Weekend overview (card 7): the weather now and the race weekend's forecast at the selected track.


def add_session_lines(fig, chart_table, sessions):
    """Draw a dashed line at every session inside the chart's time range."""
    first = chart_table["time_utc"].min()
    last = chart_table["time_utc"].max()
    for session in sessions:
        if first <= session["start_utc"] <= last:
            fig.add_vline(x=session["start_utc"], line_dash="dash", line_color="grey")


def add_interval_band(fig, chart_table, column, yaxis, fill_color, name):
    """Shade the 95% interval of one column, only for the windows where all 3 providers answered."""
    # With only 2 providers Student's t is 12.7, so the band would be so wide that the
    # axis stretches and the line looks flat. With 3 providers it stays readable.
    all_three = chart_table["providers"] == 3
    band_low = chart_table[column + "_low"].where(all_three)
    band_high = chart_table[column + "_high"].where(all_three)
    # Two invisible lines: "tonexty" fills the space between the second one and the first.
    fig.add_scatter(x=chart_table["time_utc"], y=band_low, yaxis=yaxis,
                    mode="lines", line_width=0, showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=chart_table["time_utc"], y=band_high, yaxis=yaxis,
                    mode="lines", line_width=0, fill="tonexty", fillcolor=fill_color, name=name)


def rain_and_temperature_chart(chart_table, sessions):
    """Rain as bars (left axis) and temperature as a line with its 95% band (right axis)."""
    chart_table = chart_table.copy()
    # Rain is the total over a 3-hour window, so its bar sits in the middle of the window, not at its start.
    chart_table["window_middle"] = chart_table["time_utc"] + timedelta(minutes=90)
    fig = px.bar(
        chart_table,
        x="window_middle",
        y="rain",
        title="Rain and temperature",
        labels={"window_middle": "Time (UTC)", "rain": "Rain (mm per 3 hours)"},
    )
    fig.update_traces(name="Rain (mm)", showlegend=True, marker_color="steelblue", opacity=0.6)

    # The temperature goes on a second y-axis ("y2"), because °C and mm have different scales.
    add_interval_band(fig, chart_table, "temperature", "y2", "rgba(214, 39, 40, 0.15)", "Temperature 95% interval")
    fig.add_scatter(x=chart_table["time_utc"], y=chart_table["temperature"], yaxis="y2",
                    mode="lines", line_color="firebrick", line_shape="spline", name="Temperature (°C)")
    # 20% headroom above the biggest bar, so it never touches the top; at least 0.5 mm when it barely rains.
    rain_top = chart_table["rain"].max() * 1.2
    # "not >=" also catches NaN, when no provider sent any rain value.
    if not rain_top >= 0.5:
        rain_top = 0.5
    fig.update_layout(
        yaxis={"range": [0, rain_top]},
        yaxis2={"title": "Temperature (°C)", "overlaying": "y", "side": "right", "showgrid": False, "tickformat": ".0f"},
        legend={"orientation": "h", "y": -0.25},
    )
    add_session_lines(fig, chart_table, sessions)
    return fig


def wind_chart(chart_table, sessions):
    """Wind speed as a line with its 95% band, in the same style as the temperature."""
    fig = px.line(
        chart_table,
        x="time_utc",
        y="wind_kmh",
        title="Wind",
        labels={"time_utc": "Time (UTC)", "wind_kmh": "Wind (km/h)"},
    )
    fig.update_traces(name="Wind (km/h)", showlegend=True, line_color="seagreen", line_shape="spline")
    add_interval_band(fig, chart_table, "wind_kmh", "y", "rgba(46, 139, 87, 0.15)", "Wind 95% interval")
    fig.update_layout(legend={"orientation": "h", "y": -0.25})
    add_session_lines(fig, chart_table, sessions)
    return fig


def race_weekend_rows(combined):
    """Keep only the windows of the 3 race days, so the charts match the sessions in the sidebar."""
    first_day = weekend_start()
    last_day = first_day + timedelta(days=3)
    return combined[(combined["time_utc"] >= first_day) & (combined["time_utc"] < last_day)]


# Free satellite pictures from Esri, in the same {z}/{x}/{y} tile form as the radar (Esri puts y before x).
SATELLITE_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


def show_track_map(track):
    """A satellite map zoomed in on the circuit, with a red dot on the track's point."""
    track_point = pd.DataFrame([track])
    fig = px.scatter_map(
        track_point,
        lat="latitude",
        lon="longitude",
        hover_name="location",
        center={"lat": track["latitude"], "lon": track["longitude"]},
        # Zoom 14 shows about 3 km across: the whole circuit fits.
        zoom=14,
        # An empty background: the satellite pictures below fill the whole map.
        map_style="white-bg",
        title="Track",
    )
    fig.update_traces(marker={"size": 14, "color": "red"})
    fig.update_layout(map_layers=[{"sourcetype": "raster", "source": [SATELLITE_TILES], "below": "traces", "sourceattribution": "Esri World Imagery"}])
    st.plotly_chart(fig)


def show_wind_direction(column, window_rows):
    """The wind direction in big letters, and how many providers agree in small text under it."""
    votes = direction_votes(window_rows)
    if votes is None:
        column.metric("Wind from", "Unknown")
        return
    sector, agreeing, providers = votes
    column.metric("Wind from", sector)
    column.caption(f"{agreeing} of {providers} providers agree")


def show_radar(track):
    """A map around the track with a rain radar image laid over it, and a slider to go back up to 2 hours."""
    try:
        frames = fetch_radar_frames()
    except ValueError as error:
        st.warning(f"No rain radar right now: {error}")
        return
    # The slider shows the image times; it starts on the newest one (the last in the list).
    times = [f"{frame['time_utc']:%H:%M}" for frame in frames]
    chosen_time = st.select_slider("Radar time (UTC)", options=times, value=times[-1])
    radar_url = frames[times.index(chosen_time)]["url"]
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
        title=f"Rain radar at {chosen_time} UTC",
    )
    # The radar is a picture made of map tiles; the map fills in {z}/{x}/{y} itself.
    # RainViewer's free images stop at their zoom 7. The map asks for one zoom level more detail
    # than it shows, so from map zoom 6.5 it would get grey "not supported" tiles: hide the radar there.
    fig.update_layout(map_layers=[{"sourcetype": "raster", "source": [radar_url], "maxzoom": 6.5}])
    st.plotly_chart(fig)
    st.caption("The map opens at the most detailed free radar there is (about 1 km per pixel). Zoom in further and the radar hides, since RainViewer has no finer images.")


def show_weekend_overview(track):
    """The main page: the weather now, the race weekend's forecast and the maps, for the track picked in the sidebar."""
    if track is None:
        st.info("Pick a track in the sidebar.")
        return
    st.header(f"Weekend overview: {track['location']}")

    # Every provider for this track, fetched first because "Weather now" uses it for the wind direction.
    # A provider that fails is skipped and named here.
    with st.spinner("Fetching the forecasts"):
        table, failures = fetch_forecasts_and_log(track)
    for failure in failures:
        st.warning(f"Skipped {failure}")

    show_weather_now(track, table)

    if len(table) == 0:
        st.info("No forecast could be loaded. Try again in a few minutes.")
    else:
        show_race_weekend_charts(combine_forecasts(table))

    # Two maps: the satellite view shows the circuit itself, the radar shows the rain
    # around it. One map cannot do both, as the free radar stops before the track is visible.
    map_left, map_right = st.columns(2)
    with map_left:
        show_track_map(track)
    with map_right:
        show_radar(track)


def show_weather_now(track, table):
    """The current weather from OpenWeatherMap, and the wind direction the providers agree on now."""
    st.subheader("Weather now")
    # The weather now needs the OpenWeatherMap key; the forecasts and charts work without it.
    if not API_KEY:
        st.warning(SETUP_MESSAGE)
        return
    try:
        reading = fetch_and_log(track)
    except ValueError as error:
        st.warning(f"Could not load the weather now: {error}")
        return
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Temperature", f"{reading.temperature:.1f} °C")
    col2.metric("Feels like", f"{reading.feels_like:.1f} °C")
    col3.metric("Wind", f"{reading.wind_kmh:.0f} km/h")
    # WeatherReading has no wind direction, so it comes from the providers' current 3-hour window.
    show_wind_direction(col4, session_window_rows(table, datetime.now(timezone.utc)))
    # Plain text, not a metric: a metric's big font cuts "broken clouds" to "broken cl...".
    col5.caption("Conditions")
    col5.markdown(f"**{reading.conditions.capitalize()}**")


def show_race_weekend_charts(combined):
    """The two forecast charts for the 3 race days, with the sessions as dashed lines."""
    st.subheader("Race weekend")
    weekend = race_weekend_rows(combined)
    if len(weekend) == 0:
        st.info("No forecast reaches the race weekend yet.")
        return
    sessions = session_times()
    st.plotly_chart(rain_and_temperature_chart(weekend, sessions))
    st.plotly_chart(wind_chart(weekend, sessions))
    st.caption(
        "Lines and bars: the mean of the providers. Shaded band: the 95% confidence interval, "
        "drawn where all 3 providers answered. Dashed lines: the session times. MET Norway "
        "forecasts only about 2.5 days ahead, so the last day averages 2 providers."
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
    show_wind_direction(col4, rows)

    table = provider_table(rows)
    left, right = st.columns(2)
    with left:
        st.markdown("**Per provider**")
        st.dataframe(table.round(1), hide_index=True)
        st.caption(f"Combined from {window['providers']} providers. MET Norway only forecasts about 2.5 days ahead.")
    with right:
        st.plotly_chart(session_chart(table, window, session["session"]))


# History and Track comparison (card 5): both read the collector's logged history.


def history_track_names(history):
    """Return the track ids that have logged history, and a dictionary from id to track name."""
    tracks = history[history["location_id"].notna()][["location_id", "location"]].drop_duplicates()
    track_ids = list(tracks["location_id"])
    track_names = dict(zip(tracks["location_id"], tracks["location"]))
    return track_ids, track_names


def show_history(history, selected_track):
    """The logged history of the track picked in the sidebar: daily rain, temperature range and variability."""
    st.subheader("Track history")
    if selected_track is None:
        st.info("Pick a track in the sidebar to see its logged history.")
        return

    # Tracks are matched on their id, not their name, so a renamed track keeps its history.
    track_id = selected_track["id"]
    track_name = selected_track["location"]
    if len(history[history["location_id"] == track_id]) == 0:
        st.info("No logged history for this track yet.")
        return

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


def show_track_comparison(history):
    """Two tracks side by side over the days both were logged, ranked with sorted()."""
    st.subheader("Compare two tracks")
    track_ids, track_names = history_track_names(history)
    if len(track_ids) < 2:
        st.info("Track comparison needs history for at least two tracks.")
        return
    col1, col2 = st.columns(2)
    first_id = col1.selectbox("First track", track_ids, index=0, format_func=lambda value: track_names[value])
    second_options = [value for value in track_ids if value != first_id]
    second_id = col2.selectbox("Second track", second_options, format_func=lambda value: track_names[value])
    first_rows = history[history["location_id"] == first_id]
    second_rows = history[history["location_id"] == second_id]
    # Only the period both tracks were logged, so the two are compared fairly.
    start = max(first_rows["timestamp_utc"].min(), second_rows["timestamp_utc"].min())
    end = min(first_rows["timestamp_utc"].max(), second_rows["timestamp_utc"].max())
    if start > end:
        st.info("These tracks do not have history over the same period.")
        return
    shared = history[(history["location_id"].isin([first_id, second_id])) & (history["timestamp_utc"] >= start) & (history["timestamp_utc"] <= end)].copy()
    # compare_track_history returns TrackSummary objects ranked with sorted() (wettest first).
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


def show_logged_period(history):
    """One line saying how much history there is, shown above the History and Track comparison pages."""
    first = history["timestamp_utc"].min().strftime("%d %b %Y")
    last = history["timestamp_utc"].max().strftime("%d %b %Y")
    st.caption(f"{len(history)} logged readings from {first} to {last} (UTC), collected every 30 minutes.")


# The four views, as pages in the bar at the top of the window, so they stay visible while
# scrolling. Only the open page runs, so switching pages does not redraw the other three.
# Each page is a small function without arguments, because st.Page calls it that way.


def weekend_page():
    """The Weekend overview page."""
    show_weekend_overview(selected_track)


def session_page():
    """The Session dashboard page."""
    show_session_dashboard(selected_track)


def history_page():
    """The History page, read from the collector's logged history."""
    history = load_history()
    if len(history) == 0:
        st.info("No logged history yet.")
        return
    show_logged_period(history)
    show_history(history, selected_track)


def comparison_page():
    """The Track comparison page, read from the collector's logged history."""
    history = load_history()
    if len(history) == 0:
        st.info("No logged history yet.")
        return
    show_logged_period(history)
    show_track_comparison(history)


pages = [
    st.Page(weekend_page, title="Weekend overview", default=True),
    st.Page(session_page, title="Session dashboard", url_path="session-dashboard"),
    st.Page(history_page, title="History", url_path="history"),
    st.Page(comparison_page, title="Track comparison", url_path="track-comparison"),
]
st.navigation(pages, position="top").run()
