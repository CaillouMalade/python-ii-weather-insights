# Weather Insights

Python II group assignment: a small object-oriented weather app built on OpenWeatherMap and Streamlit.

## What it does

Pick cities in the sidebar from a fixed list of 12 (`data/cities.csv`), or type another city to add it. The app checks the text and looks the city up with OpenWeatherMap's geocoding.

- **Live conditions:** the chosen cities' current weather, ranked warmest first, with the warmest and coldest highlighted, a bar chart of temperatures (°C) and a table with feels-like, humidity, wind (km/h) and conditions. A city that fails to load is skipped with a warning, and the rest still show.
- **Analytics,** computed only from our own log:
  - **Trend over time:** one city's logged temperature and feels-like (°C).
  - **Compare cities:** each city's average, lowest and highest logged temperature, warmest first.
  - **Derived metrics:** the daily range (highest minus lowest reading in a day) and the feels-like gap (feels-like minus real temperature).

Every successful fetch is appended to `data/weather_log.csv` with a UTC timestamp. Readings are cached for 10 minutes, so clicking around does not add duplicate rows.

## Setup from a clean clone

Requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/CaillouMalade/python-ii-weather-insights.git
cd python-ii-weather-insights
uv sync
cp variables.env.example variables.env        # Windows PowerShell: Copy-Item variables.env.example variables.env
```

Put your own OpenWeatherMap key in `variables.env`. Git ignores this file. Without a key the app still opens: Live conditions shows a setup message, and Analytics works on the committed log.

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
- `src/weather_app/storage.py`: the city list and the CSV log.
- `src/weather_app/analytics.py`: the pandas analyses.
- `src/weather_app/config.py`: loads the key from `variables.env` with `python-dotenv`.
- `tests/`: the tests.
- `PROMPTS.md`: the AI collaboration log.
- `assignment/BRIEF.md` and `summary.md`: the assignment material.
- `ROADMAP.md`: what is left, the build order and who owns which module.

Earlier, larger versions are kept on the branches `archive/city-app` and `archive/racetrack-poc`.

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
