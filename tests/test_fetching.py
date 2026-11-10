from weather_app import fetching
from weather_app.models import WeatherReading


def fake_fetch(location):
    if location["location"] == "Bad":
        raise ValueError("OpenWeatherMap could not find this location.")
    return WeatherReading(location["location"], 0.0, 0.0, 10.0, 9.0, 50, 1.0, "clouds")


def test_one_bad_location_does_not_stop_the_rest():
    original = fetching.fetch_and_log
    fetching.fetch_and_log = fake_fetch
    try:
        readings, failures = fetching.fetch_many([{"location": "A"}, {"location": "Bad"}, {"location": "B"}])
    finally:
        fetching.fetch_and_log = original
    assert [reading.location for reading in readings] == ["A", "B"]
    assert failures == ["Bad: OpenWeatherMap could not find this location."]
