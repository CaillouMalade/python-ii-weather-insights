"""The page: the track picker, my sessions in the sidebar, then the Today and History views."""

from datetime import time
from html import escape

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from . import cards
from .config import SETUP_MESSAGE
from .display import format_local_time
from .fetching import fetch_radar_image, fetch_wind_grid, now_seconds
from .forecast import RAIN_LIKELY, STEP_HOURS, calm_clouds, rain_timing, status_lights, today_high_low
from .history import circuit_readings, daily, daily_extremes, hourly, rain_finding, temperature_finding, wind_finding
from .maps import circuit_bounds, radar_figure, wind_field, wind_figure, wind_grid_bounds, wind_grid_points
from .sessions import add_default_weekend, check_session, session_status, session_times
from .storage import load_history, load_sessions, load_track, save_sessions

# The same tokens as style.py. Red only ever means rain; green marks the selection.
TEXT = "#E8EDEA"
MUTED = "#8A948F"
BORDER = "#242A27"
SURFACE = "#161A18"
RED = "#E5484D"
RED_UNLIKELY = "rgba(229, 72, 77, 0.35)"
CLOUD_BAND = "rgba(138, 148, 143, 0.12)"
SESSION_BAND = "rgba(47, 210, 122, 0.12)"
ONE_DAY_MS = 24 * 3600 * 1000


@st.cache_data(show_spinner=False)
def circuit_track(track_file):
    """The outline's segments, read once per file: they never change while the app runs."""
    return load_track(track_file)


def local_now(circuit):
    """The time at the track now, without a zone, to compare with forecast and session times."""
    return pd.Timestamp.now(tz=circuit["timezone"]).tz_localize(None)


# Track picker


def chosen_track(circuits):
    """The selected circuit id: from the address (?track=spa), else this session, else the first.
    It is written back to both, so a reload or a bookmark keeps it."""
    ids = [circuit["id"] for circuit in circuits]
    track = st.query_params.get("track")
    if track not in ids:
        track = st.session_state.get("track")
    if track not in ids:
        track = ids[0]
    st.session_state["track"] = track
    st.query_params["track"] = track
    return track


def track_changed():
    st.query_params["track"] = st.session_state["track"]
    st.session_state["session"] = None


def show_track_picker(circuits):
    names = {}
    for circuit in circuits:
        names[circuit["id"]] = circuit["location"]
    st.selectbox("Track", list(names.keys()), format_func=lambda track: names[track], key="track", on_change=track_changed, label_visibility="collapsed", width=320)


# Sessions (sidebar)


def toggle_session(index):
    """Tapping a row selects it (its band shows on the charts) and opens it for editing."""
    st.session_state["session"] = None if st.session_state.get("session") == index else index


def form_session(track, prefix):
    """A checked session from a form's inputs. Raises ValueError with a clear message."""
    values = st.session_state
    return check_session(track, values[f"{prefix}-name"], values[f"{prefix}-day"], values[f"{prefix}-start"], values[f"{prefix}-end"])


def add_session(track):
    try:
        new = form_session(track, "add")
    except ValueError as e:
        st.session_state["session_error"] = str(e)
        return
    sessions = load_sessions()
    sessions.append(new)
    save_sessions(sessions)
    st.session_state["add-name"] = ""


def save_session(index, track):
    try:
        changed = form_session(track, f"edit-{index}")
    except ValueError as e:
        st.session_state["session_error"] = str(e)
        return
    sessions = load_sessions()
    sessions[index] = changed
    save_sessions(sessions)
    st.session_state["session"] = None


def delete_session(index):
    sessions = load_sessions()
    sessions.pop(index)
    save_sessions(sessions)
    st.session_state["session"] = None


def use_default_weekend(circuit):
    save_sessions(add_default_weekend(load_sessions(), circuit["id"], local_now(circuit)))


def session_inputs(prefix, name, day, start, end):
    """The four inputs every session form has. Labels are hidden: each value says what it is."""
    st.text_input("Name", value=name, key=f"{prefix}-name", placeholder="Name", label_visibility="collapsed")
    st.date_input("Day", value=day, key=f"{prefix}-day", label_visibility="collapsed")
    start_column, end_column = st.columns(2)
    start_column.time_input("Start", value=start, step=900, key=f"{prefix}-start", label_visibility="collapsed")
    end_column.time_input("End", value=end, step=900, key=f"{prefix}-end", label_visibility="collapsed")


def show_edit_form(index, session, track):
    start, end = session_times(session)
    with st.sidebar.form(f"edit-{index}", border=False):
        session_inputs(f"edit-{index}", session["name"], start.date(), start.time(), end.time())
        save_column, delete_column = st.columns(2)
        save_column.form_submit_button("Save", on_click=save_session, args=(index, track))
        delete_column.form_submit_button("Delete", on_click=delete_session, args=(index,))


