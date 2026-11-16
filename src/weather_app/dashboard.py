"""Small helpers for the Weekend overview and Session dashboard pages (cards 7 and 8).

They take the forecast table (one row per provider and 3-hour window) and return plain
values the pages can show. No Streamlit here, so every helper can be tested on its own.
"""

import pandas as pd

from .models import METRES_PER_SECOND_TO_KMH
from .windows import window_start

# The 8 compass directions, clockwise from north, 45 degrees apart.
COMPASS_SECTORS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
DEGREES_PER_SECTOR = 45


def compass_sector(degrees):
    """Turn a wind direction in degrees into N, NE, E, SE, S, SW, W or NW."""
    # Dividing by 45 counts how many sectors we are from north; round() picks the closest.
    # % 8 sends 360 degrees (8 sectors) back to N.
    index = round(degrees / DEGREES_PER_SECTOR) % len(COMPASS_SECTORS)
    return COMPASS_SECTORS[index]


def direction_votes(window_rows):
    """Return (most common direction, how many providers say it, how many gave a direction).

    window_rows are the forecast rows of one 3-hour window. Returns None when no provider
    sent a direction. We count votes instead of averaging the degrees, because the
    average of 350 and 10 degrees would be 180: the opposite direction.
    """
    votes = {}
    for degrees in window_rows["wind_deg"].dropna():
        sector = compass_sector(degrees)
        votes[sector] = votes.get(sector, 0) + 1

    if len(votes) == 0:
        return None

    best = None
    for sector in votes:
        if best is None or votes[sector] > votes[best]:
            best = sector
    return best, votes[best], sum(votes.values())


def interval_text(window, column, unit):
    """Return the 95% interval of one combined value as text, e.g. "95%: 10.1 to 14.7 °C"."""
    # With a single provider there is nothing to compare, so combine_forecasts leaves it empty.
    if pd.isna(window[column + "_low"]):
        return "One provider only: no interval"
    return f"95%: {window[column + '_low']:.1f} to {window[column + '_high']:.1f} {unit}"


def chance_of_rain(window):
    """Percentage of providers that predict rain, for one row of combine_forecasts()."""
    return window["rain_providers"] / window["providers"] * 100


def session_window_rows(table, session_start):
    """Return the forecast rows (one per provider) of the 3-hour window a session starts in."""
    start = window_start(session_start)
    return table[table["time_utc"] == start]


def session_message(session_start, now, rows):
    """Return the message to show instead of a forecast, or None when there is one to show."""
    if window_start(session_start) < window_start(now):
        return "This session is over."
    if len(rows) == 0:
        return "No forecast yet."
    return None


def provider_table(window_rows):
    """Return one row per provider for one window, with readable column names and units."""
    rows = []
    for _, row in window_rows.iterrows():
        # A provider can leave a value out (None); then the cell stays empty and the direction "Unknown".
        direction = "Unknown"
        if not pd.isna(row["wind_deg"]):
            direction = compass_sector(row["wind_deg"])
        rows.append({
            "Provider": row["source"],
            "Temperature (°C)": row["temperature"],
            "Rain (mm)": row["rain"],
            "Wind (km/h)": row["wind_speed"] * METRES_PER_SECOND_TO_KMH,
            "Wind from": direction,
        })
    return pd.DataFrame(rows)
