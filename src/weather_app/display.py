"""Small pure helpers that turn weather values into what the page shows. No Streamlit here."""

from datetime import datetime, timedelta, timezone

COMPASS_POINTS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

# CSS gradients only: fixed text that never contains data from the API.
BACKGROUNDS = {
    "clear_day": "linear-gradient(180deg, #2f6fa8 0%, #5a93c0 55%, #41688a 100%)",
    "clear_night": "linear-gradient(180deg, #0c1530 0%, #1a2747 55%, #243252 100%)",
    "cloud_day": "linear-gradient(180deg, #5b6673 0%, #66717e 50%, #4b5561 100%)",
    "cloud_night": "linear-gradient(180deg, #1c222b 0%, #2a323d 55%, #333c48 100%)",
    "rain_day": "linear-gradient(180deg, #3d4a58 0%, #4e5c6b 55%, #38434f 100%)",
    "rain_night": "linear-gradient(180deg, #141a22 0%, #222c37 55%, #2b3743 100%)",
    "snow_day": "linear-gradient(180deg, #66788c 0%, #8596a8 55%, #5d6c7d 100%)",
    "snow_night": "linear-gradient(180deg, #232d3b 0%, #3a4656 55%, #424f60 100%)",
    "storm": "linear-gradient(180deg, #23222f 0%, #38374a 55%, #2c2c3b 100%)",
    "fog": "linear-gradient(180deg, #6a6f75 0%, #7a7f85 55%, #55595e 100%)",
    "none": "linear-gradient(180deg, #2b3440 0%, #35404d 100%)",
}


def format_local_time(unix_seconds, timezone_offset, pattern="%H:%M"):
    """Format a Unix time at a location. timezone_offset is its UTC offset in seconds."""
    zone = timezone(timedelta(seconds=timezone_offset))
    return datetime.fromtimestamp(unix_seconds, zone).strftime(pattern)


def is_night(now, sunrise, sunset):
    """Return True if now is outside today's sunrise-to-sunset period (Unix seconds)."""
    if sunrise is None or sunset is None:
        return False
    return now < sunrise or now >= sunset


def compass_direction(degrees):
    """Turn wind degrees into one of eight compass points. 0 is north, 90 is east."""
    return COMPASS_POINTS[round(degrees / 45) % 8]


def background_for(weather_id, night):
    """Choose a gradient from the OpenWeatherMap condition id and whether it is night."""
    if weather_id is None:
        return BACKGROUNDS["none"]

    if weather_id < 300:
        return BACKGROUNDS["storm"]
    if weather_id >= 700 and weather_id < 800:
        return BACKGROUNDS["fog"]

    group = "cloud"
    if weather_id < 600:
        group = "rain"
    elif weather_id < 700:
        group = "snow"
    elif weather_id <= 801:
        group = "clear"

    if night:
        return BACKGROUNDS[group + "_night"]
    return BACKGROUNDS[group + "_day"]


def high_low_text(high, low):
    """The same wording everywhere. The page keeps the two spaces (see .high-low in style.py).

    "High 31°  Low 31°" would mislead, so an equal pair shows nothing.
    """
    if round(high) == round(low):
        return ""
    return f"High {round(high)}°  Low {round(low)}°"
