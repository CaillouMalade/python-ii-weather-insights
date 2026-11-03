"""Files: the circuit list, the collected history, and the app's own weather log."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .models import READING_COLUMNS

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CIRCUITS_PATH = DATA_DIR / "circuits.csv"
# Collected every 30 minutes for every circuit since 29 October 2026, by a separate collector.
HISTORY_PATH = DATA_DIR / "current_weather.csv"
# Every reading the app itself fetches.
LOG_PATH = DATA_DIR / "weather_log.csv"

LOG_COLUMNS = ["timestamp_utc"] + READING_COLUMNS


def _read_header(path):
    """Return the first line of a file, or an empty string if it is missing or empty."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return ""


def append_reading(reading, path=LOG_PATH):
    """Append one reading with a UTC timestamp, writing the header if the file is new."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_header = _read_header(path) == ""
    values = reading.to_dict()
    row = [datetime.now(timezone.utc).isoformat()] + [values[name] for name in READING_COLUMNS]

    # utf-8 is needed for names like "Nürburgring": the Windows default encoding
    # cannot write every name, and pandas reads the file back as utf-8.
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(LOG_COLUMNS)
            writer.writerow(row)
    except PermissionError:
        raise ValueError("Could not save to the weather log. Close the file if it is open in another program.")


def load_circuits(path=CIRCUITS_PATH):
    """Return the circuits as location dictionaries, in the file's order.

    "location" holds the name, because the API client and the log expect it there.
    Coordinates are not checked here: WeatherClient checks them before any call, so a
    bad row only affects its own circuit.
    """
    circuits = []
    for _, row in pd.read_csv(path, encoding="utf-8").iterrows():
        circuits.append(
            {
                "id": row["id"],
                "location": row["name"],
                "country": row["country"],
                # float() because pandas gives a NumPy number, not a Python one.
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "timezone": row["timezone"],
                "length_km": float(row["length_km"]),
            }
        )
    return circuits


def load_history(path=HISTORY_PATH):
    """Return the collected history, or an empty table if the file is missing."""
    try:
        return pd.read_csv(path, encoding="utf-8")
    except FileNotFoundError:
        return pd.DataFrame()
