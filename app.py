"""Racetrack Weather: the Streamlit entry point. The logic lives in the weather_app package."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import MIN_DAYS_LOGGED, compare_track_history, days_logged, track_rain_history
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.dashboard import chance_of_rain, direction_votes, interval_text, provider_table, session_message, session_window_rows
from weather_app.fetching import fetch_and_log, fetch_forecasts_and_log, fetch_radar_frames
from weather_app.forecast_stats import combine_forecasts
from weather_app.sessions import session_times, weekend_start
from weather_app.storage import append_track, load_all_tracks, load_history, load_tracks
from weather_app.tracks import check_new_track

LOGO_PATH = Path(__file__).parent / "assets" / "logo.png"
# The same logo with white letters, for visitors who use dark mode.
LOGO_DARK_PATH = Path(__file__).parent / "assets" / "logo_dark.png"

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
        # The logo (with the app's name) sits in the sidebar, so the page area starts straight with the open page.
        # Without the picture, the name is written as a title instead.
        logo = LOGO_PATH
        if st.context.theme.type == "dark":
            logo = LOGO_DARK_PATH
        if logo.exists():
            st.image(str(logo))
        else:
            st.title("Racetrack Weather")
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


def line_chart(chart_table, sessions, column, title, label, line_color, band_color):
    """One value (temperature or wind) as a line with its 95% band, and the sessions as dashed lines."""
    fig = px.line(
        chart_table,
        x="time_utc",
        y=column,
        title=title,
        labels={"time_utc": "Time (UTC)", column: label},
    )
    fig.update_traces(name=label, showlegend=True, line_color=line_color, line_shape="spline")
    add_interval_band(fig, chart_table, column, "y", band_color, title + " 95% interval")
    fig.update_layout(legend={"orientation": "h", "y": -0.25})
    add_session_lines(fig, chart_table, sessions)
    return fig


def wind_chart(chart_table, sessions):
    """Wind speed as a line with its 95% band, in the same style as the temperature."""
    return line_chart(chart_table, sessions, "wind_kmh", "Wind", "Wind (km/h)", "seagreen", "rgba(46, 139, 87, 0.15)")


def temperature_chart(chart_table, sessions):
    """Temperature as a line with its 95% band."""
    return line_chart(chart_table, sessions, "temperature", "Temperature", "Temperature (°C)", "firebrick", "rgba(214, 39, 40, 0.15)")


def rain_chart(chart_table, sessions, provider_rows):
    """Rain as bars (the providers' mean) and one flat line per provider across its 3-hour window."""
    chart_table = chart_table.copy()
    # Rain is the total over a 3-hour window, so its bar sits in the middle of the window.
    chart_table["window_middle"] = chart_table["time_utc"] + timedelta(minutes=90)
    fig = px.bar(
        chart_table,
        x="window_middle",
        y="rain",
        title="Rain",
        labels={"window_middle": "Time (UTC)", "rain": "Rain (mm per 3 hours)"},
    )
    fig.update_traces(name="Mean of the providers", showlegend=True, marker_color="steelblue", opacity=0.4)
    # Each provider gives one total per window, so its line is flat from the window's start to its end.
    for _, row in provider_rows.iterrows():
        window_end = row["time_utc"] + timedelta(hours=3)
        fig.add_scatter(x=[row["time_utc"], window_end], y=[row["rain"], row["rain"]], mode="lines", name=row["source"])
    fig.update_layout(legend={"orientation": "h", "y": -0.25})
    # Rain is never negative: start the axis at 0, even when it stays dry.
    fig.update_yaxes(rangemode="nonnegative")
    add_session_lines(fig, chart_table, sessions)
    return fig


def race_weekend_rows(combined):
    """Keep only the windows of the 3 race days, so the charts match the sessions in the sidebar."""
    first_day = weekend_start()
    last_day = first_day + timedelta(days=3)
    return combined[(combined["time_utc"] >= first_day) & (combined["time_utc"] < last_day)]


# Free satellite pictures from Esri, in the same {z}/{x}/{y} tile form as the radar (Esri puts y before x).
SATELLITE_TILES = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"


# Both maps get the same height and no outer margin, so they line up side by side.
MAP_HEIGHT = 400
MAP_MARGIN = {"l": 0, "r": 0, "t": 0, "b": 0}


def show_track_map(track):
    """A satellite map zoomed in on the circuit, with a red dot on the track's point."""
    st.markdown("**Track**")
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
        height=MAP_HEIGHT,
    )
    fig.update_traces(marker={"size": 14, "color": "red"})
    fig.update_layout(
        margin=MAP_MARGIN,
        map_layers=[{"sourcetype": "raster", "source": [SATELLITE_TILES], "below": "traces", "sourceattribution": "Esri World Imagery"}],
    )
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


