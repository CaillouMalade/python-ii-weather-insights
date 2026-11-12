"""A small, invented forecast from three providers, for building and testing
the statistics and the dashboard before the real providers exist.
These numbers are made up: never use them in the app or in data/."""

from datetime import datetime, timedelta, timezone

from weather_app.models import ForecastPoint

FIRST_WINDOW = datetime(2026, 11, 13, 0, 0, tzinfo=timezone.utc)
WINDOWS = 8  # one day of 3-hour windows

# For each provider: temperature (°C), wind (m/s) and rain (mm) per window.
FAKE_VALUES = {
    "openweathermap": ([9, 8, 10, 14, 16, 13, 11, 10], [4, 4, 5, 6, 7, 6, 5, 4], [0, 0, 0, 0.4, 1.2, 0.8, 0, 0]),
    "open-meteo": ([10, 9, 10, 13, 15, 14, 11, 9], [3, 4, 5, 5, 6, 6, 5, 4], [0, 0, 0.1, 0.6, 1.5, 0.5, 0, 0]),
    "met-norway": ([9, 9, 11, 15, 17, 13, 12, 10], [4, 5, 5, 6, 8, 7, 5, 5], [0, 0, 0, 0.2, 0.9, 1.1, 0.2, 0]),
}


def fake_forecasts():
    """Return {source: [ForecastPoint, ...]} with the same 8 windows for every source."""
    forecasts = {}
    for source, (temperatures, winds, rains) in FAKE_VALUES.items():
        points = []
        for i in range(WINDOWS):
            time_utc = FIRST_WINDOW + timedelta(hours=3 * i)
            points.append(ForecastPoint(source, time_utc, temperatures[i], winds[i], 225, rains[i]))
        forecasts[source] = points
    return forecasts