def show_sessions(loaded):
    """My sessions at the selected track, then the add form. Returns the selected session, or None."""
    circuit = loaded["circuit"]
    track = circuit["id"]
    sessions = load_sessions()
    mine = []
    for index in range(len(sessions)):
        if sessions[index]["track"] == track:
            mine.append(index)
    mine = sorted(mine, key=lambda index: (sessions[index]["day"], sessions[index]["start"]))

    selected = None
    for index in mine:
        session = sessions[index]
        if st.session_state.get("session") == index:
            selected = session
            show_edit_form(index, session, track)
            continue
        state, chance = None, None
        if loaded["windows"] is not None:
            state, chance = session_status(loaded["windows"], session)
        # An invisible button lies over the row (see style.py), so the whole row is tappable.
        with st.sidebar.container(key=f"session-{index}"):
            st.html(cards.session_row(session, state, chance))
            st.button(f"Edit {session['name']}", key=f"open-{index}", on_click=toggle_session, args=(index,))

    with st.sidebar.form("add-session", border=False):
        session_inputs("add", "", local_now(circuit).date(), time(9, 0), time(10, 0))
        st.form_submit_button("Add", on_click=add_session, args=(track,))
    st.sidebar.button("Use default weekend", on_click=use_default_weekend, args=(circuit,))
    if "session_error" in st.session_state:
        st.sidebar.error(st.session_state.pop("session_error"))
    return selected


# Charts


def style_figure(fig, height):
    """The shared chart look: no gridlines, a faint baseline, day names on the time axis, no legend."""
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=0, r=0, t=4, b=0),
        showlegend=False,
        hovermode="x unified",
        font=dict(color=MUTED),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=BORDER, font_color=TEXT),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(showgrid=False, zeroline=False, tickformat="%a", dtick=ONE_DAY_MS, ticklabelmode="period", hoverformat="%a %H:%M", showline=True, linecolor=BORDER)
    fig.update_yaxes(showgrid=False, zeroline=False, nticks=3)


def show_figure(fig):
    # theme=None: Streamlit's own chart theme would replace these colours.
    st.plotly_chart(fig, theme=None, config={"displayModeBar": False})


def label_points(fig, rows, above, row=None):
    """Write each point's temperature next to it, such as 15°, above or below the line."""
    for point in rows.to_dict("records"):
        fig.add_annotation(x=point["x"], y=point["y"], text=f"{round(point['y'])}°", showarrow=False, yshift=11 if above else -11, font=dict(color=TEXT, size=11), row=row, col=1 if row else None)


def daily_high_low_points(times, temperatures):
    """The highest and lowest point of each local day, as two tables with x and y."""
    out = pd.DataFrame({"x": times, "y": temperatures})
    out["day"] = out["x"].dt.strftime("%Y-%m-%d")
    highs = out.sort_values("y", ascending=False).drop_duplicates(subset="day", keep="first")
    lows = out.sort_values("y").drop_duplicates(subset="day", keep="first")
    return highs, lows


def forecast_figure(windows, session):
    """Temperature over a faint cloud band, and rain per 3-hour window below, on one time axis.

    Rain bars are red when rain is likely (the status rule) and faint red when it is not.
    The selected session, if any, shows as a band across both.
    """
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.62, 0.38], vertical_spacing=0.08, specs=[[{"secondary_y": True}], [{}]])
    fig.add_scatter(x=windows["end"], y=calm_clouds(windows), fill="tozeroy", mode="lines", line=dict(width=0, shape="spline", smoothing=1.3), fillcolor=CLOUD_BAND, hoverinfo="skip", row=1, col=1, secondary_y=True)
    fig.add_scatter(x=windows["end"], y=windows["temperature"], mode="lines", line=dict(color=TEXT, width=2), hovertemplate="%{y:.0f}°<extra></extra>", row=1, col=1)

    highs, lows = daily_high_low_points(windows["end"], windows["temperature"])
    label_points(fig, highs, True, row=1)
    label_points(fig, lows, False, row=1)

    middles = windows["start"] + pd.to_timedelta(STEP_HOURS / 2, unit="h")
    colors = [RED if pop >= RAIN_LIKELY else RED_UNLIKELY for pop in windows["pop"]]
    chances = windows["pop"] * 100
    fig.add_bar(x=middles, y=windows["rain_3h"], width=STEP_HOURS * 3600 * 1000, marker_color=colors, customdata=chances, hovertemplate="%{y:.1f} mm · %{customdata:.0f} %<extra></extra>", row=2, col=1)
    if windows["snow_3h"].sum() > 0:
        fig.add_bar(x=middles, y=windows["snow_3h"], width=STEP_HOURS * 3600 * 1000, marker_color=MUTED, hovertemplate="%{y:.1f} mm snow<extra></extra>", row=2, col=1)

    if session is not None:
        start, end = session_times(session)
        fig.add_vrect(x0=start, x1=end, fillcolor=SESSION_BAND, line_width=0, row="all", col=1)

    style_figure(fig, 340)
    # Temperature is read from its labels, so its axis has no ticks; the cloud band has no axis at all.
    fig.update_yaxes(visible=False, row=1, col=1)
    fig.update_yaxes(visible=False, range=[0, 100], row=1, col=1, secondary_y=True)
    fig.update_layout(barmode="stack")
    # Without a fixed range, a dry forecast would draw its 0 mm baseline in the middle.
    fig.update_yaxes(range=[0, max(1, windows["precipitation_mm"].max() * 1.2)], ticksuffix=" mm", row=2, col=1)
    fig.update_xaxes(showline=False, row=1, col=1)
    return fig


