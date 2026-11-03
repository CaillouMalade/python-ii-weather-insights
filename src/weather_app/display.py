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


# Temperature colour: one cool-to-warm scale for every temperature on the page. It has no
# green or red, which keep meaning dry and rain. (°C, red, green, blue); colours in between
# are mixed in proportion, and the ends hold beyond 0° and 25°.
TEMPERATURE_STOPS = [(0, 111, 168, 220), (10, 159, 183, 201), (15, 201, 197, 185), (20, 224, 184, 120), (25, 240, 160, 64)]
RAIN_BAR_LIKELY = "#E5484D"
RAIN_BAR_UNLIKELY = "rgba(138, 148, 143, 0.45)"


def temperature_color(celsius):
    """The colour of a temperature, as #RRGGBB, from TEMPERATURE_STOPS."""
    if celsius <= TEMPERATURE_STOPS[0][0]:
        low = high = TEMPERATURE_STOPS[0]
    elif celsius >= TEMPERATURE_STOPS[-1][0]:
        low = high = TEMPERATURE_STOPS[-1]
    else:
        number = 0
        while TEMPERATURE_STOPS[number + 1][0] < celsius:
            number = number + 1
        low = TEMPERATURE_STOPS[number]
        high = TEMPERATURE_STOPS[number + 1]
    share = 0 if high[0] == low[0] else (celsius - low[0]) / (high[0] - low[0])
    parts = []
    for channel in [1, 2, 3]:
        parts.append(round(low[channel] + (high[channel] - low[channel]) * share))
    return f"#{parts[0]:02X}{parts[1]:02X}{parts[2]:02X}"


def rain_bar_color(chance, likely):
    """Red only when rain is likely (the status lights' rule); a quiet neutral otherwise,
    so a forecast that reads "Dry all week" never shows a red bar."""
    return RAIN_BAR_LIKELY if chance >= likely else RAIN_BAR_UNLIKELY


def condition_kind(weather_id, night):
    """Which glyph an OpenWeatherMap condition code gets: rain, snow, fog, sun, night or cloud.
    Thunderstorms and drizzle count as rain."""
    if weather_id is None:
        return "cloud"
    if weather_id < 600:
        return "rain"
    if weather_id < 700:
        return "snow"
    if weather_id < 800:
        return "fog"
    if weather_id <= 801:
        return "night" if night else "sun"
    return "cloud"
