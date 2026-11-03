"""The page: circuit cards in the sidebar, then the Today and History views."""

from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from . import cards
from .config import SETUP_MESSAGE
from .display import format_local_time
from .fetching import fetch_forecast, fetch_radar_image, fetch_wind_grid, now_seconds
from .forecast import STEP_HOURS, forecast_windows, rain_timing, today_high_low, upcoming
from .history import circuit_readings, coverage_text, daily, daily_extremes, gaps, hourly, rain_finding, temperature_finding, wind_finding
from .maps import radar_figure, wind_figure
from .storage import load_history

TEMPERATURE_COLOR = "#ffb86b"
CLOUD_COLOR = "rgba(200, 210, 222, 0.35)"
RAIN_COLOR = "#7fd0f5"
SNOW_COLOR = "#e8eef5"
DATA_COLOR = "rgba(255, 255, 255, 0.12)"
WIND_COLOR = "#6fd3a0"


def panel_title(title, aside=""):
    """A card's title, with an optional quiet note on the right, such as a time."""
    st.html(f'<div class="card-title">{title}<span>{aside}</span></div>')


def show_chart(fig, y_title, y2_title=None):
    """Show a Plotly figure with the shared look. A second axis, if any, is a 0-100 % scale."""
    fig.update_layout(
        yaxis_title=y_title,
        height=280,
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom"),
        hovermode="x unified",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    if y2_title is not None:
        fig.update_layout(yaxis2=dict(title=y2_title, overlaying="y", side="right", range=[0, 100], tickvals=[0, 25, 50, 75, 100], showgrid=False))
    st.plotly_chart(fig, config={"displayModeBar": False})


# Sidebar


def select_circuit(circuit_id):
    st.session_state["selected"] = circuit_id


def phone_circuit_changed():
    st.session_state["selected"] = st.session_state["phone_circuit"]


def show_sidebar(current_by_circuit, selected_id, now):
    for number in range(len(current_by_circuit)):
        current = current_by_circuit[number]
        circuit = current["circuit"]
        # An invisible button lies over the card (see style.py), so the whole card is tappable.
        with st.sidebar.container(key=f"city-{number}"):
            st.html(cards.circuit_card(circuit, current["reading"], current["note"], circuit["id"] == selected_id, now))
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
    fig = go.Figure()
    fig.add_scatter(x=windows["end"], y=windows["clouds"], name="Cloud cover", yaxis="y2", fill="tozeroy", mode="none", fillcolor=CLOUD_COLOR)
    fig.add_scatter(x=windows["end"], y=windows["temperature"], name="Temperature", mode="lines", line=dict(color=TEMPERATURE_COLOR, width=2.5))
    with st.container(key="panel-trend"):
        panel_title("Next 5 days")
        show_chart(fig, "°C", "Cloud cover %")


def show_radar(circuit, offset):
    """The radar map, with the time of the radar image in its title."""
    try:
        with st.spinner("Loading radar"):
            result = fetch_radar_image(circuit["latitude"], circuit["longitude"])
    except ValueError as e:
        panel_title("Rain radar")
        st.warning(f"Radar unavailable. {e}")
        return
    time_text = "" if result["time"] is None else format_local_time(result["time"], offset)
    panel_title("Rain radar", time_text)
    st.plotly_chart(radar_figure(result["uri"], result["bounds"], circuit["latitude"], circuit["longitude"]), config={"displayModeBar": False})
    if result["covered"] is False:
        st.html('<div class="small">No radar coverage here</div>')
    if result["missing"] > 0:
        st.html(f'<div class="small">{result["missing"]} radar tiles missing</div>')


def show_wind(circuit):
    with st.spinner("Loading wind"):
        points, missing = fetch_wind_grid(circuit["latitude"], circuit["longitude"])
    panel_title("Wind")
    if len(points) == 0:
        st.warning("Wind unavailable.")
        return
    st.plotly_chart(wind_figure(points, circuit["latitude"], circuit["longitude"]), config={"displayModeBar": False})
    st.html(cards.wind_legend())
    if missing > 0:
        st.html(f'<div class="small">{missing} of {missing + len(points)} points missing</div>')


def show_maps(circuit, offset):
    with st.container(key="maps"):
        radar_column, wind_column = st.columns(2)
        with radar_column:
            with st.container(key="panel-radar"):
                show_radar(circuit, offset)
        with wind_column:
            with st.container(key="panel-wind"):
                show_wind(circuit)


def show_precipitation(windows, now, fetched_text):
    """Rain and snow per 3-hour window as bars, the chance of rain as a line, and the timing sentence."""
    labels = [f"{start.strftime('%a %H:%M')}–{end.strftime('%H:%M')}" for start, end in zip(windows["start"], windows["end"])]
    middles = windows["start"] + pd.to_timedelta(STEP_HOURS / 2, unit="h")
    width = STEP_HOURS * 3600 * 1000
    fig = go.Figure()
    fig.add_bar(x=middles, y=windows["rain_3h"], width=width, name="Rain", marker_color=RAIN_COLOR, hovertext=labels)
    if windows["snow_3h"].sum() > 0:
        fig.add_bar(x=middles, y=windows["snow_3h"], width=width, name="Snow", marker_color=SNOW_COLOR, hovertext=labels)
    fig.add_scatter(x=middles, y=windows["pop"] * 100, name="Chance", yaxis="y2", mode="lines", line=dict(color="#ffffff", width=1.5, dash="dot"))
    # Without a fixed range, a dry forecast would draw its 0 mm axis in the middle.
    fig.update_layout(barmode="stack", yaxis=dict(range=[0, max(1, windows["precipitation_mm"].max() * 1.2)]))
    with st.container(key="panel-rain"):
        panel_title("Rain and snow per 3 hours", f"Forecast {fetched_text}")
        st.html(f'<div class="finding">{escape(rain_timing(windows, now))}</div>')
        show_chart(fig, "mm", "Chance %")


def show_today(current):
    circuit = current["circuit"]
    reading = current["reading"]
    if reading is None:
        st.warning(SETUP_MESSAGE if current["note"] == "Needs an API key" else f"{circuit['location']}: {current['note']}")
        return

    offset = reading.timezone_offset or 0
    now = now_seconds()
    high = reading.temp_max if reading.temp_max is not None else reading.temperature
    low = reading.temp_min if reading.temp_min is not None else reading.temperature
    windows = None
    rain_chance = None
    try:
        forecast = fetch_forecast(circuit["latitude"], circuit["longitude"])
        windows = upcoming(forecast_windows(pd.DataFrame(forecast["steps"]), offset), now)
        if len(windows) == 0:
            raise ValueError("It has no time left.")
        high, low = today_high_low(windows, format_local_time(now, offset, "%Y-%m-%d"), high, low)
        rain_chance = windows["pop"].to_list()[0]
    except ValueError as e:
        st.warning(f"Forecast unavailable. {e}")

    st.html(cards.header(circuit, reading, high, low, rain_chance, now))
    if windows is not None:
        show_trend(windows)
    show_maps(circuit, offset)
    if windows is not None:
        show_precipitation(windows, now, format_local_time(forecast["fetched_at"], offset))


# History


def show_temperature_history(values, full_days):
    highs, lows = daily_extremes(values, full_days)
    fig = go.Figure()
    fig.add_scatter(x=values["time"], y=values["temperature_c"], name="Hourly", mode="lines", line=dict(color=TEMPERATURE_COLOR, width=2))
    fig.add_scatter(x=highs["time"], y=highs["temperature_c"], name="Daily high", mode="markers", marker=dict(color="#ff7a59", size=9))
    fig.add_scatter(x=lows["time"], y=lows["temperature_c"], name="Daily low", mode="markers", marker=dict(color=RAIN_COLOR, size=9))
    with st.container(key="panel-history-temperature"):
        panel_title("Temperature")
        st.html(f'<div class="finding">{escape(temperature_finding(highs, lows))}</div>')
        show_chart(fig, "°C")


def show_rain_history(days):
    dates = pd.to_datetime(days["day"])
    fig = go.Figure()
    fig.add_bar(x=dates, y=days["hours"], name="Hours with data", marker_color=DATA_COLOR)
    fig.add_bar(x=dates, y=days["rain_hours"], name="Hours with rain", marker_color=RAIN_COLOR)
    fig.update_layout(barmode="overlay", yaxis=dict(range=[0, 24], tickvals=[0, 6, 12, 18, 24]))
    with st.container(key="panel-history-rain"):
        panel_title("Rain")
        st.html(f'<div class="finding">{escape(rain_finding(days))}</div>')
        show_chart(fig, "Hours")


def show_wind_history(values, readings):
    fig = go.Figure()
    fig.add_scatter(x=values["time"], y=values["wind_kmh"], name="Wind", mode="lines", line=dict(color=WIND_COLOR, width=2))
    fig.add_scatter(x=values["time"], y=values["gust_kmh"], name="Gusts", mode="lines", line=dict(color=WIND_COLOR, width=1, dash="dot"))
    with st.container(key="panel-history-wind"):
        panel_title("Wind")
        st.html(f'<div class="finding">{escape(wind_finding(readings))}</div>')
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
    st.html(f'<div class="small history-span">{escape(coverage_text(readings, gaps(readings)))}</div>')
    show_temperature_history(values, days[days["full"]]["day"].to_list())
    show_rain_history(days)
    show_wind_history(values, readings)
