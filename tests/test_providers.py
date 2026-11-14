# The providers are tested on small saved answers in tests/, with requests.get
# swapped for a fake, so these tests make no internet calls.

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from weather_app import client
from weather_app.providers import MetNorwayClient, OpenMeteoClient, sum_rain, window_start

MONZA = {"location": "Monza", "latitude": 45.62, "longitude": 9.28}
SAMPLES = Path(__file__).parent
# A fixed "now" inside the sample period, so the tests never depend on today's date.
NOW = datetime(2026, 11, 15, 22, 10, tzinfo=timezone.utc)


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


class FakeGet:
    """Stands in for requests.get and remembers the headers and params it was given."""

    def __init__(self, response):
        self.response = response
        self.params = None
        self.headers = None

    def __call__(self, url, params, timeout, headers=None):
        self.params = params
        self.headers = headers
        return self.response


def load_sample(name):
    with open(SAMPLES / name, encoding="utf-8") as file:
        return json.load(file)


def run_forecast(provider, data, now=NOW):
    """Call provider.forecast with a fake answer and return (points, fake)."""
    fake = FakeGet(FakeResponse(200, data))
    original = client.requests.get
    client.requests.get = fake
    try:
        points = provider.forecast(MONZA, now)
    finally:
        client.requests.get = original
    return points, fake


def utc(day, hour):
    return datetime(2026, 11, day, hour, 0, tzinfo=timezone.utc)


def test_window_start_and_sum_rain():
    assert window_start(datetime(2026, 11, 15, 14, 20, tzinfo=timezone.utc)) == utc(15, 12)
    assert sum_rain([0.4, 0.4, 1.4]) == pytest.approx(2.2)
    assert sum_rain([0.4, None, 1.4]) is None


def test_open_meteo_windows_units_and_rain():
    points, fake = run_forecast(OpenMeteoClient(), load_sample("sample_open_meteo.json"))

    # 18:00 is before the current window (21:00) and 09:00 has no 3 hours after it.
    times = [point.time_utc for point in points]
    assert times == [utc(15, 21), utc(16, 0), utc(16, 3), utc(16, 6)]

    first = points[0]
    assert first.source == "open-meteo"
    assert first.temperature == 7.1          # value at 21:00, °C
    assert first.wind_speed == 0.61          # m/s, because we asked for wind_speed_unit=ms
    assert first.wind_kmh == pytest.approx(2.196)
    assert first.wind_deg == 81
    # Rain 21:00-00:00 is the values at 22:00, 23:00 and 00:00.
    assert first.rain == pytest.approx(0.1)
    # Rain 00:00-03:00 is the values at 01:00, 02:00 and 03:00.
    assert points[1].rain == pytest.approx(2.2)

    assert fake.params["wind_speed_unit"] == "ms"
    assert fake.params["timezone"] == "UTC"
    assert "appid" not in fake.params        # no key is sent


def test_open_meteo_unreadable_answer():
    with pytest.raises(ValueError, match="Open-Meteo sent a forecast in an unexpected format"):
        run_forecast(OpenMeteoClient(), {"hourly": {"time": ["2026-11-15T21:00"]}})


def test_open_meteo_rejects_bad_location_before_calling():
    with pytest.raises(ValueError, match="invalid coordinates"):
        OpenMeteoClient().forecast({"location": "Nowhere", "latitude": "abc", "longitude": 9.0}, NOW)


def test_met_norway_windows_units_and_rain():
    points, fake = run_forecast(MetNorwayClient(), load_sample("sample_met_norway.json"))

    # Same windows as Open-Meteo: 18:00 is in the past, 09:00 has no 10:00 and 11:00 in the sample.
    times = [point.time_utc for point in points]
    assert times == [utc(15, 21), utc(16, 0), utc(16, 3), utc(16, 6)]

    first = points[0]
    assert first.source == "met-norway"
    assert first.temperature == 5.5          # value at 21:00, °C
    assert first.wind_speed == 1.0           # MET sends m/s
    assert first.wind_deg == 12.8
    # Rain 00:00-03:00 is next_1_hours at 00:00, 01:00 and 02:00: 0.0 + 0.2 + 0.0.
    assert points[1].rain == pytest.approx(0.2)

    assert "racetrack-weather" in fake.headers["User-Agent"]
    assert fake.params == {"lat": 45.62, "lon": 9.28}


def test_met_norway_skips_windows_without_three_hourly_values():
    data = load_sample("sample_met_norway.json")
    timeseries = data["properties"]["timeseries"]
    # Like further out in a real answer: 01:00 has no hourly rain, 04:00 is missing.
    del timeseries[7]["data"]["next_1_hours"]
    del timeseries[10]
    points, fake = run_forecast(MetNorwayClient(), data)
    times = [point.time_utc for point in points]
    assert times == [utc(15, 21), utc(16, 6)]


def test_met_norway_unreadable_answer():
    with pytest.raises(ValueError, match="MET Norway sent a forecast in an unexpected format"):
        run_forecast(MetNorwayClient(), {"properties": {}})


def test_both_providers_give_the_same_windows():
    open_meteo, fake = run_forecast(OpenMeteoClient(), load_sample("sample_open_meteo.json"))
    met_norway, fake = run_forecast(MetNorwayClient(), load_sample("sample_met_norway.json"))
    open_meteo_times = [point.time_utc for point in open_meteo]
    met_norway_times = [point.time_utc for point in met_norway]
    assert open_meteo_times == met_norway_times
    assert len(open_meteo_times) > 0
