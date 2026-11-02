# Weather Insights

Python II group assignment: an object-oriented weather app built on OpenWeatherMap and Streamlit, made to look and behave like a phone or laptop weather app. This is v0.1, a general weather app.

## What it does

**Sidebar:** search about 5,000 cities in a dropdown (no exact spelling needed) and tap a saved city to open it. Each card shows local time, temperature, conditions and high/low, and ✕ removes a city. Saved cities survive a refresh. On a phone the sidebar starts closed and a city picker appears at the top of the page.

**Weather tab:**
- Overview of the city, with a background that follows the conditions and the time of day.
- Conditions for the next 24 hours in 3-hour steps, switchable between temperature, precipitation and wind, with sunrise and sunset where they fall. The free API has no hourly forecast.
- Forecast for up to 5 days, with lows and highs computed from the 3-hour steps.
- Tiles for air quality, wind, UV (hidden if that legacy endpoint fails), sunrise and sunset, feels like, humidity, visibility and pressure.
- A weather map with five layers: precipitation, temperature, wind, clouds and pressure.

**Analytics tab:**
- **Your history:** temperature and feels-like from your own log, daily low/high/range, and feels-like minus actual temperature. This works without an API key.
- **Next 5 days:** temperature, dew point, precipitation, wind, pressure tendency, and a comfort score with the best and worst daytime windows.
- **Air quality:** up to 90 days compared with the WHO 2021 guidelines, the share of days per AQI band, a day-and-hour pattern, and the outlook.
- **Compare cities:** your saved cities ranked and side by side, with heatmaps.

Each successful current-weather fetch is added to `data/weather_log.csv` with a UTC timestamp. Readings are cached for 10 minutes, so ordinary page reruns do not add duplicate rows. Forecasts are not logged.

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

Then put your own OpenWeatherMap key in `variables.env`. Git ignores this file; never commit or display a real key. A free-tier key is enough.

Without a key, the app still opens. The Weather tab shows a setup message, and the analyses built on the log still work.

A fresh clone starts with Madrid, Tokyo and New York City. Your own list is saved in `data/saved_cities.csv`, which Git ignores.

## Run the app

```bash
uv run streamlit run app.py
```

## Run the tests

```bash
uv run pytest
```

The tests use small hand-made cases with known answers. They need no key and make no API calls.

## How the API key stays private

The key is only used on the server. Weather map tile URLs need the key, so the server downloads the tiles, joins them into one image with Pillow, and sends the browser only that image. The map background comes from CARTO's free basemap, which needs no token.

## Project structure

- `app.py`: the entry point.
- `src/weather_app/client.py`: `APIClient` (generic GET) and `WeatherClient` (OpenWeatherMap).
- `src/weather_app/models.py`: `WeatherReading`.
- `src/weather_app/storage.py`: the CSV log, the city list and the saved cities.
- `src/weather_app/analytics.py`: pandas analyses, each taking and returning a DataFrame.
- `src/weather_app/maps.py`: tile maths, stitching and the Plotly map.
- `src/weather_app/fetching.py`: cached API calls.
- `src/weather_app/display.py`: small helpers for local time, compass and backgrounds.
- `src/weather_app/sidebar.py`, `views_weather.py`, `views_analytics.py`, `cards.py`, `style.py`: the UI.
- `scripts/build_cities_csv.py`: rebuilds `data/cities.csv`. Not needed to run the app.
- `tests/`: the tests.
- `PROMPTS.md`: the AI collaboration log.
- `assignment/BRIEF.md`, `summary.md` and `starter_template/`: the original assignment material.

## Data sources and credits

- Weather, air quality and map layers: [OpenWeatherMap](https://openweathermap.org). Air quality is modelled data, not readings from local stations.
- City list: `data/cities.csv` is derived from [GeoNames](https://www.geonames.org) (`cities15000`, `admin1CodesASCII`, `countryInfo`), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). We kept the roughly 5,000 largest cities and added our own label columns.
- Basemap: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors © [CARTO](https://carto.com/attributions).
- Air quality guideline values: WHO global air quality guidelines, 2021.

## Team

Add group members and their actual contributions as work progresses.
