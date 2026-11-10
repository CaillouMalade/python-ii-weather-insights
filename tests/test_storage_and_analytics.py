import tempfile
from pathlib import Path

import pandas as pd

from weather_app.analytics import city_comparison, city_trend, daily_range, feels_like_gap
from weather_app.models import WeatherReading
from weather_app.storage import CITIES_PATH, LOG_COLUMNS, LOG_PATH, append_reading, load_cities, load_log


def test_append_writes_header_once_and_load_reads_rows():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        reading = WeatherReading("São Paulo, BR", -23.5, -46.6, 20.0, 19.0, 50, 2.0, "clear sky")
        append_reading(reading, path)
        append_reading(reading, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(LOG_COLUMNS)
        assert len(lines) == 3
        log = load_log(path)
        assert list(log["location"]) == ["São Paulo, BR", "São Paulo, BR"]


def test_missing_log_is_empty():
    assert len(load_log(Path(tempfile.gettempdir()) / "no-such-log.csv")) == 0


def test_committed_files_load():
    assert len(load_cities(CITIES_PATH)) >= 10
    assert list(load_log(LOG_PATH).columns) == LOG_COLUMNS


def make_log():
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(["2026-11-01T08:00Z", "2026-11-01T14:00Z", "2026-11-02T08:00Z", "2026-11-01T12:00Z"], utc=True),
            "location": ["Madrid", "Madrid", "Madrid", "Oslo"],
            "temperature": [10.0, 20.0, 12.0, 2.0],
            "feels_like": [9.0, 19.0, 11.0, -2.0],
        }
    )


def test_trend_is_in_time_order():
    log = make_log().iloc[[2, 0, 1]]
    assert list(city_trend(log, "Madrid")["temperature"]) == [10.0, 20.0, 12.0]


def test_comparison_ranks_by_average():
    comparison = city_comparison(make_log())
    assert list(comparison["location"]) == ["Madrid", "Oslo"]
    assert comparison.loc[0, "average"] == 14.0
    assert comparison.loc[0, "highest"] == 20.0


def test_daily_range_skips_single_reading_days():
    ranges = daily_range(make_log())
    assert len(ranges) == 1
    assert ranges.loc[0, "range"] == 10.0


def test_feels_like_gap_per_city():
    gaps = feels_like_gap(make_log())
    assert list(gaps["location"]) == ["Oslo", "Madrid"]
    assert gaps.loc[0, "gap"] == -4.0
