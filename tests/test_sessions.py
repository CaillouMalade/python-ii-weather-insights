# Known-answer tests for my sessions: the default weekend, checking input, overlap and rain status.

from datetime import date, datetime, time

import pandas as pd
import pytest

from weather_app.forecast import forecast_windows
from weather_app.sessions import add_default_weekend, check_session, default_weekend, session_status, session_windows, weekend_friday

# 5 to 11 January 2026: Monday 5 to Sunday 11.
MONDAY = datetime(2026, 1, 5, 12, 0)
HOUR = 3600


def days(sessions):
    return [(session["name"], session["day"], session["start"], session["end"]) for session in sessions]


def test_default_weekend_is_the_next_one_from_a_weekday():
    assert days(default_weekend("spa", MONDAY)) == [
        ("FP1", "2026-01-09", "09:00", "10:00"),
        ("FP2", "2026-01-09", "15:00", "16:00"),
        ("FP3", "2026-01-10", "09:00", "10:00"),
        ("Qualifying", "2026-01-10", "15:00", "16:00"),
        ("Race", "2026-01-11", "14:00", "16:00"),
    ]
    assert weekend_friday(datetime(2026, 1, 8, 23, 59)) == date(2026, 1, 9)


def test_inside_the_weekend_it_is_the_current_one():
    assert weekend_friday(datetime(2026, 1, 9, 7, 0)) == date(2026, 1, 9)
    assert weekend_friday(datetime(2026, 1, 10, 18, 0)) == date(2026, 1, 9)
    # Sunday before the race has finished.
    assert weekend_friday(datetime(2026, 1, 11, 15, 59)) == date(2026, 1, 9)


def test_on_sunday_evening_it_is_the_next_one():
    assert weekend_friday(datetime(2026, 1, 11, 16, 0)) == date(2026, 1, 16)
    assert weekend_friday(datetime(2026, 1, 11, 21, 30)) == date(2026, 1, 16)
    assert default_weekend("spa", datetime(2026, 1, 11, 21, 30))[-1]["day"] == "2026-01-18"


def test_default_weekend_adds_no_duplicates_and_keeps_custom_sessions():
    custom = {"track": "spa", "name": "Track walk", "day": "2026-01-08", "start": "17:00", "end": "18:00"}
    other_track = {"track": "monza", "name": "FP1", "day": "2026-01-09", "start": "09:00", "end": "10:00"}
    once = add_default_weekend([custom, other_track], "spa", MONDAY)
    assert len(once) == 7
    twice = add_default_weekend(once, "spa", MONDAY)
    assert twice == once
    assert once[0] == custom and once[1] == other_track


def test_default_weekend_skips_only_the_same_name_and_day():
    moved = {"track": "spa", "name": "FP1", "day": "2026-01-09", "start": "08:00", "end": "09:30"}
    added = add_default_weekend([moved], "spa", MONDAY)
    assert len(added) == 5
    assert added[0] == moved


def test_check_session_cleans_and_explains():
    assert check_session("spa", "  FP1 ", date(2026, 1, 9), time(9, 0), time(10, 0)) == {"track": "spa", "name": "FP1", "day": "2026-01-09", "start": "09:00", "end": "10:00"}
    with pytest.raises(ValueError, match="name"):
        check_session("spa", "   ", date(2026, 1, 9), time(9, 0), time(10, 0))
    with pytest.raises(ValueError, match="under 30"):
        check_session("spa", "x" * 31, date(2026, 1, 9), time(9, 0), time(10, 0))
    with pytest.raises(ValueError, match="end after it starts"):
        check_session("spa", "FP1", date(2026, 1, 9), time(10, 0), time(10, 0))


def make_windows(pops, rains):
    """3-hour windows on Friday 9 January 2026, local time: 00-03, 03-06, 06-09 and so on."""
    friday = int(pd.Timestamp("2026-01-09").timestamp())
    steps = []
    for number in range(len(pops)):
        steps.append({"dt": friday + (number + 1) * 3 * HOUR, "temperature": 10, "clouds": 50, "pop": pops[number], "rain_3h": rains[number], "snow_3h": 0})
    return forecast_windows(pd.DataFrame(steps), 0)


def session(start, end, day="2026-01-09"):
    return {"track": "spa", "name": "FP1", "day": day, "start": start, "end": end}


def test_a_session_overlaps_every_window_it_touches():
    windows = make_windows([0] * 8, [0] * 8)
    # 08:00-10:00 touches 06-09 and 09-12.
    assert session_windows(windows, session("08:00", "10:00"))["start"].dt.hour.to_list() == [6, 9]
    # Exactly 09:00-12:00 is one window: touching an edge does not count.
    assert session_windows(windows, session("09:00", "12:00"))["start"].dt.hour.to_list() == [9]


def test_session_rain_rule_is_the_status_rule():
    windows = make_windows([0, 0, 0.2, 0.6, 0.1, 0, 0, 0], [0, 0, 0, 1.2, 0, 0, 0, 0])
    # FP1 09:00-10:00 sits in the 09-12 window, where rain is likely.
    assert session_status(windows, session("09:00", "10:00")) == ("rain", 0.6)
    # 07:00-08:00 only touches 06-09: dry, with its 20 % chance.
    assert session_status(windows, session("07:00", "08:00")) == ("dry", 0.2)
    # 08:30-09:30 touches both: one likely window is enough.
    assert session_status(windows, session("08:30", "09:30"))[0] == "rain"


def test_a_session_beyond_the_forecast_has_no_status():
    windows = make_windows([0.9] * 8, [1] * 8)
    assert session_status(windows, session("09:00", "10:00", day="2026-01-20")) == (None, None)
