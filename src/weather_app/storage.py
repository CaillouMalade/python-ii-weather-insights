"""Files: the circuit list, the collector's history and the app's own weather log."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .models import READING_COLUMNS

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CIRCUITS_PATH = DATA_DIR / "circuits.csv"
# Every reading the app itself fetches.
LOG_PATH = DATA_DIR / "weather_log.csv"
# Written by the collector (data-collection branch) every 30 minutes for every circuit since 29 October 2026.
HISTORY_PATH = DATA_DIR / "current_weather.csv"
# Every forecast the app fetches: one row per provider and 3-hour window, per fetch.
FORECAST_LOG_PATH = DATA_DIR / "forecasts.csv"

# The collector's column names, and the log column each one becomes.
HISTORY_COLUMNS = {
    "fetched_at_utc": "timestamp_utc",
    "location_id": "location_id",
    "location_name": "location",
    "latitude_deg": "latitude",
    "longitude_deg": "longitude",
    "temperature_c": "temperature",
    "rain_1h_mm": "rain",
    "feels_like_c": "feels_like",
    "humidity_pct": "humidity",
    "wind_speed_m_s": "wind_speed",
    "weather_description": "conditions",
}

LOG_COLUMNS = ["timestamp_utc"] + READING_COLUMNS

FORECAST_LOG_COLUMNS = [
    "fetched_at_utc", "location", "latitude", "longitude",
    "source", "time_utc", "temperature", "wind_speed", "wind_deg", "rain",
]


def load_circuits(path=CIRCUITS_PATH):
    """Return the circuit list as location dictionaries: location, latitude, longitude."""
    circuits = []
    for _, row in pd.read_csv(path, encoding="utf-8").iterrows():
        # float() because pandas gives a NumPy number, not a Python one.
        circuits.append({"location": row["location"], "latitude": float(row["latitude"]), "longitude": float(row["longitude"])})
    return circuits


def append_reading(reading, path=LOG_PATH):
    """Append one reading with a UTC timestamp, writing the header if the file is new or empty."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0
    values = reading.to_dict()
    row = [datetime.now(timezone.utc).isoformat()]
    for name in READING_COLUMNS:
        row.append(values[name])

    # utf-8 so names like "São Paulo" are written the same way on Windows and macOS.
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(LOG_COLUMNS)
            writer.writerow(row)
    except PermissionError:
        raise ValueError("Could not save to the weather log. Close the file if it is open in another program.") from None


def append_forecasts(table, location, path=FORECAST_LOG_PATH):
    """Append one fetch of forecasts with the UTC time we asked, writing the header if the file is new."""
    if len(table) == 0:
        return  # no provider answered, so there is nothing to log
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    rows = table.copy()
    # Every row of one fetch gets the same time, so fetches can be told apart later.
    rows["fetched_at_utc"] = datetime.now(timezone.utc).isoformat()
    rows["location"] = location["location"]
    rows["latitude"] = location["latitude"]
    rows["longitude"] = location["longitude"]

    # mode="a" adds to the end of the file; a missing value (None) is written as an empty cell.
    try:
        rows[FORECAST_LOG_COLUMNS].to_csv(path, mode="a", header=write_header, index=False, encoding="utf-8")
    except PermissionError:
        raise ValueError("Could not save the forecasts. Close the file if it is open in another program.") from None


def load_log(path=LOG_PATH):
    """Return the log as a DataFrame with a parsed UTC timestamp, or an empty one if there is none."""
    try:
        log = pd.read_csv(path, encoding="utf-8")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=LOG_COLUMNS)
    log["timestamp_utc"] = pd.to_datetime(log["timestamp_utc"], utc=True, format="ISO8601")
    return log


def load_history(path=HISTORY_PATH):
    """Return the collector's readings with the log's column names, or an empty DataFrame."""
    try:
        history = pd.read_csv(path, encoding="utf-8")
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=LOG_COLUMNS)
    history = history[list(HISTORY_COLUMNS.keys())].rename(columns=HISTORY_COLUMNS)
    history["timestamp_utc"] = pd.to_datetime(history["timestamp_utc"], utc=True, format="ISO8601")
    return history


def load_all_readings(log_path=LOG_PATH, history_path=HISTORY_PATH):
    """The collector's history and the app's own log together, in time order."""
    readings = pd.concat([load_history(history_path), load_log(log_path)], ignore_index=True)
    return readings.sort_values("timestamp_utc").reset_index(drop=True)
