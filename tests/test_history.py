# Known-answer tests for the collected history: local time, hourly values with gaps, and findings.

import pandas as pd

from weather_app.history import circuit_readings, daily, daily_extremes, hourly, rain_finding, temperature_finding, wind_finding
from weather_app.storage import load_circuits, load_history


def make_history(times, temperatures, codes=None, winds=None, gusts=None, location="spa"):
    """Collector rows with the columns the app reads. times are UTC text."""
    count = len(times)
    return pd.DataFrame(
        {
            "fetched_at_utc": times,
            "location_id": [location] * count,
            "temperature_c": temperatures,
            "wind_speed_m_s": winds if winds is not None else [5.0] * count,
            "wind_gust_m_s": gusts if gusts is not None else [None] * count,
            "wind_direction_deg": [225] * count,
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


def test_daily_extremes_only_for_full_days():
    times = every_half_hour("2026-11-01 00:00", 48) + every_half_hour("2026-11-02 00:00", 2)
    temperatures = [10.0] * 48 + [30.0, 30.0]
    temperatures[29] = 18.0  # 14:30
    temperatures[8] = 4.0  # 04:00
    values = hourly(circuit_readings(make_history(times, temperatures), "spa", "UTC"))
    highs, lows = daily_extremes(values, ["2026-11-01"])
    assert highs["time"].to_list() == [pd.Timestamp("2026-11-01 14:00")]
    assert highs["temperature_c"].to_list() == [14.0]
    assert lows["time"].to_list() == [pd.Timestamp("2026-11-01 04:00")]
    assert lows["temperature_c"].to_list() == [7.0]
    assert temperature_finding(highs, lows) == "Warmest 14 °C on Sun 1 Nov 14:00, coldest 7 °C on Sun 1 Nov 04:00."


def test_temperature_finding_without_a_full_day():
    empty = pd.DataFrame({"time": [], "temperature_c": []})
    assert temperature_finding(empty, empty) == "No full day collected yet."


def test_rain_finding():
    days = pd.DataFrame({"day": ["2026-10-31", "2026-11-01", "2026-11-02"], "hours": [24, 24, 12], "rain_hours": [3, 0, 3]})
    assert rain_finding(days) == "Rain in 6 of the 60 hours collected (10 %), on Sat 31 Oct, Mon 2 Nov."
    days["rain_hours"] = [0, 0, 0]
    assert rain_finding(days) == "No rain in the 60 hours collected."


def test_wind_finding_names_the_gust_and_the_usual_direction():
    times = every_half_hour("2026-11-01 10:00", 3)
    readings = circuit_readings(make_history(times, [10.0] * 3, winds=[2.0, 4.0, 0.5], gusts=[None, 10.0, None]), "spa", "UTC")
    assert wind_finding(readings) == "Average 8 km/h, gusts up to 36 km/h on Sun 1 Nov 10:30, mostly from the SW."


def test_wind_finding_when_calm_and_without_gusts():
    readings = circuit_readings(make_history(every_half_hour("2026-11-01 10:00", 2), [10.0] * 2, winds=[0.5, 0.5]), "spa", "UTC")
    assert wind_finding(readings) == "Average 2 km/h."


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
