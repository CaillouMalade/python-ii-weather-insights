# Small hand-made cases with known answers, the pattern from the starter's test comment.

import pandas as pd

from weather_app.display import today_high_low
from weather_app.analytics import (
    add_local_time,
    air_by_hour,
    aqi_day_shares,
    city_week_summary,
    comfort_score,
    complete_days,
    daily_log_stats,
    daily_summary,
    daily_worst_aqi,
    day_parts,
    days_over_any_guideline,
    forecast_measures,
    history_series,
    log_coverage,
    next_rain,
    next_steps,
    part_of_day,
    pressure_tendency,
    who_comparison,
    windiest_moment,
    with_today_range,
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


def test_days_over_any_guideline():
    assert days_over_any_guideline(make_air()).to_dict("records") == [{"days": 2, "days_over": 1}]


def test_complete_days_drop_part_days():
    hours = [MONDAY + 12 * HOUR + hour * HOUR for hour in range(36)]
    air = add_local_time(pd.DataFrame({"dt": hours}), 0)
    # 12 hours on Monday, then all 24 on Tuesday.
    assert complete_days(air, 90)["local_date"].unique().tolist() == ["2026-01-06"]


def test_complete_days_keep_only_the_latest_count():
    air = add_local_time(pd.DataFrame({"dt": [MONDAY + hour * HOUR for hour in range(72)]}), 0)
    assert complete_days(air, 2)["local_date"].unique().tolist() == ["2026-01-06", "2026-01-07"]


def test_daily_worst_aqi():
    assert daily_worst_aqi(make_air())["aqi"].to_list() == [1, 4]


def test_air_by_hour_uses_local_hours():
    air = add_local_time(pd.DataFrame({"dt": [MONDAY, MONDAY + 24 * HOUR, MONDAY + HOUR], "pm2_5": [10.0, 20.0, 40.0]}), HOUR)
    rows = air_by_hour(air, "pm2_5").to_dict("records")
    assert rows == [{"hour": 1, "level": 15.0}, {"hour": 2, "level": 40.0}]


# City comparison


def test_forecast_measures_units():
    measures = forecast_measures(make_steps())
    assert measures["wind_kmh"].to_list() == [3.6, 36.0, 7.2]
    assert measures["gust_kmh"].to_list() == [7.2, 72.0, 10.8]
    assert measures["precipitation_mm"].to_list() == [0.0, 2.0, 1.5]


def test_forecast_measures_with_no_gusts_at_all():
    steps = make_steps()
    steps["wind_gust"] = [None, None, None]
    measures = forecast_measures(steps)
    assert measures["gust_kmh"].isna().to_list() == [True, True, True]


def test_today_row_agrees_with_the_header_figures():
    # Rio: the current reading says 33°, while the forecast's rest of today only reaches 32°.
    days = pd.DataFrame({"local_date": ["2026-01-05", "2026-01-06"], "high": [32.0, 30.0], "low": [24.0, 22.0]})
    high, low = today_high_low(days, "2026-01-05", 33.0, 25.0)
    out = with_today_range(days, "2026-01-05", high, low).to_dict("records")
    assert (out[0]["high"], out[0]["low"]) == (high, low) == (33.0, 24.0)
    # Other days and the original table stay as they were.
    assert (out[1]["high"], out[1]["low"]) == (30.0, 22.0)
    assert days["high"].to_list() == [32.0, 30.0]


def test_next_rain_and_windiest_moment():
    measures = forecast_measures(make_steps())
    assert next_rain(measures)["dt"].to_list() == [MONDAY + 12 * HOUR]
    assert windiest_moment(measures)["dt"].to_list() == [MONDAY + 12 * HOUR]


def test_part_of_day_boundaries():
    assert part_of_day(5) is None
    assert part_of_day(6) == "Morning"
    assert part_of_day(12) == "Afternoon"
    assert part_of_day(18) == "Evening"


def test_day_parts_groups_rates_and_gives_reasons():
    # 03:00 is night and left out. 09:00 is morning. 12:00 and 15:00 are afternoon.
    steps = pd.DataFrame(
        {
            "dt": [MONDAY + 3 * HOUR, MONDAY + 9 * HOUR, MONDAY + 12 * HOUR, MONDAY + 15 * HOUR],
            "temperature": [5.0, 18.0, 20.0, 20.0],
            "feels_like": [5.0, 21.0, 21.0, 21.0],
            "pop": [0.0, 0.0, 0.8, 0.2],
            "rain_3h": [0.0, 0.0, 2.0, 0.0],
            "snow_3h": [0.0, 0.0, 0.0, 0.0],
            "wind_speed": [1.0, 1.0, 1.0, 1.0],
            "wind_gust": [1.0, 1.0, 1.0, 1.0],
            "humidity": [50, 50, 50, 50],
        }
    )
    parts = day_parts(forecast_measures(add_local_time(steps, 0))).to_dict("records")
    assert [row["part"] for row in parts] == ["Morning", "Afternoon"]
    assert parts[0]["rating"] == "Great"
    assert parts[0]["reason"] == "pleasant"
    # Afternoon's mean score is 85, but rain likely limits it to 59, so the word cannot contradict the weather.
    assert parts[1]["comfort"] == 59
    assert parts[1]["rating"] == "OK"
    assert parts[1]["reason"] == "rain likely"


def test_day_parts_keep_time_order_across_days():
    steps = make_steps()
    later = steps.copy()
    later["dt"] = later["dt"] + 24 * HOUR
    both = add_local_time(pd.concat([later, steps], ignore_index=True)[["dt", "temperature", "feels_like", "pop", "rain_3h", "snow_3h", "wind_speed", "wind_gust", "humidity"]], 0)
    parts = day_parts(forecast_measures(both)).to_dict("records")
    assert [(row["local_date"], row["part"]) for row in parts] == [
        ("2026-01-05", "Morning"),
        ("2026-01-05", "Afternoon"),
        ("2026-01-06", "Morning"),
        ("2026-01-06", "Afternoon"),
    ]


def test_who_comparison_counts_days_and_puts_the_worst_first():
    rows = who_comparison(make_air()).to_dict("records")
    # PM2.5 and ozone are each over on the polluted day. PM10 and NO2 never are.
    assert rows[0] == {"pollutant": "pm2_5", "guideline": 15, "days": 2, "days_over": 1}
    assert rows[1] == {"pollutant": "o3", "guideline": 100, "days": 2, "days_over": 1}
    assert rows[2]["days_over"] == 0


def test_who_comparison_uses_the_8_hour_mean_for_ozone():
    # 150 for only three hours, then 50: the 8-hour mean stays under 100 although single hours do not.
    air = make_air()
    air["o3"] = [50.0] * 21 + [150.0] * 3 + [50.0] * 24
    ozone = who_comparison(air).to_dict("records")
    days_over = [row["days_over"] for row in ozone if row["pollutant"] == "o3"]
    assert days_over == [0]


def test_aqi_day_shares_counts_all_five_bands_by_each_days_worst_hour():
    shares = aqi_day_shares(make_air()).to_dict("records")
    assert [row["band"] for row in shares] == ["Good", "Fair", "Moderate", "Poor", "Very poor"]
    assert [row["days"] for row in shares] == [1, 0, 0, 1, 0]
    assert [row["share"] for row in shares] == [50.0, 0.0, 0.0, 50.0, 0.0]


def test_city_week_summary():
    measures = pd.DataFrame(
        {
            "location": ["Oslo, NO", "Oslo, NO", "Madrid, ES"],
            "temperature": [0.0, 2.0, 20.0],
            "precipitation_mm": [1.0, 2.0, 0.0],
            "wind_kmh": [10.0, 20.0, 5.0],
        }
    )
    rows = city_week_summary(measures).to_dict("records")
    assert rows[0] == {"location": "Madrid, ES", "high": 20.0, "low": 20.0, "rain_mm": 0.0, "wind_kmh": 5.0}
    assert rows[1] == {"location": "Oslo, NO", "high": 2.0, "low": 0.0, "rain_mm": 3.0, "wind_kmh": 15.0}
