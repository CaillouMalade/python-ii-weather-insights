"""Public errors have fixed safe messages; raw request URLs never escape."""

class WeatherError(Exception):
    """A user-facing weather failure."""

class InputError(WeatherError):
    """Input rejected before a request."""

class LocationNotFoundError(WeatherError):
    """The API could not resolve the requested location."""

class AuthenticationError(WeatherError):
    """Missing, invalid or inactive provider credential."""

class RateLimitError(WeatherError):
    """The provider's request allowance was exceeded."""

class NetworkError(WeatherError):
    """Timeout, DNS, transport or remote server failure."""

class DataError(WeatherError):
    """A response did not contain usable weather data."""
