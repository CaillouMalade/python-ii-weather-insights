# Known-answer tests for the collected history: local time, hourly values with gaps, and findings.

import pandas as pd

from weather_app.history import SHOWN_DAY_HOURS, circuit_readings, daily, daily_rows, drop_stuck, hourly, rain_finding, shown_days, usual_direction
from weather_app.storage import load_circuits, load_history


def make_history(times, temperatures, codes=None, winds=None, gusts=None, location="spa", directions=None):
    """Collector rows with the columns the app reads. times are UTC text."""
    count = len(times)
    return pd.DataFrame(
        {
            "fetched_at_utc": times,
            "location_id": [location] * count,
            "temperature_c": temperatures,
            "wind_speed_m_s": winds if winds is not None else [5.0] * count,
            "wind_gust_m_s": gusts if gusts is not None else [None] * count,
            "wind_direction_deg": directions if directions is not None else [225] * count,
            "rain_1h_mm": [None] * count,
            "weather_code": codes if codes is not None else [800] * count,
        }
    )


def every_half_hour(start, count):
    """UTC times 30 minutes apart, written like the collector writes them."""
    times = pd.date_range(start, periods=count, freq="30min")
    return [time.strftime("%Y-%m-%dT%H:%M:%S.000000Z") for time in times]


def test_readings_are_one_circuit_in_local_time_and_order():
    history = make_history(["2026-11-01T12:00:00.5Z", "2026-11-01T11:00:00Z"], [12.0, 11.0], winds=[10.0, 2.0])
    history = pd.concat([history, make_history(["2026-11-01T11:30:00Z"], [30.0], location="jerez")], ignore_index=True)
    readings = circuit_readings(history, "spa", "Europe/Brussels")
    # Brussels is UTC+1 in November.
    assert readings["time"].to_list() == [pd.Timestamp("2026-11-01 12:00:00"), pd.Timestamp("2026-11-01 13:00:00.5")]
    assert readings["temperature_c"].to_list() == [11.0, 12.0]
    assert readings["wind_kmh"].to_list() == [7.2, 36.0]


def test_summer_time_is_handled_by_the_zone_name():
    readings = circuit_readings(make_history(["2026-07-01T12:00:00Z"], [25.0]), "spa", "Europe/Brussels")
    assert readings["time"].to_list() == [pd.Timestamp("2026-07-01 14:00:00")]


def test_wet_from_the_condition_code_or_rain_amount():
    history = make_history(every_half_hour("2026-11-01 00:00", 4), [10.0] * 4, codes=[800, 500, 300, 804])
    history.loc[3, "rain_1h_mm"] = 0.3
    assert circuit_readings(history, "spa", "UTC")["wet"].to_list() == [False, True, True, True]


def test_a_gap_stays_empty_in_the_hourly_values():
    # Two hours of readings, then nothing for 5 hours, then one more hour.
    times = every_half_hour("2026-11-02 00:00", 4) + every_half_hour("2026-11-02 07:00", 2)
    readings = circuit_readings(make_history(times, [10.0, 12.0, 14.0, 16.0, 20.0, 22.0]), "spa", "UTC")
    values = hourly(readings)
    assert len(values) == 8
    assert values["temperature_c"].to_list()[:2] == [11.0, 15.0]
    assert values["temperature_c"][2:7].isna().all()
    assert values["temperature_c"].to_list()[7] == 21.0


def test_daily_counts_hours_with_data_and_rain_and_marks_full_days():
    times = every_half_hour("2026-11-01 00:00", 48) + every_half_hour("2026-11-02 00:00", 6)
    codes = [800] * 48 + [500, 500, 800, 800, 800, 800]
    readings = circuit_readings(make_history(times, [10.0] * 54, codes=codes), "spa", "UTC")
    days = daily(hourly(readings))
    assert days["day"].to_list() == ["2026-11-01", "2026-11-02"]
    assert days["hours"].to_list() == [24, 3]
    assert days["rain_hours"].to_list() == [0, 1]
    assert days["full"].to_list() == [True, False]


def test_daily_rows_give_each_day_its_range_wind_and_rain():
    # A full Sunday: 10° most of the day, 4° at 04:00 and 18° at 14:30, rain in two readings,
    # wind from the SW at 18 km/h. Then two calm readings on Monday morning, a partial day.
    times = every_half_hour("2026-11-01 00:00", 48) + every_half_hour("2026-11-02 00:00", 2)
    temperatures = [10.0] * 48 + [6.0, 7.0]
    temperatures[8] = 4.0
    temperatures[29] = 18.0
    codes = [800] * 50
    codes[20] = 500
    codes[21] = 500
    winds = [5.0] * 48 + [0.5, 0.5]
    rows = daily_rows(circuit_readings(make_history(times, temperatures, codes=codes, winds=winds), "spa", "UTC"))
    assert rows["day"].to_list() == ["2026-11-01", "2026-11-02"]
    assert rows["low"].to_list() == [4.0, 6.0]
    assert rows["high"].to_list() == [18.0, 7.0]
    assert rows["wind_kmh"].round(1).to_list() == [18.0, 1.8]
    # 225° is SW; Monday's wind is below CALM_KMH, so it has no usual direction.
    assert rows["direction"].to_list()[0] == 225
    assert pd.isna(rows["direction"].to_list()[1])
    assert rows["rain_hours"].to_list() == [1, 0]
    assert rows["hours"].to_list() == [24, 1]
    assert rows["full"].to_list() == [True, False]


