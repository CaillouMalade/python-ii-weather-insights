"""Cached API calls. Failures raise ValueError and are not cached, so they are retried."""

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from .analytics import add_local_time, daily_summary, with_today_range
from .client import RainViewerClient, WeatherClient
from .config import API_KEY
from .display import format_local_time, today_high_low
from .maps import RADAR_BOOST, TILE_ZOOM, WEATHER_LAYER_BOOST, boost_opacity, has_radar_coverage, image_to_data_uri, radar_over_coverage, stitch_tiles, tile_grid
from .storage import append_reading

FIVE_MINUTES = 300
TEN_MINUTES = 600
ONE_HOUR = 3600


def now_seconds():
    return datetime.now(timezone.utc).timestamp()


# Logging happens inside the cached function, so ordinary Streamlit reruns reuse
# the cached reading and cannot append duplicate rows.
@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_and_log_current(location):
    reading = WeatherClient(API_KEY).current(location)
    append_reading(reading)
    return reading


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_forecast(latitude, longitude):
    return WeatherClient(API_KEY).forecast(latitude, longitude)


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_air_now(latitude, longitude):
    return WeatherClient(API_KEY).air_now(latitude, longitude)


@st.cache_data(ttl=ONE_HOUR, show_spinner=False)
def fetch_air_forecast(latitude, longitude):
    return WeatherClient(API_KEY).air_forecast(latitude, longitude)


@st.cache_data(ttl=ONE_HOUR, show_spinner=False)
def fetch_air_history(latitude, longitude, days):
    # Whole hours, so the request is the same during one hour.
    end = int(now_seconds()) // 3600 * 3600
    start = end - days * 24 * 3600
    return WeatherClient(API_KEY).air_history(latitude, longitude, start, end)


@st.cache_data(ttl=ONE_HOUR, show_spinner=False)
def fetch_uv(latitude, longitude):
    return WeatherClient(API_KEY).uv_index(latitude, longitude)


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_tile(layer, zoom, x, y):
    return WeatherClient(API_KEY).tile(layer, zoom, x, y)


@st.cache_data(ttl=FIVE_MINUTES, show_spinner=False)
def fetch_radar_frame():
    return RainViewerClient().latest_frame()


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_radar_tile(frame, x, y):
    return RainViewerClient().radar_tile(frame, TILE_ZOOM, x, y)


@st.cache_data(ttl=ONE_HOUR, show_spinner=False)
def fetch_coverage_tile(frame, x, y):
    return RainViewerClient().coverage_tile(frame, TILE_ZOOM, x, y)


def collect_tiles(grid, fetch_one):
    """Fetch every tile of a grid. Return the rows of bytes and how many tiles failed."""
    missing = 0
    rows_of_bytes = []
    for row in grid["rows"]:
        row_of_bytes = []
        for x, y in row:
            try:
                row_of_bytes.append(fetch_one(x, y))
            except ValueError:
                row_of_bytes.append(None)
                missing = missing + 1
        rows_of_bytes.append(row_of_bytes)
    return rows_of_bytes, missing


def fetch_weather_layer(layer, latitude, longitude):
    """Return the OpenWeatherMap image for a layer, stitched and boosted, as a dictionary."""
    grid = tile_grid(latitude, longitude, TILE_ZOOM)
    rows, missing = collect_tiles(grid, lambda x, y: fetch_tile(layer, TILE_ZOOM, x, y))
    image = boost_opacity(stitch_tiles(rows), WEATHER_LAYER_BOOST)
    return {"uri": image_to_data_uri(image), "bounds": grid["bounds"], "missing": missing}


def fetch_radar_image(latitude, longitude):
    """Return the newest radar image as a dictionary, with its time and whether radar covers the place."""
    frame = fetch_radar_frame()
    grid = tile_grid(latitude, longitude, TILE_ZOOM)
    rows, missing = collect_tiles(grid, lambda x, y: fetch_radar_tile(frame, x, y))
    coverage_rows, coverage_missing = collect_tiles(grid, lambda x, y: fetch_coverage_tile(frame, x, y))
    radar = boost_opacity(stitch_tiles(rows), RADAR_BOOST)
    coverage = stitch_tiles(coverage_rows)

    # A coverage tile that failed looks clear, which would wrongly mean "covered".
    covered = None
    if coverage_missing == 0:
        covered = has_radar_coverage(coverage, latitude, longitude, TILE_ZOOM, grid)
    image = radar_over_coverage(radar, coverage)
    return {"uri": image_to_data_uri(image), "bounds": grid["bounds"], "missing": missing, "time": frame["time"], "covered": covered}


def load_city_weather(location):
    """Return a dictionary with everything known about one city. One failure stays inside it."""
    result = {"location": location, "reading": None, "steps": None, "days": None, "high": None, "low": None, "note": ""}

    if not API_KEY:
        result["note"] = "Needs an API key"
        return result

    try:
        result["reading"] = fetch_and_log_current(location)
    except ValueError as e:
        result["note"] = str(e)
        return result

    reading = result["reading"]
    offset = reading.timezone_offset or 0
    # temp_max and temp_min are not always sent, and then the temperature itself stands in.
    high = reading.temp_max if reading.temp_max is not None else reading.temperature
    low = reading.temp_min if reading.temp_min is not None else reading.temperature
    result["high"] = high
    result["low"] = low
    try:
        steps = pd.DataFrame(fetch_forecast(location["latitude"], location["longitude"]))
    except ValueError as e:
        result["note"] = str(e)
        return result

    if len(steps) > 0:
        steps = add_local_time(steps, offset)
        result["steps"] = steps
        result["days"] = daily_summary(steps)
        today = format_local_time(now_seconds(), offset, "%Y-%m-%d")
        result["high"], result["low"] = today_high_low(result["days"], today, high, low)
        result["days"] = with_today_range(result["days"], today, result["high"], result["low"])
    return result
