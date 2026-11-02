"""One-shot OpenWeatherMap current-weather collection; no scheduler or UI."""

import argparse
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
import requests


ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"
ROOT = Path(__file__).resolve().parents[2]
FIELDS = (
    "fetched_at_utc", "observed_at_utc", "location_id", "location_name",
    "latitude_deg", "longitude_deg", "provider_latitude_deg", "provider_longitude_deg",
    "temperature_c", "feels_like_c", "humidity_pct", "pressure_hpa",
    "wind_speed_m_s", "wind_direction_deg", "wind_gust_m_s", "cloud_cover_pct",
    "visibility_m", "rain_1h_mm", "snow_1h_mm", "weather_code", "weather_description",
)


class CollectorError(Exception):
    """A safe, user-facing failure: never include provider or requests text."""


class AuthError(CollectorError):
    pass


class RateLimitError(CollectorError):
    pass


class NetworkError(CollectorError):
    pass


class LocationError(CollectorError):
    pass


class PayloadError(CollectorError):
    pass


class StorageError(CollectorError):
    pass


def number(value, low=None, high=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError
    try:
        if not math.isfinite(value):
            raise ValueError
    except OverflowError:
        raise ValueError from None
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError
    return value


def validate_location(location):
    try:
        for field in ("id", "name"):
            value = location[field]
            if not isinstance(value, str) or not value.strip() or len(value) > 200:
                raise ValueError
        number(location["latitude"], -90, 90)
        number(location["longitude"], -180, 180)
    except (KeyError, TypeError, ValueError):
        raise LocationError("Location needs an id, name and valid numeric latitude/longitude.") from None
    return location


def utc_timestamp(value):
    return datetime.fromtimestamp(number(value, 0), timezone.utc).isoformat().replace("+00:00", "Z")


def parse_weather(payload, location, fetched_at):
    try:
        main = payload["main"]
        wind = payload["wind"]
        coord = payload["coord"]
        weather = payload["weather"][0]
        code = number(weather["id"], 0)
        description = weather["description"]
        if not isinstance(description, str) or not description.strip() or code != int(code):
            raise ValueError

        def optional(mapping, key, low=0, high=None):
            value = mapping.get(key)
            return "" if value is None else number(value, low, high)

        return dict(zip(FIELDS, (
            fetched_at, utc_timestamp(payload["dt"]), location["id"], location["name"],
            location["latitude"], location["longitude"],
            number(coord["lat"], -90, 90), number(coord["lon"], -180, 180),
            number(main["temp"]), number(main["feels_like"]),
            number(main["humidity"], 0, 100), number(main["pressure"], 0),
            number(wind["speed"], 0), optional(wind, "deg", 0, 360),
            optional(wind, "gust"), number(payload["clouds"]["all"], 0, 100),
            optional(payload, "visibility"), optional(payload.get("rain", {}), "1h"),
            optional(payload.get("snow", {}), "1h"), int(code), description,
        )))
    except (KeyError, IndexError, TypeError, ValueError, OverflowError, OSError, AttributeError):
        raise PayloadError("Malformed current-weather payload.") from None


def fetch_current(location, api_key, session):
    validate_location(location)
    try:
        response = session.get(
            ENDPOINT,
            params={"lat": location["latitude"], "lon": location["longitude"],
                    "appid": api_key, "units": "metric"},
            timeout=(5, 20), allow_redirects=False,
        )
    except requests.RequestException:
        raise NetworkError("Network request failed or timed out.") from None
    fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if response.status_code in (401, 403):
        raise AuthError("API authentication failed; check the local key and activation.")
    if response.status_code == 429:
        raise RateLimitError("Provider rate limit reached; retry on a later run.")
    if response.status_code in (400, 404):
        raise LocationError("Provider rejected this location.")
    if response.status_code != 200:
        raise NetworkError("Provider returned an unsuccessful HTTP status.")
    try:
        payload = response.json()
    except ValueError:
        raise PayloadError("Provider response is not valid JSON.") from None
    return parse_weather(payload, location, fetched_at)


@contextmanager
def output_lock(path):
    """Atomic directory creation excludes cooperating writers on local filesystems."""
    lock = path.with_name(path.name + ".lock")
    acquired = False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            lock.mkdir()
        except FileExistsError:
            raise StorageError("CSV is locked; another collector may be running. See README recovery.") from None
        acquired = True
        yield
    finally:
        if acquired:
            lock.rmdir()


def check_header(path):
    if path.exists() and path.stat().st_size:
        with path.open("r", newline="", encoding="utf-8") as stream:
            if next(csv.reader(stream), None) != list(FIELDS):
                raise StorageError("Existing CSV header is incompatible; choose another output file.")
        with path.open("rb") as stream:
            stream.seek(-1, os.SEEK_END)
            if stream.read(1) != b"\n":
                raise StorageError("Existing CSV has an incomplete final line; repair it before appending.")


def append_row(path, row):
    """Caller holds output_lock; each row is flushed and synced before continuing."""
    check_header(path)
    needs_header = not path.exists() or not path.stat().st_size
    with path.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)
        stream.flush()
        os.fsync(stream.fileno())


def collect(locations, api_key, output, session, report=print):
    output = Path(output).resolve()
    successes = failures = 0
    with output_lock(output):
        check_header(output)
        for index, location in enumerate(locations, 1):
            try:
                row = fetch_current(location, api_key, session)
            except CollectorError as error:
                # Index avoids echoing arbitrary user/provider content, URLs or keys.
                report(f"Location {index}: {type(error).__name__}: {error}")
                failures += 1
                continue
            append_row(output, row)
            successes += 1
            report(f"Location {index}: saved current weather.")
    return successes, failures


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True, help="JSON file containing a locations list")
    parser.add_argument("--output", type=Path, default=Path("data/current_weather.csv"))
    args = parser.parse_args(argv)
    try:
        with args.config.open(encoding="utf-8") as stream:
            config = json.load(stream)
        locations = config["locations"]
        if not isinstance(locations, list) or not locations:
            raise CollectorError("Configure a nonempty locations list before collecting.")
        # Load root secrets only when executing the CLI, never during module import.
        load_dotenv(ROOT / "variables.env", override=False)
        api_key = os.getenv("OPENWEATHER_API_KEY", "").strip()
        if not api_key or api_key == "your_key_here":
            raise CollectorError("Configure OPENWEATHER_API_KEY locally in root variables.env.")
        with requests.Session() as session:
            successes, failures = collect(locations, api_key, args.output, session)
        print(f"Saved {successes}; failed {failures}.")
        return 1 if failures else 0
    except CollectorError as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
    except (OSError, UnicodeError, csv.Error):
        print("Storage/config access failed; check files and permissions.", file=sys.stderr)
    except (ValueError, KeyError, TypeError):
        print("Invalid config: expected a JSON object with a locations list.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
