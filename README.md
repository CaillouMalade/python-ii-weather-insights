# Racetrack Weather

Python II group assignment: a small object-oriented weather app for 18 European racetracks, built on OpenWeatherMap and Streamlit. It grew out of a general weather app, kept on the `weather-legacy` branch.

## What it does

Pick circuits in the sidebar from the fixed list in `data/circuits.csv`, or type a town near another track to add it. The app checks the text and looks the town up with OpenWeatherMap's geocoding.

- **Live conditions:** current weather at the chosen circuits, ranked warmest first, with the warmest and coldest highlighted, a bar chart of temperatures (°C) and a table with feels-like, humidity, wind (km/h) and conditions. A circuit that fails to load is skipped with a warning, and the rest still show.
- **Analytics,** computed only from collected data:
  - **Trend over time:** one circuit's temperature and feels-like (°C).
  - **Compare circuits:** each circuit's average, lowest and highest temperature, warmest first.
  - **Derived metrics:** the average daily range (highest minus lowest reading in a day) and the feels-like gap (feels-like minus real temperature).

The collected data has two sources, read together:

- `data/current_weather.csv`: the collector's readings for all 18 circuits, every 30 minutes since 29 October 2026. The collector lives on the `data-collection` branch.
- `data/weather_log.csv`: every successful fetch the app itself makes, with a UTC timestamp. Readings are cached for 10 minutes, so clicking around does not add duplicate rows.

## Setup from a clean clone

Requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/CaillouMalade/python-ii-weather-insights.git
cd python-ii-weather-insights
uv sync
cp variables.env.example variables.env        # Windows PowerShell: Copy-Item variables.env.example variables.env
```

Put your own OpenWeatherMap key in `variables.env`. Git ignores this file. Without a key the app still opens: Live conditions shows a setup message, and Analytics works on the committed data.

## Run the app

```bash
uv run streamlit run app.py
```

## Run the tests

```bash
uv run pytest
```

The tests need no key and make no API calls.

## How the code is organised

- `app.py`: the Streamlit page with its two tabs.
- `src/weather_app/client.py`: `APIClient`, a generic JSON client (sends the request, checks the status code, raises a clear `ValueError`), and `WeatherClient(APIClient)`, which knows OpenWeatherMap's endpoints and fields. The key is stored as `__api_key`, and helpers such as `_get` are protected.
- `src/weather_app/models.py`: `WeatherReading`, with the properties `wind_kmh` and `feels_like_gap`, plus `__repr__`, `__str__` and `__lt__` (so `sorted()` ranks readings by temperature).
- `src/weather_app/fetching.py`: cached fetch-and-log, and the loop that skips a failing city.
- `src/weather_app/storage.py`: the circuit list, the collector's history and the app's CSV log.
- `src/weather_app/analytics.py`: the pandas analyses.
- `src/weather_app/config.py`: loads the key from `variables.env` with `python-dotenv`.
- `tests/`: the tests.
- `PROMPTS.md`: the AI collaboration log.
- `assignment/BRIEF.md` and `summary.md`: the assignment material.
- `ROADMAP.md`: what is left, the build order and who owns which module.

Branches: `main` is the submitted app, `dev` is where we work, `data-collection` holds the collector, and `weather-legacy` is the general weather app this started from.

## Errors the app explains

| What goes wrong | Message |
|---|---|
| Empty or letter-free city name | "Please enter a city name." / "... contains no letters." (no API call is made) |
| Unknown city | "City 'X' was not found. Check the spelling." |
| Invalid key | "Invalid or inactive API key. Check the key in variables.env." |
| No connection or timeout | "Could not connect ..." / "... took too long to respond." |
| Other server error | "The weather service returned status N." |

## Data sources

Weather and geocoding: [OpenWeatherMap](https://openweathermap.org).

## Team

Add group members and their actual contributions as work progresses.
