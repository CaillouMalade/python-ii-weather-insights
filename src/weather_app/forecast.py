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


def window_state(windows):
    """"rain" if any of these windows has rain likely, "dry" if none has, None if there are none."""
    if len(windows) == 0:
        return None
    if windows["pop"].max() >= RAIN_LIKELY:
        return "rain"
    return "dry"


def next_three_hours(windows, now):
    """The windows that overlap the next 3 hours: the one running now and the next one.

    The header's chance of rain and the middle status light both come from these windows,
    so the two can never disagree.
    """
    left = upcoming(windows, now)
    return left[left["dt"] - STEP_SECONDS < now + STEP_SECONDS]


def status_lights(windows, now, today):
    """The three track-status lights: now, the next 3 hours and later today.

    Each is "rain", "dry" or None when no forecast window covers it, by the same rule as
    rain_timing. now is the window running at this moment. The next 3 hours are the windows
    from next_three_hours. Later today is every window that starts after that and still
    today, so late in the evening it has none. today is the local date as text.
    """
    left = upcoming(windows, now)
    starts = left["dt"] - STEP_SECONDS
    running = left[starts <= now]
    later = left[(starts >= now + STEP_SECONDS) & (left["start"].dt.strftime("%Y-%m-%d") == today)]
    return [window_state(running), window_state(next_three_hours(windows, now)), window_state(later)]


def calm_clouds(windows):
    """Cloud cover averaged over 5 windows (15 hours) around each one, for a calm band on the chart.

    Only that chart uses it. min_periods=1 keeps the first and last windows, which have
    fewer neighbours.
    """
    return windows["clouds"].rolling(5, center=True, min_periods=1).mean()


def short_time(moment):
    """A time such as Wed 15:00."""
    return moment.strftime("%a %H:%M")


def rain_timing(windows, now):
    """One short line on when rain is likely, from the windows that have not ended yet (at least one).

    A window counts as wet when its chance of precipitation is at least RAIN_LIKELY.
    "Dry" is only said when no earlier window has any rain at all; otherwise "Mostly dry".
    """
    left = upcoming(windows, now)
    likely = (left["pop"] >= RAIN_LIKELY).to_list()
    if True not in likely:
        return "Dry all week"

    first = likely.index(True)
    count = 0
    while first + count < len(likely) and likely[first + count]:
        count = count + 1
    to_the_end = first + count == len(likely)
    until = "" if to_the_end else f" until {short_time(left['end'].to_list()[first + count - 1])}"

    # The first window has started already when its start is before now.
    if first == 0 and left["dt"].to_list()[0] - STEP_SECONDS <= now:
        return "Rain likely all week" if to_the_end else f"Rain likely{until}"

    earlier_rain = left["precipitation_mm"].to_list()[:first]
    opening = "Dry" if sum(earlier_rain) == 0 else "Mostly dry"
    return f"{opening} until {short_time(left['start'].to_list()[first])}, then rain{until}"


def daily_conditions(windows):
    """One row per local day: its midday (12:00, where the day's icon goes) and the condition
    code of the window closest to 13:00, which describes the day better than a night one.
    On a tie (12:00 and 15:00 are both an hour away), the earlier window wins."""
    out = windows.copy()
    out["day"] = out["end"].dt.strftime("%Y-%m-%d")
    out["from_midday"] = (out["end"].dt.hour - 13).abs()
    out = out.sort_values(["day", "from_midday", "end"]).drop_duplicates(subset="day", keep="first")
    out["midday"] = pd.to_datetime(out["day"]) + pd.to_timedelta(12, unit="h")
    return out[["day", "midday", "weather_id"]].reset_index(drop=True)
