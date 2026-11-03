"""Our collected history: one reading per circuit every 30 minutes. No Streamlit and no key needed.

Each function takes a DataFrame and returns a new one, or returns the sentence for the page.
"""

import pandas as pd

from .display import COMPASS_POINTS, compass_direction
from .models import METRES_PER_SECOND_TO_KMH

# A day with fewer hours of data than this is partial: its low and high are not the day's.
FULL_DAY_HOURS = 20
# OpenWeatherMap condition codes below 700 are thunderstorm, drizzle, rain and snow.
WET_CODE_LIMIT = 700
# Below this, a wind direction means little, so it is left out of the usual direction.
CALM_KMH = 5
# Each compass point's direction in degrees: N 0, NE 45 and so on.
COMPASS_DEGREES = {}
for number in range(len(COMPASS_POINTS)):
    COMPASS_DEGREES[COMPASS_POINTS[number]] = number * 45


def day_text(moment):
    """A date such as Sat 31 Oct. Built by hand because %-d does not work on Windows."""
    return f"{moment.strftime('%a')} {moment.day} {moment.strftime('%b')}"


def circuit_readings(history, circuit_id, timezone):
    """One circuit's readings in time order, in the circuit's local time.

    timezone is a name such as "Europe/Brussels", so summer time is handled. The times are
    then stored without a zone, so the charts show local clock time as it is.
    """
    out = history[history["location_id"] == circuit_id].copy()
    times = pd.to_datetime(out["fetched_at_utc"], format="mixed", utc=True)
    out["time"] = times.dt.tz_convert(timezone).dt.tz_localize(None)
    out = out.sort_values("time")
    out["wind_kmh"] = out["wind_speed_m_s"] * METRES_PER_SECOND_TO_KMH
    # rain_1h_mm is blank when it did not rain, and a blank is never above 0.
    out["wet"] = (out["weather_code"] < WET_CODE_LIMIT) | (out["rain_1h_mm"] > 0)
    return out[["time", "temperature_c", "wind_kmh", "wind_direction_deg", "wet"]]


def hourly(readings):
    """Hourly averages on an unbroken hourly timeline.

    An hour with no reading stays empty (NaN), so a chart line stops there instead of
    being drawn straight across a gap in the collection. wet is the share of the hour's
    readings that were wet, so above 0 means it rained during that hour.
    """
    out = readings.copy()
    out["wet"] = out["wet"].astype(float)
    out = out.set_index("time")[["temperature_c", "wind_kmh", "wet"]]
    return out.resample("h").mean().reset_index()


def daily(hourly_values):
    """One row per local day: hours with data, hours with rain, and whether the day is full."""
    out = hourly_values.copy()
    out["day"] = out["time"].dt.strftime("%Y-%m-%d")
    out["has_data"] = out["temperature_c"].notna()
    out["rain_hour"] = out["wet"] > 0
    out = out.groupby("day").agg(hours=("has_data", "sum"), rain_hours=("rain_hour", "sum")).reset_index()
    out["full"] = out["hours"] >= FULL_DAY_HOURS
    return out


def usual_direction(degrees):
    """The compass point the wind came from most often, as degrees (0, 45 ... 315), or None
    when there are no readings to go by."""
    if len(degrees) == 0:
        return None
    points = [compass_direction(value) for value in degrees]
    return COMPASS_DEGREES[pd.Series(points).value_counts().index[0]]


def daily_rows(readings):
    """One row per local day for the History view: low and high, average wind, the direction
    it came from most often (only readings above CALM_KMH count), and from daily(), the hours
    with data, the hours with rain and whether the day is full."""
    out = readings.copy()
    out["day"] = out["time"].dt.strftime("%Y-%m-%d")
    rows = out.groupby("day").agg(low=("temperature_c", "min"), high=("temperature_c", "max"), wind_kmh=("wind_kmh", "mean")).reset_index()
    directions = []
    for day in rows["day"]:
        moving = out[(out["day"] == day) & (out["wind_kmh"] >= CALM_KMH)]
        directions.append(usual_direction(moving["wind_direction_deg"].to_list()))
    rows["direction"] = directions
    return rows.merge(daily(hourly(readings)), on="day", how="left")


def rain_finding(days):
    """How many hours with data had rain, and on which days."""
    hours = int(days["hours"].sum())
    rain_hours = int(days["rain_hours"].sum())
    if rain_hours == 0:
        return f"No rain in the {hours} hours collected."
    names = [day_text(pd.to_datetime(day)) for day in days[days["rain_hours"] > 0]["day"]]
    return f"Rain in {rain_hours} of the {hours} hours collected ({rain_hours / hours * 100:.0f} %), on {', '.join(names)}."
