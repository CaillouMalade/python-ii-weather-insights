# Known-answer tests for the forecast windows and the rain-timing sentence.

import pandas as pd

from weather_app.forecast import forecast_windows, rain_timing, today_high_low, upcoming

MONDAY = 1767571200  # 2026-01-05 00:00 UTC, a Monday
HOUR = 3600


def make_windows(pops, rains=None, offset=0):
    """Forecast steps every 3 hours from Monday 03:00 UTC, with the given chances and rain."""
    if rains is None:
        rains = [0] * len(pops)
    steps = []
    for number in range(len(pops)):
        steps.append({"dt": MONDAY + (number + 1) * 3 * HOUR, "temperature": 10 + number, "clouds": 50, "pop": pops[number], "rain_3h": rains[number], "snow_3h": 0})
    return forecast_windows(pd.DataFrame(steps), offset)


def test_each_step_is_the_three_hours_up_to_its_time_in_local_time():
    windows = make_windows([0, 0], [1.0, 0], offset=HOUR)
    assert windows["start"].to_list()[0] == pd.Timestamp("2026-01-05 01:00")
    assert windows["end"].to_list()[0] == pd.Timestamp("2026-01-05 04:00")
    assert windows["precipitation_mm"].to_list() == [1.0, 0]


def test_snow_counts_as_precipitation():
    steps = pd.DataFrame([{"dt": MONDAY, "temperature": 0, "clouds": 90, "pop": 1, "rain_3h": 0.5, "snow_3h": 2.0}])
    assert forecast_windows(steps, 0)["precipitation_mm"].to_list() == [2.5]


def test_upcoming_keeps_windows_that_have_not_ended():
    windows = make_windows([0, 0, 0])
    assert len(upcoming(windows, MONDAY + 3 * HOUR)) == 2


def test_today_high_low_widens_the_forecast_with_the_current_reading():
    windows = make_windows([0] * 10)
    # Monday's steps run from 10° to 16°; the current reading's 18° is higher.
    assert today_high_low(windows, "2026-01-05", 18, 12) == (18, 10)


def test_today_high_low_falls_back_when_nothing_is_left_today():
    windows = make_windows([0, 0])
    assert today_high_low(windows, "2026-01-06", 7, 3) == (7, 3)


def test_dry_until_then_rain_likely_for_six_hours():
    windows = make_windows([0, 0, 0.8, 0.9, 0.2, 0])
    # The third window runs from 06:00 to 09:00 and the fourth ends at 12:00.
    assert rain_timing(windows, MONDAY) == "Dry until Mon 06:00, then rain likely for about 6 hours, until Mon 12:00."


def test_rain_unlikely_when_earlier_windows_have_a_little_rain():
    windows = make_windows([0.3, 0.6, 0], [0.2, 1.0, 0])
    assert rain_timing(windows, MONDAY) == "Rain unlikely until Mon 03:00, then rain likely for about 3 hours, until Mon 06:00."


def test_rain_likely_now_when_the_current_window_is_wet():
    windows = make_windows([0.7, 0.7, 0.1])
    assert rain_timing(windows, MONDAY + HOUR) == "Rain likely now, for about 6 hours, until Mon 06:00."


def test_rain_to_the_end_of_the_forecast_says_at_least():
    windows = make_windows([0, 0.5, 0.5])
    assert rain_timing(windows, MONDAY) == "Dry until Mon 03:00, then rain likely for at least 6 hours, to the end of the forecast."


def test_no_rain_likely_names_the_highest_chance():
    windows = make_windows([0.1, 0.3, 0.3, 0])
    assert rain_timing(windows, MONDAY) == "No rain likely before Mon 12:00, the end of the forecast. Highest chance 30 %, Mon 03:00–06:00."


def test_no_rain_at_all():
    assert rain_timing(make_windows([0, 0]), MONDAY) == "No rain likely before Mon 06:00, the end of the forecast."


def test_windows_already_over_are_ignored():
    windows = make_windows([0.9, 0, 0])
    assert rain_timing(windows, MONDAY + 3 * HOUR) == "No rain likely before Mon 09:00, the end of the forecast."
