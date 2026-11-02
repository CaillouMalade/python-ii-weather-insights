"""The Weather tab: hero, conditions, daily forecast, detail tiles and map."""

import pandas as pd
import streamlit as st

from . import cards
from .analytics import hourly_plan, pressure_tendency
from .config import SETUP_MESSAGE
from .display import format_local_time
from .fetching import fetch_air_now, fetch_map_image, fetch_uv, now_seconds
from .maps import build_map_figure

MAP_LAYERS = {
    "Precipitation": "precipitation_new",
    "Temperature": "temp_new",
    "Wind": "wind_new",
    "Clouds": "clouds_new",
    "Pressure": "pressure_new",
}
# The tile zoom gives sharp tiles when the map itself is one zoom level further out.
MAP_ZOOMS = {"Region": 6, "Continent": 4}


def show_conditions(weather):
    reading = weather["reading"]
    offset = reading.timezone_offset or 0
    with st.container(key="conditions-card"):
        st.html('<div class="card-title">Conditions: next 24 hours, in 3-hour steps</div>')
        measure = st.segmented_control("Measure", ["Temperature", "Precipitation", "Wind"], default="Temperature", required=True, key="measure", label_visibility="collapsed")
        plan = hourly_plan(weather["steps"], now_seconds(), reading.sunrise, reading.sunset)
        st.html(cards.conditions_strip(plan, offset, measure, reading))
        units = {"Temperature": "°C", "Precipitation": "mm, % is the chance", "Wind": "km/h"}
        st.caption(f"Times are local. Unit: {units[measure]}. The free forecast has 3-hour steps, not hourly ones.")


def show_daily(weather):
    days = weather["days"]
    offset = weather["reading"].timezone_offset or 0
    today = format_local_time(now_seconds(), offset, "%Y-%m-%d")
    day_names = []
    for date in days["local_date"].to_list():
        if date == today:
            day_names.append("Today")
        else:
            day_names.append(pd.to_datetime(date).strftime("%a"))
    st.html(cards.daily_card(days, today, day_names, weather["reading"].temperature))
    st.caption("Lows and highs come from the 3-hour forecast steps.")


def show_tiles(weather):
    reading = weather["reading"]
    steps = weather["steps"]
    location = weather["location"]

    air_html = ""
    try:
        air_rows = fetch_air_now(location["latitude"], location["longitude"])
        if len(air_rows) > 0:
            air_html = cards.air_tile(air_rows[0])
    except ValueError:
        air_html = cards.tile("Air quality", "Unavailable", "The air quality service did not answer.").replace('class="card"', 'class="card wide"')

    dew_point = None
    tendency = ""
    if steps is not None:
        dew_point = steps["dew_point"].to_list()[0]
        change = pressure_tendency(steps).to_dict("records")[0]
        tendency = f"{change['tendency'].capitalize()} over the next 24 hours ({change['change']:+.0f} hPa)"

    uv_value = fetch_uv(location["latitude"], location["longitude"])
    st.html(
        '<div class="tiles">'
        + air_html
        + cards.wind_tile(reading)
        + cards.uv_tile(uv_value)
        + cards.sun_tile(reading)
        + cards.feels_tile(reading)
        + cards.humidity_tile(reading, dew_point)
        + cards.visibility_tile(reading)
        + cards.pressure_tile(reading, tendency)
        + "</div>"
    )


def show_map(weather):
    location = weather["location"]
    with st.container(key="map-card"):
        st.html('<div class="card-title">Weather map</div>')
        layer_column, zoom_column = st.columns(2)
        layer = layer_column.selectbox("Layer", list(MAP_LAYERS.keys()), key="map_layer")
        zoom_name = zoom_column.selectbox("Area", list(MAP_ZOOMS.keys()), key="map_area")
        zoom = MAP_ZOOMS[zoom_name]
        image_uri, bounds, missing = fetch_map_image(MAP_LAYERS[layer], location["latitude"], location["longitude"], zoom)
        fig = build_map_figure(image_uri, bounds, location["latitude"], location["longitude"], zoom - 1)
        st.plotly_chart(fig, config={"displayModeBar": False})
        if missing > 0:
            st.warning(f"{missing} map tiles could not be loaded, so part of the {layer.lower()} layer is missing.")
        st.caption("Weather layers © OpenWeatherMap. The layer covers a fixed area around the city.")


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

    st.html(cards.hero(weather["location"]["city"], reading, weather["high"], weather["low"], now_seconds()))

    if weather["steps"] is None:
        st.warning(f"Could not load the forecast: {weather['note']}")

    with st.container(key="main-grid"):
        tiles_column, forecast_column = st.columns(2)
        with tiles_column:
            show_tiles(weather)
        with forecast_column:
            if weather["steps"] is not None:
                show_conditions(weather)
                show_daily(weather)
    show_map(weather)
