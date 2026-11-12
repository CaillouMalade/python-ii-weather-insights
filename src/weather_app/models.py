"""The data class for one weather reading."""

METRES_PER_SECOND_TO_KMH = 3.6

# The fields of a reading, in the order the log stores them.
READING_COLUMNS = ["location", "latitude", "longitude", "temperature", "feels_like", "humidity", "wind_speed", "conditions"]


class WeatherReading:
    """Current conditions at one location. Units: °C, %, m/s."""

    def __init__(self, location, latitude, longitude, temperature, feels_like, humidity, wind_speed, conditions):
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.temperature = temperature
        self.feels_like = feels_like
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.conditions = conditions

    @property
    def wind_kmh(self):
        """Wind speed in km/h. OpenWeatherMap sends m/s, and the page shows km/h."""
        return self.wind_speed * METRES_PER_SECOND_TO_KMH

    @property
    def feels_like_gap(self):
        """How much colder (negative) or warmer (positive) it feels than the thermometer says, in °C."""
        return self.feels_like - self.temperature

    def __repr__(self):
        return f"WeatherReading({self.location!r}, {self.temperature}°C)"

    def __str__(self):
        return f"{self.location}: {self.temperature:.1f}°C, {self.conditions}"

    def __lt__(self, other):
        # This is what lets sorted() rank readings by temperature.
        return self.temperature < other.temperature

    def to_dict(self):
        values = {}
        for name in READING_COLUMNS:
            values[name] = getattr(self, name)
        return values


class ForecastPoint:
    """One provider's forecast for one 3-hour window. Units: °C, m/s, degrees, mm.

    Every provider turns its own answer into a list of these, on the same
    3-hour windows in UTC, so the statistics can compare them directly.
    A value the provider does not send stays None.
    """

    def __init__(self, source, time_utc, temperature, wind_speed, wind_deg, rain):
        self.source = source          # e.g. "openweathermap", "open-meteo", "met-norway"
        self.time_utc = time_utc      # start of the 3-hour window, a datetime in UTC
        self.temperature = temperature
        self.wind_speed = wind_speed
        self.wind_deg = wind_deg      # direction the wind comes from
        self.rain = rain              # mm over the whole 3-hour window

    @property
    def wind_kmh(self):
        """Wind speed in km/h, or None when the provider sent no wind."""
        if self.wind_speed is None:
            return None
        return self.wind_speed * METRES_PER_SECOND_TO_KMH

    def __repr__(self):
        return f"ForecastPoint({self.source!r}, {self.time_utc:%a %H:%M}, {self.temperature}°C)"
