"""Mocked secure-wrapper checks; never use the real secure credential."""

import csv
import importlib.util
import json
from pathlib import Path
import subprocess
from unittest.mock import Mock

from weather_app.collector import FIELDS


spec = importlib.util.spec_from_file_location("collect_once", Path(__file__).resolve().parents[1] / "tools/collect_once.py")
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)


def inputs(tmp_path):
    config = tmp_path / "circuits.json"
    config.write_text(json.dumps({"locations": [{"id": "fixture"}]}), encoding="utf-8")
    key = tmp_path / "synthetic-key"
    key.write_text("FAKE_TEST_CREDENTIAL", encoding="utf-8")
    output = tmp_path / "weather.csv"
    return key, config, output, ["--key-file", str(key), "--config", str(config), "--output", str(output)]


def test_environment_only_and_verified_append(tmp_path, monkeypatch, capsys):
    key, config, output, args = inputs(tmp_path)
    def child(argv, **kwargs):
        assert kwargs["env"]["OPENWEATHER_API_KEY"] == "FAKE_TEST_CREDENTIAL"
        assert "FAKE_TEST_CREDENTIAL" not in " ".join(argv)
        assert kwargs["capture_output"] is True
        row = dict.fromkeys(FIELDS, "")
        row.update(location_id="fixture", fetched_at_utc="2026-01-01T00:00:01Z", observed_at_utc="2026-01-01T00:00:00Z")
        with output.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerow(row)
        return subprocess.CompletedProcess(argv, 0, "Saved 1; failed 0.\nFAKE_TEST_CREDENTIAL", "https://private.invalid/")
    run = Mock(side_effect=child)
    monkeypatch.setattr(wrapper.subprocess, "run", run)
    assert wrapper.main(args) == 0
    run.assert_called_once()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["rows_added"] == 1 and summary["new_location_coverage"] == 1
    assert summary["header_verified"] and summary["utc_timestamps_verified"]
    assert "FAKE_TEST_CREDENTIAL" not in captured.out + captured.err
    assert "https://" not in captured.out + captured.err


def test_auth_failure_is_sanitized_without_retry(tmp_path, monkeypatch, capsys):
    key, config, output, args = inputs(tmp_path)
    run = Mock(return_value=subprocess.CompletedProcess([], 1, "Location 1: AuthError: FAKE_TEST_CREDENTIAL\nSaved 0; failed 1.\n", "https://private.invalid/"))
    monkeypatch.setattr(wrapper.subprocess, "run", run)
    assert wrapper.main(args) == 1
    run.assert_called_once()
    captured = capsys.readouterr()
    summary = json.loads(captured.out)
    assert summary["errors"] == {"AuthError": 1}
    assert summary["rows_added"] == 0 and not output.exists()
    assert "FAKE_TEST_CREDENTIAL" not in captured.out + captured.err
    assert "https://" not in captured.out + captured.err


def test_bad_header_prevents_child_start(tmp_path, monkeypatch, capsys):
    key, config, output, args = inputs(tmp_path)
    output.write_text("incompatible,header\n", encoding="utf-8")
    run = Mock()
    monkeypatch.setattr(wrapper.subprocess, "run", run)
    assert wrapper.main(args) == 2
    run.assert_not_called()
    assert "no retry" in capsys.readouterr().err
