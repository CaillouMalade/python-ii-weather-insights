"""API clients: a generic JSON client and an OpenWeatherMap subclass."""

from datetime import datetime, timedelta, timezone

import requests

from .models import ForecastPoint, WeatherReading
from .windows import WINDOW_HOURS, is_window_start, keep_next_five_days

BASE_URL = "https://api.openweathermap.org"


class APIClient:
    """Calls any JSON API, with or without a key.

    Another provider would subclass this and only say which endpoints and fields it uses.
    A provider without a key passes api_key=None and key_param=None.
    """

    def __init__(self, base_url, api_key, key_param, timeout=10):
        self.base_url = base_url
        self.key_param = key_param
        self.timeout = timeout
        # Extra request headers; empty by default. MET Norway needs a User-Agent here.
        self.headers = {}
        self._not_found_message = "The requested resource was not found."
        # Name-mangled so callers and subclasses cannot read it by accident.
        # The real protection is keeping the key out of the repo and the browser.
        self.__api_key = api_key

    def _get(self, endpoint, params):
        """Send a GET request and return the JSON, or raise ValueError with a clear message."""
        # Only providers that use a key get one added to the request.
        if self.key_param is not None:
            params[self.key_param] = self.__api_key

        # The messages are fixed text on purpose: the text of a requests error
        # contains the full URL, and the URL contains the API key.
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params, headers=self.headers, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise ValueError("The weather service took too long to respond. Please try again.") from None
        except requests.exceptions.ConnectionError:
            raise ValueError("Could not connect to the weather service. Check your internet connection.") from None
        except requests.exceptions.RequestException:
            raise ValueError("The request to the weather service failed. Please try again.") from None

        if response.status_code == 401:
            raise ValueError("Invalid or inactive API key. Check the key in variables.env.")
        if response.status_code == 404:
            raise ValueError(self._not_found_message)
        if response.status_code == 400:
            raise ValueError("The weather service did not accept the request. Check the location's coordinates.")
        if response.status_code == 429:
            raise ValueError("Too many requests to the weather service. Wait a minute and try again.")
        if response.status_code >= 500:
            raise ValueError(f"The weather service has a problem on its side (status {response.status_code}). Try again later.")
        if response.status_code != 200:
            raise ValueError(f"The weather service returned status {response.status_code}.")

        # requests raises a subclass of ValueError when the body is not JSON.
        try:
            return response.json()
        except ValueError:
            raise ValueError("The weather service sent a response that could not be read.") from None


def validate_location(location):
    """Raise ValueError before any API call if a location dictionary is unusable."""
    name = location.get("location")
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    if not isinstance(name, str) or name.strip() == "":
        raise ValueError("The location has no name.")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise ValueError(f"{name} has invalid coordinates.")
    # Written as "not inside" so nan (not a number) is rejected too: every comparison with nan is False.
    if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
        raise ValueError(f"{name} has coordinates outside the valid range.")


class WeatherClient(APIClient):
    """Knows the OpenWeatherMap endpoints and fields."""

    def __init__(self, api_key):
        super().__init__(BASE_URL, api_key, "appid")
        self.source = "openweathermap"
        self._not_found_message = "OpenWeatherMap could not find this location."

    def current(self, location):
        """Return a WeatherReading for a location dictionary."""
        validate_location(location)
        params = {"lat": location["latitude"], "lon": location["longitude"], "units": "metric"}
        data = self._get("data/2.5/weather", params)
        try:
            return WeatherReading(
                location["location"],
                location["latitude"],
                location["longitude"],
                data["main"]["temp"],
                data["main"]["feels_like"],
                data["main"]["humidity"],
                data["wind"]["speed"],
                data["weather"][0]["description"],
            )
        except (KeyError, IndexError):
            raise ValueError("OpenWeatherMap sent current weather in an unexpected format.") from None

    def forecast(self, location, now=None):
        """Return a list of ForecastPoints (3-hour windows, up to 5 days) for a location dictionary."""
        validate_location(location)
        if now is None:
            now = datetime.now(timezone.utc)
        params = {"lat": location["latitude"], "lon": location["longitude"], "units": "metric"}
        data = self._get("data/2.5/forecast", params)

        try:
            # First note the rain of every item. OWM leaves "rain" out when it
            # doesn't rain, so a missing value is 0 mm, not unknown.
            rain_by_time = {}
            for item in data["list"]:
                time_utc = datetime.fromtimestamp(item["dt"], timezone.utc)
                rain = 0
                if "rain" in item:
                    rain = item["rain"].get("3h", 0)
                rain_by_time[time_utc] = rain

            points = []
            for item in data["list"]:
                # "dt" is a Unix time (seconds since 1970, in UTC).
                time_utc = datetime.fromtimestamp(item["dt"], timezone.utc)
                if not is_window_start(time_utc):
                    continue
                # rain.3h at 03:00 is the rain from 00:00 to 03:00, so the window
                # 00:00 takes the next item's rain. The last window has no next
                # item, so its rain stays None (unknown), never a made-up 0.
                rain = rain_by_time.get(time_utc + timedelta(hours=WINDOW_HOURS))
                points.append(ForecastPoint(
                    self.source,
                    time_utc,
                    item["main"].get("temp"),
                    item["wind"].get("speed"),
                    item["wind"].get("deg"),
                    rain,
                ))
        except (KeyError, TypeError, ValueError, AttributeError):
            raise ValueError("OpenWeatherMap sent a forecast in an unexpected format.") from None

        return keep_next_five_days(points, now)
