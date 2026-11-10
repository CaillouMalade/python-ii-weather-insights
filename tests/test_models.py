from weather_app.analytics import rank_by_temperature
from weather_app.models import WeatherReading


def make(location, temperature, feels_like=None, wind_speed=2.0):
    if feels_like is None:
        feels_like = temperature
    return WeatherReading(location, 0.0, 0.0, temperature, feels_like, 50, wind_speed, "clear sky")


def test_wind_kmh_converts_from_metres_per_second():
    assert make("A", 10, wind_speed=10).wind_kmh == 36


def test_feels_like_gap():
    assert make("A", 10, feels_like=7.5).feels_like_gap == -2.5


def test_sorted_uses_temperature():
    readings = [make("Mild", 15), make("Cold", 2), make("Hot", 30)]
    assert [reading.location for reading in sorted(readings)] == ["Cold", "Mild", "Hot"]
    assert [reading.location for reading in rank_by_temperature(readings)] == ["Hot", "Mild", "Cold"]


def test_text_forms():
    reading = make("Madrid, ES", 20)
    assert repr(reading) == "WeatherReading('Madrid, ES', 20°C)"
    assert str(reading) == "Madrid, ES: 20.0°C, clear sky"