# Today


def show_maps(circuit, radar):
    segments = circuit_track(circuit["track_file"])
    with st.container(key="panel-maps"):
        radar_column, wind_column = st.columns(2)
        with radar_column:
            if radar is None:
                st.warning("Radar unavailable.")
            else:
                st.plotly_chart(radar_figure(radar["uri"], radar["bounds"], circuit, segments), config={"displayModeBar": False})
        with wind_column:
            area = circuit_bounds(circuit, segments)
            grid_bounds = wind_grid_bounds(area)
            with st.spinner("Loading wind"):
                readings = fetch_wind_grid(wind_grid_points(grid_bounds))
            if readings.count(None) == len(readings):
                st.warning("Wind unavailable.")
            else:
                st.plotly_chart(wind_figure(wind_field(readings, grid_bounds, area), circuit, segments), config={"displayModeBar": False})


def show_today(loaded, session):
    circuit = loaded["circuit"]
    reading = loaded["reading"]
    if reading is None:
        st.warning(SETUP_MESSAGE if loaded["note"] == "Needs an API key" else f"{circuit['location']}: {loaded['note']}")
        return

    windows = loaded["windows"]
    now = now_seconds()
    today = format_local_time(now, reading.timezone_offset or 0, "%Y-%m-%d")
    high = reading.temp_max if reading.temp_max is not None else reading.temperature
    low = reading.temp_min if reading.temp_min is not None else reading.temperature

    radar = None
    try:
        with st.spinner("Loading radar"):
            radar = fetch_radar_image(circuit["latitude"], circuit["longitude"])
    except ValueError:
        radar = None

    if windows is None:
        states = [None, None, None]
        sentence = f"Forecast unavailable. {loaded['note']}"
    else:
        high, low = today_high_low(windows, today, high, low)
        states = status_lights(windows, now, today)
        sentence = rain_timing(windows, now)
    with st.container(key="panel-now"):
        st.html(cards.now_group(reading, high, low, now, states, sentence, cards.radar_problem(radar)))
    if windows is not None:
        with st.container(key="panel-forecast"):
            show_figure(forecast_figure(windows, session))
    show_maps(circuit, radar)


# History


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
    highs, lows = daily_extremes(values, days[days["full"]]["day"].to_list())
    with st.container(key="panel-history"):
        st.html(f'<div class="finding">{escape(temperature_finding(highs, lows))}</div>')
        fig = go.Figure()
        fig.add_scatter(x=values["time"], y=values["temperature_c"], mode="lines", line=dict(color=TEXT, width=1.5), hovertemplate="%{y:.0f}°<extra></extra>")
        label_points(fig, highs.rename(columns={"time": "x", "temperature_c": "y"}), True)
        label_points(fig, lows.rename(columns={"time": "x", "temperature_c": "y"}), False)
        style_figure(fig, 220)
        fig.update_yaxes(visible=False)
        show_figure(fig)

        st.html(f'<div class="finding">{escape(rain_finding(days))}</div>')
        if days["rain_hours"].sum() > 0:
            fig = go.Figure()
            fig.add_bar(x=pd.to_datetime(days["day"]) + pd.to_timedelta(12, unit="h"), y=days["rain_hours"], marker_color=RED, hovertemplate="%{y} h<extra></extra>")
            style_figure(fig, 160)
            # Whole hours only, with about four ticks.
            fig.update_yaxes(ticksuffix=" h", dtick=max(1, round(days["rain_hours"].max() / 4)))
            show_figure(fig)

        st.html(f'<div class="finding">{escape(wind_finding(readings))}</div>')
        fig = go.Figure()
        fig.add_scatter(x=values["time"], y=values["wind_kmh"], mode="lines", line=dict(color=TEXT, width=1.5), hovertemplate="%{y:.0f} km/h<extra></extra>")
        style_figure(fig, 200)
        fig.update_yaxes(ticksuffix=" km/h")
        show_figure(fig)


def show_credits():
    """The sources that have no credit on the maps, in one quiet line at the foot of the page."""
    st.html('<div class="credit">OpenWeatherMap · RainViewer · f1-circuits (MIT)</div>')
