# Small hand-made cases with known answers, the pattern from the starter's test comment.

import pandas as pd

from weather_app.analytics import (
    add_local_time,
    air_by_hour,
    air_calendar,
    city_day_grid,
    city_day_values,
    comfort_score,
    daily_log_stats,
    daily_summary,
    daily_worst_aqi,
    days_over_any_guideline,
    forecast_measures,
    history_series,
    log_coverage,
    next_rain,
    next_steps,
    pressure_tendency,
    rank_cities,
    ranked_windows,
    week_grid,
    who_comparison,
    windiest_moment,
)

# 2026-01-05 is a Monday. This is 00:00 UTC that day, in Unix seconds.
MONDAY = 1767571200
HOUR = 3600


def make_log():
    """Four readings, deliberately out of time order. Only Madrid has a logged UTC offset."""
    return pd.DataFrame(
        {
            "timestamp_utc": pd.to_datetime(
                [
                    "2026-01-02T12:00:00+00:00",
                    "2026-01-01T10:00:00+00:00",
                    "2026-01-01T11:00:00+00:00",
                    "2026-01-01T09:00:00+00:00",
                ]
            ),
            "location": ["Madrid, ES", "Madrid, ES", "Oslo, NO", "Oslo, NO"],
            "temperature": [20.0, 15.0, -2.0, 30.0],
            "feels_like": [19.0, 15.5, -6.0, 30.0],
            "humidity": [40, 50, 60, 70],
            "wind_speed": [10.0, 5.0, 1.0, 2.0],
            "timezone_offset": [3600.0, None, None, None],
        }
    )


