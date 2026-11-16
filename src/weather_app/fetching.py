"""Calls to the weather services the pages use.

First the plain functions that ask every forecast provider and put the answers in one
table, then the cached calls: Streamlit reruns the whole page on every click, and the
cache stops those reruns from calling the APIs (and writing the logs) again.
"""

import pandas as pd
import streamlit as st

from .client import WeatherClient
from .config import API_KEY
from .providers import MetNorwayClient, OpenMeteoClient, RainViewerClient
from .storage import append_forecasts, append_reading

TEN_MINUTES = 600

# One row per provider and 3-hour window; "source" says which provider it came from.
FORECAST_COLUMNS = ["source", "time_utc", "temperature", "wind_speed", "wind_deg", "rain"]


def points_to_frame(points):
    """Turn a list of ForecastPoints into a DataFrame with one row per point."""
    rows = []
    for point in points:
        rows.append({
            "source": point.source,
            "time_utc": point.time_utc,
            "temperature": point.temperature,
            "wind_speed": point.wind_speed,
            "wind_deg": point.wind_deg,
            "rain": point.rain,
        })
    # Giving the columns keeps the table's shape even when no provider answered.
    return pd.DataFrame(rows, columns=FORECAST_COLUMNS)


def fetch_all_forecasts(location, providers, now=None):
    """Ask every provider for a forecast and return (table, failure messages).

    A provider that fails is skipped and its message kept, so the others still load.
    """
    all_points = []
    failures = []
    for provider in providers:
        try:
            points = provider.forecast(location, now)
        except ValueError as error:
            failures.append(f"{provider.source}: {error}")
            continue
        all_points.extend(points)
    return points_to_frame(all_points), failures


# The cached calls.


# The log is written inside the cached function, so a rerun reuses the cached
# reading and cannot add a duplicate row. A failure raises and is not cached.
@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_and_log(location):
    """Return the current weather at a location from OpenWeatherMap, and log it."""
    reading = WeatherClient(API_KEY).current(location)
    append_reading(reading)
    return reading


# Same idea as fetch_and_log: the forecasts are logged inside the cached function,
# so a rerun reuses them and cannot log the same fetch twice.
@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_forecasts_and_log(location):
    """Return (table, failure messages) for every provider, and log what came back."""
    providers = [OpenMeteoClient(), MetNorwayClient()]
    # OpenWeatherMap needs a key; without one, the two keyless providers still work.
    if API_KEY is not None:
        providers.append(WeatherClient(API_KEY))
    table, failures = fetch_all_forecasts(location, providers)
    append_forecasts(table, location)
    return table, failures


# RainViewer makes a new radar image every 10 minutes, so a 10-minute cache loses nothing.
@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_radar_frames():
    """Return the last 2 hours of rain radar images, oldest first. A failure raises and is not cached."""
    return RainViewerClient().radar_frames()
