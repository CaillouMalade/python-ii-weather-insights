"""Files: the weather log (our own time series), the city list and the saved cities."""

import csv
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
LOG_PATH = DATA_DIR / "weather_log.csv"
CITIES_PATH = DATA_DIR / "cities.csv"
SAVED_CITIES_PATH = DATA_DIR / "saved_cities.csv"

READING_COLUMNS = [
    "location", "latitude", "longitude", "temperature", "feels_like", "humidity", "wind_speed", "conditions",
    "temp_min", "temp_max", "pressure", "clouds", "wind_deg", "wind_gust", "visibility", "rain_1h", "snow_1h",
    "weather_id", "icon", "observed_at", "timezone_offset", "sunrise", "sunset",
]
LOG_COLUMNS = ["timestamp_utc"] + READING_COLUMNS

SAVED_CITY_COLUMNS = ["location", "label", "city", "latitude", "longitude"]
# What a fresh clone shows.
DEFAULT_CITIES = ["Madrid, ES", "Tokyo, JP", "New York City, US"]


def _read_header(path):
    """Return the first line of a file, or an empty string if it is missing or empty."""
    try:
        with open(path, encoding="utf-8") as f:
            return f.readline().strip()
    except FileNotFoundError:
        return ""


def migrate_log(path=LOG_PATH):
    """Add any missing columns to an older log, leaving them blank. Existing rows are kept.

    The new file is written beside the old one and checked before it replaces it,
    so a problem part-way through cannot damage the real data.
    """
    header = _read_header(path)
    if header == "" or header == ",".join(LOG_COLUMNS):
        return

    # dtype=str and keep_default_na=False keep every old value exactly as it was written.
    old = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")
    new = old.copy()
    for name in LOG_COLUMNS:
        if name not in new.columns:
            new[name] = ""

    temporary_path = Path(str(path) + ".tmp")
    new[LOG_COLUMNS].to_csv(temporary_path, index=False, encoding="utf-8")

    check = pd.read_csv(temporary_path, dtype=str, keep_default_na=False, encoding="utf-8")
    if not check[old.columns.to_list()].equals(old):
        raise ValueError("The weather log could not be upgraded safely, so it was left unchanged.")
    temporary_path.replace(path)


def append_reading(reading, path=LOG_PATH):
    """Append one reading with a UTC timestamp, writing the header if the file is new."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    migrate_log(path)
    write_header = _read_header(path) == ""
    values = reading.to_dict()
    row = [datetime.now(timezone.utc).isoformat()] + [values[name] for name in READING_COLUMNS]

    # utf-8 is needed for names like "São Paulo": the Windows default encoding
    # cannot write every city name, and pandas reads the file back as utf-8.
    try:
        with open(path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(LOG_COLUMNS)
            writer.writerow(row)
    except PermissionError:
        raise ValueError("Could not save to the weather log. Close the file if it is open in another program.")


def load_log(path=LOG_PATH):
    """Return the whole log as a DataFrame, or an empty one if nothing has been logged."""
    migrate_log(path)
    if _read_header(path) == "":
        return pd.DataFrame(columns=LOG_COLUMNS)

    log = pd.read_csv(path, encoding="utf-8")
    # format="mixed" because isoformat() leaves out the microseconds when they are exactly 0.
    log["timestamp_utc"] = pd.to_datetime(log["timestamp_utc"], format="mixed")
    return log


def load_city_list(path=CITIES_PATH):
    """Return the GeoNames city list used by the search dropdown."""
    # keep_default_na=False because Namibia's country code "NA" is not a missing value.
    return pd.read_csv(path, encoding="utf-8", keep_default_na=False)


def rows_to_locations(rows):
    """Turn DataFrame rows into the location dictionaries used across the app."""
    locations = []
    for _, row in rows.iterrows():
        locations.append(
            {
                "location": row["location"],
                "label": row["label"],
                "city": row["city"],
                # float() because pandas gives a NumPy number, not a Python one.
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
            }
        )
    return locations


def load_saved_cities(path=SAVED_CITIES_PATH, cities_path=CITIES_PATH):
    """Return the saved cities, or the defaults if nothing has ever been saved."""
    if _read_header(path) == "":
        city_list = load_city_list(cities_path)
        return rows_to_locations(city_list[city_list["location"].isin(DEFAULT_CITIES)])
    return rows_to_locations(pd.read_csv(path, encoding="utf-8", keep_default_na=False))


def save_cities(locations, path=SAVED_CITIES_PATH):
    """Write the saved cities. An empty list still writes the header, so removals stick."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(locations, columns=SAVED_CITY_COLUMNS).to_csv(path, index=False, encoding="utf-8")
