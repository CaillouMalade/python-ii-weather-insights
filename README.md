# Weather Insights

Python II group assignment: an object-oriented weather app built on OpenWeatherMap and Streamlit. This is v0.1, a general weather app.

## What it does

**Sidebar:** search about 5,000 cities in a dropdown, largest first, and tap a saved city to open it. The list holds the largest cities plus national capitals. Each card shows local time, temperature, conditions, high and low, and ✕ removes a city. Saved cities survive a refresh. On a phone the sidebar starts closed and a city picker appears at the top of the page.

**Weather tab**, in one consistent grid, which adapts to the width available:
- A header with the city, local time, temperature, conditions, high and low, plus feels like, wind, humidity and chance of rain.
- Next hours, switchable between temperature, precipitation and wind.
- A 5-day forecast beside a weather map. The map opens on real rain radar and also offers temperature, wind, clouds and pressure, each with a colour scale.
- Same-size detail tiles: air quality, UV index today, sunrise, sunset, dew point, visibility, pressure and cloud cover.

**Analytics tab**, written to be read without knowing weather terms. Four short answers sit at the top: best time outside, next rain, windiest moment and air quality. All times are local to the city. Below them:
- **Plan the week:** one headline, a temperature-and-rain chart, and a card per day with a one-sentence summary and morning, afternoon and evening rated in words with a reason.
- **Air:** how the air usually is, the share of days in each band, each pollutant in plain words against its health guideline, the best and worst time of day, and the coming days.
- **Compare:** the warmest, driest, calmest and cleanest of your saved cities, and a sortable table.
- **History:** your own logged data: how much there is, a trend chart once a city has 3 readings over at least an hour, and how much the temperature moves within a day. This is the only section that works without an API key.

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

Without a key, the app still opens. The Weather tab and the first three Analytics sections show a setup message, and History works on the existing log.

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

The key is only used on the server. Weather map tile URLs need the key, so the server downloads the tiles, joins them into one image with Pillow, and sends the browser only that image. Radar comes from RainViewer and needs no key; it is fetched the same way. The map background comes from CARTO's free basemap, which needs no token.

## Project structure

- `app.py`: the entry point.
- `src/weather_app/client.py`: `APIClient` (generic GET, with or without a key), `WeatherClient` (OpenWeatherMap) and `RainViewerClient` (radar).
- `src/weather_app/models.py`: `WeatherReading`.
- `src/weather_app/storage.py`: the CSV log, the city list and the saved cities.
- `src/weather_app/analytics.py`: pandas analyses, each taking and returning a DataFrame.
- `src/weather_app/findings.py`: the plain-language ratings and sentences on the Analytics tab.
- `src/weather_app/maps.py`: tile maths, stitching and the Plotly map.
- `src/weather_app/fetching.py`: cached API calls.
- `src/weather_app/display.py`: small helpers for local time, wind direction and backgrounds.
- `src/weather_app/sidebar.py`, `views_weather.py`, `views_analytics.py`, `cards.py`, `style.py`: the UI.
- `scripts/build_cities_csv.py`: rebuilds `data/cities.csv`. Not needed to run the app.
- `tests/`: the tests.
- `PROMPTS.md`: the AI collaboration log.
- `assignment/BRIEF.md`, `summary.md` and `starter_template/`: the original assignment material.

## Data sources and credits

- Weather, air quality and the temperature, wind, clouds and pressure map layers: [OpenWeatherMap](https://openweathermap.org). Air quality is modelled data, not readings from local stations.
- Rain radar: [RainViewer](https://www.rainviewer.com/), whose API is for personal and educational use.
- City list: `data/cities.csv` is derived from [GeoNames](https://www.geonames.org) (`cities15000`, `admin1CodesASCII`, `countryInfo`), licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). We kept the 5,000 largest cities plus every national capital in that file, and added our own label columns.
- Basemap: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors © [CARTO](https://carto.com/attributions).
- Air quality guideline values: WHO global air quality guidelines, 2021.

## Team

Add group members and their actual contributions as work progresses.
