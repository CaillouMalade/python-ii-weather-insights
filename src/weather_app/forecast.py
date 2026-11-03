"""The forecast as a table of 3-hour windows, and the rain-timing sentence. No Streamlit here.

Our free key only has the 5-day forecast in 3-hour steps. OpenWeatherMap gives the rain and
snow of each step as the amount in the 3 hours up to its time dt, so each step is treated as
the window from dt - 3 hours to dt. Temperature and cloud cover are the values at dt.
"""

import pandas as pd

STEP_HOURS = 3
STEP_SECONDS = STEP_HOURS * 3600
# From this chance of precipitation (0 to 1), a window counts as "rain likely".
RAIN_LIKELY = 0.5


def forecast_windows(steps, timezone_offset):
    """Add each window's local start and end, and its total precipitation in mm.

    steps is a DataFrame of the client's forecast steps. timezone_offset is the circuit's
    UTC offset in seconds. One offset is used for the whole table.
    """
    out = steps.copy()
    out = out.sort_values("dt")
    out["end"] = pd.to_datetime(out["dt"], unit="s") + pd.to_timedelta(timezone_offset, unit="s")
    out["start"] = out["end"] - pd.to_timedelta(STEP_HOURS, unit="h")
    out["precipitation_mm"] = out["rain_3h"] + out["snow_3h"]
    return out


def upcoming(windows, now):
    """The windows that have not ended yet. now is in Unix seconds."""
    out = windows.copy()
    return out[out["dt"] > now]


def today_high_low(windows, today, current_high, current_low):
    """Return today's (high, low): the forecast's values today, widened by the current reading.

    today is the local date as text, such as "2026-11-03". Late in the evening no forecast
    time may be left today, and then the current reading is all we can honestly show.
    """
    today_rows = windows[windows["end"].dt.strftime("%Y-%m-%d") == today]
    if len(today_rows) == 0:
        return current_high, current_low
    return max(today_rows["temperature"].max(), current_high), min(today_rows["temperature"].min(), current_low)


def short_time(moment):
    """A time such as Wed 15:00."""
    return moment.strftime("%a %H:%M")


def rain_timing(windows, now):
    """One sentence on when rain is likely, from the windows that have not ended yet (at least one).

    A window counts as wet when its chance of precipitation is at least RAIN_LIKELY.
    "Dry until" is only said when no earlier window has any rain at all.
    """
    left = upcoming(windows, now)
    likely = (left["pop"] >= RAIN_LIKELY).to_list()
    starts = left["start"].to_list()
    ends = left["end"].to_list()

    if True not in likely:
        sentence = f"No rain likely before {short_time(ends[-1])}, the end of the forecast."
        highest = left["pop"].max()
        if highest > 0:
            top = left[left["pop"] == highest].head(1).to_dict("records")[0]
            sentence = f"{sentence} Highest chance {highest * 100:.0f} %, {short_time(top['start'])}–{top['end'].strftime('%H:%M')}."
        return sentence

    first = likely.index(True)
    count = 0
    while first + count < len(likely) and likely[first + count]:
        count = count + 1

    hours = count * STEP_HOURS
    if first + count == len(likely):
        duration = f"for at least {hours} hours, to the end of the forecast"
    else:
        duration = f"for about {hours} hours, until {short_time(ends[first + count - 1])}"

    # The first window has started already when its start is before now.
    if first == 0 and left["dt"].to_list()[0] - STEP_SECONDS <= now:
        return f"Rain likely now, {duration}."

    earlier_rain = left["precipitation_mm"].to_list()[:first]
    opening = "Dry" if sum(earlier_rain) == 0 else "Rain unlikely"
    return f"{opening} until {short_time(starts[first])}, then rain likely {duration}."
