"""API clients: a generic client and its OpenWeatherMap subclass."""

import requests

from .models import WeatherReading

BASE_URL = "https://api.openweathermap.org"
TILE_URL = "https://tile.openweathermap.org"

TILE_LAYERS = ["precipitation_new", "temp_new", "wind_new", "clouds_new", "pressure_new"]
POLLUTANTS = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]


class APIClient:
    """Calls any API that takes its key as a query parameter."""

    def __init__(self, base_url, api_key, key_param, timeout=10):
        self.base_url = base_url
        self.key_param = key_param
        self.timeout = timeout
        self._not_found_message = "The requested resource was not found."
        # Name-mangling only discourages outside access; it is not security.
        # The real protection is keeping the key out of the repo and the browser.
        self.__api_key = api_key

    def _request(self, url, params):
        """Send a GET request and return the response, or raise ValueError with a clear message."""
        params[self.key_param] = self.__api_key

        # The messages are fixed text on purpose: the text of a requests error
        # contains the full URL, and the URL contains the API key.
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
        except requests.exceptions.Timeout:
            raise ValueError("The weather service took too long to respond. Please try again.")
        except requests.exceptions.ConnectionError:
            raise ValueError("Could not connect to the weather service. Check your internet connection.")
        except requests.exceptions.RequestException:
            raise ValueError("The request to the weather service failed. Please try again.")

        if response.status_code == 401:
            raise ValueError("Invalid or inactive API key. Check the key in variables.env.")
        if response.status_code == 404:
            raise ValueError(self._not_found_message)
        if response.status_code != 200:
            raise ValueError(f"The weather service returned status {response.status_code}.")
        return response

    def _get(self, endpoint, params):
        """Return the JSON from an endpoint of this API."""
        response = self._request(f"{self.base_url}/{endpoint}", params)
        # requests raises a subclass of ValueError when the body is not JSON.
        try:
            return response.json()
        except ValueError:
            raise ValueError("The weather service sent a response that could not be read.")

    def _get_bytes(self, url, params):
        """Return the raw bytes at a URL, for example an image."""
        return self._request(url, params).content


def validate_location(location):
    """Raise ValueError before any API call if a location dictionary is unusable."""
    name = location.get("location")
    latitude = location.get("latitude")
    longitude = location.get("longitude")

    if not isinstance(name, str) or name.strip() == "":
        raise ValueError("The location has no name.")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        raise ValueError(f"{name} has invalid coordinates.")
    if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
        raise ValueError(f"{name} has coordinates outside the valid range.")


class WeatherClient(APIClient):
    """Knows the OpenWeatherMap endpoints and fields."""

    def __init__(self, api_key):
        super().__init__(BASE_URL, api_key, "appid")
        self._not_found_message = "OpenWeatherMap could not find this location."

    def current(self, location):
        """Return a WeatherReading for a location dictionary from the city list."""
        validate_location(location)
        params = {"lat": location["latitude"], "lon": location["longitude"], "units": "metric"}
        data = self._get("data/2.5/weather", params)
        return self._parse_current(data, location)

    def forecast(self, latitude, longitude):
        """Return the 5-day/3-hour forecast as a list of step dictionaries."""
        params = {"lat": latitude, "lon": longitude, "units": "metric"}
        data = self._get("data/2.5/forecast", params)
        return self._parse_forecast(data)

    def air_now(self, latitude, longitude):
        """Return current air quality as a list of rows (normally one)."""
        data = self._get("data/2.5/air_pollution", {"lat": latitude, "lon": longitude})
        return self._parse_air(data)

    def air_forecast(self, latitude, longitude):
        """Return the air quality forecast as a list of hourly rows."""
        data = self._get("data/2.5/air_pollution/forecast", {"lat": latitude, "lon": longitude})
        return self._parse_air(data)

    def air_history(self, latitude, longitude, start, end):
        """Return past air quality as a list of hourly rows. start and end are Unix seconds."""
        params = {"lat": latitude, "lon": longitude, "start": start, "end": end}
        data = self._get("data/2.5/air_pollution/history", params)
        return self._parse_air(data)

    def uv_index(self, latitude, longitude):
        """Return the UV index, or None: this endpoint is legacy and may stop working."""
        try:
            data = self._get("data/2.5/uvi", {"lat": latitude, "lon": longitude})
        except ValueError:
            return None
        return data.get("value")

    def tile(self, layer, zoom, x, y):
        """Return the PNG bytes of one map tile. Only the server ever sees this URL."""
        if layer not in TILE_LAYERS:
            raise ValueError(f"Unknown map layer: {layer}")
        return self._get_bytes(f"{TILE_URL}/map/{layer}/{zoom}/{x}/{y}.png", {})

    def _parse_current(self, data, location):
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
                temp_min=data["main"].get("temp_min"),
                temp_max=data["main"].get("temp_max"),
                pressure=data["main"].get("pressure"),
                clouds=data.get("clouds", {}).get("all"),
                wind_deg=data["wind"].get("deg"),
                wind_gust=data["wind"].get("gust"),
                visibility=data.get("visibility"),
                rain_1h=data.get("rain", {}).get("1h"),
                snow_1h=data.get("snow", {}).get("1h"),
                weather_id=data["weather"][0].get("id"),
                icon=data["weather"][0].get("icon"),
                observed_at=data.get("dt"),
                timezone_offset=data.get("timezone"),
                sunrise=data.get("sys", {}).get("sunrise"),
                sunset=data.get("sys", {}).get("sunset"),
            )
        except (KeyError, IndexError):
            raise ValueError("OpenWeatherMap sent current weather in an unexpected format.")

    def _parse_forecast(self, data):
        steps = []
        try:
            for entry in data["list"]:
                steps.append(
                    {
                        "dt": entry["dt"],
                        "temperature": entry["main"]["temp"],
                        "feels_like": entry["main"]["feels_like"],
                        "dew_point": entry["main"].get("dew_point"),
                        "humidity": entry["main"].get("humidity"),
                        "pressure": entry["main"].get("pressure"),
                        "clouds": entry.get("clouds", {}).get("all"),
                        "wind_speed": entry.get("wind", {}).get("speed"),
                        "wind_deg": entry.get("wind", {}).get("deg"),
                        "wind_gust": entry.get("wind", {}).get("gust"),
                        "visibility": entry.get("visibility"),
                        "pop": entry.get("pop", 0),
                        # The API leaves out rain and snow when there is none, so 0 mm is correct here.
                        "rain_3h": entry.get("rain", {}).get("3h", 0),
                        "snow_3h": entry.get("snow", {}).get("3h", 0),
                        "pod": entry.get("sys", {}).get("pod"),
                        "weather_id": entry["weather"][0].get("id"),
                        "icon": entry["weather"][0].get("icon"),
                        "conditions": entry["weather"][0].get("description"),
                    }
                )
        except (KeyError, IndexError):
            raise ValueError("OpenWeatherMap sent a forecast in an unexpected format.")
        return steps

    def _parse_air(self, data):
        # Only "coord" and "list" were confirmed, so every other field is read carefully.
        if not isinstance(data, dict):
            raise ValueError("OpenWeatherMap sent air quality data in an unexpected format.")

        rows = []
        for entry in data.get("list", []):
            if "dt" not in entry:
                continue
            row = {"dt": entry["dt"], "aqi": entry.get("main", {}).get("aqi")}
            for name in POLLUTANTS:
                row[name] = entry.get("components", {}).get(name)
            rows.append(row)
        return rows
