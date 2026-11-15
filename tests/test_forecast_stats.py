# The statistics are checked on the invented forecast in fake_forecast.py, never on real API calls.

import math

import pandas as pd
import pytest
from fake_forecast import fake_forecasts

from weather_app.fetching import fetch_all_forecasts, points_to_frame
from weather_app.forecast_stats import RESULT_COLUMNS, combine_forecasts, t_value


def fake_table():
    """All three fake providers in one table, as fetch_all_forecasts would return it."""
    points = []
    for source_points in fake_forecasts().values():
        points.extend(source_points)
    return points_to_frame(points)


def test_one_row_per_window_with_every_column():
    combined = combine_forecasts(fake_table())
    assert list(combined.columns) == RESULT_COLUMNS
    assert len(combined) == 8
    assert list(combined["providers"]) == [3] * 8


def test_first_window_mean_and_interval_by_hand():
    # Temperatures 9, 10 and 9 °C: mean 9.33, standard deviation 0.577,
    # margin 4.30 × 0.577 / √3 = 1.43, so the interval is 7.90 to 10.77.
    first = combine_forecasts(fake_table()).iloc[0]
    assert first["temperature"] == pytest.approx(9.333, abs=0.001)
    assert first["temperature_low"] == pytest.approx(7.900, abs=0.001)
    assert first["temperature_high"] == pytest.approx(10.766, abs=0.001)


def test_wind_is_averaged_in_kmh():
    # 4, 3 and 4 m/s average 3.67 m/s, which is 13.2 km/h.
    first = combine_forecasts(fake_table()).iloc[0]
    assert first["wind_kmh"] == pytest.approx(13.2)


def test_rain_providers_counts_from_point_one_mm():
    combined = combine_forecasts(fake_table())
    # Window 0: nobody. Window 2: only open-meteo's 0.1 mm. Window 3: all three. Window 6: met-norway's 0.2 mm.
    assert combined["rain_providers"].iloc[0] == 0
    assert combined["rain_providers"].iloc[2] == 1
    assert combined["rain_providers"].iloc[3] == 3
    assert combined["rain_providers"].iloc[6] == 1


def test_rain_and_wind_intervals_never_go_below_zero():
    combined = combine_forecasts(fake_table())
    assert (combined["rain_low"] >= 0).all()
    assert (combined["wind_kmh_low"] >= 0).all()


def test_providers_that_agree_give_a_zero_width_interval():
    points = fake_forecasts()["open-meteo"]
    table = pd.concat([points_to_frame(points)] * 3, ignore_index=True)
    table["source"] = ["a"] * 8 + ["b"] * 8 + ["c"] * 8
    first = combine_forecasts(table).iloc[0]
    assert first["temperature_low"] == first["temperature"] == first["temperature_high"]


def test_one_provider_gives_the_value_without_an_interval():
    combined = combine_forecasts(points_to_frame(fake_forecasts()["met-norway"]))
    assert list(combined["providers"]) == [1] * 8
    assert combined["temperature"].iloc[0] == 9
    assert math.isnan(combined["temperature_low"].iloc[0])


def test_two_providers_use_the_wider_t_value():
    # Windows a provider doesn't reach (e.g. beyond OpenWeatherMap's 5 days) have fewer providers.
    table = fake_table()
    table = table[table["source"] != "openweathermap"]
    first = combine_forecasts(table).iloc[0]
    # 10 and 9 °C: mean 9.5, standard deviation 0.707, margin 12.71 × 0.707 / √2 = 6.355.
    assert first["providers"] == 2
    assert first["temperature_high"] == pytest.approx(9.5 + 6.355, abs=0.001)


def test_t_value_for_each_number_of_providers():
    assert t_value(1) is None
    assert t_value(3) == 4.30
    assert t_value(30) == 1.96


def test_no_forecast_gives_an_empty_table():
    empty = points_to_frame([])
    combined = combine_forecasts(empty)
    assert len(combined) == 0
    assert list(combined.columns) == RESULT_COLUMNS


def test_missing_column_is_a_clear_error():
    with pytest.raises(ValueError, match="missing the columns"):
        combine_forecasts(fake_table().drop(columns=["rain"]))


def test_the_input_table_is_not_changed():
    table = fake_table()
    before = table.copy()
    combine_forecasts(table)
    pd.testing.assert_frame_equal(table, before)


def test_works_on_the_fetch_all_forecasts_output():
    """The real path: providers -> fetch_all_forecasts -> combine_forecasts."""
    forecasts = fake_forecasts()

    class FakeProvider:
        def __init__(self, source):
            self.source = source

        def forecast(self, location, now=None):
            return forecasts[self.source]

    providers = []
    for source in forecasts:
        providers.append(FakeProvider(source))
    table, failures = fetch_all_forecasts({"location": "Monza", "latitude": 45.62, "longitude": 9.28}, providers)
    combined = combine_forecasts(table)
    assert failures == []
    assert len(combined) == 8
    assert combined["rain_providers"].iloc[4] == 3
