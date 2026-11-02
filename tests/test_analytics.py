# Small hand-made cases with known answers, the pattern from the starter's test comment.

import pandas as pd
import pytest

from weather_app.analytics import feels_like_delta, latest_ranking, reading_counts, temperature_trend
from weather_app.client import validate_city
from weather_app.models import WeatherReading


def make_log():
    """Four readings, deliberately out of time order."""
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                [
                    "2026-01-01T12:00:00+00:00",
                    "2026-01-01T10:00:00+00:00",
                    "2026-01-01T11:00:00+00:00",
                    "2026-01-01T09:00:00+00:00",
                ]
            ),
            "location": ["Madrid, ES", "Madrid, ES", "Oslo, NO", "Oslo, NO"],
            "temperature": [20.0, 15.0, -2.0, 30.0],
            "feels_like": [19.0, 15.5, -6.0, 30.0],
        }
    )


def make_reading(location, temperature, feels_like):
    return WeatherReading(location, 40.4, -3.7, temperature, feels_like, 50, 3.5, "clear sky")


# Analytics


def test_trend_keeps_one_location_in_time_order():
    trend = temperature_trend(make_log(), "Madrid, ES")
    assert trend["temperature"].to_list() == [15.0, 20.0]


def test_trend_of_unknown_location_is_empty():
    assert len(temperature_trend(make_log(), "Lima, PE")) == 0


def test_ranking_uses_latest_reading_of_each_location():
    # Oslo's 30.0 is older than its -2.0, so Madrid (latest 20.0) must rank first.
    ranking = latest_ranking(make_log())
    assert ranking["location"].to_list() == ["Madrid, ES", "Oslo, NO"]
    assert ranking["temperature"].to_list() == [20.0, -2.0]
    assert ranking["rank"].to_list() == [1, 2]


def test_delta_is_feels_like_minus_temperature():
    delta = feels_like_delta(make_log())
    # In time order: 09:00, 10:00, 11:00, 12:00.
    assert delta["feels_like_delta"].to_list() == [0.0, 0.5, -4.0, -1.0]


def test_reading_counts():
    counts = reading_counts(make_log())
    assert counts["location"].to_list() == ["Madrid, ES", "Oslo, NO"]
    assert counts["readings"].to_list() == [2, 2]


def test_functions_do_not_change_the_input():
    log = make_log()
    temperature_trend(log, "Madrid, ES")
    latest_ranking(log)
    feels_like_delta(log)
    reading_counts(log)
    assert log.columns.to_list() == ["timestamp_utc", "location", "temperature", "feels_like"]
    assert log["temperature"].to_list() == [20.0, 15.0, -2.0, 30.0]


# Reading class


def test_feels_like_delta_property():
    assert make_reading("Madrid, ES", 20.0, 18.5).feels_like_delta == -1.5


def test_sorted_orders_readings_by_temperature():
    cold = make_reading("Oslo, NO", -2.0, -6.0)
    warm = make_reading("Madrid, ES", 20.0, 19.0)
    assert sorted([warm, cold]) == [cold, warm]


def test_repr():
    assert repr(make_reading("Madrid, ES", 20.0, 19.0)) == "WeatherReading('Madrid, ES', 20.0°C)"


def test_to_dict():
    values = make_reading("Madrid, ES", 20.0, 19.0).to_dict()
    assert values["location"] == "Madrid, ES"
    assert values["feels_like"] == 19.0
    assert values["conditions"] == "clear sky"


# Input validation


def test_validate_city_strips_spaces():
    assert validate_city("  Madrid ") == "Madrid"


def test_validate_city_accepts_accents_and_country_codes():
    assert validate_city("São Paulo, BR") == "São Paulo, BR"


def test_validate_city_rejects_empty_text():
    with pytest.raises(ValueError, match="enter a city"):
        validate_city("   ")


def test_validate_city_rejects_text_without_letters():
    with pytest.raises(ValueError, match="no letters"):
        validate_city("12345")


def test_validate_city_rejects_very_long_text():
    with pytest.raises(ValueError, match="too long"):
        validate_city("a" * 101)


def test_validate_city_rejects_non_text():
    with pytest.raises(ValueError, match="must be text"):
        validate_city(None)
