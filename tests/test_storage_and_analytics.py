import tempfile
from pathlib import Path

import pandas as pd
from fake_forecast import fake_forecasts

from weather_app.aggregator import points_to_frame
from weather_app.analytics import city_comparison, city_trend, compare_track_history, daily_range, feels_like_gap, track_rain_history
from weather_app.models import WeatherReading
from weather_app.storage import CIRCUITS_PATH, FORECAST_LOG_COLUMNS, HISTORY_PATH, LOG_COLUMNS, LOG_PATH, append_forecasts, append_reading, load_all_readings, load_circuits, load_history, load_log


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
    assert len(load_circuits(CIRCUITS_PATH)) == 18
    assert list(load_log(LOG_PATH).columns) == LOG_COLUMNS
    history = load_history(HISTORY_PATH)
    assert "location_id" in history.columns
    assert "rain" in history.columns
    assert len(history) > 1000


def test_every_circuit_has_history():
    history = load_history(HISTORY_PATH)
    for circuit in load_circuits(CIRCUITS_PATH):
        assert circuit["location"] in set(history["location"])


def test_history_and_log_are_combined_in_time_order():
    with tempfile.TemporaryDirectory() as folder:
        history_path = Path(folder) / "history.csv"
        history_path.write_text(
            "fetched_at_utc,location_id,location_name,latitude_deg,longitude_deg,temperature_c,feels_like_c,humidity_pct,wind_speed_m_s,weather_description,rain_1h_mm\n"
            "2026-11-01T12:00:00Z,spa,Spa,50.4,5.9,9.0,7.0,80,3.0,light rain,0.4\n",
            encoding="utf-8",
        )
        log_path = Path(folder) / "log.csv"
        append_reading(WeatherReading("Spa", 50.4, 5.9, 10.0, 8.0, 70, 2.0, "clouds"), log_path)
        readings = load_all_readings(log_path, history_path)
        assert list(readings["temperature"]) == [9.0, 10.0]
        assert "location_id" in readings.columns
        assert "rain" in readings.columns


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


def make_track_history():
    history = pd.read_csv("tests/sample_track_history.csv")
    history["timestamp_utc"] = pd.to_datetime(history["fetched_at_utc"], utc=True)
    return history


def test_daily_track_history_sums_rain_and_finds_temperature_range():
    daily = track_rain_history(make_track_history(), "imola")
    assert round(daily.loc[0, "rain_mm"], 2) == 0.86
    assert list(daily["temperature_range_c"]) == [0.0]


def test_track_comparison_sorts_and_counts_rain_days():
    summaries = compare_track_history(make_track_history(), ["imola", "monza"])
    assert [summary["location"] for summary in summaries] == ["Monza", "Imola"]
    assert summaries[1]["average_temperature_c"] == 9.03
    assert summaries[1]["rain_days"] == 1
    assert round(summaries[1]["total_rain_mm"], 2) == 0.86
    assert summaries[1]["days_logged"] == 1


def test_append_forecasts_adds_fetch_time_and_location():
    points = fake_forecasts()["open-meteo"]
    points[0].rain = None  # a missing value must stay empty, not become "nan"
    table = points_to_frame(points)
    monza = {"location": "Monza", "latitude": 45.62, "longitude": 9.28}
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "forecasts.csv"
        append_forecasts(table, monza, path)
        append_forecasts(table, monza, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(FORECAST_LOG_COLUMNS)
        assert len(lines) == 1 + 2 * len(points)   # one header, then every row of both fetches
        assert "nan" not in lines[1]
        saved = pd.read_csv(path)
        assert list(saved["location"].unique()) == ["Monza"]
        assert saved["rain"].isna().sum() == 2


def test_append_forecasts_skips_an_empty_table():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "forecasts.csv"
        append_forecasts(points_to_frame([]), {"location": "Monza", "latitude": 45.62, "longitude": 9.28}, path)
        assert not path.exists()
