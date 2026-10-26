"""Public domain objects use explicit units and aware UTC timestamps."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite, log
from typing import Optional
from .errors import InputError


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def optional_number(value) -> Optional[float]:
    """Missing/invalid values remain missing; bool and NaN are not observations."""
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if isfinite(number) else None


@dataclass(frozen=True)
class Location:
    name: str
    latitude: float
    longitude: float
    timezone: str = "UTC"

    def __post_init__(self):
        name = self.name.strip() if isinstance(self.name, str) else ""
        if not 1 <= len(name) <= 120 or any(ord(c) < 32 for c in name):
            raise InputError("Give the location a name between 1 and 120 characters.")
        lat, lon = optional_number(self.latitude), optional_number(self.longitude)
        if lat is None or lon is None or not -90 <= lat <= 90 or not -180 <= lon <= 180:
            raise InputError("Latitude must be -90 to 90 and longitude -180 to 180.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "latitude", lat)
        object.__setattr__(self, "longitude", lon)

    def __str__(self):
        return f"{self.name} ({self.latitude:.4f}, {self.longitude:.4f})"


@dataclass(frozen=True)
class WeatherSnapshot:
    location: Location
    provider: str
    fetched_at: str
    valid_at: str
    temperature_c: Optional[float]
    humidity_pct: Optional[float]
    wind_kmh: Optional[float]
    gust_kmh: Optional[float] = None
    precipitation_mm: Optional[float] = None
    precipitation_interval_minutes: Optional[int] = None
    feels_like_c: Optional[float] = None
    dewpoint_c: Optional[float] = None
    kind: str = "modeled current conditions"

    @property
    def dewpoint_spread_c(self) -> Optional[float]:
        """Air minus dewpoint; no claim that this measures circuit grip."""
        if self.temperature_c is None or self.dewpoint_c is None:
            return None
        return round(self.temperature_c - self.dewpoint_c, 2)

    @property
    def feels_like_delta_c(self) -> Optional[float]:
        if self.feels_like_c is None or self.temperature_c is None:
            return None
        return round(self.feels_like_c - self.temperature_c, 2)

    def __lt__(self, other):
        if not isinstance(other, WeatherSnapshot):
            return NotImplemented
        # Missing temperatures sort last rather than becoming a fictional 0 °C.
        left = self.temperature_c if self.temperature_c is not None else float("inf")
        right = other.temperature_c if other.temperature_c is not None else float("inf")
        return (left, self.location.name, self.provider) < (right, other.location.name, other.provider)

    def to_record(self):
        result = asdict(self)
        result.pop("location")
        result.update(location=self.location.name, latitude=self.location.latitude,
                      longitude=self.location.longitude, timezone=self.location.timezone,
                      dewpoint_spread_c=self.dewpoint_spread_c,
                      feels_like_delta_c=self.feels_like_delta_c)
        return result


def estimated_dewpoint(temperature_c, humidity_pct):
    """Magnus approximation for water, valid here for RH > 0; marked as derived."""
    if temperature_c is None or humidity_pct is None or not 0 < humidity_pct <= 100 or temperature_c <= -243.04:
        return None
    alpha = log(humidity_pct / 100) + 17.625 * temperature_c / (243.04 + temperature_c)
    return round(243.04 * alpha / (17.625 - alpha), 2)