def test_usual_direction_is_the_most_frequent_compass_point():
    # 350° and 10° are both N, so north wins over the two easterly readings.
    assert usual_direction([350, 10, 5, 90, 95]) == 0
    assert usual_direction([200, 230, 225]) == 225
    assert usual_direction([]) is None


def test_rain_finding():
    days = pd.DataFrame({"day": ["2026-10-31", "2026-11-01", "2026-11-02"], "hours": [24, 24, 12], "rain_hours": [3, 0, 3]})
    assert rain_finding(days) == "Rain in 6 of the 60 hours collected (10 %), on Sat 31 Oct, Mon 2 Nov."
    days["rain_hours"] = [0, 0, 0]
    assert rain_finding(days) == "No rain in the 60 hours collected."


def test_le_mans_shows_the_providers_frozen_reading():
    # OpenWeatherMap answered exactly 8.87 °C and 1.34 m/s from 230° for 40 of Le Mans's readings,
    # mostly at night, while humidity and pressure kept changing: a stuck value at that point.
    history = load_history()
    le_mans = history[history["location_id"] == "lemans"]
    frozen = le_mans[(le_mans["temperature_c"] == 8.87) & (le_mans["wind_speed_m_s"] == 1.34)]
    assert len(frozen) == 40
    assert frozen["wind_direction_deg"].unique().tolist() == [230]
    assert frozen["humidity_pct"].nunique() > 5
    # After drop_stuck, only the first of each stuck run is left.
    cleaned = drop_stuck(history)
    left = cleaned[(cleaned["location_id"] == "lemans") & (cleaned["temperature_c"] == 8.87) & (cleaned["wind_speed_m_s"] == 1.34)]
    assert 0 < len(left) < 20
    # The raw history is untouched.
    assert len(history) == 2971


def test_the_real_snapshot_shows_the_2_to_3_november_gap():
    circuits = load_circuits()
    assert len(circuits) == 18
    spa = circuits[[circuit["id"] for circuit in circuits].index("spa")]
    readings = circuit_readings(load_history(), "spa", spa["timezone"])
    values = hourly(readings)
    # The collector stopped after 13:21 on 2 November and restarted at 07:10 on 3 November, Spa time.
    hours = values.set_index("time")["temperature_c"]
    assert hours["2026-11-02 14:00":"2026-11-03 06:00"].isna().all()
    assert len(hours["2026-11-02 14:00":"2026-11-03 06:00"]) == 17
    assert pd.notna(hours["2026-11-02 13:00"])
    assert pd.notna(hours["2026-11-03 07:00"])


def test_a_stuck_run_of_three_keeps_only_its_first_reading():
    times = every_half_hour("2026-11-01 00:00", 5)
    history = make_history(times, [9.0, 8.0, 8.0, 8.0, 7.0])
    cleaned = drop_stuck(history)
    assert cleaned["temperature_c"].to_list() == [9.0, 8.0, 7.0]
    assert cleaned["fetched_at_utc"].to_list() == [times[0], times[1], times[4]]


def test_a_genuine_repeat_of_two_is_kept():
    history = make_history(every_half_hour("2026-11-01 00:00", 4), [9.0, 8.0, 8.0, 7.0])
    assert drop_stuck(history)["temperature_c"].to_list() == [9.0, 8.0, 8.0, 7.0]


def test_a_run_needs_the_same_wind_too():
    # Same temperature three times, but the wind changes: weather, not a stuck reading.
    history = make_history(every_half_hour("2026-11-01 00:00", 3), [8.0, 8.0, 8.0], winds=[2.0, 2.5, 2.0])
    assert len(drop_stuck(history)) == 3


def test_stuck_readings_at_one_location_leave_the_others_alone():
    times = every_half_hour("2026-11-01 00:00", 3)
    history = pd.concat([make_history(times, [8.0, 8.0, 8.0]), make_history(times, [8.0, 8.0, 8.0], winds=[1.0, 2.0, 3.0], location="jerez")], ignore_index=True)
    cleaned = drop_stuck(history)
    assert (cleaned["location_id"] == "spa").sum() == 1
    assert (cleaned["location_id"] == "jerez").sum() == 3


def test_days_with_too_few_hours_are_hidden():
    rows = pd.DataFrame({"day": ["2026-10-29", "2026-10-30", "2026-10-31"], "hours": [SHOWN_DAY_HOURS - 1, SHOWN_DAY_HOURS, 24]})
    assert SHOWN_DAY_HOURS == 12
    assert shown_days(rows)["day"].to_list() == ["2026-10-30", "2026-10-31"]
