"""Simple HTML for the now group, the lights and the session rows. Text from the API or data
files always goes through escape()."""

from html import escape

import pandas as pd

from .display import compass_direction, format_local_time, high_low_text
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
    return f'<span class="light {state or "off"}" role="img" aria-label="{escape(label)}" title="{escape(label)}"></span>'


def radar_problem(radar):
    """A few words when the radar cannot be trusted here, and nothing when it can."""
    if radar is None:
        return "Radar unavailable"
    if not radar["complete"]:
        return "Radar incomplete"
    if radar["covered"] is False:
        return "No radar here"
    return ""


def now_group(reading, high, low, now, states, sentence, problem):
    """Everything about now in one tight group: the temperature, the facts beside it, then the
    three status lights with the rain-timing line. Labels only where a value cannot say it alone."""
    lines = [
        [escape(reading.conditions.capitalize()), format_local_time(now, reading.timezone_offset or 0, "%a %H:%M")],
        [high_low_text(high, low), f"Feels {round(reading.feels_like)}°"],
        [wind_text(reading), f"Humidity {reading.humidity} %"],
    ]
    if reading.wind_gust is not None:
        lines[2].insert(1, f"Gusts {reading.wind_gust * METRES_PER_SECOND_TO_KMH:.0f}")
    # Each fact stays whole when a line wraps on a phone. An empty fact (an equal high and low) is left out.
    facts = []
    for line in lines:
        facts.append(" · ".join([f'<span class="fact">{part}</span>' for part in line if part != ""]))
    lights = "".join([light(state, name) for state, name in zip(states, LIGHT_NAMES)])
    problem_html = f'<span class="muted">{problem}</span>' if problem else ""
    return (
        '<div class="now">'
        f'<div class="now-temp">{round(reading.temperature)}°</div>'
        '<div class="now-facts">' + "".join([f"<div>{fact}</div>" for fact in facts]) + "</div>"
        f'<div class="status"><div class="lights">{lights}</div><div class="status-text">{escape(sentence)}</div>{problem_html}</div>'
        "</div>"
    )


def session_row(session, state, chance):
    """One session in the sidebar: its light, name, day and times, and its highest chance of rain."""
    start = pd.Timestamp(f"{session['day']} {session['start']}")
    value = "" if chance is None else f"{chance * 100:.0f} %"
    return (
        '<div class="session">'
        f'{light(state, session["name"])}'
        f'<div class="session-main"><div class="session-name">{escape(session["name"])}</div>'
        f'<div class="muted">{start.strftime("%a %H:%M")}–{escape(session["end"])}</div></div>'
        f'<span class="session-value">{value}</span>'
        "</div>"
    )
