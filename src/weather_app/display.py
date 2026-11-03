"""Small pure helpers that turn weather values into what the page shows. No Streamlit here."""

from datetime import datetime, timedelta, timezone

COMPASS_POINTS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def format_local_time(unix_seconds, timezone_offset, pattern="%H:%M"):
    """Format a Unix time at a location. timezone_offset is its UTC offset in seconds."""
    zone = timezone(timedelta(seconds=timezone_offset))
    return datetime.fromtimestamp(unix_seconds, zone).strftime(pattern)


def compass_direction(degrees):
    """Turn wind degrees into one of eight compass points. 0 is north, 90 is east."""
    return COMPASS_POINTS[round(degrees / 45) % 8]


def high_low_text(high, low):
    """The same wording everywhere. The page keeps the two spaces (see .high-low in style.py).

    "High 31°  Low 31°" would mislead, so an equal pair shows nothing.
    """
    if round(high) == round(low):
        return ""
    return f"High {round(high)}°  Low {round(low)}°"
