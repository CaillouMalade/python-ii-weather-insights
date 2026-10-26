"""One HTTP/error-handling base shared by two real JSON weather APIs."""
import json
import socket
from datetime import datetime, timezone
from typing import Callable, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .errors import (AuthenticationError, DataError, InputError, LocationNotFoundError,
                     NetworkError, RateLimitError, WeatherError)
from .models import Location, WeatherSnapshot, estimated_dewpoint, optional_number, utc_now


class APIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None,
                 timeout: float = 15, opener: Callable = urlopen):
        self.base_url = base_url.rstrip("/")
        # Protected: subclasses need this for provider-specific request parameters.
        # It is never included in repr, errors, logs or UI output.
        self._api_key = api_key
        self._timeout = timeout
        self._opener = opener

    def __repr__(self):
        return f"{type(self).__name__}(base_url={self.base_url!r})"

    def _get(self, endpoint: str, params: Dict):
        request = Request(self.base_url + "/" + endpoint.lstrip("/") + "?" + urlencode(params),
                          headers={"User-Agent": "PitwallWeather/0.1 (educational weather comparison)",
                                   "Accept": "application/json"})
        try:
            with self._opener(request, timeout=self._timeout) as response:
                payload = response.read(2_000_001)
                if len(payload) > 2_000_000:
                    raise DataError("The weather response was unexpectedly large.")
                result = json.loads(payload)
        except HTTPError as error:
            if error.code in (401, 403):
                raise AuthenticationError("The provider rejected the key or this product's access. Check key activation and subscription.") from None
            if error.code == 404:
                raise LocationNotFoundError("The provider could not find this location.") from None
            if error.code == 429:
                raise RateLimitError("The provider request limit was reached. Try again later.") from None
            if error.code == 400:
                raise InputError("The provider rejected the location or request parameters.") from None
            raise NetworkError(f"The provider returned HTTP {error.code}. Try again later.") from None
        except (URLError, TimeoutError, socket.timeout, OSError):
            raise NetworkError("The weather provider could not be reached. Check the connection and retry.") from None
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise DataError("The weather provider returned an unreadable response.") from None
        if not isinstance(result, dict):
            raise DataError("The weather provider returned an unexpected response shape.")
        return result


class OpenWeatherClient(APIClient):
    def __init__(self, api_key: Optional[str], **kwargs):
        super().__init__("https://api.openweathermap.org/data/2.5", api_key, **kwargs)

    def current(self, location: Location) -> WeatherSnapshot:
        if not self._api_key or not self._api_key.strip():
            raise AuthenticationError("OpenWeather needs OPENWEATHER_API_KEY in variables.env or your environment.")
        data = self._get("weather", {"lat": location.latitude, "lon": location.longitude,
                                     "appid": self._api_key, "units": "metric"})
        try:
            main = data["main"]
            wind = data.get("wind", {})
            temp = optional_number(main.get("temp"))
            humidity = optional_number(main.get("humidity"))
            if temp is None:
                raise DataError("OpenWeather returned no air temperature.")
            valid_at = datetime.fromtimestamp(float(data["dt"]), timezone.utc).isoformat()
            rain = data.get("rain", {}).get("1h")
            snow = data.get("snow", {}).get("1h")
            # Absence of a provider's optional rain/snow fields remains unavailable.
            # No missing field is silently converted into dry weather.
            components = [x for x in (optional_number(rain), optional_number(snow)) if x is not None]
            precip = sum(components) if components else None
            speed, gust = optional_number(wind.get("speed")), optional_number(wind.get("gust"))
            return WeatherSnapshot(location, "OpenWeather current", utc_now(), valid_at,
                temp, humidity, None if speed is None else speed * 3.6,
                None if gust is None else gust * 3.6, precip, 60 if precip is not None else None,
                optional_number(main.get("feels_like")), estimated_dewpoint(temp, humidity),
                "provider current conditions; dewpoint derived from temperature and RH")
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            raise DataError("OpenWeather returned incomplete or malformed conditions.") from None


class OpenMeteoClient(APIClient):
    def __init__(self, **kwargs):
        super().__init__("https://api.open-meteo.com/v1", **kwargs)

    def current(self, location: Location) -> WeatherSnapshot:
        data = self._get("forecast", {"latitude": location.latitude, "longitude": location.longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m,wind_gusts_10m",
            "wind_speed_unit": "kmh", "timezone": "UTC", "timeformat": "unixtime", "forecast_days": 1})
        try:
            current = data["current"]
            temp, humidity = optional_number(current.get("temperature_2m")), optional_number(current.get("relative_humidity_2m"))
            if temp is None:
                raise DataError("Open-Meteo returned no modeled air temperature.")
            interval = optional_number(current.get("interval"))
            valid_at = datetime.fromtimestamp(float(current["time"]), timezone.utc).isoformat()
            return WeatherSnapshot(location, "Open-Meteo best match", utc_now(), valid_at,
                temp, humidity, optional_number(current.get("wind_speed_10m")),
                optional_number(current.get("wind_gusts_10m")), optional_number(current.get("precipitation")),
                int(interval / 60) if interval is not None else None,
                optional_number(current.get("apparent_temperature")), estimated_dewpoint(temp, humidity),
                "modeled current conditions; dewpoint derived from temperature and RH")
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            raise DataError("Open-Meteo returned incomplete or malformed conditions.") from None


class GeocodingClient(APIClient):
    def __init__(self, **kwargs):
        super().__init__("https://geocoding-api.open-meteo.com/v1", **kwargs)

    def search(self, name: str):
        query = name.strip() if isinstance(name, str) else ""
        if not 2 <= len(query) <= 100 or any(ord(c) < 32 for c in query):
            raise InputError("Enter a place name with 2 to 100 characters, or use coordinates.")
        data = self._get("search", {"name": query, "count": 5, "language": "en", "format": "json"})
        results = data.get("results", [])
        if not results:
            raise LocationNotFoundError("No matching place was found. Try a nearby town or coordinates.")
        try:
            return [Location(f"{r['name']}, {r.get('country', '')}".rstrip(", "), r["latitude"], r["longitude"],
                             r.get("timezone", "UTC")) for r in results]
        except (KeyError, TypeError):
            raise DataError("The location service returned malformed places.") from None


def fetch_many(clients, locations, store=None):
    """One failed provider/location does not discard another successful fetch."""
    successes, failures = [], []
    for location in locations:
        for client in clients:
            try:
                snapshot = client.current(location)
                if store is not None:
                    store.append(snapshot)
                successes.append(snapshot)
            except WeatherError as error:
                failures.append({"location": location.name, "provider": type(client).__name__, "error": str(error)})
    return successes, failures
