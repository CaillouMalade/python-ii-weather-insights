"""Simple HTML for the cards. Text from the API or data files always goes through escape()."""

from html import escape

from .display import METRES_PER_SECOND_TO_KMH, background_for, compass_direction, format_local_time, high_low_text, is_night
from .maps import WIND_BANDS


def wind_text(reading):
    """Such as 12 km/h SW."""
    text = f"{reading.wind_speed * METRES_PER_SECOND_TO_KMH:.0f} km/h"
    if reading.wind_deg is not None:
        text = f"{text} {compass_direction(reading.wind_deg)}"
    return text


def circuit_card(circuit, reading, note, selected, now):
    """A sidebar entry: name, local time and country, temperature, conditions and wind."""
    outline = " selected" if selected else ""
    name = escape(circuit["location"])
    country = escape(circuit["country"])
    if reading is None:
        return (
            f'<div class="city{outline}" style="background:rgba(255,255,255,.08)">'
            f'<div class="city-name">{name}</div><div class="city-small">{country}</div>'
            f'<div class="city-small city-note">{escape(note)}</div></div>'
        )

    background = background_for(reading.weather_id, is_night(now, reading.sunrise, reading.sunset))
    return (
        f'<div class="city{outline}" style="background:{background}">'
        f'<div class="city-row"><div class="city-main"><div class="city-name">{name}</div>'
        f'<div class="city-small">{format_local_time(now, reading.timezone_offset or 0)} · {country}</div></div>'
        f'<div class="city-temp">{round(reading.temperature)}°</div></div>'
        f'<div class="city-row"><div class="city-small">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="city-small">{wind_text(reading)}</div></div></div>'
    )


def stat(label, value, small=""):
    """One key figure in the header."""
    return f'<div class="stat"><div class="card-title">{label}</div><div class="stat-value">{value}</div><div class="small">{small}</div></div>'


def header(circuit, reading, high, low, rain_chance, now):
    """The top card: circuit, temperature and conditions on the left, key figures beside or below."""
    place = f"{escape(circuit['country'])} · {circuit['length_km']:.1f} km · {format_local_time(now, reading.timezone_offset or 0, '%a %H:%M')}"
    gusts = ""
    if reading.wind_gust is not None:
        gusts = f"Gusts {reading.wind_gust * METRES_PER_SECOND_TO_KMH:.0f} km/h"
    rain_value = "–" if rain_chance is None else f"{rain_chance * 100:.0f} %"
    stats = (
        stat("Feels like", f"{round(reading.feels_like)}°")
        + stat("Wind", wind_text(reading), gusts)
        + stat("Humidity", f"{reading.humidity} %")
        + stat("Rain, next 3 h", rain_value)
    )
    return (
        '<div class="card header">'
        '<div class="header-main">'
        f'<div class="header-city">{escape(circuit["location"])}</div>'
        f'<div class="small">{place}</div>'
        f'<div class="header-temp">{round(reading.temperature)}°</div>'
        f'<div class="header-line">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="header-line high-low">{high_low_text(high, low)}</div>'
        "</div>"
        f'<div class="header-stats">{stats}</div>'
        "</div>"
    )


def wind_legend():
    """The speed bands under the wind map, as one bar with hard colour stops."""
    width = 100 / len(WIND_BANDS)
    stops = []
    labels = ""
    for number in range(len(WIND_BANDS)):
        lowest, color = WIND_BANDS[number]
        stops.append(f"{color} {number * width:.0f}% {(number + 1) * width:.0f}%")
        # Each label sits at the start of its band. The last band is open-ended.
        text = f"{lowest}+ km/h" if number == len(WIND_BANDS) - 1 else f"{lowest}"
        labels = labels + f"<span>{text}</span>"
    return f'<div class="legend-bar" style="background:linear-gradient(90deg, {", ".join(stops)})"></div><div class="legend-labels">{labels}</div>'
