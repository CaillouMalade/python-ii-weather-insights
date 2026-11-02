"""API clients: a generic client and one subclass per provider."""

import requests

from .models import WeatherReading

BASE_URL = "https://api.openweathermap.org"
TILE_URL = "https://tile.openweathermap.org"
RAINVIEWER_URL = "https://api.rainviewer.com"

TILE_LAYERS = ["temp_new", "wind_new", "clouds_new", "pressure_new"]
POLLUTANTS = ["co", "no", "no2", "o3", "so2", "pm2_5", "pm10", "nh3"]


class APIClient:
    """Calls any API. A provider with a key passes it as a query parameter; one without passes None."""

    def __init__(self, base_url, api_key=None, key_param=None, timeout=10):
        self.base_url = base_url
        self.key_param = key_param
        self.timeout = timeout
        self._not_found_message = "The requested resource was not found."
        # Name-mangling only discourages outside access; it is not security.
        # The real protection is keeping the key out of the repo and the browser.
        self.__api_key = api_key

    def _with_key(self, params):
        """Add the key to the parameters, if this provider has one."""
        if self.__api_key:
            params[self.key_param] = self.__api_key
        return params

    def _request(self, url, params):
        """Send a GET request and return the response, or raise ValueError with a clear message."""
        params = self._with_key(params)

        # The messages are fixed text on purpose: the text of a requests error
        # contains the full URL, and the URL contains the API key. "from None"
        # also stops Python keeping that error attached to the new one.
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
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


def validate_city(city):
    """Return the cleaned city name, or raise ValueError if it is obviously invalid."""
    if not isinstance(city, str):
        raise ValueError("The city name must be text.")

    cleaned = city.strip()
    if cleaned == "":
        raise ValueError("Please enter a city name.")
    if len(cleaned) > 100:
        raise ValueError("That city name is too long.")

    letters = [character for character in cleaned if character.isalpha()]
    if len(letters) == 0:
        raise ValueError(f"'{cleaned}' is not a valid city name: it contains no letters.")

    return cleaned


class WeatherClient(APIClient):
    """Knows the OpenWeatherMap endpoints and fields."""

    def __init__(self, api_key):
        super().__init__(BASE_URL, api_key, "appid")
        self._not_found_message = "OpenWeatherMap could not find this location."

    def find_city(self, city):
        """Check a typed city, then return its top geocoding match as a location dictionary."""
        cleaned = validate_city(city)
        data = self._get("geo/1.0/direct", {"q": cleaned, "limit": 1})
        return self._parse_city(data, cleaned)

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

    def _parse_city(self, data, cleaned):
        if len(data) == 0:
            raise ValueError(f"City '{cleaned}' was not found. Check the spelling.")
        try:
            top_match = data[0]
            name = f"{top_match['name']}, {top_match['country']}"
            return {"location": name, "label": name, "city": top_match["name"], "latitude": top_match["lat"], "longitude": top_match["lon"]}
        except (KeyError, IndexError):
            raise ValueError("OpenWeatherMap sent a location in an unexpected format.")

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
                        "wind_speed": entry.get("wind", {}).get("speed"),
                        "wind_gust": entry.get("wind", {}).get("gust"),
                        "pop": entry.get("pop", 0),
                        # The API leaves out rain and snow when there is none, so 0 mm is correct here.
                        "rain_3h": entry.get("rain", {}).get("3h", 0),
                        "snow_3h": entry.get("snow", {}).get("3h", 0),
                        "icon": entry["weather"][0].get("icon"),
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


class RainViewerClient(APIClient):
    """Real radar from RainViewer, which needs no key. See https://www.rainviewer.com/api.html"""

    # Colour scheme 2 is Universal Blue, the one RainViewer's documentation lists.
    # "1_1" means smoothed, with snow in its own colours.
    COLOR_SCHEME = 2
    OPTIONS = "1_1"

    def __init__(self):
        super().__init__(RAINVIEWER_URL)
        self._not_found_message = "RainViewer has no radar image for this place right now."

    def latest_frame(self):
        """Return the newest radar frame: a dictionary with host, path and time (Unix seconds)."""
        return self._parse_latest_frame(self._get("public/weather-maps.json", {}))

    def radar_tile(self, frame, zoom, x, y):
        """Return the PNG bytes of one radar tile. RainViewer's maximum zoom is 7."""
        url = f"{frame['host']}{frame['path']}/256/{zoom}/{x}/{y}/{self.COLOR_SCHEME}/{self.OPTIONS}.png"
        return self._get_bytes(url, {})

    def coverage_tile(self, frame, zoom, x, y):
        """Return the PNG bytes of one coverage tile: black where there is no radar, clear where there is."""
        return self._get_bytes(f"{frame['host']}/v2/coverage/0/256/{zoom}/{x}/{y}/0/0_0.png", {})

    def _parse_latest_frame(self, data):
        try:
            newest = data["radar"]["past"][-1]
            return {"host": data["host"], "path": newest["path"], "time": newest.get("time")}
        except (KeyError, IndexError, TypeError):
            raise ValueError("RainViewer sent its radar list in an unexpected format.")
