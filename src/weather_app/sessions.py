"""My sessions at a track: the default weekend, checking a session, and its rain status.

A session is a dictionary with track (a circuit id), name, day ("2026-11-06"), start and
end ("09:00"), all in the track's local time. No Streamlit here.
"""

from datetime import timedelta

import pandas as pd

from .forecast import window_state

# (name, weekday with Monday as 0, start, end). The durations are our own defaults.
DEFAULT_WEEKEND = [
    ("FP1", 4, "09:00", "10:00"),
    ("FP2", 4, "15:00", "16:00"),
    ("FP3", 5, "09:00", "10:00"),
    ("Qualifying", 5, "15:00", "16:00"),
    ("Race", 6, "14:00", "16:00"),
]
FRIDAY = 4
NAME_LIMIT = 30


def weekend_friday(now_local):
    """The Friday of the weekend to plan: the current one until its last session ends, else the next.

    now_local is a datetime in the track's local time.
    """
    weekday = now_local.weekday()
    last_end = DEFAULT_WEEKEND[-1][3]
    inside = weekday in (FRIDAY, FRIDAY + 1) or (weekday == FRIDAY + 2 and now_local.strftime("%H:%M") < last_end)
    if inside:
        return now_local.date() - timedelta(days=weekday - FRIDAY)
    return now_local.date() + timedelta(days=(FRIDAY - weekday) % 7)


def default_weekend(track, now_local):
    """The standard weekend's sessions for a track, on the weekend from weekend_friday."""
    friday = weekend_friday(now_local)
    sessions = []
    for name, weekday, start, end in DEFAULT_WEEKEND:
        day = friday + timedelta(days=weekday - FRIDAY)
        sessions.append({"track": track, "name": name, "day": day.isoformat(), "start": start, "end": end})
    return sessions


def add_default_weekend(sessions, track, now_local):
    """Return the sessions with the default weekend added, skipping any with the same track, name and day."""
    out = list(sessions)
    for new in default_weekend(track, now_local):
        taken = False
        for old in out:
            if old["track"] == new["track"] and old["name"] == new["name"] and old["day"] == new["day"]:
                taken = True
        if not taken:
            out.append(new)
    return out


def check_session(track, name, day, start, end):
    """Return a clean session dictionary, or raise ValueError with a clear message.

    day is a date, start and end are times, as Streamlit's date and time inputs give them.
    """
    cleaned = name.strip()
    if cleaned == "":
        raise ValueError("Give the session a name.")
    if len(cleaned) > NAME_LIMIT:
        raise ValueError(f"Keep the name under {NAME_LIMIT} characters.")
    if end <= start:
        raise ValueError("The session must end after it starts.")
    return {"track": track, "name": cleaned, "day": day.isoformat(), "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M")}


def session_times(session):
    """The session's start and end as local timestamps."""
    return pd.Timestamp(f"{session['day']} {session['start']}"), pd.Timestamp(f"{session['day']} {session['end']}")


def session_windows(windows, session):
    """The forecast windows that overlap the session. Both are in the track's local time."""
    start, end = session_times(session)
    return windows[(windows["start"] < end) & (windows["end"] > start)]


def session_status(windows, session):
    """The session's light ("rain", "dry" or None beyond the forecast) and its highest chance of rain.

    The same rule as the status strip: rain likely if any overlapping window reaches RAIN_LIKELY.
    """
    overlapping = session_windows(windows, session)
    if len(overlapping) == 0:
        return None, None
    return window_state(overlapping), overlapping["pop"].max()
