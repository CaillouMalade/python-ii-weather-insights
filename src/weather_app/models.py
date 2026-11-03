"""The data class for one weather reading."""

METRES_PER_SECOND_TO_KMH = 3.6

# The fields of a reading. The log's columns come from this list too.
READING_COLUMNS = [
    "location", "latitude", "longitude", "temperature", "feels_like", "humidity", "wind_speed", "conditions",
    "temp_min", "temp_max", "pressure", "clouds", "wind_deg", "wind_gust", "visibility", "rain_1h", "snow_1h",
    "weather_id", "icon", "observed_at", "timezone_offset", "sunrise", "sunset",
]


class WeatherReading:
    """Current conditions at one location. Units: °C, %, m/s, hPa, metres, mm."""

    def __init__(
        self,
        location,
        latitude,
        longitude,
        temperature,
        feels_like,
        humidity,
        wind_speed,
        conditions,
        temp_min=None,
        temp_max=None,
        pressure=None,
        clouds=None,
        wind_deg=None,
        wind_gust=None,
        visibility=None,
        rain_1h=None,
        snow_1h=None,
        weather_id=None,
        icon=None,
        observed_at=None,
        timezone_offset=None,
        sunrise=None,
        sunset=None,
    ):
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.temperature = temperature
        self.feels_like = feels_like
        self.humidity = humidity
        self.wind_speed = wind_speed
        self.conditions = conditions
        # The API does not always send these, so they can stay None.
        self.temp_min = temp_min
        self.temp_max = temp_max
        self.pressure = pressure
        self.clouds = clouds
        self.wind_deg = wind_deg
        self.wind_gust = wind_gust
        self.visibility = visibility
        self.rain_1h = rain_1h
        self.snow_1h = snow_1h
        self.weather_id = weather_id
        self.icon = icon
        self.observed_at = observed_at
        self.timezone_offset = timezone_offset
        self.sunrise = sunrise
        self.sunset = sunset

    @property
    def wind_kmh(self):
        """Wind speed in km/h. OpenWeatherMap sends m/s, and the page shows km/h."""
        return self.wind_speed * METRES_PER_SECOND_TO_KMH

    def __repr__(self):
        return f"WeatherReading({self.location!r}, {self.temperature}°C)"

    def __lt__(self, other):
        # This is what lets sorted() order readings by temperature.
        return self.temperature < other.temperature

    def to_dict(self):
        values = {}
        for name in READING_COLUMNS:
            values[name] = getattr(self, name)
        return values
