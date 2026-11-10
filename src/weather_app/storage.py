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

# The collector's column names, and the log column each one becomes.
HISTORY_COLUMNS = {
    "fetched_at_utc": "timestamp_utc",
    "location_name": "location",
    "latitude_deg": "latitude",
    "longitude_deg": "longitude",
    "temperature_c": "temperature",
    "feels_like_c": "feels_like",
    "humidity_pct": "humidity",
    "wind_speed_m_s": "wind_speed",
    "weather_description": "conditions",
}

LOG_COLUMNS = ["timestamp_utc"] + READING_COLUMNS


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
