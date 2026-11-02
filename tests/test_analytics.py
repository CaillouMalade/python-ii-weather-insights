# Small hand-made cases with known answers, the pattern from the starter's test comment.

import pandas as pd

from weather_app.analytics import (
    add_local_time,
    air_daily_means,
    air_pattern,
    aqi_band_share,
    city_daily_highs,
    city_forecast_summary,
    comfort_score,
    comfort_windows,
    daily_log_stats,
    daily_summary,
    feels_like_delta,
    history_coverage,
    hourly_plan,
    latest_ranking,
    pressure_tendency,
    reading_counts,
    temperature_trend,
    who_comparison,
)

# 2026-01-05 is a Monday. This is 00:00 UTC that day, in Unix seconds.
MONDAY = 1767571200
HOUR = 3600


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


def make_steps():
    """Three forecast steps, three hours apart, starting at Monday 09:00 local (offset 0)."""
    steps = pd.DataFrame(
        {
            "dt": [MONDAY + 9 * HOUR, MONDAY + 12 * HOUR, MONDAY + 15 * HOUR],
            "temperature": [10.0, 16.0, 13.0],
            "pop": [0.0, 0.5, 0.2],
            "rain_3h": [0.0, 2.0, 1.0],
            "snow_3h": [0.0, 0.0, 0.0],
            "icon": ["01d", "10d", "03d"],
            "conditions": ["clear sky", "light rain", "clouds"],
        }
    )
    return add_local_time(steps, 0)


# Time


def test_local_time_applies_the_offset():
    out = add_local_time(pd.DataFrame({"dt": [MONDAY]}), 2 * HOUR)
    assert out["local_time"].to_list()[0] == pd.Timestamp("2026-01-05 02:00:00")
    assert out["local_date"].to_list() == ["2026-01-05"]


def test_negative_offset_moves_the_local_date_back():
    out = add_local_time(pd.DataFrame({"dt": [MONDAY]}), -5 * HOUR)
    assert out["local_date"].to_list() == ["2026-01-04"]


# Logged history


def test_trend_keeps_one_location_in_time_order():
    trend = temperature_trend(make_log(), "Madrid, ES")
    assert trend["temperature"].to_list() == [15.0, 20.0]
    assert trend["feels_like"].to_list() == [15.5, 19.0]


def test_trend_of_unknown_location_is_empty():
    assert len(temperature_trend(make_log(), "Lima, PE")) == 0


def test_daily_log_stats():
    stats = daily_log_stats(make_log(), "Madrid, ES")
    assert stats["day"].to_list() == ["2026-01-01"]
    assert stats["low"].to_list() == [15.0]
    assert stats["high"].to_list() == [20.0]
    assert stats["range"].to_list() == [5.0]
    assert stats["readings"].to_list() == [2]


def test_history_coverage():
    assert history_coverage(make_log(), "Madrid, ES").to_dict("records") == [{"readings": 2, "span_hours": 2.0}]


def test_history_coverage_of_unknown_location_is_zero():
    assert history_coverage(make_log(), "Lima, PE").to_dict("records") == [{"readings": 0, "span_hours": 0.0}]


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


# Forecast


def test_daily_summary():
    days = daily_summary(make_steps())
    assert days["local_date"].to_list() == ["2026-01-05"]
    assert days["low"].to_list() == [10.0]
    assert days["high"].to_list() == [16.0]
    assert days["pop"].to_list() == [0.5]
    assert days["rain"].to_list() == [3.0]
    # 12:00 is the step closest to 13:00.
    assert days["icon"].to_list() == ["10d"]


def test_daily_summary_splits_days_by_local_time_not_utc():
    # 23:00 UTC and 01:00 UTC are one day at UTC+2 (01:00 and 03:00), but two days at UTC.
    steps = pd.DataFrame(
        {
            "dt": [MONDAY - HOUR, MONDAY + HOUR],
            "temperature": [1.0, 2.0],
            "pop": [0.0, 0.0],
            "rain_3h": [0.0, 0.0],
            "snow_3h": [0.0, 0.0],
            "icon": ["01n", "01n"],
            "conditions": ["clear sky", "clear sky"],
        }
    )
    assert len(daily_summary(add_local_time(steps, 0))) == 2
    assert len(daily_summary(add_local_time(steps, 2 * HOUR))) == 1


