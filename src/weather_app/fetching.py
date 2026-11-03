"""Cached API calls. Failures raise ValueError and are not cached, so they are retried."""

from datetime import datetime, timezone

import streamlit as st

from .client import RainViewerClient, WeatherClient
from .config import API_KEY
from .display import METRES_PER_SECOND_TO_KMH
from .maps import RADAR_BOOST, TILE_ZOOM, boost_opacity, has_radar_coverage, image_to_data_uri, radar_over_coverage, stitch_tiles, tile_grid, wind_grid_points
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
    """The forecast steps, and when they were fetched (Unix seconds)."""
    return {"steps": WeatherClient(API_KEY).forecast(latitude, longitude), "fetched_at": now_seconds()}


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_wind_point(latitude, longitude):
    reading = WeatherClient(API_KEY).current({"location": "Wind grid point", "latitude": latitude, "longitude": longitude})
    return {"latitude": latitude, "longitude": longitude, "speed_kmh": reading.wind_speed * METRES_PER_SECOND_TO_KMH, "degrees": reading.wind_deg}


@st.cache_data(ttl=FIVE_MINUTES, show_spinner=False)
def fetch_radar_frame():
    return RainViewerClient().latest_frame()


@st.cache_data(ttl=TEN_MINUTES, show_spinner=False)
def fetch_radar_tile(frame, x, y):
    return RainViewerClient().radar_tile(frame, TILE_ZOOM, x, y)


@st.cache_data(ttl=ONE_HOUR, show_spinner=False)
def fetch_coverage_tile(frame, x, y):
    return RainViewerClient().coverage_tile(frame, TILE_ZOOM, x, y)


def load_current(circuit):
    """Return {"circuit", "reading", "note"}. A failure stays with its own circuit as a note."""
    result = {"circuit": circuit, "reading": None, "note": ""}
    if not API_KEY:
        result["note"] = "Needs an API key"
        return result
    try:
        result["reading"] = fetch_and_log_current(circuit)
    except ValueError as e:
        result["note"] = str(e)
    return result


def fetch_wind_grid(latitude, longitude):
    """Wind at every grid point. A failed point is skipped and counted, so the rest still show."""
    points = []
    missing = 0
    for point_latitude, point_longitude in wind_grid_points(latitude, longitude):
        try:
            points.append(fetch_wind_point(point_latitude, point_longitude))
        except ValueError:
            missing = missing + 1
    return points, missing


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
