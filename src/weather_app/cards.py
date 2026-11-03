"""Simple HTML for the cards and lights. Text from the API or data files always goes through escape()."""

from html import escape

from .display import compass_direction, format_local_time, high_low_text
from .maps import WIND_BANDS
from .models import METRES_PER_SECOND_TO_KMH

LIGHT_NAMES = ["Now", "Next 3 hours", "Later today"]
LIGHT_WORDS = {"rain": "rain likely", "dry": "dry", None: "no forecast"}


def wind_text(reading):
    """Such as 12 km/h SW."""
    text = f"{reading.wind_kmh:.0f} km/h"
    if reading.wind_deg is not None:
        text = f"{text} {compass_direction(reading.wind_deg)}"
    return text


def light(state, name):
    """One status light: green when dry, red when rain is likely, unlit without a forecast.
    The words say the same as the colour, for screen readers and on hover."""
    label = f"{name}: {LIGHT_WORDS[state]}"
    return f'<span class="light {state or "off"}" role="img" aria-label="{label}" title="{label}"></span>'


def radar_text(radar, offset):
    """The radar's state in a few words: its time, or why it cannot be trusted here."""
    if radar is None:
        return "Radar unavailable"
    if not radar["complete"]:
        return "Radar incomplete"
    if radar["covered"] is False:
        return "No radar here"
    return f"Radar {format_local_time(radar['time'], offset)}"


def status_strip(states, sentence, radar_words):
    """The track-status strip: three lights, the rain-timing sentence and the radar's state."""
    lights = "".join([light(state, name) for state, name in zip(states, LIGHT_NAMES)])
    return (
        '<div class="status">'
        f'<div class="lights">{lights}</div>'
        f'<div class="status-text">{escape(sentence)}</div>'
        f'<div class="muted">{radar_words}</div>'
        "</div>"
    )


def circuit_card(circuit, reading, state, note, selected, now):
    """A sidebar entry: status light and name, local time and conditions, temperature and wind."""
    outline = " selected" if selected else ""
    name = escape(circuit["location"])
    title = f'<div class="card-name">{light(state, "Next 3 hours")}<span>{name}</span></div>'
    if reading is None:
        return f'<div class="circuit{outline}">{title}<div class="small muted">{escape(note)}</div></div>'
    return (
        f'<div class="circuit{outline}">'
        f'<div class="card-row">{title}<div class="card-temp">{round(reading.temperature)}°</div></div>'
        f'<div class="card-row small muted"><span>{format_local_time(now, reading.timezone_offset or 0)} · {escape(reading.conditions.capitalize())}</span>'
        f"<span>{wind_text(reading)}</span></div></div>"
    )


def stat(label, value, small=""):
    """One key figure in the header."""
    return f'<div><div class="label">{label}</div><div class="stat-value">{value}</div><div class="small muted">{small}</div></div>'


def header(circuit, reading, high, low, rain_chance, now):
    """The top card: circuit, local time and temperature on the left, key figures beside or below."""
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
        '<div class="header">'
        '<div class="header-main">'
        f'<div class="header-name">{escape(circuit["location"])}</div>'
        f'<div class="muted">{format_local_time(now, reading.timezone_offset or 0, "%a %H:%M")}</div>'
        f'<div class="header-temp">{round(reading.temperature)}°</div>'
        f'<div>{escape(reading.conditions.capitalize())}</div>'
        f'<div class="high-low muted">{high_low_text(high, low)}</div>'
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
    return f'<div class="legend-bar" style="background:linear-gradient(90deg, {", ".join(stops)})"></div><div class="legend-labels muted">{labels}</div>'
