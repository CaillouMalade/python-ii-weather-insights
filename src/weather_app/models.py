"""The data class for one weather reading."""


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
    def feels_like_delta(self):
        """How much warmer (+) or colder (-) it feels than the actual temperature, in °C."""
        return round(self.feels_like - self.temperature, 2)

    def __repr__(self):
        return f"WeatherReading({self.location!r}, {self.temperature}°C)"

    def __lt__(self, other):
        # This is what lets sorted() order readings by temperature.
        return self.temperature < other.temperature

    def to_dict(self):
        return {
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "temperature": self.temperature,
            "feels_like": self.feels_like,
            "humidity": self.humidity,
            "wind_speed": self.wind_speed,
            "conditions": self.conditions,
        }
