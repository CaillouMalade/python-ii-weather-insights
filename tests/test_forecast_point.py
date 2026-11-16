from fake_forecast import fake_forecasts

from weather_app.models import ForecastPoint


def test_wind_kmh_converts_from_metres_per_second():
    point = ForecastPoint("openweathermap", None, 10, 5, 180, 0)
    assert point.wind_kmh == 18


def test_wind_kmh_is_none_without_wind():
    point = ForecastPoint("open-meteo", None, 10, None, None, 0)
    assert point.wind_kmh is None


def test_fake_providers_share_the_same_windows():
    forecasts = fake_forecasts()
    assert len(forecasts) == 3
    times = [[point.time_utc for point in points] for points in forecasts.values()]
    assert times[0] == times[1] == times[2]
