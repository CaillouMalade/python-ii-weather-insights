"""Files: the fixed city list and the weather log (our own time series)."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .models import READING_COLUMNS

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CITIES_PATH = DATA_DIR / "cities.csv"
LOG_PATH = DATA_DIR / "weather_log.csv"

LOG_COLUMNS = ["timestamp_utc"] + READING_COLUMNS


def load_cities(path=CITIES_PATH):
    """Return the city list as location dictionaries: location, latitude, longitude."""
    cities = []
    for _, row in pd.read_csv(path, encoding="utf-8").iterrows():
        # float() because pandas gives a NumPy number, not a Python one.
        cities.append({"location": row["location"], "latitude": float(row["latitude"]), "longitude": float(row["longitude"])})
    return cities


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
