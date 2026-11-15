# The page helpers are checked on the invented forecast in fake_forecast.py, never on real API calls.
# Its 8 windows are Friday 13 November 2026, 00:00 to 21:00 UTC, and every provider says 225° (SW).

from datetime import datetime, timezone

import pandas as pd
import pytest
from fake_forecast import fake_forecasts

from weather_app.aggregator import points_to_frame
from weather_app.dashboard import chance_of_rain, compass_sector, direction_votes, provider_table, session_message, session_window_rows
from weather_app.forecast_stats import combine_forecasts

FP1 = datetime(2026, 11, 13, 8, 0, tzinfo=timezone.utc)  # in the 06:00 window


def fake_table():
    """All three fake providers in one table, as the aggregator would return it."""
    points = []
    for source_points in fake_forecasts().values():
        points.extend(source_points)
    return points_to_frame(points)


# Wind direction

def test_compass_sector_main_directions():
    assert compass_sector(0) == "N"
    assert compass_sector(90) == "E"
    assert compass_sector(180) == "S"
    assert compass_sector(225) == "SW"
    assert compass_sector(270) == "W"


def test_compass_sector_both_sides_of_north():
    # 350° and 10° are both close to north; 360° is north again.
    assert compass_sector(350) == "N"
    assert compass_sector(10) == "N"
    assert compass_sector(360) == "N"


def test_direction_votes_on_the_fake_forecast():
    rows = session_window_rows(fake_table(), FP1)
    assert direction_votes(rows) == ("SW", 3, 3)


def test_direction_votes_with_a_disagreement_and_a_missing_value():
    rows = pd.DataFrame({"wind_deg": [350, 10, 90, None]})
    # Two providers say N, one says E, one sent no direction.
    assert direction_votes(rows) == ("N", 2, 3)


def test_direction_votes_with_no_direction():
    rows = pd.DataFrame({"wind_deg": [None, None]})
    assert direction_votes(rows) is None


# Chance of rain

def test_chance_of_rain_from_the_combined_table():
    combined = combine_forecasts(fake_table())
    # Window 0: nobody predicts rain. Window 2: only open-meteo (0.1 mm). Window 3: all three.
    assert chance_of_rain(combined.iloc[0]) == 0
    assert chance_of_rain(combined.iloc[2]) == pytest.approx(33.33, abs=0.01)
    assert chance_of_rain(combined.iloc[3]) == 100


# Sessions

def test_session_window_rows_picks_the_window_of_the_session():
    rows = session_window_rows(fake_table(), FP1)
    assert len(rows) == 3  # one row per provider
    # 08:00 falls in the 06:00 window, the third one: 10, 10 and 11 °C in fake_forecast.py.
    assert list(rows["temperature"]) == [10, 10, 11]


def test_session_message():
    rows = session_window_rows(fake_table(), FP1)
    thursday = datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc)
    saturday = datetime(2026, 11, 14, 10, 0, tzinfo=timezone.utc)
    assert session_message(FP1, thursday, rows) is None
    assert session_message(FP1, saturday, rows) == "This session is over."
    assert session_message(FP1, thursday, rows.iloc[0:0]) == "No forecast yet."


# Per-provider table

def test_provider_table_for_fp1():
    table = provider_table(session_window_rows(fake_table(), FP1))
    assert list(table.columns) == ["Provider", "Temperature (°C)", "Rain (mm)", "Wind (km/h)", "Wind from"]
    assert list(table["Provider"]) == ["openweathermap", "open-meteo", "met-norway"]
    # The 06:00 window: wind 5 m/s for every provider, which is 18 km/h, from 225° (SW).
    assert list(table["Wind (km/h)"]) == [18, 18, 18]
    assert list(table["Wind from"]) == ["SW", "SW", "SW"]


def test_provider_table_with_a_missing_direction():
    rows = pd.DataFrame({"source": ["met-norway"], "temperature": [10.0], "rain": [None], "wind_speed": [2.0], "wind_deg": [None]})
    table = provider_table(rows)
    assert table["Wind from"].iloc[0] == "Unknown"
