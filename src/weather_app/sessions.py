"""The race weekend: fixed session times in UTC, the same for every track."""

from datetime import datetime, timedelta, timezone

FRIDAY = 4  # datetime.weekday(): Monday is 0, Friday is 4

# (session, days after Friday, hour in UTC)
# 写死在 UTC，CET 下就是 09:00 / 15:00 / 14:00 这些常见时间
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
    # 周一到周四：往后找周五；周六 -1、周日 -2：退回本周末的周五
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