def choose_radar_frame():
    """A slider over the radar images of the last 2 hours; returns the chosen one, or None if there is no radar."""
    try:
        frames = fetch_radar_frames()
    except ValueError as error:
        st.warning(f"No rain radar right now: {error}")
        return None
    # The slider shows the image times; it starts on the newest one (the last in the list).
    times = [f"{frame['time_utc']:%H:%M}" for frame in frames]
    chosen_time = st.select_slider("Radar time (UTC)", options=times, value=times[-1])
    return frames[times.index(chosen_time)]


def show_radar(track, frame):
    """A map around the track with the chosen rain radar image laid over it."""
    st.markdown(f"**Rain radar at {frame['time_utc']:%H:%M} UTC**")
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
        height=MAP_HEIGHT,
    )
    # The radar is a picture made of map tiles; the map fills in {z}/{x}/{y} itself.
    # RainViewer's free images stop at their zoom 7. The map asks for one zoom level more detail
    # than it shows, so from map zoom 6.5 it would get grey "not supported" tiles: hide the radar there.
    fig.update_layout(margin=MAP_MARGIN, map_layers=[{"sourcetype": "raster", "source": [frame["url"]], "maxzoom": 6.5}])
    st.plotly_chart(fig)


def show_maps(track):
    """The satellite map of the circuit and the rain radar around it, side by side."""
    st.subheader("Track and rain radar")
    # The slider sits above both maps, so the two maps start at the same height.
    frame = choose_radar_frame()
    # Two maps: the satellite view shows the circuit itself, the radar shows the rain
    # around it. One map cannot do both, as the free radar stops before the track is visible.
    map_left, map_right = st.columns(2)
    with map_left:
        show_track_map(track)
    with map_right:
        if frame is not None:
            show_radar(track, frame)
    if frame is not None:
        st.caption("MVP preview using free APIs. On the final app both maps would be overlaid.")


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

    show_maps(track)


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
    st.caption("Note: MET Norway API is limited to 2.5 days.")


# Session dashboard (card 8): one session at a time, per provider and combined.


def previous_session():
    """Runs when Previous is pressed, before the page reruns."""
    st.session_state["session_index"] = st.session_state["session_index"] - 1


def next_session():
    """Runs when Next is pressed, before the page reruns."""
    st.session_state["session_index"] = st.session_state["session_index"] + 1


