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
    migrate_log,
    save_cities,
)

OLD_HEADER = "timestamp_utc,location,latitude,longitude,temperature,feels_like,humidity,wind_speed,conditions\n"
OLD_ROW = '2026-11-02T13:35:12.002708+00:00,"Madrid, ES",40.4167047,-3.7035825,17.53,16.38,40,1.54,clear sky\n'


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


def test_migrate_keeps_old_values_exactly_and_leaves_new_columns_blank():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        path.write_text(OLD_HEADER + OLD_ROW, encoding="utf-8")
        migrate_log(path)

        migrated = pd.read_csv(path, dtype=str, keep_default_na=False)
        assert migrated.columns.to_list() == LOG_COLUMNS
        assert migrated["timestamp_utc"].to_list() == ["2026-11-02T13:35:12.002708+00:00"]
        assert migrated["longitude"].to_list() == ["-3.7035825"]
        assert migrated["wind_gust"].to_list() == [""]
        assert not Path(str(path) + ".tmp").exists()


def test_migrate_twice_changes_nothing():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        path.write_text(OLD_HEADER + OLD_ROW, encoding="utf-8")
        migrate_log(path)
        first = path.read_text(encoding="utf-8")
        migrate_log(path)
        assert path.read_text(encoding="utf-8") == first


def test_append_to_an_old_log_migrates_it_first():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        path.write_text(OLD_HEADER + OLD_ROW, encoding="utf-8")
        append_reading(make_reading(), path)
        log = load_log(path)
        assert log["temperature"].to_list() == [17.53, 20.0]
        assert log["wind_gust"].isna().to_list() == [True, False]


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
