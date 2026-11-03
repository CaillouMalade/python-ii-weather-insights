"""The page: circuit cards in the sidebar, then the Today and History views."""

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import cards
from .config import SETUP_MESSAGE
from .display import format_local_time
from .fetching import fetch_radar_image, fetch_wind_grid, now_seconds
from .forecast import STEP_HOURS, calm_clouds, next_three_hours, rain_timing, status_lights, today_high_low
from .history import circuit_readings, daily, daily_extremes, hourly, rain_finding, temperature_finding, wind_finding
from .maps import radar_figure, wind_figure
from .storage import load_history, load_track

# The same tokens as style.py. Red only ever means rain.
TEXT = "#E8EDEA"
MUTED = "#8A948F"
BORDER = "#242A27"
RED = "#E5484D"
SURFACE = "#161A18"
CLOUD_BAND = "rgba(138, 148, 143, 0.12)"


def panel_title(title):
    st.html(f'<div class="label">{title}</div>')


def show_finding(text):
    st.html(f'<div class="finding">{escape(text)}</div>')


def show_chart(fig, y_title, y2_title=None):
    """Show a Plotly figure with the shared look. A second axis, if any, is a 0-100 % scale."""
    axis = dict(gridcolor=BORDER, zeroline=False, linecolor=BORDER)
    # theme=None below: Streamlit's own chart theme would replace these colours.
    fig.update_layout(
        template="plotly_dark",
        yaxis_title=y_title,
        xaxis=axis,
        yaxis=axis,
        height=260,
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom"),
        hovermode="x unified",
        font=dict(color=MUTED),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font_color=TEXT),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    if y2_title is not None:
        fig.update_layout(yaxis2=dict(title=y2_title, overlaying="y", side="right", range=[0, 100], tickvals=[0, 50, 100], showgrid=False, zeroline=False))
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False})


def local_today(loaded):
    return format_local_time(now_seconds(), loaded["reading"].timezone_offset or 0, "%Y-%m-%d")


def lights_for(loaded):
    """The three status lights of a loaded circuit, all unlit without a forecast."""
    if loaded["windows"] is None:
        return [None, None, None]
    return status_lights(loaded["windows"], now_seconds(), local_today(loaded))


@st.cache_data(show_spinner=False)
def circuit_track(track_file):
    """The outline's segments, read once per file: they never change while the app runs."""
    return load_track(track_file)


# Sidebar


def select_circuit(circuit_id):
    st.session_state["selected"] = circuit_id


def phone_circuit_changed():
    st.session_state["selected"] = st.session_state["phone_circuit"]


def show_sidebar(loaded_circuits, selected_id, now):
    for number in range(len(loaded_circuits)):
        loaded = loaded_circuits[number]
        circuit = loaded["circuit"]
        next_hours = lights_for(loaded)[1]
        # An invisible button lies over the card (see style.py), so the whole card is tappable.
        with st.sidebar.container(key=f"circuit-{number}"):
            st.html(cards.circuit_card(circuit, loaded["reading"], next_hours, loaded["note"], circuit["id"] == selected_id, now))
            st.button(f"Open {circuit['location']}", key=f"open-{number}", on_click=select_circuit, args=(circuit["id"],))
    st.sidebar.html('<div class="credit">OpenWeatherMap · RainViewer</div>')


def show_phone_picker(circuits, selected_id):
    """Only visible on narrow screens (see style.py), where the sidebar starts closed."""
    names = {}
    for circuit in circuits:
        names[circuit["id"]] = circuit["location"]
    st.session_state["phone_circuit"] = selected_id
    with st.container(key="phone-circuit"):
        st.selectbox("Circuit", list(names.keys()), format_func=lambda circuit_id: names[circuit_id], key="phone_circuit", on_change=phone_circuit_changed, label_visibility="collapsed")


# Today


def show_trend(windows):
    """Temperature as the line, cloud cover as a quiet smoothed band behind it."""
    fig = go.Figure()
    fig.add_scatter(x=windows["end"], y=calm_clouds(windows), name="Cloud cover", yaxis="y2", fill="tozeroy", mode="lines", line=dict(width=0, shape="spline", smoothing=1.3), fillcolor=CLOUD_BAND)
    fig.add_scatter(x=windows["end"], y=windows["temperature"], name="Temperature", mode="lines", line=dict(color=TEXT, width=2))
    with st.container(key="panel-trend"):
        show_chart(fig, "°C", "Cloud %")


def show_radar(circuit, radar):
    panel_title("Rain radar")
    if radar is None:
        st.warning("Radar unavailable.")
        return
    fig = radar_figure(radar["uri"], radar["bounds"], circuit, circuit_track(circuit["track_file"]))
    st.plotly_chart(fig, config={"displayModeBar": False})


def show_wind(circuit):
    panel_title("Wind")
    with st.spinner("Loading wind"):
        points = fetch_wind_grid(circuit["latitude"], circuit["longitude"])
    if len(points) == 0:
        st.warning("Wind unavailable.")
        return
    st.plotly_chart(wind_figure(points, circuit, circuit_track(circuit["track_file"])), config={"displayModeBar": False})
    st.html(cards.wind_legend())


