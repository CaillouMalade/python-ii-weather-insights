"""The Weather tab: header, next hours, forecast and map, then details."""

import pandas as pd
import streamlit as st

from . import cards
from .analytics import next_steps, pressure_tendency
from .config import SETUP_MESSAGE
from .display import format_local_time
from .fetching import fetch_air_now, fetch_map_image, fetch_uv, now_seconds
from .maps import MAP_LAYERS, build_map_figure

# The current reading plus seven forecast steps fill the eight columns of the strip.
FORECAST_STEPS_SHOWN = 7


def show_next_hours(weather):
    reading = weather["reading"]
    with st.container(key="next-hours"):
        st.html('<div class="card-title">Next hours</div>')
        measure = st.segmented_control("Measure", ["Temperature", "Precipitation", "Wind"], default="Temperature", required=True, key="measure", label_visibility="collapsed")
        steps = next_steps(weather["steps"], now_seconds(), FORECAST_STEPS_SHOWN)
        st.html(cards.next_hours_strip(steps, reading.timezone_offset or 0, measure, reading))


def show_daily(weather):
    days = weather["days"]
    today = format_local_time(now_seconds(), weather["reading"].timezone_offset or 0, "%Y-%m-%d")
    day_names = []
    for date in days["local_date"].to_list():
        if date == today:
            day_names.append("Today")
        else:
            day_names.append(pd.to_datetime(date).strftime("%a"))
    with st.container(key="daily-card"):
        st.html(cards.daily_card(days, today, day_names, weather["reading"].temperature))


def show_map(weather):
    location = weather["location"]
    with st.container(key="map-card"):
        st.html('<div class="card-title">Weather map</div>')
        layer = st.selectbox("Layer", list(MAP_LAYERS.keys()), key="map_layer", label_visibility="collapsed")
        image_uri, bounds, missing = fetch_map_image(MAP_LAYERS[layer], location["latitude"], location["longitude"])
        fig = build_map_figure(image_uri, bounds, location["latitude"], location["longitude"])
        st.plotly_chart(fig, config={"displayModeBar": False})
        if missing > 0:
            st.warning(f"{missing} map tiles could not be loaded, so part of this layer is missing.")
        st.caption("Weather layers © OpenWeatherMap")


def show_details(weather):
    location = weather["location"]
    steps = weather["steps"]

    air_row = None
    try:
        air_rows = fetch_air_now(location["latitude"], location["longitude"])
        if len(air_rows) > 0:
            air_row = air_rows[0]
    except ValueError:
        air_row = None

    dew_point = None
    tendency = ""
    if steps is not None:
        dew_point = steps["dew_point"].to_list()[0]
        tendency = pressure_tendency(steps)["tendency"].to_list()[0].capitalize()

    uv_value = fetch_uv(location["latitude"], location["longitude"])
    st.html(cards.detail_tiles(weather["reading"], air_row, uv_value, dew_point, tendency))


def show_weather_tab(weather):
    if weather is None:
        st.info("Search in the sidebar to add a city.")
        return

    reading = weather["reading"]
    if reading is None:
        if weather["note"] == "Needs an API key":
            st.warning(SETUP_MESSAGE)
        else:
            st.warning(f"Could not load {weather['location']['city']}: {weather['note']}")
        return

    rain_chance = None
    if weather["steps"] is not None:
        rain_chance = next_steps(weather["steps"], now_seconds(), 1)["pop"].max()
    st.html(cards.header(weather["location"]["city"], reading, weather["high"], weather["low"], rain_chance, now_seconds()))

    if weather["steps"] is None:
        st.warning(f"Could not load the forecast: {weather['note']}")
        show_map(weather)
    else:
        show_next_hours(weather)
        with st.container(key="week-row"):
            forecast_column, map_column = st.columns(2)
            with forecast_column:
                show_daily(weather)
            with map_column:
                show_map(weather)
    show_details(weather)