def test_daily_summary_stops_at_five_days():
    steps = pd.DataFrame(
        {
            "dt": [MONDAY + day * 24 * HOUR for day in range(7)],
            "temperature": [1.0] * 7,
            "pop": [0.0] * 7,
            "rain_3h": [0.0] * 7,
            "snow_3h": [0.0] * 7,
            "icon": ["01d"] * 7,
            "conditions": ["clear sky"] * 7,
        }
    )
    assert len(daily_summary(add_local_time(steps, 0))) == 5


def test_hourly_plan_places_sunset_between_steps():
    now = MONDAY + 8 * HOUR
    sunset = MONDAY + 13 * HOUR
    plan = hourly_plan(make_steps(), now, sunrise=None, sunset=sunset)
    assert plan["kind"].to_list() == ["step", "step", "sunset", "step"]


def test_hourly_plan_uses_tomorrow_for_a_sunrise_already_passed():
    now = MONDAY + 8 * HOUR
    sunrise = MONDAY + 7 * HOUR
    plan = hourly_plan(make_steps(), now, sunrise=sunrise, sunset=None)
    assert plan["dt"].to_list()[-1] == sunrise + 24 * HOUR
    assert plan["kind"].to_list()[-1] == "sunrise"


def test_hourly_plan_leaves_out_steps_beyond_24_hours():
    now = MONDAY + 15 * HOUR - 25 * HOUR
    plan = hourly_plan(make_steps(), now)
    assert len(plan) == 2


def make_comfort_steps():
    return pd.DataFrame(
        {
            "feels_like": [21.0, 11.0, 21.0, -30.0],
            "pop": [0.0, 0.5, 0.0, 1.0],
            # 10 m/s is 36 km/h, which is 16 km/h above the 20 km/h limit.
            "wind_speed": [1.0, 1.0, 10.0, 30.0],
            "humidity": [50, 50, 80, 100],
        }
    )


def test_comfort_score_known_answers():
    scores = comfort_score(make_comfort_steps())["comfort"].to_list()
    # 1: perfect. 2: 100 - 3x10 - 30x0.5. 3: 100 - 16 - 0.3x10. 4: below zero, limited to 0.
    assert scores == [100.0, 55.0, 81.0, 0.0]


def test_comfort_windows_are_daytime_pairs_best_first():
    steps = pd.DataFrame(
        {
            "dt": [1, 2, 3, 4, 5],
            "local_time": pd.to_datetime(
                ["2026-01-05 06:00", "2026-01-05 09:00", "2026-01-05 12:00", "2026-01-05 15:00", "2026-01-05 18:00"]
            ),
            "pod": ["n", "d", "d", "d", "n"],
            "comfort": [100.0, 50.0, 70.0, 90.0, 100.0],
        }
    )
    windows = comfort_windows(steps)
    # Only 09:00-15:00 (mean 60) and 12:00-18:00 (mean 80) have two daytime steps.
    assert windows["score"].to_list() == [80.0, 60.0]
    assert windows["local_time"].to_list()[0] == pd.Timestamp("2026-01-05 12:00")
    assert windows["end_time"].to_list()[0] == pd.Timestamp("2026-01-05 18:00")


def test_pressure_tendency_uses_24_hours_only():
    # The tenth value is more than 24 hours ahead, so it must be ignored.
    steps = pd.DataFrame({"dt": list(range(10)), "pressure": [1000.0] * 8 + [1005.0, 900.0]})
    assert pressure_tendency(steps).to_dict("records") == [{"start": 1000.0, "end": 1005.0, "change": 5.0, "tendency": "rising"}]


