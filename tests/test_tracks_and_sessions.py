import tempfile
from datetime import datetime, timezone
from pathlib import Path

from weather_app.sessions import session_times, weekend_start
from weather_app.storage import GRADE1_TRACKS_PATH, TRACK_COLUMNS, append_track, load_all_tracks, load_tracks
from weather_app.tracks import NOT_FOUND_MESSAGE, check_new_track, distance_km

GRADE1 = load_tracks(GRADE1_TRACKS_PATH)


# Sessions

def test_weekend_starts_tomorrow():
    monday_evening = datetime(2026, 11, 16, 18, 30, tzinfo=timezone.utc)
    assert weekend_start(monday_evening) == datetime(2026, 11, 17, tzinfo=timezone.utc)


def test_weekend_crosses_the_end_of_a_month():
    last_day = datetime(2026, 11, 30, 9, 0, tzinfo=timezone.utc)
    assert weekend_start(last_day) == datetime(2026, 12, 1, tzinfo=timezone.utc)


def test_session_times_in_utc():
    sessions = session_times(datetime(2026, 11, 16, 10, 0, tzinfo=timezone.utc))
    assert [s["session"] for s in sessions] == ["FP1", "FP2", "FP3", "Qualifying", "Race"]
    assert sessions[0]["start_utc"] == datetime(2026, 11, 17, 8, 0, tzinfo=timezone.utc)
    assert sessions[-1]["start_utc"] == datetime(2026, 11, 19, 13, 0, tzinfo=timezone.utc)


# Track files

def test_grade1_tracks_load_as_locations():
    assert len(GRADE1) == 16
    monza = GRADE1[7]
    assert monza["id"] == "monza"
    assert monza["location"] == "Monza"
    assert isinstance(monza["latitude"], float)


def test_missing_my_tracks_file_is_empty():
    assert load_tracks(Path(tempfile.gettempdir()) / "no-such-tracks.csv") == []


def test_append_track_then_load_all():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "my_tracks.csv"
        track = {"id": "monza-pit", "location": "Monza pit", "country": "Italy", "latitude": 45.62, "longitude": 9.28}
        append_track(track, path)
        append_track(track, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(TRACK_COLUMNS)
        assert len(lines) == 3
        tracks = load_all_tracks(GRADE1_TRACKS_PATH, path)
        assert len(tracks) == 18
        assert tracks[-1]["location"] == "Monza pit"


# Distance

def test_distance_same_point_is_zero():
    assert distance_km(45.6, 9.28, 45.6, 9.28) == 0


def test_distance_madrid_barcelona():
    # About 505 km, to check the formula is right.
    assert 495 < distance_km(40.4168, -3.7038, 41.3874, 2.1686) < 515


# The checks, one message each

def error_for(name, latitude, longitude):
    """Run the checks and return the error message, or None if the track is accepted."""
    try:
        check_new_track(name, latitude, longitude, GRADE1, GRADE1)
    except ValueError as error:
        return str(error)
    return None


def test_empty_name():
    assert error_for("   ", "45.62", "9.28") == "Please enter a name for the track."


def test_name_already_used_any_case():
    assert error_for("monza", "45.62", "9.28") == "A track called Monza is already in the list."


def test_latitude_not_a_number():
    assert error_for("Test", "north", "9.28") == "Latitude must be a number, for example 50.43."


def test_latitude_out_of_range():
    assert error_for("Test", "95", "9.28") == "Latitude must be between -90 and 90."


def test_latitude_nan_is_rejected():
    assert error_for("Test", "nan", "9.28") == "Latitude must be between -90 and 90."


def test_longitude_not_a_number():
    assert error_for("Test", "45.62", "") == "Longitude must be a number, for example 50.43."


def test_longitude_out_of_range():
    assert error_for("Test", "45.62", "-200") == "Longitude must be between -180 and 180."


def test_far_from_any_circuit():
    # Madrid city centre: no Grade 1 circuit nearby.
    assert error_for("Madrid", "40.4168", "-3.7038") == NOT_FOUND_MESSAGE


def test_close_to_a_circuit_is_accepted():
    assert error_for("Monza Parabolica", "45.615", "9.29") is None
    track = check_new_track("Monza Parabolica", "45.615", "9.29", GRADE1, GRADE1)
    assert track == {
        "id": "monza-parabolica",
        "location": "Monza Parabolica",
        "country": "Italy",
        "latitude": 45.615,
        "longitude": 9.29,
    }
