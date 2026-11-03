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

- Decided for the MVP: no race calendar and no track outlines.
- Decided for the MVP: fans first.

The rest of this README describes the app as it is now.

## What it does

**Sidebar:** the 18 circuits from `data/circuits.csv`, one card each with local time, temperature, conditions and wind. Tap a card to open the circuit. On a phone the sidebar starts closed and a circuit picker appears at the top of the page.

**Today:**
- A header with the circuit, its country and length, local time, temperature, conditions, high and low, feels like, wind with gusts, humidity, and the chance of rain in the next 3 hours.
- The next 5 days: temperature and cloud cover in one chart.
- Two maps side by side, stacked on a phone: rain radar from RainViewer, with the radar image's time, and wind arrows from a 3 by 3 grid of points around the circuit, coloured by speed in km/h.
- Rain and snow per 3-hour forecast window in mm, with the chance of rain, one sentence on when rain is likely, and the forecast's fetch time.

**History**, from our own collected readings for the selected circuit, every 30 minutes since 29 October 2026:
- Temperature by the hour, with each full day's high and low.
- Hours with rain on each day, beside the hours with data.
- Wind and gusts by the hour.

Each section starts with one finding computed from the data. Hours with no reading stay blank, so the collector's gap on 2 and 3 November shows as a gap. History works without an API key.

Each current-weather fetch for a circuit is added to `data/weather_log.csv` with a UTC timestamp. Readings are cached for 10 minutes, so ordinary page reruns do not add duplicate rows. Forecasts and the wind grid points are not logged.

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

Without a key, the app still opens: Today shows a setup message and History works on the collected data.

## Run the app

```bash
uv run streamlit run app.py
```

## Run the tests

```bash
uv run pytest
```

The tests use small hand-made cases with known answers, plus checks on the committed circuit list and history. They need no key and make no API calls.

## How the API key stays private

The key is only used on the server. The browser receives the radar as one finished image, stitched on the server with Pillow, and the wind as plain numbers for the arrows. RainViewer needs no key. The map background comes from CARTO's free basemap, which needs no token.

## The hardest parts to explain

For the team's walkthrough. Start with these, because they are the least obvious code in the project.

- **Map tiles (`src/weather_app/maps.py`):** a web map is a grid of square images. `lat_lon_to_tile` turns a place into a tile number, `tile_grid` picks the tiles around it, and `stitch_tiles` joins them into one picture.
- **Wind arrows (`wind_grid_points` and `wind_arrow` in `maps.py`):** OpenWeatherMap's wind map shows speed only, so the app asks for current weather at 9 points around the circuit. Wind direction says where the wind comes from, so each arrow is drawn the opposite way, as a short line plus two head lines. A degree of longitude shrinks towards the poles, so longitude distances are divided by `cos(latitude)`.
- **3-hour windows (`src/weather_app/forecast.py`):** OpenWeatherMap gives each forecast step's rain as the amount in the 3 hours before its time, so each step is drawn as the window that ends at that time. `rain_timing` walks through the windows to find the first run with a chance of rain of at least 50 %.
- **Gaps in history (`hourly` in `src/weather_app/history.py`):** `resample("h").mean()` makes one row for every hour, and an hour without readings gets no value. Plotly stops a line at a missing value, so a gap stays a gap. Times are converted with each circuit's time zone name, so summer time is handled.
- **Logging inside the cache (`fetch_and_log_current` in `src/weather_app/fetching.py`):** Streamlit reruns the whole script on every click. The log is written inside the function decorated with `@st.cache_data`, so a rerun reuses the saved answer and adds no duplicate row.
- **Tappable cards (`src/weather_app/style.py`, `show_sidebar` in `src/weather_app/views.py`):** a Streamlit button cannot contain a designed card. So each card is plain HTML, and an invisible real button is stretched over it with CSS.

## Project structure

- `app.py`: the entry point.
- `src/weather_app/client.py`: `APIClient` (generic GET, with or without a key), `WeatherClient` (OpenWeatherMap) and `RainViewerClient` (radar).
- `src/weather_app/models.py`: `WeatherReading`.
- `src/weather_app/storage.py`: the circuit list, the collected history and the app's own log.
- `src/weather_app/forecast.py`: forecast windows and the rain-timing sentence.
- `src/weather_app/history.py`: the collected history, its gaps and its findings.
- `src/weather_app/maps.py`: tile maths, the radar image, wind arrows and the two Plotly maps.
- `src/weather_app/fetching.py`: cached API calls.
- `src/weather_app/display.py`: small helpers for local time, wind direction and backgrounds.
- `src/weather_app/views.py`, `cards.py`, `style.py`: the UI.
- `data/circuits.csv`: the circuits. `straight_heading_deg` is blank for now and not used.
- `data/current_weather.csv`: a snapshot of the collected history, taken 3 November 2026.
- `data/weather_log.csv`: the app's own fetches.
- `tests/`: the tests.
- `PROMPTS.md`: the AI collaboration log.
- `assignment/BRIEF.md`, `summary.md` and `starter_template/`: the original assignment material.

## Data sources and credits

- Weather and forecasts: [OpenWeatherMap](https://openweathermap.org).
- Rain radar: [RainViewer](https://www.rainviewer.com/), whose API is for personal and educational use.
- Basemap: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors © [CARTO](https://carto.com/attributions).

## Team

Add group members and their actual contributions as work progresses.
