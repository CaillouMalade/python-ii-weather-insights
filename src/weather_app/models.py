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
