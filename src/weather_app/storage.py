"""Appends readings to the CSV log and loads them back. The log is our own time series."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LOG_PATH = DATA_DIR / "weather_log.csv"

READING_COLUMNS = ["location", "latitude", "longitude", "temperature", "feels_like", "humidity", "wind_speed", "conditions"]
LOG_COLUMNS = ["timestamp_utc"] + READING_COLUMNS


def _log_has_content():
    """Return True if the log file exists and is not empty."""
    try:
        with open(LOG_PATH, encoding="utf-8") as f:
            return f.readline() != ""
    except FileNotFoundError:
        return False


def append_reading(reading):
    """Append one reading with a UTC timestamp, writing the header if the file is new."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_header = not _log_has_content()
    values = reading.to_dict()
    row = [datetime.now(timezone.utc).isoformat()] + [values[name] for name in READING_COLUMNS]

    # utf-8 is needed for names like "São Paulo": the Windows default encoding
    # cannot write every city name, and pandas reads the file back as utf-8.
    try:
        with open(LOG_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(LOG_COLUMNS)
            writer.writerow(row)
    except PermissionError:
        raise ValueError("Could not save to the weather log. Close the file if it is open in another program.")


def load_log():
    """Return the whole log as a DataFrame, or an empty one if nothing has been logged."""
    if not _log_has_content():
        return pd.DataFrame(columns=LOG_COLUMNS)

    log = pd.read_csv(LOG_PATH)
    # format="mixed" because isoformat() leaves out the microseconds when they are exactly 0.
    log["timestamp_utc"] = pd.to_datetime(log["timestamp_utc"], format="mixed")
    return log


def load_saved_locations():
    """Return the distinct logged locations, in the same form as WeatherClient.find_city."""
    distinct = load_log().drop_duplicates(subset="location", keep="first")
    locations = []
    for _, row in distinct.iterrows():
        locations.append({"name": row["location"], "latitude": row["latitude"], "longitude": row["longitude"]})
    return locations