def make_steps():
    """Three forecast steps, three hours apart, starting at Monday 09:00 local (offset 0)."""
    steps = pd.DataFrame(
        {
            "dt": [MONDAY + 9 * HOUR, MONDAY + 12 * HOUR, MONDAY + 15 * HOUR],
            "temperature": [10.0, 16.0, 13.0],
            "feels_like": [21.0, 11.0, 21.0],
            "pop": [0.0, 0.5, 0.2],
            "rain_3h": [0.0, 2.0, 1.0],
            "snow_3h": [0.0, 0.0, 0.5],
            "icon": ["01d", "10d", "03d"],
            "wind_speed": [1.0, 10.0, 2.0],
            "wind_gust": [2.0, 20.0, 3.0],
            "humidity": [50, 50, 50],
            "pod": ["d", "d", "d"],
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


def test_log_coverage():
    rows = log_coverage(make_log()).to_dict("records")
    assert rows[0] == {"location": "Madrid, ES", "readings": 2, "span_hours": 26.0}
    assert rows[1] == {"location": "Oslo, NO", "readings": 2, "span_hours": 2.0}


def test_history_series_is_in_order_with_local_time_from_the_known_offset():
    series = history_series(make_log(), "Madrid, ES")
    assert series["temperature"].to_list() == [15.0, 20.0]
    assert series["is_local"].to_list() == [True, True]
    # 10:00 UTC at the logged offset of one hour, even though this older row has no offset itself.
    assert series["time"].to_list()[0] == pd.Timestamp("2026-01-01 11:00:00")


def test_history_series_stays_utc_without_any_offset():
    series = history_series(make_log(), "Oslo, NO")
    assert series["is_local"].to_list() == [False, False]
    assert series["time"].to_list()[0] == pd.Timestamp("2026-01-01 09:00:00")


def test_history_series_measures():
    series = history_series(make_log(), "Madrid, ES")
    assert series["feels_delta"].to_list() == [0.5, -1.0]
    assert series["wind_kmh"].to_list() == [18.0, 36.0]


def test_history_series_of_unknown_location_is_empty():
    assert len(history_series(make_log(), "Lima, PE")) == 0


def test_daily_log_stats():
    series = pd.DataFrame(
        {
            "time": pd.to_datetime(["2026-01-01 09:00", "2026-01-01 18:00", "2026-01-02 09:00"]),
            "temperature": [10.0, 14.5, 7.0],
        }
    )
    stats = daily_log_stats(series)
    assert stats["day"].to_list() == ["2026-01-01", "2026-01-02"]
    assert stats["low"].to_list() == [10.0, 7.0]
    assert stats["high"].to_list() == [14.5, 7.0]
    assert stats["range"].to_list() == [4.5, 0.0]
    assert stats["readings"].to_list() == [2, 1]


def test_functions_do_not_change_the_input():
    log = make_log()
    columns = log.columns.to_list()
    log_coverage(log)
    history_series(log, "Madrid, ES")
    assert log.columns.to_list() == columns
    assert log["temperature"].to_list() == [20.0, 15.0, -2.0, 30.0]


# Forecast


def test_daily_summary():
    days = daily_summary(make_steps())
    assert days["local_date"].to_list() == ["2026-01-05"]
    assert days["low"].to_list() == [10.0]
    assert days["high"].to_list() == [16.0]
    assert days["pop"].to_list() == [0.5]
    # 12:00 is the step closest to 13:00.
    assert days["icon"].to_list() == ["10d"]


def test_daily_summary_splits_days_by_local_time_not_utc():
    # 23:00 UTC and 01:00 UTC are one day at UTC+2 (01:00 and 03:00), but two days at UTC.
    steps = pd.DataFrame({"dt": [MONDAY - HOUR, MONDAY + HOUR], "temperature": [1.0, 2.0], "pop": [0.0, 0.0], "icon": ["01n", "01n"]})
    assert len(daily_summary(add_local_time(steps, 0))) == 2
    assert len(daily_summary(add_local_time(steps, 2 * HOUR))) == 1


def test_daily_summary_stops_at_five_days():
    steps = pd.DataFrame({"dt": [MONDAY + day * 24 * HOUR for day in range(7)], "temperature": [1.0] * 7, "pop": [0.0] * 7, "icon": ["01d"] * 7})
    assert len(daily_summary(add_local_time(steps, 0))) == 5


def test_next_steps_skips_the_past_and_limits_the_count():
    steps = make_steps()
    assert next_steps(steps, MONDAY + 10 * HOUR, 5)["temperature"].to_list() == [16.0, 13.0]
    assert next_steps(steps, MONDAY, 1)["temperature"].to_list() == [10.0]


def test_comfort_score_known_answers():
    steps = pd.DataFrame(
        {
            "feels_like": [21.0, 11.0, 21.0, -30.0],
            "pop": [0.0, 0.5, 0.0, 1.0],
            # 10 m/s is 36 km/h, which is 16 km/h above the 20 km/h limit.
            "wind_speed": [1.0, 1.0, 10.0, 30.0],
            "humidity": [50, 50, 80, 100],
        }
    )
    # 1: perfect. 2: 100 - 3x10 - 30x0.5. 3: 100 - 16 - 0.3x10. 4: below zero, limited to 0.
    assert comfort_score(steps)["comfort"].to_list() == [100.0, 55.0, 81.0, 0.0]


def test_forecast_measures_units_and_labels():
    measures = forecast_measures(make_steps())
    assert measures["wind_kmh"].to_list() == [3.6, 36.0, 7.2]
    assert measures["pop_percent"].to_list() == [0.0, 50.0, 20.0]
    assert measures["precipitation_mm"].to_list() == [0.0, 2.0, 1.5]
    assert measures["time_of_day"].to_list() == ["09:00", "12:00", "15:00"]


def test_week_grid_has_one_row_per_date_and_one_column_per_time():
    measures = pd.DataFrame(
        {
            "local_date": ["2026-01-05", "2026-01-05", "2026-01-06"],
            "time_of_day": ["09:00", "12:00", "09:00"],
            "temperature": [10.4, 16.0, 7.6],
        }
    )
    grid = week_grid(measures, "temperature")
    assert grid.index.to_list() == ["2026-01-05", "2026-01-06"]
    assert grid.columns.to_list() == ["09:00", "12:00"]
    assert grid.loc["2026-01-05", "09:00"] == 10.0
    assert grid.loc["2026-01-06", "09:00"] == 8.0
    # Nothing was forecast for that cell, and it must stay empty rather than become zero.
    assert pd.isna(grid.loc["2026-01-06", "12:00"])


def make_window_measures():
    """Five daytime steps then a night step. Scores peak at 12:00-15:00."""
    return pd.DataFrame(
        {
            "dt": [1, 2, 3, 4, 5, 6],
            "local_time": pd.to_datetime(
                ["2026-01-05 06:00", "2026-01-05 09:00", "2026-01-05 12:00", "2026-01-05 15:00", "2026-01-05 18:00", "2026-01-05 21:00"]
            ),
            "pod": ["d", "d", "d", "d", "d", "n"],
            "comfort": [10.0, 50.0, 90.0, 70.0, 30.0, 100.0],
            "feels_like": [10.0, 14.0, 20.0, 22.0, 16.0, 21.0],
            "pop_percent": [0.0, 10.0, 20.0, 40.0, 0.0, 0.0],
            "wind_kmh": [5.0, 6.0, 7.0, 12.0, 8.0, 3.0],
        }
    )


def test_ranked_windows_are_best_first_and_do_not_overlap():
    windows = ranked_windows(make_window_measures())
    # 12:00-18:00 (mean 80) wins. 09:00-15:00 and 15:00-21:00 overlap it, so 06:00-12:00 (mean 30) is next.
    assert windows["score"].to_list() == [80.0, 30.0]
    assert windows["local_time"].to_list() == [pd.Timestamp("2026-01-05 12:00"), pd.Timestamp("2026-01-05 06:00")]
    assert windows["end_time"].to_list()[0] == pd.Timestamp("2026-01-05 18:00")


def test_ranked_windows_give_the_reasons():
    best = ranked_windows(make_window_measures()).to_dict("records")[0]
    assert best["feels"] == 21.0
    assert best["rain_chance"] == 40.0
    assert best["wind"] == 12.0


def test_ranked_windows_skip_night_and_can_be_empty():
    measures = make_window_measures()
    measures["pod"] = ["n", "n", "d", "n", "n", "n"]
    assert len(ranked_windows(measures)) == 0


def test_next_rain_and_windiest_moment():
    measures = forecast_measures(make_steps())
    assert next_rain(measures)["time_of_day"].to_list() == ["12:00"]
    assert windiest_moment(measures)["time_of_day"].to_list() == ["12:00"]


def test_next_rain_empty_when_dry():
    measures = pd.DataFrame({"precipitation_mm": [0.0, 0.0]})
    assert len(next_rain(measures)) == 0


def test_pressure_tendency_uses_24_hours_only():
    # The tenth value is more than 24 hours ahead, so it must be ignored.
    steps = pd.DataFrame({"dt": list(range(10)), "pressure": [1000.0] * 8 + [1005.0, 900.0]})
    assert pressure_tendency(steps).to_dict("records") == [{"change": 5.0, "tendency": "rising"}]


def test_pressure_tendency_steady_and_falling():
    steady = pd.DataFrame({"dt": [1, 2], "pressure": [1000.0, 1002.0]})
    falling = pd.DataFrame({"dt": [1, 2], "pressure": [1000.0, 996.0]})
    assert pressure_tendency(steady)["tendency"].to_list() == ["steady"]
    assert pressure_tendency(falling)["tendency"].to_list() == ["falling"]


# Air quality


def make_air():
    """48 hourly rows over two days: day one is clean, day two is polluted."""
    air = pd.DataFrame(
        {
            "dt": [MONDAY + hour * HOUR for hour in range(48)],
            "aqi": [1] * 24 + [3] * 23 + [4],
            "pm2_5": [10.0] * 24 + [20.0] * 24,
            "pm10": [10.0] * 48,
            "no2": [10.0] * 48,
            "o3": [50.0] * 24 + [120.0] * 24,
        }
    )
    return add_local_time(air, 0)


def test_who_comparison_counts_days_over_each_guideline():
    rows = who_comparison(make_air()).to_dict("records")
    assert rows[0] == {"pollutant": "PM2.5", "guideline": 15, "average_level": 15, "days": 2, "days_over": 1, "share_over": 50}
    assert rows[1]["days_over"] == 0


def test_who_comparison_uses_the_8_hour_mean_for_ozone():
    ozone = who_comparison(make_air()).to_dict("records")[3]
    # Day one's 8-hour means are all 50, day two's reach 120.
    assert ozone["pollutant"] == "O3"
    assert ozone["days_over"] == 1
    assert ozone["average_level"] == 85


def test_days_over_any_guideline():
    assert days_over_any_guideline(make_air()).to_dict("records") == [{"days": 2, "days_over": 1}]


def test_daily_worst_aqi():
    assert daily_worst_aqi(make_air())["aqi"].to_list() == [1, 4]


def test_air_calendar_places_days_by_week_and_weekday():
    # Monday 5 and Tuesday 6 January, then Monday 12 January in the next week.
    air = pd.DataFrame({"local_date": ["2026-01-05", "2026-01-06", "2026-01-12"], "aqi": [1, 2, 5]})
    calendar = air_calendar(air)
    assert calendar.columns.to_list() == ["2026-01-05", "2026-01-12"]
    assert calendar.index.to_list() == [0, 1]
    assert calendar.loc[0, "2026-01-05"] == 1
    assert calendar.loc[1, "2026-01-05"] == 2
    assert calendar.loc[0, "2026-01-12"] == 5
    assert pd.isna(calendar.loc[1, "2026-01-12"])


def test_air_by_hour_uses_local_hours():
    air = add_local_time(pd.DataFrame({"dt": [MONDAY, MONDAY + 24 * HOUR, MONDAY + HOUR], "pm2_5": [10.0, 20.0, 40.0]}), HOUR)
    rows = air_by_hour(air, "pm2_5").to_dict("records")
    assert rows == [{"hour": 1, "level": 15.0}, {"hour": 2, "level": 40.0}]


# City comparison


def make_combined():
    return pd.DataFrame(
        {
            "location": ["Oslo, NO", "Oslo, NO", "Oslo, NO", "Madrid, ES", "Madrid, ES"],
            "local_date": ["2026-01-05", "2026-01-05", "2026-01-06", "2026-01-05", "2026-01-05"],
            "temperature": [0.0, 2.0, 4.0, 10.0, 20.0],
            "precipitation_mm": [1.0, 2.0, 0.0, 0.0, 0.5],
        }
    )


def test_city_day_values_max_and_sum():
    highs = city_day_values(make_combined(), "temperature", "max").to_dict("records")
    assert highs[0] == {"location": "Madrid, ES", "local_date": "2026-01-05", "value": 20.0}
    assert highs[1] == {"location": "Oslo, NO", "local_date": "2026-01-05", "value": 2.0}
    rain = city_day_values(make_combined(), "precipitation_mm", "sum").to_dict("records")
    assert rain[1]["value"] == 3.0


def test_rank_cities_highest_first():
    highs = city_day_values(make_combined(), "temperature", "max")
    ranking = rank_cities(highs, "mean")
    assert ranking["location"].to_list() == ["Madrid, ES", "Oslo, NO"]
    assert ranking["value"].to_list() == [20.0, 3.0]
    assert ranking["rank"].to_list() == [1, 2]


def test_city_day_grid_follows_the_given_order_and_leaves_gaps_empty():
    highs = city_day_values(make_combined(), "temperature", "max")
    grid = city_day_grid(highs, ["Oslo, NO", "Madrid, ES", "Lima, PE"])
    assert grid.index.to_list() == ["Oslo, NO", "Madrid, ES"]
    assert grid.columns.to_list() == ["2026-01-05", "2026-01-06"]
    assert pd.isna(grid.loc["Madrid, ES", "2026-01-06"])
