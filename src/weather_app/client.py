"""API clients: a generic JSON client and its OpenWeatherMap subclass."""

import requests

from .models import WeatherReading

BASE_URL = "https://api.openweathermap.org"


class APIClient:
    """Calls any JSON API that takes its key as a query parameter."""

    def __init__(self, base_url, api_key, key_param, timeout=10):
        self.base_url = base_url
        self.key_param = key_param
        self.timeout = timeout
        self._not_found_message = "The requested resource was not found."
        # Name-mangling only discourages outside access; it is not security.
        # The real protection is keeping the key out of the repo and the UI.
        self.__api_key = api_key

    def _get(self, endpoint, params):
        """Send a GET request and return the JSON, or raise ValueError with a clear message."""
        params[self.key_param] = self.__api_key

        # The messages are fixed text on purpose: the text of a requests error
        # contains the full URL, and the URL contains the API key.
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=self.timeout)
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

        # requests raises a subclass of ValueError when the body is not JSON.
        try:
            return response.json()
        except ValueError:
            raise ValueError("The weather service sent a response that could not be read.")


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
        """Return the top geocoding match as a dictionary with name, latitude and longitude."""
        cleaned = validate_city(city)
        data = self._get("geo/1.0/direct", {"q": cleaned, "limit": 1})
        if len(data) == 0:
            raise ValueError(f"City '{cleaned}' was not found.")

        try:
            top_match = data[0]
            return {
                "name": f"{top_match['name']}, {top_match['country']}",
                "latitude": top_match["lat"],
                "longitude": top_match["lon"],
            }
        except (KeyError, IndexError):
            raise ValueError("OpenWeatherMap sent a location in an unexpected format.")

    def current(self, location):
        """Return a WeatherReading for a location dictionary from find_city."""
        params = {"lat": location["latitude"], "lon": location["longitude"], "units": "metric"}
        data = self._get("data/2.5/weather", params)
        return self._parse_current(data, location)

    def forecast(self, latitude, longitude):
        """Return the 5-day/3-hour forecast as a list of dictionaries with time and temperature."""
        params = {"lat": latitude, "lon": longitude, "units": "metric"}
        data = self._get("data/2.5/forecast", params)
        return self._parse_forecast(data)

    def _parse_current(self, data, location):
        # We keep the geocoded name: for coordinates, /weather can return the
        # name of a nearby station, which would split one city into several in the log.
        try:
            return WeatherReading(
                location["name"],
                location["latitude"],
                location["longitude"],
                data["main"]["temp"],
                data["main"]["feels_like"],
                data["main"]["humidity"],
                data["wind"]["speed"],
                data["weather"][0]["description"],
            )
        except (KeyError, IndexError):
            raise ValueError("OpenWeatherMap sent current weather in an unexpected format.")

    def _parse_forecast(self, data):
        try:
            return [{"time": entry["dt_txt"], "temperature": entry["main"]["temp"]} for entry in data["list"]]
        except KeyError:
            raise ValueError("OpenWeatherMap sent a forecast in an unexpected format.")
