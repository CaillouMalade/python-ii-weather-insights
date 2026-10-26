# Pitwall · Python companion

A small, inspectable Python implementation of the Weather Insights assignment, alongside the richer Pitwall web app. It fetches current conditions near selected circuit centres from **Open-Meteo** and optionally **OpenWeather**, logs every successful response in SQLite, and provides a CLI and an optional Streamlit interface.

The two applications have separate data stores. The hosted web app stores forecast snapshots; this Python companion stores current-condition snapshots on the computer running it. A logged forecast is not a measurement.

## Setup from a clean checkout

Requires Python 3.9 or newer. Run these commands from this folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[ui]'
cp variables.env.example variables.env
```

On Windows use `py -m venv .venv` and `.venv\Scripts\activate` in place of the first two commands. For CLI only, install with `python -m pip install -e .` instead.

Open-Meteo works without a key for the documented non-commercial API. To use OpenWeather, obtain your own API key and set `OPENWEATHER_API_KEY` in the ignored `variables.env`. Do not commit it. Environment variables already set in your shell take precedence over the file. No existing key was read, tested or copied during this build.

## Run

```sh
# No-key current snapshot capture; each success is appended to SQLite.
pitwall-weather fetch --track portimao --track nogaro --track spa

# Compare both provider products; an OpenWeather key is required for its rows.
pitwall-weather fetch --provider both --track portimao

# Any place, with validation and isolated failures.
pitwall-weather fetch --city 'Madrid' --coordinates 'Custom circuit' 43.1 1.2

# Inspect / analyze only genuine stored data.
pitwall-weather history
pitwall-weather analytics
pitwall-weather export data/snapshots.csv
pitwall-weather tracks

# Optional course-facing UI with Live conditions, Analytics, Sources & export.
python -m streamlit run streamlit_app.py

# An explicit storage path can be selected before the subcommand.
pitwall-weather --database data/weekend.sqlite3 fetch --track spa
```

City lookup selects its first match in the CLI; use a full place name or explicit coordinates for exact selection. Streamlit lets you select among matches. Neither city geocoding nor a circuit-centre forecast is exact racing-line weather.

## What to inspect

| Module | Purpose |
|---|---|
| `clients.py` | Reusable JSON API base; OpenWeather, Open-Meteo and geocoder subclasses; specific errors and resilient multi-location fetch |
| `models.py` | Validated `Location`, sortable `WeatherSnapshot`, computed dewpoint spread and apparent-temperature delta |
| `storage.py` | Append-only SQLite snapshots, parameterized queries and real CSV export |
| `analytics.py` | Distinct-valid-time trends, latest cross-location comparison and derived metrics |
| `cli.py` | Commands and clear failure output |
| `streamlit_app.py` | Location input, two analytical charts, three views and export |

OpenWeather returns wind in m/s with metric parameters; the client converts it to km/h. Open-Meteo is requested in km/h. Every precipitation total retains its own accumulation interval. A missing precipitation field remains missing, rather than becoming a fabricated dry value. Fetch time and provider-valid time are stored separately in UTC. The estimated dewpoint uses a Magnus approximation from air temperature and relative humidity; it is identified as derived.

Trend calculations keep each provider and coordinate pair separate and require at least two **distinct provider-valid times** for a change. Re-fetching the same valid time adds an audit snapshot, not an additional observation. Cross-location charts use the latest stored samples and display their valid times, so stale samples cannot silently appear simultaneous.

## Real capture included

`data/verified-snapshots.csv` contains the three genuine Open-Meteo current-condition responses captured during this build for Portimão, Nogaro and Spa. Their fetched and valid timestamps are in the file. It is one capture across three locations, **not** a multi-day history or evidence of forecast accuracy. The live SQLite database is ignored; users generate their own by running the app. CSV is committed/exportable evidence without a machine-specific binary database.

## Verification

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

Verified in this build: a clean isolated install, 18 passing unit tests, CLI listing/analytics, all three Streamlit views via Streamlit AppTest, and a real refresh that logged two Open-Meteo locations while isolating two missing-key OpenWeather failures. OpenWeather itself was tested with mocked responses only.

The tests use explicitly mocked provider responses to check error isolation, secret-safe messages, invalid coordinates, missing data, wind conversion, precipitation intervals, SQLite/CSV round-trips and source-separated analytics. Test fixtures are never shown as real weather. See `../docs/ASSIGNMENT_ALIGNMENT.md` for remaining submission responsibilities.

## Source documentation

- [Open-Meteo Forecast API](https://open-meteo.com/en/docs)
- [OpenWeather current weather API](https://openweathermap.org/api/current)

Current model/provider conditions do not establish track-surface temperature, grip or standing water. This companion calculates no tyre recommendation or calibrated wet-track probability.
