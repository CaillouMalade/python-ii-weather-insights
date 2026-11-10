# requests.get is swapped for a fake and put back afterwards, so these tests need
# no key and make no calls. (pytest fixtures such as monkeypatch are not used in this project.)

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


class FakeGet:
    """Stands in for requests.get: returns a response, or raises an error."""

    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = 0

    def __call__(self, url, params, timeout):
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
