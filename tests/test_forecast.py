# Known-answer tests for the forecast windows, the rain-timing sentence and the status lights.

import pandas as pd

from weather_app.forecast import RAIN_LIKELY, calm_clouds, forecast_windows, next_three_hours, rain_timing, status_lights, today_high_low, upcoming

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


def test_dry_until_then_rain_until():
    windows = make_windows([0, 0, 0.8, 0.9, 0.2, 0])
    # The third window runs from 06:00 to 09:00 and the fourth ends at 12:00.
    assert rain_timing(windows, MONDAY) == "Dry until Mon 06:00, then rain until Mon 12:00"


def test_mostly_dry_when_earlier_windows_have_a_little_rain():
    windows = make_windows([0.3, 0.6, 0], [0.2, 1.0, 0])
    assert rain_timing(windows, MONDAY) == "Mostly dry until Mon 03:00, then rain until Mon 06:00"


def test_rain_likely_now_until_it_stops():
    windows = make_windows([0.7, 0.7, 0.1])
    assert rain_timing(windows, MONDAY + HOUR) == "Rain likely until Mon 06:00"


def test_rain_to_the_end_of_the_forecast():
    assert rain_timing(make_windows([0, 0.5, 0.5]), MONDAY) == "Dry until Mon 03:00, then rain"
    assert rain_timing(make_windows([0.6, 0.5, 0.5]), MONDAY + HOUR) == "Rain likely all week"


def test_a_dry_forecast_is_one_short_line_even_with_small_chances():
    assert rain_timing(make_windows([0.1, 0.3, 0.3, 0]), MONDAY) == "Dry all week"
    assert rain_timing(make_windows([0, 0]), MONDAY) == "Dry all week"


def test_windows_already_over_are_ignored():
    windows = make_windows([0.9, 0, 0])
    assert rain_timing(windows, MONDAY + 3 * HOUR) == "Dry all week"


# Status lights: now, the next 3 hours, later today. Windows run 00-03, 03-06 ... on Monday.


def test_lights_for_now_next_three_hours_and_later_today():
    # Rain likely from 06 to 09 and from 12 to 15, and again on Tuesday from 00 to 03.
    windows = make_windows([0, 0, 0.7, 0, 0.6, 0, 0, 0, 0.9])
    # At 01:00 the running window is 00-03, the next 3 hours reach into 03-06, and later today is 06-24.
    assert status_lights(windows, MONDAY + HOUR, "2026-01-05") == ["dry", "dry", "rain"]
    # At 04:00 the next 3 hours reach into 06-09, where rain is likely.
    assert status_lights(windows, MONDAY + 4 * HOUR, "2026-01-05") == ["dry", "rain", "rain"]


def test_next_three_hours_are_the_running_window_and_the_next_one():
    windows = make_windows([0.1, 0.2, 0.3, 0.4])
    assert next_three_hours(windows, MONDAY + HOUR)["pop"].to_list() == [0.1, 0.2]
    # Exactly at a window's start, the next 3 hours are that window alone.
    assert next_three_hours(windows, MONDAY + 3 * HOUR)["pop"].to_list() == [0.2]


def test_header_chance_and_middle_light_always_agree():
    # Le Mans in the live check: dry now, rain likely from 10:00. At 08:30 the header said 0 %
    # (the running window only) while the light was red. Both now read the same windows.
    # Windows end every 3 hours UTC; Le Mans is UTC+1, so 10:00 local is the 09-12 UTC window.
    windows = make_windows([0, 0, 0, 0.8, 0.8], offset=HOUR)
    now = MONDAY + 7 * HOUR + 1800
    chance = next_three_hours(windows, now)["pop"].max()
    assert chance == 0.8
    assert status_lights(windows, now, "2026-01-05")[1] == "rain"
    for pops in [[0, 0.49, 0.5, 0], [0.6, 0, 0, 0], [0, 0, 0, 0], [0.2, 0.9, 0.1, 0]]:
        for hour in [0, 1, 2, 3, 4, 5]:
            windows = make_windows(pops)
            chance = next_three_hours(windows, MONDAY + hour * HOUR)["pop"].max()
            light = status_lights(windows, MONDAY + hour * HOUR, "2026-01-05")[1]
            assert (chance >= RAIN_LIKELY) == (light == "rain"), (pops, hour)


def test_later_today_is_unlit_late_in_the_evening():
    windows = make_windows([0, 0, 0, 0, 0, 0, 0, 0, 0.9])
    # At 22:00 the running window is 21-24 and the next starts at midnight, still within 3 hours.
    assert status_lights(windows, MONDAY + 22 * HOUR, "2026-01-05") == ["dry", "rain", None]


def test_lights_use_the_same_threshold_as_the_sentence():
    assert status_lights(make_windows([0.5, 0.49, 0.49]), MONDAY + HOUR, "2026-01-05") == ["rain", "rain", "dry"]
    assert rain_timing(make_windows([0.5, 0.49, 0.49]), MONDAY + HOUR).startswith("Rain likely")


def test_a_dry_forecast_lights_all_green():
    assert status_lights(make_windows([0.1] * 8), MONDAY + HOUR, "2026-01-05") == ["dry", "dry", "dry"]


def test_a_forecast_starting_later_leaves_now_unlit():
    # The first window runs from 00 to 03, but it is not yet midnight, so nothing covers now.
    assert status_lights(make_windows([0, 0]), MONDAY - HOUR, "2026-01-04") == [None, "dry", None]


def test_calm_clouds_is_a_centred_15_hour_mean():
    steps = []
    for number, clouds in enumerate([0, 100, 0, 100, 0, 100]):
        steps.append({"dt": MONDAY + (number + 1) * 3 * HOUR, "temperature": 10, "clouds": clouds, "pop": 0, "rain_3h": 0, "snow_3h": 0})
    windows = forecast_windows(pd.DataFrame(steps), 0)
    # Each value averages up to two windows on either side; the ends have fewer neighbours.
    assert calm_clouds(windows).round(1).to_list() == [33.3, 50.0, 40.0, 60.0, 50.0, 66.7]
    # The table itself is left as it was.
    assert windows["clouds"].to_list() == [0, 100, 0, 100, 0, 100]
