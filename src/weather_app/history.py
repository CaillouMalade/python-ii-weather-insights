"""Our collected history: one reading per circuit every 30 minutes. No Streamlit and no key needed.

Each function takes a DataFrame and returns a new one, or returns a sentence for the page.
"""

import pandas as pd

from .display import compass_direction
from .models import METRES_PER_SECOND_TO_KMH

# A day with fewer hours of data than this is partial: its low and high are not the day's.
FULL_DAY_HOURS = 20
# OpenWeatherMap condition codes below 700 are thunderstorm, drizzle, rain and snow.
WET_CODE_LIMIT = 700
# Below this, a wind direction means little, so it is left out of the usual direction.
CALM_KMH = 5


def day_text(moment):
    """A date such as Sat 31 Oct. Built by hand because %-d does not work on Windows."""
    return f"{moment.strftime('%a')} {moment.day} {moment.strftime('%b')}"


def moment_text(moment):
    """A date and time such as Sat 31 Oct 14:00."""
    return f"{day_text(moment)} {moment.strftime('%H:%M')}"


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
    out["gust_kmh"] = out["wind_gust_m_s"] * METRES_PER_SECOND_TO_KMH
    # rain_1h_mm is blank when it did not rain, and a blank is never above 0.
    out["wet"] = (out["weather_code"] < WET_CODE_LIMIT) | (out["rain_1h_mm"] > 0)
    return out[["time", "temperature_c", "wind_kmh", "gust_kmh", "wind_direction_deg", "wet"]]


def hourly(readings):
    """Hourly averages on an unbroken hourly timeline.

    An hour with no reading stays empty (NaN), so a chart line stops there instead of
    being drawn straight across a gap in the collection. wet is the share of the hour's
    readings that were wet, so above 0 means it rained during that hour.
    """
    out = readings.copy()
    out["wet"] = out["wet"].astype(float)
    out = out.set_index("time")[["temperature_c", "wind_kmh", "gust_kmh", "wet"]]
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


def daily_extremes(hourly_values, full_days):
    """The hour of each full day's highest and lowest temperature, as two tables in time order."""
    out = hourly_values.dropna(subset=["temperature_c"]).copy()
    out["day"] = out["time"].dt.strftime("%Y-%m-%d")
    out = out[out["day"].isin(full_days)]
    highs = out.sort_values("temperature_c", ascending=False).drop_duplicates(subset="day", keep="first")
    lows = out.sort_values("temperature_c").drop_duplicates(subset="day", keep="first")
    return highs.sort_values("time"), lows.sort_values("time")


# One short finding per section, computed from the data


def temperature_finding(highs, lows):
    """The warmest and coldest moments of the full days."""
    if len(highs) == 0:
        return "No full day collected yet."
    warmest = highs.sort_values("temperature_c", ascending=False).to_dict("records")[0]
    coldest = lows.sort_values("temperature_c").to_dict("records")[0]
    return (
        f"Warmest {round(warmest['temperature_c'])} °C on {moment_text(warmest['time'])}, "
        f"coldest {round(coldest['temperature_c'])} °C on {moment_text(coldest['time'])}."
    )


def rain_finding(days):
    """How many hours with data had rain, and on which days."""
    hours = int(days["hours"].sum())
    rain_hours = int(days["rain_hours"].sum())
    if rain_hours == 0:
        return f"No rain in the {hours} hours collected."
    names = [day_text(pd.to_datetime(day)) for day in days[days["rain_hours"] > 0]["day"]]
    return f"Rain in {rain_hours} of the {hours} hours collected ({rain_hours / hours * 100:.0f} %), on {', '.join(names)}."


def wind_finding(readings):
    """Average wind, the strongest gust, and the usual direction."""
    parts = [f"Average {readings['wind_kmh'].mean():.0f} km/h"]
    gusts = readings.dropna(subset=["gust_kmh"])
    if len(gusts) > 0:
        strongest = gusts.sort_values("gust_kmh", ascending=False).to_dict("records")[0]
        parts.append(f"gusts up to {strongest['gust_kmh']:.0f} km/h on {moment_text(strongest['time'])}")
    moving = readings[readings["wind_kmh"] >= CALM_KMH]
    if len(moving) > 0:
        directions = [compass_direction(degrees) for degrees in moving["wind_direction_deg"]]
        parts.append(f"mostly from the {pd.Series(directions).value_counts().index[0]}")
    return ", ".join(parts) + "."
