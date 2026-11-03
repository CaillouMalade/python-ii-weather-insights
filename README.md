# Weather Insights

Python II group assignment: an object-oriented weather app built on OpenWeatherMap and Streamlit.

## Racetrack MVP (branch `racetrack-mvp`, in progress)

This branch turns the v0.1 general weather app into a racetrack weather monitor. It is deliberately an **MVP**: a small, clean and working app with one weather provider, not a feature-complete product. Features are added only once the existing ones work well.

### Why

Anyone heading to a circuit, whether driving, working in a team or watching, asks the same questions: is it going to rain during my session, when, how hard, and what is the wind doing? General weather apps answer for the nearest town and in broad terms. They don't show the circuit itself, and they mix today's conditions with everything else.

### The problem it solves

One page per circuit that answers "what is happening at this track today and in the next hours", using real data and being honest about what that data can and can't tell you. Our own collected history of every circuit then shows how each track's weather really behaves over time.

### What the MVP will include

- **Circuits from a CSV**, like the city list: the 18 circuits we already collect, easy to extend.
- **A main page about today** at the selected circuit:
  - a full-width pane with the temperature trend and cloud cover;
  - two maps side by side: rain (radar) and wind with its direction;
  - a precipitation histogram, as fine-grained as the data allows.
- **Rain timing:** the radar for the next hour or so, then rain risk per forecast window.
- **Analytics built on our collected history**, the readings gathered every 30 minutes for each circuit since 29 October 2026.
- **One provider, OpenWeatherMap**, done well.

### Deliberately left out

- Circuit comparison.
- Track temperature, grip, and slick/wet tyre calls: they can't be estimated honestly from forecast data.
- Several providers and a settings pane to choose them: planned for a later version.

### Known data limits

- Our free OpenWeatherMap key only gives forecasts in 3-hour steps, so exact rain timing is limited to the radar's short range. OpenWeatherMap's free student plan lists an hourly 4-day forecast, so applying for it would give hourly steps.
- Wind direction comes from forecast points, not from the wind map, which only shows speed. The app fetches a small grid of points around the circuit for the arrows.
- One weather point can't capture rain on only part of a very large circuit, such as Spa, the Nordschleife or Le Mans.

### Still to decide

- Whether the app knows real race weekend dates.
- Whether track outlines are drawn on the map (easy for the 9 F1 circuits only).
- The main audience: fans, teams, or both.

The rest of this README describes v0.1, the general weather app this branch builds on.

## What it does

**Sidebar:** search about 5,000 cities in a dropdown, largest first, and tap a saved city to open it. The list holds the largest cities plus national capitals. A city that is not listed can be typed under "Not listed?" just below it, which checks the text and looks the city up with OpenWeatherMap's geocoding. Each card shows local time, temperature, conditions, high and low, and ✕ removes a city. Saved cities survive a refresh. On a phone the sidebar starts closed and a city picker appears at the top of the page.

**Weather tab**, in one consistent grid, which adapts to the width available:
- A header with the city, local time, temperature, conditions, high and low, plus feels like, wind, humidity and chance of rain.
- Next hours, switchable between temperature, precipitation and wind.
- A 5-day forecast beside a weather map. The map opens on real rain radar and also offers temperature, wind, clouds and pressure, each with a colour scale.
- Same-size detail tiles: air quality, UV index today, sunrise, sunset, dew point, visibility, pressure and cloud cover.

**Analytics tab**, written to be read without knowing weather terms. Four short answers sit at the top: best time outside, next rain, windiest moment and air quality. All times are local to the city. Below them:
- **Plan the week:** one headline, a temperature-and-rain chart, and a card per day with a one-sentence summary and morning, afternoon and evening rated in words with a reason.
- **Air:** how the air usually is, the share of days in each band, each pollutant in plain words against its health guideline, the best and worst time of day, and the coming days.
- **Compare:** the warmest, driest, calmest and cleanest of your saved cities, and a sortable table.
- **History:** your own logged data: how much there is, a trend chart once a city has 3 readings over at least an hour, and, from 3 days of data, how much the temperature moves within a day. This is the only section that works without an API key.

Each successful current-weather fetch is added to `data/weather_log.csv` with a UTC timestamp. Readings are cached for 10 minutes, so ordinary page reruns do not add duplicate rows. Forecasts are not logged.

## Setup from a clean clone

Requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/CaillouMalade/python-ii-weather-insights.git
cd python-ii-weather-insights
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

## The hardest parts to explain

For the team's walkthrough. Start with these, because they are the least obvious code in the project.

- **Map tiles (`src/weather_app/maps.py`):** a web map is a grid of square images. `lat_lon_to_tile` turns a place into a tile number, `tile_grid` picks the tiles around it, and `stitch_tiles` joins them into one picture. The server does this because OpenWeatherMap's tile URLs contain the key, so the browser only ever gets the finished image.
- **Logging inside the cache (`fetch_and_log_current` in `src/weather_app/fetching.py`):** Streamlit reruns the whole script on every click. The log is written inside the function decorated with `@st.cache_data`, so a rerun reuses the saved answer and adds no duplicate row. A new row appears only when the 10-minute cache runs out.
- **Tab callbacks (`app.py`, `src/weather_app/views_analytics.py`, `src/weather_app/sidebar.py`):** `st.tabs(..., on_change="rerun")` makes the script rerun when a tab changes, and `.open` says which tab is showing, so hidden tabs make no API calls. Callbacks such as `on_click=select_city` run before the script reruns, which is why they can safely change `st.session_state`.
- **Ozone rolling mean (`daily_guideline_levels` in `src/weather_app/analytics.py`):** the WHO's ozone guideline is an 8-hour level and the others are daily. So ozone uses each day's highest 8-hour rolling mean, while the others use the daily mean.
- **Tappable cards (`src/weather_app/style.py`, `show_sidebar` in `src/weather_app/sidebar.py`):** a Streamlit button cannot contain a designed card. So each card is plain HTML, and an invisible real button is stretched over it with CSS. The ✕ sits above that button so it can still be pressed.

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