def session_chart(table, window, column, value, title):
    """Bar chart of one value: each provider's forecast, and the combined one with its 95% interval."""
    chart_rows = []
    for _, row in table.iterrows():
        chart_rows.append({"Forecast": row["Provider"], column: row[column], "Above": 0, "Below": 0})
    # The error bar on the combined bar goes from the low to the high end of the interval.
    # Up and down are kept apart, because the low end of rain and wind is never below 0.
    chart_rows.append({
        "Forecast": "Combined",
        column: window[value],
        "Above": window[value + "_high"] - window[value],
        "Below": window[value] - window[value + "_low"],
    })
    fig = px.bar(
        pd.DataFrame(chart_rows),
        x="Forecast",
        y=column,
        error_y="Above",
        error_y_minus="Below",
        title=title,
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

    # The weekend charts, cut to the session's 3-hour window. The next window's start is kept
    # too, so the temperature and wind lines run across the whole slot instead of being one dot.
    slot_start = rows["time_utc"].iloc[0]
    slot_end = slot_start + timedelta(hours=3)
    combined = combine_forecasts(table)
    slot_rows = combined[(combined["time_utc"] >= slot_start) & (combined["time_utc"] <= slot_end)]
    temperature_fig = temperature_chart(slot_rows, [session])
    rain_fig = rain_chart(slot_rows, [session], rows)
    wind_fig = wind_chart(slot_rows, [session])
    for fig in [temperature_fig, rain_fig, wind_fig]:
        fig.update_xaxes(range=[slot_start, slot_end])
    st.plotly_chart(temperature_fig)
    st.plotly_chart(rain_fig)
    st.caption("Flat forecast on each 3-hour window due to current API restrictions.")
    st.plotly_chart(wind_fig)

    st.subheader("Per provider detail")
    table = provider_table(rows)
    st.dataframe(table.round(1), hide_index=True)
    st.caption(f"Combined from {window['providers']} providers. Note: MET Norway API is limited to 2.5 days.")

    col1, col2, col3 = st.columns(3)
    col1.plotly_chart(session_chart(table, window, "Temperature (°C)", "temperature", "Temperature"))
    col2.plotly_chart(session_chart(table, window, "Rain (mm)", "rain", "Rain"))
    col3.plotly_chart(session_chart(table, window, "Wind (km/h)", "wind_kmh", "Wind"))


# History and Track comparison (card 5): both read the collector's logged history.


def history_track_names(history):
    """Return the ids of the tracks with enough logged history, and a dictionary from id to track name."""
    tracks = history[history["location_id"].notna()][["location_id", "location"]].drop_duplicates()
    track_ids = []
    for track_id in tracks["location_id"]:
        if days_logged(history, track_id) >= MIN_DAYS_LOGGED:
            track_ids.append(track_id)
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
    if days_logged(history, track_id) < MIN_DAYS_LOGGED:
        st.info("Not enough logged history for this track yet. Pick another track in the sidebar.")
        return

    daily = track_rain_history(history, track_id)
    rain_fig = px.line(daily, x="day", y="rain_mm", markers=True, title=f"{track_name}: daily rain")
    rain_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Rain (mm)")
    # Rain is never negative: start the axis at 0, even on a dry track where every day is 0 mm.
    rain_fig.update_yaxes(rangemode="nonnegative")
    st.plotly_chart(rain_fig)
    temperature = daily.rename(columns={"temperature_min_c": "Lowest", "temperature_max_c": "Highest"})
    temp_fig = px.line(temperature, x="day", y=["Lowest", "Highest"], markers=True, title=f"{track_name}: daily temperature range")
    temp_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature (°C)", legend_title_text="")
    temp_fig.update_traces(line_color="firebrick", marker_color="firebrick", selector={"name": "Highest"})
    st.plotly_chart(temp_fig)
    # Bars coloured from blue (a steady day) to red (a big swing between night and day).
    variation_fig = px.bar(
        daily,
        x="day",
        y="temperature_range_c",
        color="temperature_range_c",
        color_continuous_scale="Bluered",
        title="Daily temperature variability (highest − lowest)",
    )
    variation_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature range (°C)", coloraxis_colorbar_title="°C")
    st.plotly_chart(variation_fig)


def show_track_comparison(history):
    """Two to four tracks side by side over the days all of them were logged, ranked with sorted()."""
    st.subheader("Compare tracks")
    st.info(
        "**MVP preview.** The goal is to reconcile this historical weather with the team's own data "
        "(lap times, tyre type, tyre degradation, etc.) to run advanced analytics. "
        "Historical data may be incomplete for some tracks."
    )
    track_ids, track_names = history_track_names(history)
    if len(track_ids) < 2:
        st.info("Track comparison needs history for at least two tracks.")
        return
    # At most 4, so the cards and the grouped bars stay readable.
    chosen_ids = st.multiselect("Tracks to compare (2 to 4)", track_ids, default=track_ids[:2],
                                max_selections=4, format_func=lambda value: track_names[value])
    if len(chosen_ids) < 2:
        st.info("Pick at least two tracks to compare.")
        return
    # Only the period every chosen track was logged, so they are compared fairly.
    starts = []
    ends = []
    for track_id in chosen_ids:
        rows = history[history["location_id"] == track_id]
        starts.append(rows["timestamp_utc"].min())
        ends.append(rows["timestamp_utc"].max())
    start = max(starts)
    end = min(ends)
    if start > end:
        st.info("These tracks do not have history over the same period.")
        return
    shared = history[(history["location_id"].isin(chosen_ids)) & (history["timestamp_utc"] >= start) & (history["timestamp_utc"] <= end)].copy()
    # compare_track_history returns TrackSummary objects ranked with sorted() (wettest first).
    summaries = compare_track_history(shared, chosen_ids)
    # One column of cards per track, wettest on the left: the order comes from sorted().
    columns = st.columns(len(summaries))
    for column, summary in zip(columns, summaries):
        column.markdown(f"**{summary.location}**")
        column.metric("Average temperature", f"{summary.average_temperature_c:.1f} °C")
        column.metric("Rain days", summary.rain_days)
        column.metric("Total rain", f"{summary.total_rain_mm:.1f} mm")
        column.caption(f"Over {summary.days_logged} logged days")
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
    # Rain is never negative: start the axis at 0, even on a dry track where every day is 0 mm.
    rain_fig.update_yaxes(rangemode="nonnegative")
    st.plotly_chart(rain_fig)

    # The same daily range (highest − lowest) as the History page, one track at a time, then stacked.
    ranges = []
    for track_id in chosen_ids:
        daily = track_rain_history(shared, track_id)
        daily["location"] = track_names[track_id]
        ranges.append(daily)
    range_compare = pd.concat(ranges)
    range_fig = px.bar(range_compare, x="day", y="temperature_range_c", color="location", barmode="group",
                       title="Daily temperature variability comparison (highest − lowest)")
    range_fig.update_layout(xaxis_title="Day (UTC)", yaxis_title="Temperature range (°C)", legend_title_text="")
    st.plotly_chart(range_fig)


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
    show_history(history, selected_track)


def comparison_page():
    """The Track comparison page, read from the collector's logged history."""
    history = load_history()
    if len(history) == 0:
        st.info("No logged history yet.")
        return
    show_track_comparison(history)


pages = [
    st.Page(weekend_page, title="Weekend overview", default=True),
    st.Page(session_page, title="Session dashboard", url_path="session-dashboard"),
    st.Page(history_page, title="History", url_path="history"),
    st.Page(comparison_page, title="Track comparison", url_path="track-comparison"),
]
st.navigation(pages, position="top").run()
