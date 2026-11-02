# Weather Insights

Python II group assignment: an object-oriented weather app built on OpenWeatherMap and Streamlit. This is v0.1, a general weather app.

## What it does

**Sidebar:** search about 5,000 cities in a dropdown (no exact spelling needed) and tap a saved city to open it. Each card shows local time, temperature, conditions, high and low, and ✕ removes a city. Saved cities survive a refresh. On a phone the sidebar starts closed and a city picker appears at the top of the page.

**Weather tab**, in one consistent grid, which adapts to the width available:
- A header with the city, local time, temperature, conditions, high and low, plus feels like, wind, humidity and chance of rain.
- Next hours, switchable between temperature, precipitation and wind.
- A 5-day forecast beside a weather map with five layers (stacked on a phone).
- Same-size detail tiles: air quality, UV index today, sunrise, sunset, dew point, visibility, pressure and cloud cover.

**Analytics tab:** four short answers for the selected city (best time outside, next rain, windiest moment, air quality), then four sections. Each section leads with a finding computed from the data, and all times are local to the city.
- **Plan the week:** a day-by-time heatmap of comfort, temperature, chance of rain or wind, and the three best windows to be outside, with reasons.
- **Air:** 90 days of daily AQI as a calendar, the hour-of-day pattern of a chosen pollutant, a comparison with the WHO 2021 guidelines, and the outlook.
- **Compare:** your saved cities ranked and day by day on temperature, rain, wind or air quality.
- **History:** your own logged data: how much there is for each city, a trend chart, and a daily range table. This is the only section that works without an API key.

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

The key is only used on the server. Weather map tile URLs need the key, so the server downloads the tiles, joins them into one image with Pillow, and sends the browser only that image. The map background comes from CARTO's free basemap, which needs no token.

## Project structure

- `app.py`: the entry point.
- `src/weather_app/client.py`: `APIClient` (generic GET) and `WeatherClient` (OpenWeatherMap).
- `src/weather_app/models.py`: `WeatherReading`.
- `src/weather_app/storage.py`: the CSV log, the city list and the saved cities.
- `src/weather_app/analytics.py`: pandas analyses, each taking and returning a DataFrame.
- `src/weather_app/findings.py`: the plain-language sentences on the Analytics tab.
- `src/weather_app/maps.py`: tile maths, stitching and the Plotly map.
- `src/weather_app/fetching.py`: cached API calls.
- `src/weather_app/display.py`: small helpers for local time, wind direction and backgrounds.
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
