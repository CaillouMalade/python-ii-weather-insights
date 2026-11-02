# Weather Insights

Python II group assignment: an object-oriented weather app built on OpenWeatherMap and Streamlit. This is v0.1, a general weather app.

## What it does

- **Sidebar:** add cities by name, select one, remove one, and switch between the two views. At start-up, the city list is filled from the locations already in the log.
- **Live Conditions:** a weather card for the selected city (temperature, conditions, feels-like, humidity, wind), a chart of the forecast temperature, and a comparison of all your cities, warmest first. If one city fails, you get a warning and the others still load.
- **Analytics:** three analyses that read only the saved log and make no API calls:
  1. Temperature trend for the selected city.
  2. All cities ranked by latest temperature.
  3. Feels-like minus actual temperature, per city, over time. This is a metric the API does not return.

Each successful current-weather fetch is added to `data/weather_log.csv` with a UTC timestamp. Readings are cached for 10 minutes, so ordinary page reruns do not add duplicate rows. The file is created on the first live fetch. Forecasts are not logged.

Removing a city lasts until you refresh the page: its history stays in the log, and the list is rebuilt from the log.

## Setup from a clean clone

Requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repository-url>
cd <repository-folder>
uv sync
```

Copy the example settings file. On Windows PowerShell:

```powershell
Copy-Item variables.env.example variables.env
```

On macOS/Linux:

```bash
cp variables.env.example variables.env
```

Then put your own OpenWeatherMap key in `variables.env`. Git ignores this file; never commit or display a real key.

Without a key, the app still opens. Live Conditions shows a setup message, and Analytics works on any existing log data.

## Run the app

```bash
uv run streamlit run app.py
```

## Run the tests

```bash
uv run pytest
```

The tests use small hand-made cases with known answers for the analytics, the reading class and input validation. They need no key and make no API calls.

## Project structure

- `app.py`: the Streamlit UI.
- `src/weather_app/client.py`: `APIClient` (generic JSON GET) and `WeatherClient` (OpenWeatherMap).
- `src/weather_app/models.py`: `WeatherReading`.
- `src/weather_app/storage.py`: appends to and loads the CSV log.
- `src/weather_app/analytics.py`: the pandas analyses.
- `src/weather_app/config.py`: reads the API key.
- `tests/`: the tests.
- `PROMPTS.md`: the AI collaboration log.
- `assignment/BRIEF.md`, `summary.md` and `starter_template/`: the original assignment material.

## Team

Add group members and their actual contributions as work progresses.
