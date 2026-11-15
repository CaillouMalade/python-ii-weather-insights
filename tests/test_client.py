# requests.get is swapped for a fake and put back afterwards, so these tests need
# no key and make no calls. (pytest fixtures such as monkeypatch are not used in this project.)

from datetime import datetime, timedelta, timezone

import pytest
import requests

from weather_app import client
from weather_app.client import WeatherClient, validate_city, validate_location

MADRID = {"location": "Madrid, ES", "latitude": 40.4, "longitude": -3.7}
CURRENT = {"main": {"temp": 20.0, "feels_like": 19.0, "humidity": 40}, "wind": {"speed": 2.0}, "weather": [{"description": "clear sky"}]}


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self.data = data

    def json(self):
        return self.data


class UnreadableResponse(FakeResponse):
    """A 200 answer whose body is not JSON, as requests reports it."""

    def json(self):
        raise ValueError("Expecting value: line 1 column 1")


class FakeGet:
    """Stands in for requests.get: returns a response, or raises an error."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def __call__(self, url, params, timeout, headers=None):
        self.calls = self.calls + 1
        if self.error is not None:
            raise self.error
        return self.response


def error_message(fake, action, *args):
    """Run action with the fake in place of requests.get and return the ValueError's message."""
    original = client.requests.get
    client.requests.get = fake
    try:
        action(*args)
    except ValueError as error:
        return str(error)
    finally:
        client.requests.get = original
    return None


def test_current_builds_a_reading():
    original = client.requests.get
    client.requests.get = FakeGet(FakeResponse(200, CURRENT))
    try:
        reading = WeatherClient("key").current(MADRID)
    finally:
        client.requests.get = original
    assert reading.location == "Madrid, ES"
    assert reading.temperature == 20.0


def test_each_failure_has_its_own_message():
    current = WeatherClient("key").current
    assert "API key" in error_message(FakeGet(FakeResponse(401)), current, MADRID)
    assert "could not find" in error_message(FakeGet(FakeResponse(404)), current, MADRID)
    assert "status 500" in error_message(FakeGet(FakeResponse(500)), current, MADRID)
    assert "too long" in error_message(FakeGet(error=requests.exceptions.Timeout()), current, MADRID)
    message = error_message(FakeGet(error=requests.exceptions.ConnectionError("https://x?appid=secret")), current, MADRID)
    assert "internet connection" in message
    assert "secret" not in message


def test_unknown_city_is_reported():
    message = error_message(FakeGet(FakeResponse(200, [])), WeatherClient("key").find_city, "  Atlantis ")
    assert message == "City 'Atlantis' was not found. Check the spelling."


def test_find_city_returns_a_location():
    original = client.requests.get
    client.requests.get = FakeGet(FakeResponse(200, [{"name": "Oslo", "country": "NO", "lat": 59.9, "lon": 10.7}]))
    try:
        city = WeatherClient("key").find_city("oslo")
    finally:
        client.requests.get = original
    assert city == {"location": "Oslo, NO", "latitude": 59.9, "longitude": 10.7}


def test_bad_input_is_stopped_before_any_call():
    fake = FakeGet(FakeResponse(200, []))
    for text in ["", "   ", "12345", "x" * 101]:
        assert error_message(fake, WeatherClient("key").find_city, text) is not None
    assert fake.calls == 0
    with pytest.raises(ValueError, match="outside the valid range"):
        validate_location({"location": "Nowhere", "latitude": 95.0, "longitude": 0.0})
    assert validate_city("  Paris ") == "Paris"


def test_key_is_private():
    weather = WeatherClient("secret")
    assert not hasattr(weather, "api_key")
    assert not hasattr(weather, "__api_key")


# A small invented OpenWeatherMap forecast, starting Monday 16 Nov 2026 at 00:00 UTC.
START = datetime(2026, 11, 16, 0, 0, tzinfo=timezone.utc)


def owm_item(hours_after_start, temperature, rain=None):
    """One item of OWM's forecast list; "rain" is left out when it doesn't rain, as OWM does."""
    time_utc = START + timedelta(hours=hours_after_start)
    item = {"dt": int(time_utc.timestamp()), "main": {"temp": temperature}, "wind": {"speed": 4.0, "deg": 225}}
    if rain is not None:
        item["rain"] = {"3h": rain}
    return item


def run_forecast(data, now=START):
    """Call WeatherClient.forecast with a fake 200 answer and return the points."""
    original = client.requests.get
    client.requests.get = FakeGet(FakeResponse(200, data))
    try:
        return WeatherClient("key").forecast(MADRID, now)
    finally:
        client.requests.get = original


def test_forecast_puts_rain_in_the_window_it_fell_in():
    data = {"list": [owm_item(0, 10.0), owm_item(3, 11.0, rain=1.2), owm_item(6, 12.0)]}
    points = run_forecast(data)
    assert [point.time_utc.hour for point in points] == [0, 3, 6]
    assert points[0].source == "openweathermap"
    assert points[0].temperature == 10.0
    assert points[0].wind_deg == 225
    # rain.3h sent at 03:00 fell from 00:00 to 03:00.
    assert points[0].rain == 1.2
    # No "rain" at 06:00 means it didn't rain: 0 mm.
    assert points[1].rain == 0
    # The last window has no item after it, so its rain is unknown.
    assert points[2].rain is None


def test_forecast_keeps_five_days_from_the_current_window():
    items = []
    for step in range(48):  # 6 days of 3-hour items
        items.append(owm_item(step * 3, 10.0))
    points = run_forecast({"list": items}, now=START + timedelta(hours=1))
    assert len(points) == 40  # 5 days x 8 windows
    assert points[0].time_utc == START
    assert points[-1].time_utc == START + timedelta(days=5, hours=-3)


def test_forecast_each_failure_has_its_own_message():
    forecast = WeatherClient("key").forecast
    assert "API key" in error_message(FakeGet(FakeResponse(401)), forecast, MADRID)
    assert "could not find" in error_message(FakeGet(FakeResponse(404)), forecast, MADRID)
    assert "did not accept" in error_message(FakeGet(FakeResponse(400)), forecast, MADRID)
    assert "Too many requests" in error_message(FakeGet(FakeResponse(429)), forecast, MADRID)
    assert "problem on its side" in error_message(FakeGet(FakeResponse(503)), forecast, MADRID)
    assert "too long" in error_message(FakeGet(error=requests.exceptions.Timeout()), forecast, MADRID)
    assert "internet connection" in error_message(FakeGet(error=requests.exceptions.ConnectionError()), forecast, MADRID)
    assert "could not be read" in error_message(FakeGet(UnreadableResponse(200)), forecast, MADRID)
    message = error_message(FakeGet(FakeResponse(200, {"cod": "200"})), forecast, MADRID)
    assert message == "OpenWeatherMap sent a forecast in an unexpected format."
    message = error_message(FakeGet(FakeResponse(200, {"list": [{"dt": 0}]})), forecast, MADRID)
    assert message == "OpenWeatherMap sent a forecast in an unexpected format."


def test_forecast_bad_location_is_stopped_before_any_call():
    fake = FakeGet(FakeResponse(200, {"list": []}))
    assert "outside the valid range" in error_message(fake, WeatherClient("key").forecast, {"location": "Nowhere", "latitude": 95.0, "longitude": 0.0})
    assert "no name" in error_message(fake, WeatherClient("key").forecast, {"location": "", "latitude": 45.0, "longitude": 9.0})
    assert fake.calls == 0
