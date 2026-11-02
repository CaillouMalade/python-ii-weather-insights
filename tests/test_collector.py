"""Synthetic provider fixtures only: these tests never fetch real weather."""

import copy
import csv
from datetime import datetime
from unittest.mock import Mock

import pytest
import requests

from weather_app.collector import (
    ENDPOINT, FIELDS, AuthError, LocationError, NetworkError, PayloadError,
    RateLimitError, StorageError, collect, fetch_current, main, output_lock,
)


@pytest.fixture
def location():
    # Artificial test coordinates; not a proposed racetrack.
    return {"id": "test", "name": "Synthetic fixture", "latitude": 0, "longitude": 0}


@pytest.fixture
def payload():
    return {
        "dt": 1704067200, "coord": {"lat": 0, "lon": 0},
        "main": {"temp": 12.5, "feels_like": 11, "humidity": 75, "pressure": 1010},
        "wind": {"speed": 3.5, "deg": 180}, "clouds": {"all": 40},
        "weather": [{"id": 800, "description": "clear sky"}], "visibility": 10000,
    }


def response(payload, status=200):
    result = Mock(status_code=status)
    result.json.return_value = payload
    return result


def test_append_each_success_and_both_utc_timestamps(tmp_path, location, payload, monkeypatch):
    output = tmp_path / "nested" / "weather.csv"
    session = Mock()
    session.get.return_value = response(payload)
    import os
    sync = Mock(wraps=os.fsync)
    monkeypatch.setattr("weather_app.collector.os.fsync", sync)
    start = datetime.now().astimezone()
    for _ in range(2):
        assert collect([location], "fake-test-key", output, session) == (1, 0)
    with output.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        assert reader.fieldnames == list(FIELDS)
        rows = list(reader)
    assert len(rows) == 2
    assert sync.call_count == 2
    assert rows[0]["observed_at_utc"] == "2024-01-01T00:00:00Z"
    assert start <= datetime.fromisoformat(rows[0]["fetched_at_utc"]) <= datetime.now().astimezone()
    assert rows[0]["temperature_c"] == "12.5"
    assert rows[0]["wind_speed_m_s"] == "3.5"
    assert rows[0]["rain_1h_mm"] == ""  # Missing is not a fabricated zero.
    assert rows[0]["location_id"] == "test"
    assert rows[0]["latitude_deg"] == "0"
    session.get.assert_called_with(
        ENDPOINT, params={"lat": 0, "lon": 0, "appid": "fake-test-key", "units": "metric"},
        timeout=(5, 20), allow_redirects=False,
    )


def test_success_is_durable_before_next_request(tmp_path, location, payload):
    output = tmp_path / "weather.csv"
    def second_request(*args, **kwargs):
        with output.open(newline="", encoding="utf-8") as stream:
            assert len(list(csv.DictReader(stream))) == 1
        raise requests.Timeout("sensitive URL and key")
    session = Mock()
    calls = iter([lambda: response(payload), lambda: second_request()])
    session.get.side_effect = lambda *a, **kw: next(calls)()
    assert collect([location, location], "fake-test-key", output, session) == (1, 1)


@pytest.mark.parametrize("status,error", [
    (401, AuthError), (403, AuthError), (429, RateLimitError),
    (400, LocationError), (404, LocationError), (500, NetworkError), (302, NetworkError),
])
def test_distinct_http_errors(location, status, error):
    session = Mock()
    session.get.return_value = response({"message": "SECRET https://secret-url"}, status)
    with pytest.raises(error) as caught:
        fetch_current(location, "SECRET", session)
    assert "SECRET" not in str(caught.value)
    assert "https://" not in str(caught.value)


def test_isolated_failures_and_redacted_output(tmp_path, location, payload, capsys):
    session = Mock()
    session.get.side_effect = [
        requests.ConnectionError("https://example/?appid=SECRET"),
        response({"dt": "SECRET"}), response(payload),
    ]
    invalid = {**location, "latitude": 91, "name": "SECRET"}
    assert collect([invalid, location, location, location], "SECRET", tmp_path / "w.csv", session) == (1, 3)
    output = capsys.readouterr().out
    assert "LocationError" in output and "NetworkError" in output and "PayloadError" in output
    assert "SECRET" not in output and "https://" not in output
    assert session.get.call_count == 3


@pytest.mark.parametrize("latitude,longitude", [
    (91, 0), (0, -181), (float("nan"), 0), (True, 0), ("1", 0), (10 ** 400, 0),
])
def test_invalid_coordinates_do_not_request(location, latitude, longitude):
    session = Mock()
    with pytest.raises(LocationError):
        fetch_current({**location, "latitude": latitude, "longitude": longitude}, "fake", session)
    session.get.assert_not_called()


@pytest.mark.parametrize("change", [
    lambda p: p.update(dt="wrong"), lambda p: p.update(weather=[]),
    lambda p: p["main"].update(temp=float("inf")),
    lambda p: p["main"].update(humidity=101), lambda p: p.update(rain=None),
])
def test_malformed_payload(location, payload, change):
    broken = copy.deepcopy(payload)
    change(broken)
    session = Mock()
    session.get.return_value = response(broken)
    with pytest.raises(PayloadError):
        fetch_current(location, "fake", session)


def test_invalid_json_is_redacted(location):
    session = Mock()
    session.get.return_value = response(None)
    session.get.return_value.json.side_effect = ValueError("SECRET URL")
    with pytest.raises(PayloadError, match="not valid JSON"):
        fetch_current(location, "fake", session)


@pytest.mark.parametrize("contents", ["wrong,header\n", ",".join(FIELDS)])
def test_reject_existing_incompatible_or_partial_csv(tmp_path, location, contents):
    output = tmp_path / "w.csv"
    output.write_text(contents, encoding="utf-8")
    session = Mock()
    with pytest.raises(StorageError):
        collect([location], "fake", output, session)
    assert output.read_text(encoding="utf-8") == contents
    session.get.assert_not_called()


def test_lock_excludes_other_writer_and_releases_on_error(tmp_path, location):
    output = tmp_path / "w.csv"
    session = Mock()
    with pytest.raises(RuntimeError):
        with output_lock(output):
            with pytest.raises(StorageError, match="locked"):
                collect([location], "fake", output, session)
            session.get.assert_not_called()
            raise RuntimeError("test interruption")
    assert not output.with_name("w.csv.lock").exists()


def test_cli_empty_config_never_requests(tmp_path, monkeypatch, capsys):
    config = tmp_path / "circuits.json"
    config.write_text('{"locations": []}', encoding="utf-8")
    session = Mock()
    monkeypatch.setattr("weather_app.collector.requests.Session", session)
    assert main(["--config", str(config)]) == 2
    session.assert_not_called()
    assert "nonempty" in capsys.readouterr().err


@pytest.mark.parametrize("key", ["", "your_key_here"])
def test_cli_unconfigured_key_never_requests(tmp_path, location, monkeypatch, capsys, key):
    import json
    config = tmp_path / "circuits.json"
    config.write_text(json.dumps({"locations": [location]}), encoding="utf-8")
    monkeypatch.setenv("OPENWEATHER_API_KEY", key)
    load = Mock()
    monkeypatch.setattr("weather_app.collector.load_dotenv", load)
    session = Mock()
    monkeypatch.setattr("weather_app.collector.requests.Session", session)
    assert main(["--config", str(config)]) == 2
    load.assert_called_once()
    assert load.call_args.args[0].name == "variables.env"
    session.assert_not_called()
    assert "Configure OPENWEATHER_API_KEY" in capsys.readouterr().err
