import tempfile
from pathlib import Path

import pandas as pd
from fake_forecast import fake_forecasts

from weather_app.fetching import points_to_frame
from weather_app.analytics import compare_track_history, days_logged, track_rain_history
from weather_app.models import WeatherReading
from weather_app.storage import FORECAST_LOG_COLUMNS, HISTORY_PATH, LOG_COLUMNS, append_forecasts, append_reading, load_history


def test_append_writes_header_once_and_load_reads_rows():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        reading = WeatherReading("São Paulo, BR", -23.5, -46.6, 20.0, 19.0, 50, 2.0, "clear sky")
        append_reading(reading, path)
        append_reading(reading, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(LOG_COLUMNS)
        assert len(lines) == 3
        log = pd.read_csv(path, encoding="utf-8")
        assert list(log["location"]) == ["São Paulo, BR", "São Paulo, BR"]


def test_missing_history_is_empty():
    assert len(load_history(Path(tempfile.gettempdir()) / "no-such-history.csv")) == 0


def test_committed_history_loads():
    history = load_history(HISTORY_PATH)
    assert "location_id" in history.columns
    assert "rain" in history.columns
    assert len(history) > 1000


def make_track_history():
    history = pd.read_csv("tests/sample_track_history.csv")
    history["timestamp_utc"] = pd.to_datetime(history["fetched_at_utc"], utc=True)
    return history


def test_daily_track_history_estimates_rain_and_finds_temperature_range():
    daily = track_rain_history(make_track_history(), "imola")
    assert round(daily.loc[0, "rain_mm"], 2) == 10.32
    assert list(daily["temperature_range_c"]) == [0.0]


def test_days_logged_counts_different_days():
    history = make_track_history()
    assert days_logged(history, "imola") == 1
    assert days_logged(history, "no-such-track") == 0


def test_track_comparison_sorts_and_counts_rain_days():
    summaries = compare_track_history(make_track_history(), ["imola", "monza"])
    assert [summary.location for summary in summaries] == ["Monza", "Imola"]
    assert summaries[1].average_temperature_c == 9.03
    assert summaries[1].rain_days == 1
    assert round(summaries[1].total_rain_mm, 2) == 10.32
    assert summaries[1].days_logged == 1
    assert str(summaries[1]) == "Imola: average 9.0 °C, 1 rain days, 10.3 mm total rain over 1 logged days."


def test_a_day_under_0_1_mm_is_not_a_rain_day():
    history = make_track_history()
    # 0.002 mm per hour on average, so about 0.05 mm over the day: below the 0.1 mm threshold.
    history.loc[history["location_id"] == "imola", "rain"] = 0.002
    imola = [summary for summary in compare_track_history(history, ["imola"])][0]
    assert imola.total_rain_mm > 0
    assert imola.rain_days == 0


def test_missing_rain_becomes_zero_mm():
    history = make_track_history()
    history.loc[history["location_id"] == "imola", "rain"] = float("nan")
    daily = track_rain_history(history, "imola")
    assert daily.loc[0, "rain_mm"] == 0


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
