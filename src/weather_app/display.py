"""Small pure helpers that turn weather values into what the page shows. No Streamlit here."""

from datetime import datetime, timedelta, timezone

COMPASS_POINTS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
AQI_LABELS = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very poor"}

# OpenWeatherMap icon codes: the first two characters are the weather, the last is d or n.
EMOJI = {
    "01d": "☀️", "01n": "🌙", "02d": "🌤️", "02n": "☁️", "03": "☁️", "04": "☁️",
    "09": "🌧️", "10d": "🌦️", "10n": "🌧️", "11": "⛈️", "13": "❄️", "50": "🌫️",
}

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


def weather_emoji(icon):
    """Return the emoji for an OpenWeatherMap icon code such as "10d"."""
    if icon is None or not isinstance(icon, str):
        return "☁️"
    return EMOJI.get(icon, EMOJI.get(icon[:2], "☁️"))


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

    Late in the day the forecast can have nothing left, and the current reading's own range
    can be a single value. "High 31° Low 31°" would mislead, so an equal pair shows nothing.
    """
    if round(high) == round(low):
        return ""
    return f"High {round(high)}°  Low {round(low)}°"


def display_names(locations):
    """Return the name to show for each location: just the city, unless that would be ambiguous.

    Same city name: add the country, which is the last part of the label. Still the same
    (two Springfields in one country): use the location, which includes the region.
    """
    city_names = [location["city"] for location in locations]
    with_country = []
    for location in locations:
        with_country.append(f"{location['city']}, {location['label'].split(', ')[-1]}")

    names = []
    for number in range(len(locations)):
        if city_names.count(city_names[number]) == 1:
            names.append(city_names[number])
        elif with_country.count(with_country[number]) == 1:
            names.append(with_country[number])
        else:
            names.append(locations[number]["location"])
    return names


def aqi_label(aqi):
    return AQI_LABELS.get(aqi, "Unknown")


def aqi_position(aqi):
    """Where the marker sits on the air quality scale, as a percentage: 1 is 0, 5 is 100."""
    return (aqi - 1) / 4 * 100


def uv_label(value):
    """The standard WHO exposure categories for the UV index."""
    if value < 3:
        return "Low"
    if value < 6:
        return "Moderate"
    if value < 8:
        return "High"
    if value < 11:
        return "Very high"
    return "Extreme"


def range_bar(low, high, overall_low, overall_high):
    """Return (left, width) percentages of a day's bar within the whole forecast's range."""
    span = overall_high - overall_low
    if span <= 0:
        return 0.0, 100.0
    left = (low - overall_low) / span * 100
    width = (high - low) / span * 100
    return round(left, 1), round(width, 1)


def today_high_low(days, today, current_high, current_low):
    """Return today's (high, low), widening the forecast with the current reading's values.

    days is the daily_summary table. Late in the evening there may be no forecast
    step left today, and then the current reading is all we can honestly show.
    """
    today_rows = days[days["local_date"] == today]
    if len(today_rows) == 0:
        return current_high, current_low
    high = max(today_rows["high"].to_list()[0], current_high)
    low = min(today_rows["low"].to_list()[0], current_low)
    return high, low
