"""Cached API calls. Failures raise ValueError and are not cached, so they are retried."""

from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from .client import RainViewerClient, WeatherClient
from .config import API_KEY
from .forecast import forecast_windows, upcoming
from .maps import RADAR_BOOST, RADAR_ZOOM, boost_opacity, enlarge, has_radar_coverage, image_to_data_uri, radar_area, radar_over_coverage, stitch_tiles, wind_grid_points
from .storage import append_reading

FIVE_MINUTES = 300
TEN_MINUTES = 600
ONE_HOUR = 3600


def now_seconds():
    return datetime.now(timezone.utc).timestamp()


# Logging happens inside the cached function, so ordinary Streamlit reruns reuse
# the cached reading and cannot append duplicate rows.
@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_and_log_current(circuit):
    reading = WeatherClient(API_KEY).current(circuit)
    append_reading(reading)
    return reading


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_forecast(latitude, longitude):
    return WeatherClient(API_KEY).forecast(latitude, longitude)


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_wind_point(latitude, longitude):
    reading = WeatherClient(API_KEY).current({"location": "Wind grid point", "latitude": latitude, "longitude": longitude})
    return {"latitude": latitude, "longitude": longitude, "speed_kmh": reading.wind_kmh, "degrees": reading.wind_deg}


@st.cache_data(ttl=FIVE_MINUTES, show_spinner=False)
def fetch_radar_frame():
    return RainViewerClient().latest_frame()


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_radar_tile(frame, x, y):
    return RainViewerClient().radar_tile(frame, RADAR_ZOOM, x, y)


@st.cache_data(ttl=ONE_HOUR, show_spinner=False)
def fetch_coverage_tile(frame, x, y):
    return RainViewerClient().coverage_tile(frame, RADAR_ZOOM, x, y)


def load_circuit(circuit):
    """Everything known about one circuit: {"circuit", "reading", "windows", "note"}.

    windows holds the forecast windows that have not ended yet, or None. A failure stays
    with its own circuit as a note, so the other circuits still load.
    """
    result = {"circuit": circuit, "reading": None, "windows": None, "note": ""}
    if not API_KEY:
        result["note"] = "Needs an API key"
        return result
    try:
        result["reading"] = fetch_and_log_current(circuit)
        steps = pd.DataFrame(fetch_forecast(circuit["latitude"], circuit["longitude"]))
    except ValueError as e:
        result["note"] = str(e)
        return result

    windows = upcoming(forecast_windows(steps, result["reading"].timezone_offset or 0), now_seconds())
    if len(windows) == 0:
        result["note"] = "The forecast has no time left."
    else:
        result["windows"] = windows
    return result


def fetch_wind_grid(latitude, longitude):
    """Wind at every grid point. A failed point is skipped, so the rest still show."""
    points = []
    for point_latitude, point_longitude in wind_grid_points(latitude, longitude):
        try:
            points.append(fetch_wind_point(point_latitude, point_longitude))
        except ValueError:
            continue
    return points


def collect_tiles(rows, fetch_one):
    """Fetch every tile in the rows. Return the rows of bytes and how many tiles failed."""
    missing = 0
    rows_of_bytes = []
    for row in rows:
        row_of_bytes = []
        for x, y in row:
            try:
                row_of_bytes.append(fetch_one(x, y))
            except ValueError:
                row_of_bytes.append(None)
                missing = missing + 1
        rows_of_bytes.append(row_of_bytes)
    return rows_of_bytes, missing


def fetch_radar_image(latitude, longitude):
    """The newest radar around a place, cropped and enlarged, as a dictionary.

    complete is False when a radar or coverage tile failed, because a missing tile looks dry.
    covered says whether radar reaches the place at all.
    """
    frame = fetch_radar_frame()
    area = radar_area(latitude, longitude)
    rows, missing = collect_tiles(area["rows"], lambda x, y: fetch_radar_tile(frame, x, y))
    coverage_rows, coverage_missing = collect_tiles(area["rows"], lambda x, y: fetch_coverage_tile(frame, x, y))
    radar = boost_opacity(stitch_tiles(rows), RADAR_BOOST).crop(area["crop"])
    coverage = stitch_tiles(coverage_rows).crop(area["crop"])
    image = enlarge(radar_over_coverage(radar, coverage))
    return {
        "uri": image_to_data_uri(image),
        "bounds": area["bounds"],
        "time": frame["time"],
        "complete": missing + coverage_missing == 0,
        "covered": has_radar_coverage(coverage),
    }
