# Storage needs real files. pytest fixtures are off-limits in this project, so each test
# makes its own folder with the standard library's tempfile.

import tempfile
from pathlib import Path

import pandas as pd

from weather_app.models import WeatherReading
from weather_app.storage import LOG_COLUMNS, append_reading, load_circuits, load_history


def test_append_writes_header_once():
    reading = WeatherReading("Nürburgring GP", 50.3, 6.9, 8.0, 6.0, 80, 2.0, "light rain", wind_gust=5.0)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        append_reading(reading, path)
        append_reading(reading, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(LOG_COLUMNS)
        assert len(lines) == 3
        log = pd.read_csv(path, encoding="utf-8")
        assert log["location"].to_list() == ["Nürburgring GP", "Nürburgring GP"]
        assert log["wind_gust"].to_list() == [5.0, 5.0]


def test_log_columns_keep_the_order_of_the_existing_log():
    # Changing this order would misalign new rows with the rows already in data/weather_log.csv.
    assert ",".join(LOG_COLUMNS) == (
        "timestamp_utc,location,latitude,longitude,temperature,feels_like,humidity,wind_speed,conditions,"
        "temp_min,temp_max,pressure,clouds,wind_deg,wind_gust,visibility,rain_1h,snow_1h,"
        "weather_id,icon,observed_at,timezone_offset,sunrise,sunset"
    )


def test_circuit_file_matches_the_collector_ids():
    circuits = load_circuits()
    ids = [circuit["id"] for circuit in circuits]
    assert len(ids) == 18
    assert len(set(ids)) == 18
    collected = set(load_history()["location_id"].unique())
    assert set(ids) == collected


def test_circuits_are_location_dictionaries():
    spa = load_circuits()[2]
    assert spa == {
        "id": "spa",
        "location": "Spa-Francorchamps",
        "country": "Belgium",
        "latitude": 50.4372,
        "longitude": 5.9714,
        "timezone": "Europe/Brussels",
        "length_km": 7.004,
    }


def test_missing_history_is_empty():
    with tempfile.TemporaryDirectory() as folder:
        assert len(load_history(Path(folder) / "none.csv")) == 0
