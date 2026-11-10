"""API clients: a generic JSON client and an OpenWeatherMap subclass."""

import requests

from .models import WeatherReading

BASE_URL = "https://api.openweathermap.org"


class APIClient:
    """Calls any JSON API that takes its key as a query parameter.

    Another provider would subclass this and only say which endpoints and fields it uses.
    """

    def __init__(self, base_url, api_key, key_param, timeout=10):
        self.base_url = base_url
        self.key_param = key_param
        self.timeout = timeout
        self._not_found_message = "The requested resource was not found."
        # Name-mangled so callers and subclasses cannot read it by accident.
        # The real protection is keeping the key out of the repo and the browser.
        self.__api_key = api_key

    def _get(self, endpoint, params):
        """Send a GET request and return the JSON, or raise ValueError with a clear message."""
        params[self.key_param] = self.__api_key

        # The messages are fixed text on purpose: the text of a requests error
        # contains the full URL, and the URL contains the API key.
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params, timeout=self.timeout)
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

        # requests raises a subclass of ValueError when the body is not JSON.
        try:
            return response.json()
        except ValueError:
            raise ValueError("The weather service sent a response that could not be read.") from None


def validate_city(city):
    """Return the cleaned city name, or raise ValueError if it is obviously invalid."""
    if not isinstance(city, str):
        raise ValueError("The city name must be text.")
    cleaned = city.strip()
    if cleaned == "":
        raise ValueError("Please enter a city name.")
    if len(cleaned) > 100:
        raise ValueError("That city name is too long.")
    has_letter = False
    for character in cleaned:
        if character.isalpha():
            has_letter = True
    if not has_letter:
        raise ValueError(f"'{cleaned}' is not a valid city name: it contains no letters.")
    return cleaned


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

    def find_city(self, city):
        """Check a typed city name, then return its best match as a location dictionary."""
        cleaned = validate_city(city)
        data = self._get("geo/1.0/direct", {"q": cleaned, "limit": 1})
        if len(data) == 0:
            raise ValueError(f"City '{cleaned}' was not found. Check the spelling.")
        try:
            match = data[0]
            return {"location": f"{match['name']}, {match['country']}", "latitude": match["lat"], "longitude": match["lon"]}
        except (KeyError, TypeError):
            raise ValueError("OpenWeatherMap sent a location in an unexpected format.") from None

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
