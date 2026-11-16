"""The 3-hour UTC windows (00, 03, ... 21) every forecast provider is cut into.

They live in their own file because both client.py and providers.py use them,
and providers.py already imports client.py (two files importing each other fails)."""

from datetime import timedelta

WINDOW_HOURS = 3
FORECAST_DAYS = 5  # same reach as OpenWeatherMap's 5-day forecast


def is_window_start(time_utc):
    """True for 00:00, 03:00, ... 21:00."""
    return time_utc.hour % WINDOW_HOURS == 0 and time_utc.minute == 0


def window_start(time_utc):
    """Return the start of the 3-hour window a time falls in (14:20 gives 12:00)."""
    hour = time_utc.hour - time_utc.hour % WINDOW_HOURS
    return time_utc.replace(hour=hour, minute=0, second=0, microsecond=0)


def sum_rain(amounts):
    """Add up the rain of the hours in one window, or None if any hour is missing."""
    # A partial sum would look like a real (too low) value, so we don't make one.
    total = 0
    for amount in amounts:
        if amount is None:
            return None
        total = total + amount
    return total


def keep_next_five_days(points, now):
    """Keep the points from the current window up to 5 days ahead."""
    first = window_start(now)
    last = first + timedelta(days=FORECAST_DAYS)
    kept = []
    for point in points:
        if first <= point.time_utc < last:
            kept.append(point)
    return kept