def test_pressure_tendency_steady_and_falling():
    steady = pd.DataFrame({"dt": [1, 2], "pressure": [1000.0, 1002.0]})
    falling = pd.DataFrame({"dt": [1, 2], "pressure": [1000.0, 996.0]})
    assert pressure_tendency(steady)["tendency"].to_list() == ["steady"]
    assert pressure_tendency(falling)["tendency"].to_list() == ["falling"]


# Air quality


def make_air():
    """48 hourly rows over two days: day one is clean, day two is polluted."""
    hours = list(range(48))
    air = pd.DataFrame(
        {
            "dt": [MONDAY + hour * HOUR for hour in hours],
            "aqi": [1] * 24 + [3] * 23 + [4],
            "pm2_5": [10.0] * 24 + [20.0] * 24,
            "pm10": [10.0] * 48,
            "no2": [10.0] * 48,
            "o3": [50.0] * 24 + [120.0] * 24,
        }
    )
    return add_local_time(air, 0)


def test_who_comparison_counts_days_over_each_guideline():
    table = who_comparison(make_air())
    rows = table.to_dict("records")
    pm25 = rows[0]
    assert pm25["pollutant"] == "PM2.5"
    assert pm25["guideline"] == 15
    assert pm25["average_level"] == 15.0
    assert pm25["days"] == 2
    assert pm25["days_over"] == 1
    assert pm25["share_over"] == 50.0
    assert rows[1]["days_over"] == 0


def test_who_comparison_uses_the_8_hour_mean_for_ozone():
    ozone = who_comparison(make_air()).to_dict("records")[3]
    # Day one's 8-hour means are all 50, day two's reach 120.
    assert ozone["pollutant"] == "O3"
    assert ozone["days_over"] == 1
    assert ozone["average_level"] == 85.0


def test_air_daily_means():
    daily = air_daily_means(make_air())
    assert daily["local_date"].to_list() == ["2026-01-05", "2026-01-06"]
    assert daily["pm2_5"].to_list() == [10.0, 20.0]
    assert daily["aqi"].to_list() == [1, 4]


def test_air_pattern_groups_by_day_and_hour():
    pattern = air_pattern(make_air(), "pm2_5")
    assert len(pattern) == 48
    first = pattern.to_dict("records")[0]
    # Monday (0) at hour 0, in the clean first day.
    assert first == {"day_of_week": 0, "hour": 0, "level": 10.0}


def test_aqi_band_share_includes_empty_bands_and_uses_worst_hour():
    bands = aqi_band_share(make_air())
    assert bands["band"].to_list() == ["Good", "Fair", "Moderate", "Poor", "Very poor"]
    assert bands["days"].to_list() == [1, 0, 0, 1, 0]
    assert bands["share"].to_list() == [50.0, 0.0, 0.0, 50.0, 0.0]


# City comparison


def make_combined_steps():
    return pd.DataFrame(
        {
            "location": ["Oslo, NO", "Oslo, NO", "Madrid, ES", "Madrid, ES"],
            "local_date": ["2026-01-05", "2026-01-06", "2026-01-05", "2026-01-05"],
            "temperature": [0.0, 2.0, 10.0, 20.0],
            "rain_3h": [1.0, 0.0, 0.0, 0.5],
            "pop": [0.2, 0.9, 0.0, 0.1],
            "wind_speed": [10.0, 10.0, 5.0, 5.0],
        }
    )


def test_city_forecast_summary_ranks_warmest_first():
    summary = city_forecast_summary(make_combined_steps())
    assert summary["location"].to_list() == ["Madrid, ES", "Oslo, NO"]
    assert summary["average"].to_list() == [15.0, 1.0]
    assert summary["high"].to_list() == [20.0, 2.0]
    assert summary["rain_mm"].to_list() == [0.5, 1.0]
    assert summary["highest_pop"].to_list() == [0.1, 0.9]
    assert summary["wind_kmh"].to_list() == [18.0, 36.0]


def test_city_daily_highs():
    daily = city_daily_highs(make_combined_steps())
    assert daily.to_dict("records")[0] == {"location": "Madrid, ES", "local_date": "2026-01-05", "high": 20.0, "rain_mm": 0.5}
    assert len(daily) == 3
