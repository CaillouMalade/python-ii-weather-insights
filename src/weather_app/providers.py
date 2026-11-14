"""Keyless forecast providers. Each one turns its own answer into ForecastPoints
on the same 3-hour UTC windows as OpenWeatherMap (00, 03, ... 21)."""

from datetime import datetime, timedelta, timezone

from .client import APIClient, validate_location
from .models import ForecastPoint

WINDOW_HOURS = 3
FORECAST_DAYS = 5  # same reach as OpenWeatherMap's 5-day forecast

# MET Norway's terms ask every app to name itself; requests without a User-Agent are refused.
MET_USER_AGENT = "racetrack-weather/0.1 github.com/CaillouMalade/python-ii-weather-insights"


def is_window_start(time_utc):
    """True for 00:00, 03:00, ... 21:00."""
    return time_utc.hour % WINDOW_HOURS == 0 and time_utc.minute == 0


def window_start(time_utc):
    """Return the start of the 3-hour window a time falls in (14:20 gives 12:00)."""
    hour = time_utc.hour - time_utc.hour % WINDOW_HOURS
    return time_utc.replace(hour=hour, minute=0, second=0, microsecond=0)


def sum_rain(amounts):
    """Add up the rain of the hours in one window, or None if any hour is missing."""
    # A partial sum would look like a real (too low) value, so we don't make one.
    total = 0
    for amount in amounts:
        if amount is None:
            return None
        total = total + amount
    return total


def keep_next_five_days(points, now):
    """Keep the points from the current window up to 5 days ahead."""
    first = window_start(now)
    last = first + timedelta(days=FORECAST_DAYS)
    kept = []
    for point in points:
        if first <= point.time_utc < last:
            kept.append(point)
    return kept


class OpenMeteoClient(APIClient):
    """Open-Meteo: free, no key, hourly values."""

    def __init__(self):
        super().__init__("https://api.open-meteo.com/v1", None, None)
        self.source = "open-meteo"

    def forecast(self, location, now=None):
        """Return a list of ForecastPoints for a location dictionary."""
        validate_location(location)
        if now is None:
            now = datetime.now(timezone.utc)
        params = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "hourly": "temperature_2m,wind_speed_10m,wind_direction_10m,precipitation",
            "wind_speed_unit": "ms",
            "timezone": "UTC",
            "forecast_days": FORECAST_DAYS + 1,  # one extra day, so the cut below always has enough
        }
        data = self._get("forecast", params)

        try:
            hourly = data["hourly"]
            times = hourly["time"]
            temperatures = hourly["temperature_2m"]
            wind_speeds = hourly["wind_speed_10m"]
            wind_directions = hourly["wind_direction_10m"]
            rains = hourly["precipitation"]

            points = []
            for i in range(len(times)):
                # Open-Meteo sends "2026-11-16T03:00" without a zone; we asked for UTC.
                time_utc = datetime.fromisoformat(times[i]).replace(tzinfo=timezone.utc)
                if not is_window_start(time_utc):
                    continue
                # The window needs the 3 hours after its start in the answer.
                if i + WINDOW_HOURS >= len(times):
                    break
                # Open-Meteo's rain at 03:00 fell from 02:00 to 03:00, so the
                # window 00:00-03:00 is the values at 01:00, 02:00 and 03:00.
                rain = sum_rain([rains[i + 1], rains[i + 2], rains[i + 3]])
                points.append(ForecastPoint(self.source, time_utc, temperatures[i], wind_speeds[i], wind_directions[i], rain))
        except (KeyError, IndexError, TypeError, ValueError):
            raise ValueError("Open-Meteo sent a forecast in an unexpected format.") from None

        return keep_next_five_days(points, now)


class MetNorwayClient(APIClient):
    """MET Norway Locationforecast: free, no key, but it needs a User-Agent header."""

    def __init__(self):
        super().__init__("https://api.met.no/weatherapi/locationforecast/2.0", None, None)
        self.source = "met-norway"
        self.headers["User-Agent"] = MET_USER_AGENT

    def forecast(self, location, now=None):
        """Return a list of ForecastPoints for a location dictionary."""
        validate_location(location)
        if now is None:
            now = datetime.now(timezone.utc)
        # MET asks for no more than 4 decimals in the coordinates.
        params = {"lat": round(location["latitude"], 4), "lon": round(location["longitude"], 4)}
        data = self._get("compact", params)

        try:
            timeseries = data["properties"]["timeseries"]

            # First note the rain of every hour that has one. Further out, MET only
            # sends 6-hour blocks without "next_1_hours", so those hours are not noted.
            rain_by_hour = {}
            for entry in timeseries:
                if "next_1_hours" in entry["data"]:
                    hour = datetime.fromisoformat(entry["time"])
                    rain_by_hour[hour] = entry["data"]["next_1_hours"]["details"].get("precipitation_amount")

            points = []
            for entry in timeseries:
                # MET sends "2026-11-16T03:00:00Z"; the Z means UTC.
                time_utc = datetime.fromisoformat(entry["time"])
                if not is_window_start(time_utc):
                    continue
                # A window is used only when all 3 of its hours are hourly data.
                hours = [time_utc, time_utc + timedelta(hours=1), time_utc + timedelta(hours=2)]
                complete = True
                for hour in hours:
                    if hour not in rain_by_hour:
                        complete = False
                if not complete:
                    continue
                # "next_1_hours" at 00:00 is the rain from 00:00 to 01:00,
                # so the window 00:00-03:00 adds up 00:00, 01:00 and 02:00.
                rain = sum_rain([rain_by_hour[hours[0]], rain_by_hour[hours[1]], rain_by_hour[hours[2]]])
                details = entry["data"]["instant"]["details"]
                points.append(ForecastPoint(
                    self.source,
                    time_utc,
                    details.get("air_temperature"),
                    details.get("wind_speed"),
                    details.get("wind_from_direction"),
                    rain,
                ))
        except (KeyError, IndexError, TypeError, ValueError):
            raise ValueError("MET Norway sent a forecast in an unexpected format.") from None

        return keep_next_five_days(points, now)
