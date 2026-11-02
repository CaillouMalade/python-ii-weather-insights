"""Secure one-shot wrapper for OpenBot; contains no scheduling or retry loop."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from weather_app.collector import FIELDS


ROOT = Path(__file__).resolve().parents[1]
ERROR_TYPES = ("AuthError", "RateLimitError", "NetworkError", "LocationError", "PayloadError", "StorageError")


def read_rows(path):
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Incompatible header")
        rows = list(reader)
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("Incomplete CSV row")
        for field in ("fetched_at_utc", "observed_at_utc"):
            if not row[field].endswith("Z") or datetime.fromisoformat(row[field]).utcoffset() != timedelta(0):
                raise ValueError("Invalid UTC timestamp")
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", type=Path, required=True, help="External secure key file; never copied or displayed")
    parser.add_argument("--config", type=Path, default=ROOT / "circuits.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/current_weather.csv")
    args = parser.parse_args(argv)
    try:
        config = args.config.resolve()
        output = args.output.resolve()
        locations = json.loads(config.read_text(encoding="utf-8"))["locations"]
        if not isinstance(locations, list) or not locations:
            raise ValueError("Empty configuration")
        before = read_rows(output)
        environment = os.environ.copy()
        environment["OPENWEATHER_API_KEY"] = args.key_file.read_text(encoding="utf-8").strip()
        if not environment["OPENWEATHER_API_KEY"]:
            raise ValueError("Empty secure key")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "weather_app.collector", "--config", str(config), "--output", str(output)],
                cwd=ROOT, env=environment, capture_output=True, text=True,
                timeout=60 + 30 * len(locations),
            )
        finally:
            environment.pop("OPENWEATHER_API_KEY", None)
        # Never relay child stdout/stderr or exception text: emit only parsed aggregates.
        after = read_rows(output)
        if after[:len(before)] != before:
            raise ValueError("Existing rows changed")
        added = after[len(before):]
        match = re.search(r"^Saved (\d+); failed (\d+)\.$", result.stdout, re.MULTILINE)
        if match and len(added) != int(match[1]):
            raise ValueError("Append count mismatch")
        errors = Counter()
        for kind in ERROR_TYPES:
            count = sum(line.startswith(kind + ":") or (": " + kind + ":") in line
                        for line in (result.stdout + "\n" + result.stderr).splitlines())
            if count:
                errors[kind] = count
        configured_ids = {location["id"] for location in locations}
        new_ids = {row["location_id"] for row in added}
        if not new_ids <= configured_ids:
            raise ValueError("Unexpected new location")
        summary = {
            "status": "success" if result.returncode == 0 and match else "failure",
            "saved": int(match[1]) if match else len(added),
            "failed": int(match[2]) if match else None,
            "errors": dict(errors), "collector_exit": result.returncode,
            "rows_before": len(before), "rows_after": len(after), "rows_added": len(added),
            "configured_locations": len(locations), "new_location_coverage": len(new_ids),
            "header_verified": bool(after), "utc_timestamps_verified": bool(after),
            "existing_rows_preserved": True,
        }
        if added:
            for field in ("fetched_at_utc", "observed_at_utc"):
                summary[field + "_range"] = [min(row[field] for row in added), max(row[field] for row in added)]
        print(json.dumps(summary))
        return result.returncode if result.returncode in (1, 2) else (0 if summary["status"] == "success" else 2)
    except (OSError, ValueError, TypeError, KeyError, csv.Error, subprocess.SubprocessError):
        print("Secure collection setup, execution or CSV verification failed; no retry performed.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
