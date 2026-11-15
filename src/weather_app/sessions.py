"""The race weekend: fixed session times in UTC, the same for every track.

The weekend is always the next three days, starting tomorrow. The forecasts only
reach a few days ahead (MET Norway about 2.5 days), so a weekend further away
would have little or no forecast to show.
"""

from datetime import datetime, timedelta, timezone

# (session, day of the weekend counted from 0, hour in UTC)
# Fixed in UTC; in Central European time these are the usual 09:00 / 15:00 / 14:00.
SESSIONS = [
    ("FP1", 0, 8),
    ("FP2", 0, 14),
    ("FP3", 1, 8),
    ("Qualifying", 1, 14),
    ("Race", 2, 13),
]


def weekend_start(now=None):
    """Return the first day of the race weekend: tomorrow at 00:00 UTC."""
    if now is None:
        now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return today + timedelta(days=1)


def session_times(now=None):
    """Return the weekend's sessions as a list of {"session": name, "start_utc": datetime}."""
    first_day = weekend_start(now)
    sessions = []
    for name, day, hour in SESSIONS:
        start = first_day + timedelta(days=day, hours=hour)
        sessions.append({"session": name, "start_utc": start})
    return sessions
