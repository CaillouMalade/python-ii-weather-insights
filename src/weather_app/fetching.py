"""Calls to the weather providers, cached so Streamlit's reruns do not repeat them."""

import streamlit as st

from .aggregator import fetch_all_forecasts
from .client import WeatherClient
from .config import API_KEY
from .providers import MetNorwayClient, OpenMeteoClient
from .storage import append_forecasts, append_reading

TEN_MINUTES = 600


# The log is written inside the cached function, so a rerun reuses the cached
# reading and cannot add a duplicate row. A failure raises and is not cached.
@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_and_log(location):
    reading = WeatherClient(API_KEY).current(location)
    append_reading(reading)
    return reading


def fetch_many(locations):
    """Fetch every location. One failure is recorded and skipped, so the others still load."""
    readings = []
    failures = []
    for location in locations:
        try:
            readings.append(fetch_and_log(location))
        except ValueError as error:
            failures.append(f"{location['location']}: {error}")
    return readings, failures


def find_city(text):
    return WeatherClient(API_KEY).find_city(text)


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
