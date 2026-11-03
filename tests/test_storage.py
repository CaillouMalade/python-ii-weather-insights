# Storage needs real files. pytest fixtures are off-limits in this project, so each test
# makes its own folder with the standard library's tempfile.

import json
import tempfile
from pathlib import Path

import pandas as pd

from weather_app.models import WeatherReading
from weather_app.storage import LOG_COLUMNS, append_reading, load_circuits, load_history, load_track


def test_append_writes_header_once():
    reading = WeatherReading("Nürburgring GP", 50.3, 6.9, 8.0, 6.0, 80, 2.0, "light rain", wind_gust=5.0)
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.csv"
        append_reading(reading, path)
        append_reading(reading, path)
        lines = path.read_text(encoding="utf-8").splitlines()
        assert lines[0] == ",".join(LOG_COLUMNS)
        assert len(lines) == 3
        log = pd.read_csv(path, encoding="utf-8")
        assert log["location"].to_list() == ["Nürburgring GP", "Nürburgring GP"]
        assert log["wind_gust"].to_list() == [5.0, 5.0]


def test_log_columns_keep_the_order_of_the_existing_log():
    # Changing this order would misalign new rows with the rows already in data/weather_log.csv.
    assert ",".join(LOG_COLUMNS) == (
        "timestamp_utc,location,latitude,longitude,temperature,feels_like,humidity,wind_speed,conditions,"
        "temp_min,temp_max,pressure,clouds,wind_deg,wind_gust,visibility,rain_1h,snow_1h,"
        "weather_id,icon,observed_at,timezone_offset,sunrise,sunset"
    )


def test_circuit_file_matches_the_collector_ids():
    circuits = load_circuits()
    ids = [circuit["id"] for circuit in circuits]
    assert len(ids) == 18
    assert len(set(ids)) == 18
    collected = set(load_history()["location_id"].unique())
    assert set(ids) == collected


def test_circuits_are_location_dictionaries():
    spa = load_circuits()[2]
    assert spa == {
        "id": "spa",
        "location": "Spa-Francorchamps",
        "country": "Belgium",
        "latitude": 50.4372,
        "longitude": 5.9714,
        "timezone": "Europe/Brussels",
        "length_km": 7.004,
        "track_file": "be-1925.geojson",
        "track_credit": "f1-circuits (MIT)",
    }


def test_missing_history_is_empty():
    with tempfile.TemporaryDirectory() as folder:
        assert len(load_history(Path(folder) / "none.csv")) == 0


def write_geojson(folder, name, features):
    (Path(folder) / name).write_text(json.dumps({"type": "FeatureCollection", "features": features}), encoding="utf-8")


def line(coordinates):
    return {"type": "Feature", "properties": {}, "geometry": {"type": "LineString", "coordinates": coordinates}}


def test_load_track_keeps_each_way_as_its_own_segment():
    with tempfile.TemporaryDirectory() as folder:
        point = {"type": "Feature", "properties": {}, "geometry": {"type": "Point", "coordinates": [0, 0]}}
        write_geojson(folder, "t.geojson", [line([[0, 0], [1, 1]]), point, line([[5, 5]]), line([[2, 2], [3, 3], [4, 4]])])
        # The point and the one-point line cannot be drawn, so they are skipped.
        assert load_track("t.geojson", Path(folder)) == [[[0, 0], [1, 1]], [[2, 2], [3, 3], [4, 4]]]


def test_load_track_without_a_usable_file_gives_no_outline():
    with tempfile.TemporaryDirectory() as folder:
        (Path(folder) / "broken.geojson").write_text("{not json", encoding="utf-8")
        assert load_track("broken.geojson", Path(folder)) == []
        assert load_track("missing.geojson", Path(folder)) == []
        assert load_track("", Path(folder)) == []


def test_real_outlines_one_f1_line_or_several_openstreetmap_ways():
    circuits = load_circuits()
    by_id = {}
    for circuit in circuits:
        by_id[circuit["id"]] = circuit
    assert len(load_track(by_id["spa"]["track_file"])) == 1
    assert len(load_track(by_id["nordschleife"]["track_file"])) == 53
    assert by_id["nordschleife"]["track_credit"] == ""
