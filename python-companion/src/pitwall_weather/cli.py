"""Fetch, inspect and export genuine snapshots without printing credentials."""
import argparse
import json
import sys
from .analytics import derived_metrics, latest_comparison, temperature_trends
from .clients import GeocodingClient, OpenMeteoClient, OpenWeatherClient, fetch_many
from .config import load_config
from .errors import WeatherError
from .models import Location
from .storage import SnapshotStore
from .tracks import TRACKS


def parser():
    result = argparse.ArgumentParser(description="Pitwall Python weather companion")
    result.add_argument("--env", default="variables.env", help="Local dotenv file (never committed)")
    result.add_argument("--database", help="SQLite path, overriding PITWALL_DATABASE")
    commands = result.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Fetch and append live current conditions")
    fetch.add_argument("--track", action="append", choices=sorted(TRACKS), default=[])
    fetch.add_argument("--city", action="append", default=[], help="First city match; add country to disambiguate")
    fetch.add_argument("--coordinates", nargs=3, action="append", metavar=("NAME", "LAT", "LON"), default=[])
    fetch.add_argument("--provider", choices=["open-meteo", "openweather", "both"], default="open-meteo")
    history = commands.add_parser("history", help="Stored data; makes no weather requests")
    history.add_argument("--location")
    commands.add_parser("analytics", help="Trends, cross-location ranking and derived metrics")
    export = commands.add_parser("export", help="Export actual SQLite rows as CSV")
    export.add_argument("destination")
    commands.add_parser("tracks", help="List built-in circuit centres")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    if args.command == "tracks":
        for slug, location in TRACKS.items():
            print(f"{slug}: {location}")
        return 0
    try:
        settings = load_config(args.env)
        store = SnapshotStore(args.database or settings["database"])
        if args.command == "fetch":
            locations = [TRACKS[name] for name in args.track]
            input_errors = []
            geocoder = GeocodingClient()
            for city in args.city:
                try:
                    locations.append(geocoder.search(city)[0])
                except WeatherError as error:
                    input_errors.append({"location": city, "error": str(error)})
            for name, lat, lon in args.coordinates:
                try:
                    locations.append(Location(name, lat, lon))
                except WeatherError as error:
                    input_errors.append({"location": name, "error": str(error)})
            if not locations and not input_errors:
                locations = [TRACKS["portimao"]]
            clients = []
            if args.provider in ("open-meteo", "both"):
                clients.append(OpenMeteoClient())
            if args.provider in ("openweather", "both"):
                clients.append(OpenWeatherClient(settings["openweather_api_key"]))
            snapshots, failures = fetch_many(clients, locations, store)
            print(json.dumps({"snapshots": [s.to_record() for s in snapshots], "failures": input_errors + failures}, indent=2))
            return 0 if snapshots else 1
        if args.command == "history":
            print(json.dumps(store.history(location=args.location), indent=2))
        elif args.command == "analytics":
            rows = store.history()
            print(json.dumps({"temperature_trends": temperature_trends(rows), "cross_location": latest_comparison(rows),
                              "derived_metrics": derived_metrics(rows)}, indent=2))
        elif args.command == "export":
            count = store.export_csv(args.destination)
            print(f"Exported {count} real stored snapshots to {args.destination}.")
        return 0
    except (WeatherError, RuntimeError, OSError) as error:
        # API errors use controlled messages; never print urllib request objects.
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
