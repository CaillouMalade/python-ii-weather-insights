"""The race weekend: fixed session times in UTC, the same for every track."""

from datetime import datetime, timedelta, timezone

FRIDAY = 4  # datetime.weekday(): Monday is 0, Friday is 4

# (session, days after Friday, hour in UTC)
# Fixed in UTC; in Central European time these are the usual 09:00 / 15:00 / 14:00.
SESSIONS = [
    ("FP1", 0, 8),
    ("FP2", 0, 14),
    ("FP3", 1, 8),
    ("Qualifying", 1, 14),
    ("Race", 2, 13),
]


def weekend_friday(now=None):
    """Return the Friday (00:00 UTC) of the coming weekend, or of this one from Friday to Sunday."""
    if now is None:
        now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # Monday to Thursday: go forward to Friday; Saturday (-1) and Sunday (-2): go back to this weekend's Friday.
    days = FRIDAY - now.weekday()
    return today + timedelta(days=days)


def session_times(now=None):
    """Return the weekend's sessions as a list of {"session": name, "start_utc": datetime}."""
    friday = weekend_friday(now)
    sessions = []
    for name, day, hour in SESSIONS:
        start = friday + timedelta(days=day, hours=hour)
        sessions.append({"session": name, "start_utc": start})
    return sessions