def show_maps(circuit, radar):
    with st.container(key="maps"):
        radar_column, wind_column = st.columns(2)
        with radar_column:
            with st.container(key="panel-radar"):
                show_radar(circuit, radar)
        with wind_column:
            with st.container(key="panel-wind"):
                show_wind(circuit)


def show_precipitation(windows):
    """Rain and snow per 3-hour window as bars, and the chance of rain as a line."""
    labels = [f"{start.strftime('%a %H:%M')}–{end.strftime('%H:%M')}" for start, end in zip(windows["start"], windows["end"])]
    middles = windows["start"] + pd.to_timedelta(STEP_HOURS / 2, unit="h")
    width = STEP_HOURS * 3600 * 1000
    fig = go.Figure()
    fig.add_bar(x=middles, y=windows["rain_3h"], width=width, name="Rain", marker_color=RED, hovertext=labels)
    if windows["snow_3h"].sum() > 0:
        fig.add_bar(x=middles, y=windows["snow_3h"], width=width, name="Snow", marker_color=MUTED, hovertext=labels)
    fig.add_scatter(x=middles, y=windows["pop"] * 100, name="Chance", yaxis="y2", mode="lines", line=dict(color=MUTED, width=1.5, dash="dot"))
    # Without a fixed range, a dry forecast would draw its 0 mm axis in the middle.
    fig.update_layout(barmode="stack", yaxis_range=[0, max(1, windows["precipitation_mm"].max() * 1.2)])
    with st.container(key="panel-rain"):
        panel_title("Rain per 3 hours")
        show_chart(fig, "mm", "Chance %")


def show_today(loaded):
    circuit = loaded["circuit"]
    reading = loaded["reading"]
    if reading is None:
        st.warning(SETUP_MESSAGE if loaded["note"] == "Needs an API key" else f"{circuit['location']}: {loaded['note']}")
        return

    windows = loaded["windows"]
    offset = reading.timezone_offset or 0
    now = now_seconds()
    high = reading.temp_max if reading.temp_max is not None else reading.temperature
    low = reading.temp_min if reading.temp_min is not None else reading.temperature
    rain_chance = None
    if windows is not None:
        high, low = today_high_low(windows, local_today(loaded), high, low)
        rain_chance = next_three_hours(windows, now)["pop"].max()
    st.html(cards.header(circuit, reading, high, low, rain_chance, now))

    radar = None
    try:
        with st.spinner("Loading radar"):
            radar = fetch_radar_image(circuit["latitude"], circuit["longitude"])
    except ValueError:
        radar = None

    if windows is None:
        st.warning(f"Forecast unavailable. {loaded['note']}")
    else:
        st.html(cards.status_strip(lights_for(loaded), rain_timing(windows, now), cards.radar_text(radar, offset)))
        show_trend(windows)
    show_maps(circuit, radar)
    if windows is not None:
        show_precipitation(windows)


# History


def show_temperature_history(values, full_days):
    highs, lows = daily_extremes(values, full_days)
    fig = go.Figure()
    fig.add_scatter(x=values["time"], y=values["temperature_c"], name="Hourly", mode="lines", line=dict(color=TEXT, width=1.5))
    fig.add_scatter(x=highs["time"], y=highs["temperature_c"], name="Daily high", mode="markers", marker=dict(color=TEXT, size=8))
    fig.add_scatter(x=lows["time"], y=lows["temperature_c"], name="Daily low", mode="markers", marker=dict(color="rgba(0,0,0,0)", size=8, line=dict(color=TEXT, width=1.5)))
    with st.container(key="panel-history-temperature"):
        show_finding(temperature_finding(highs, lows))
        show_chart(fig, "°C")


def show_rain_history(days):
    """Only the sentence when it never rained; otherwise rainy hours per day, in red."""
    with st.container(key="panel-history-rain"):
        show_finding(rain_finding(days))
        if days["rain_hours"].sum() == 0:
            return
        fig = go.Figure()
        fig.add_bar(x=pd.to_datetime(days["day"]), y=days["rain_hours"], name="Hours with rain", marker_color=RED)
        # Whole hours only, with about four ticks.
        fig.update_layout(showlegend=False, yaxis_dtick=max(1, round(days["rain_hours"].max() / 4)))
        show_chart(fig, "Hours with rain")


def show_wind_history(values, readings):
    fig = go.Figure()
    fig.add_scatter(x=values["time"], y=values["wind_kmh"], name="Wind", mode="lines", line=dict(color=TEXT, width=1.5))
    with st.container(key="panel-history-wind"):
        show_finding(wind_finding(readings))
        show_chart(fig, "km/h")


def show_history(circuit):
    history = load_history()
    readings = pd.DataFrame()
    if len(history) > 0:
        readings = circuit_readings(history, circuit["id"], circuit["timezone"])
    if len(readings) == 0:
        st.info(f"No collected history for {circuit['location']} yet.")
        return

    values = hourly(readings)
    days = daily(values)
    show_temperature_history(values, days[days["full"]]["day"].to_list())
    show_rain_history(days)
    show_wind_history(values, readings)
