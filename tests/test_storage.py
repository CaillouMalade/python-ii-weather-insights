# Storage needs real files. pytest fixtures are off-limits in this project, so each test
# makes its own folder with the standard library's tempfile.

import tempfile
from pathlib import Path

import pandas as pd

from weather_app.models import WeatherReading
from weather_app.storage import (
    LOG_COLUMNS,
    append_reading,
    load_city_list,
    load_log,
    load_saved_cities,
    save_cities,
)

def make_reading():
    return WeatherReading("Madrid, ES", 40.4, -3.7, 20.0, 19.0, 50, 2.0, "clear sky", wind_gust=5.0)


def test_append_writes_header_once_and_load_reads_rows():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        append_reading(make_reading(), path)
        append_reading(make_reading(), path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(LOG_COLUMNS)
        assert len(lines) == 3
        log = load_log(path)
        assert log["temperature"].to_list() == [20.0, 20.0]
        assert log["wind_gust"].to_list() == [5.0, 5.0]


def test_load_missing_log_is_empty_with_columns():
    with tempfile.TemporaryDirectory() as folder:
        log = load_log(Path(folder) / "none.csv")
        assert len(log) == 0
        assert log.columns.to_list() == LOG_COLUMNS


def test_fresh_clone_defaults_come_from_the_real_city_file():
    with tempfile.TemporaryDirectory() as folder:
        cities = load_saved_cities(Path(folder) / "none.csv")
        names = sorted([city["location"] for city in cities])
        assert names == ["Madrid, ES", "New York City, US", "Tokyo, JP"]


def test_saved_cities_round_trip_and_empty_list_sticks():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "saved.csv"
        city = {"location": "Oslo, NO", "label": "Oslo, Norway", "city": "Oslo", "latitude": 59.9, "longitude": 10.7}
        save_cities([city], path)
        assert load_saved_cities(path) == [city]
        save_cities([], path)
        assert load_saved_cities(path) == []


def test_city_file_is_usable():
    cities = load_city_list()
    assert len(cities) > 4000
    # Labels feed the dropdown and locations feed the log, so both must be unique.
    assert cities["label"].is_unique
    assert cities["location"].is_unique
    # Namibia's code "NA" must not be read as a missing value.
    assert "NA" in cities["country_code"].to_list()


def test_city_file_has_small_capitals_and_is_largest_first():
    cities = load_city_list()
    assert "Reykjavík, IS" in cities["location"].to_list()
    populations = cities["population"].to_list()
    assert populations == sorted(populations, reverse=True)
    locations = cities["location"].to_list()
    assert locations.index("London, GB") < locations.index("London, CA")


def test_log_columns_keep_the_order_of_the_existing_log():
    # Changing this order would misalign new rows with the rows already in data/weather_log.csv.
    assert ",".join(LOG_COLUMNS) == (
        "timestamp_utc,location,latitude,longitude,temperature,feels_like,humidity,wind_speed,conditions,"
        "temp_min,temp_max,pressure,clouds,wind_deg,wind_gust,visibility,rain_1h,snow_1h,"
        "weather_id,icon,observed_at,timezone_offset,sunrise,sunset"
    )
