# Racetrack Weather

A Streamlit app for race teams that tells you what the weather is going to do at a racetrack over a race weekend, built for our Python II group assignment (brief and rubric in [`assignment/BRIEF.md`](assignment/BRIEF.md)). It takes three forecast providers and combines them into one forecast with a 95% confidence interval, shows the rain radar around the track, and analyses the weather history we logged ourselves on the 16 FIA Grade 1 circuits in EU countries.

## Why this app

When racing on a track, weather plays a massive role, and three factors basically drive everything:

- **Temperature:** it has a big influence on how well we can use the tyres and on overheating, so if the temperature evolves quickly during a session it can completely change our strategy (for instance in qualifying, if we can see it gets colder later, it's in our best interest to wait for maximum performance).
- **Rain:** obviously it matters a massive amount, and having a precise idea of when it's going to rain is extremely important. The main issue we encounter is that the different weather apps on our phones or the radars often give conflicting information, and it's always difficult to compare them and to know which one to trust.
- **Wind:** the cars rely on aerodynamics, so wind in a certain direction in a corner can massively influence the car and even be a cause for errors, hence having an idea of the wind strength and direction is just as important.

Knowing that, the idea is a weather app that aggregates several APIs, so instead of giving one ungrounded likelihood of rain, we give the statistical likelihood of rain and wind with more detail, on top of the wind over the track map and the rain radar. It's an MVP (we will need more granularity later), but that's the main idea.

## What the app does

You pick a track in the sidebar (or add your own), then go through the four pages in the top bar:

1. **Weekend overview:** the weather now at the track (OpenWeatherMap), then the race weekend forecast on two charts, rain and temperature on one and wind on the other, with the 95% confidence interval and the sessions as dashed lines. Below that, the circuit seen from above next to the rain radar of the last 2 hours around it (on the final app both would be on the same map, but the free radar stops before you can see the track).
2. **Session dashboard:** one session at a time (FP1, FP2, FP3, Qualifying, Race) with previous/next buttons, so temperature, chance of rain, wind strength and direction for that session's 3-hour window, combined and then provider by provider.
3. **History:** what the weather actually did at the selected track over the days we logged it, so daily rain, lowest and highest temperature, and the daily temperature swing (highest − lowest), which the API doesn't give directly and tells you how much a track's conditions move within a day.
4. **Track comparison:** 2 to 4 tracks over the same logged period, ranked from wettest to driest, with temperature, rain and temperature swing side by side.

**Adding a track:** you type a name, a latitude and a longitude. The input is checked first (empty or already used name, latitude outside −90 to 90, longitude outside −180 to 180), and the track is only saved if it's within 3 km of an FIA Grade 1 circuit, otherwise the app says "No racetrack found at these coordinates".

**When something fails** (bad input, bad or missing key, unknown location, timeout, no connection, server error, unreadable answer) you get a clear message, not a crash. And if one provider fails it's skipped with a warning, the others still load.

**Session times** are the same for every track for now, in UTC over the next 3 days starting tomorrow: FP1 and FP3 at 08:00, FP2 and Qualifying at 14:00, Race at 13:00. Changing them per track comes later.

## Setup

You need Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/CaillouMalade/python-ii-weather-insights.git
cd python-ii-weather-insights
uv sync
cp variables.env.example variables.env        # Windows PowerShell: Copy-Item variables.env.example variables.env
```

Then open `variables.env` and replace `your_key_here` with your own [OpenWeatherMap API key](https://home.openweathermap.org/api_keys) (the free plan is enough). Git ignores this file so the key never ends up in the repo. The app also runs without a key, Open-Meteo, MET Norway, the radar, History and Track comparison all work, only the "Weather now" panel needs it and tells you how to add one.

## Run

```bash
uv run streamlit run app.py     # opens the app at http://localhost:8501
uv run pytest                   # runs the tests (no key and no API calls needed)
```

## Data

Everything in `data/` is real data we fetched, nothing invented:

- `grade1_tracks.csv`: the 16 FIA Grade 1 circuits in EU countries (`id, name, country, latitude, longitude`), so the track list.
- `current_weather.csv`: our weather history, the current weather at each track every 30 minutes, logged by our collector from 29 Oct to 13 Nov 2026 (about 11,600 readings). History and Track comparison run on it. The collector stopped right after we switched to the 16-track list, so the 6 tracks added last (Red Bull Ring, Hockenheim, Hungaroring, Mugello, Zandvoort, Valencia) only have one reading and the app says there isn't enough history for them yet.
- `weather_log.csv`: every current-weather fetch the app makes, appended with a UTC timestamp.
- `forecasts.csv`: every forecast the app fetches, one row per provider and 3-hour window, with the fetch time in UTC.
- `my_tracks.csv`: the tracks users add (created with the first accepted one).

Why three weather files and not one: `forecasts.csv` holds predictions, the other two hold the weather observed at a given moment, so they don't mix. And `current_weather.csv` comes from our collector, which was built before the app with a richer format (track id, rain, pressure, gusts…), while the app logs a smaller `WeatherReading` without the track id or the rain, so its rows can't feed the history pages and stay in their own log.

Units are °C, wind stored in m/s and shown in km/h, rain in mm, and wind direction in the degrees it comes from (shown as N, NE, E…).

Sources: [OpenWeatherMap](https://openweathermap.org) (key needed), [Open-Meteo](https://open-meteo.com) and [MET Norway](https://api.met.no) (both free, no key) for the weather, [RainViewer](https://www.rainviewer.com) for the radar and Esri World Imagery for the satellite view.

## How the forecasts are combined

Every provider's forecast is cut into the same 3-hour windows in UTC (00:00, 03:00 … 21:00) up to 5 days ahead. For each window we take the mean of the providers and a 95% confidence interval, mean ± t × standard deviation / √n, with Student's t for the number of providers that answered (no interval with only one). Wind direction is never averaged (350° and 10° would give 180°, so the opposite), instead each provider votes for one of 8 compass sectors, e.g. "3 of 3 providers agree: SW". MET Norway only forecasts about 2.5 days ahead hour by hour, so after that the windows combine two providers and the interval gets a lot wider, which is expected with n = 2.

## Project structure

```
app.py                       the Streamlit pages only (sidebar and the four pages)
assets/                      the logo (light and dark mode)
src/weather_app/
    client.py                APIClient (generic JSON GET, status checks, one message per failure) and WeatherClient (OpenWeatherMap)
    providers.py             OpenMeteoClient, MetNorwayClient, RainViewerClient, all subclasses of APIClient
    windows.py               the 3-hour window helpers every provider uses
    models.py                WeatherReading and ForecastPoint
    fetching.py              fetches every provider, skips the ones that fail, logs to CSV
    forecast_stats.py        combines the providers: mean, 95% interval, rain count
    dashboard.py             session helpers: wind direction votes, per-provider table
    sessions.py              the race weekend's session times
    tracks.py                checks for a new track (input, haversine distance)
    analytics.py             History and Track comparison (TrackSummary, ranked with sorted())
    storage.py               every read and write in data/
    config.py                reads OPENWEATHER_API_KEY from variables.env
tests/                       pytest tests on fake responses and saved samples
```

On the OOP side, `APIClient` holds what any JSON API needs (the request with a timeout, the status-code checks, one clear error per failure) and the four providers inherit from it, each only adding its own URL and fields. The API key is `__private` inside `APIClient` and the helpers subclasses use are `_protected`. `ForecastPoint` and `WeatherReading` have a `wind_kmh` `@property` and `__repr__`/`__str__`, and `TrackSummary` has `__lt__` so `sorted()` can rank tracks by rain.

## For the grader

This section follows the rubric row by row, and for each point it says what we did, why, and where to find it in the code, so you don't have to dig through the repo. All paths are relative to the repo root, and the Python files are in `src/weather_app/` unless said otherwise. To check the whole thing quickly, `uv sync` then `uv run pytest` runs all the tests, and `uv run streamlit run app.py` starts the app (see Setup and Run above).

### OOP design (2 points)

**Inheritance.** We needed four different APIs (OpenWeatherMap, Open-Meteo, MET Norway and RainViewer), and they all need the same basic work: send a GET request with a timeout, check the status code, and turn every kind of failure into a clear message. So that shared part lives once in `APIClient` (`client.py`), and each API is a subclass that only adds its own URL and how to read its answer. `WeatherClient` is in the same file, and `OpenMeteoClient`, `MetNorwayClient` and `RainViewerClient` are in `providers.py`. Adding a fifth provider would mean writing one small subclass, not copying the error handling again.

**Public, protected and private.** The API key is stored as `self.__api_key` in `APIClient`, with two underscores so Python name-mangles it, and no subclass or caller can read or print it by mistake. The request method `_get` has one underscore because it is meant for the subclasses only, not for the app. Attributes like `source`, `headers` and `base_url` stay public because the rest of the app reads them (for example `source` is the provider name shown in the warning when a provider fails).

**Special method.** `TrackSummary` in `analytics.py` defines `__lt__`, which compares two tracks by their total rain. This is what lets `compare_track_history` rank the tracks with a plain `sorted()`, and that ranking sets the order of the cards on the Track comparison page (wettest track on the left). `TrackSummary` also has a `__str__` that writes its one-line summary, and `WeatherReading` and `ForecastPoint` (`models.py`) have a `__repr__` that makes them readable when debugging (plus a `__str__` on `WeatherReading`).

**`@property`.** The APIs give wind speed in m/s, but racing teams think in km/h. So `WeatherReading` and `ForecastPoint` (`models.py`) have a `wind_kmh` property that computes it from the stored value, instead of keeping two numbers that could drift apart. It is what the "Weather now" block displays.

### API integration and robustness (2 points)

**API key.** The OpenWeatherMap key is read from `variables.env` with `python-dotenv` in `config.py`. It is never hardcoded, never printed or shown in the app, and `variables.env` is in `.gitignore` (only `variables.env.example` is committed). On top of this, our error messages are fixed text on purpose: a `requests` error contains the full URL, and that URL contains the key, so showing the raw error could leak it. Without a key the app still runs, and only the "Weather now" block shows a setup message, since the other two providers don't need a key.

**Distinct error handling.** Every failure gets its own message, written for a user and not for a developer. Bad input and impossible coordinates are caught by `validate_location`, and in `APIClient._get` (both in `client.py`) a bad key (401), a location not found (404), coordinates the service refuses (400), too many requests (429), a server problem (5xx), a timeout, no connection, and an answer that can't be read each give a different message. Each case has a test with a fake response in `tests/test_client.py`. For a track a user adds, `tracks.py` also says "No racetrack found at these coordinates" when the point is not near a known circuit.

**Several locations at once.** The app fetches one track at a time, because that's how a team would use it (you look at the circuit you're racing at that weekend), and results are cached for 10 minutes, so fetching every location in one go isn't needed. The rubric's logic is still there, applied across providers instead of across locations. `fetch_all_forecasts` in `fetching.py` asks the three providers in a loop, catches the error of any provider that fails, and keeps going, so the other providers still load and the failed one is named in a warning at the top of the page. A failed call is also not cached, so it is retried on the next refresh.

**Validation before the API call.** Nothing is sent to an API before it is checked. `validate_location` (`client.py`) rejects an empty name or coordinates outside the valid range before any request, and when a user adds a track in the sidebar, `check_new_track` (`tracks.py`) checks the name (not empty, not already used), the latitude (a number between −90 and 90) and the longitude (between −180 and 180) before anything is saved.

### Data and analytics (2 points)

**Logging.** Every successful fetch is appended with a UTC timestamp: the current weather by `append_reading` to `data/weather_log.csv`, and the forecasts by `append_forecasts` to `data/forecasts.csv` (both in `storage.py`). On top of what the app logs itself, the data collector we ran from 29 Oct to 13 Nov is committed in `data/current_weather.csv`, with about 11,600 readings (see Data above), so you can see real accumulated history and not an empty file.

**Three analytical views over two categories.**
- *Trend over time:* the History page shows each track's daily rain and temperature over the logged period, computed by `track_rain_history` in `analytics.py`.
- *Comparison across locations:* the Track comparison page puts 2 to 4 tracks side by side over the same days and ranks them, through `compare_track_history` in `analytics.py`.
- *Derived metrics the API doesn't return:* the daily temperature swing (max minus min, in `track_rain_history`), and the combined forecast in `combine_forecasts` (`forecast_stats.py`), which averages the three providers for each 3-hour window and adds a 95% confidence interval and how many providers predict rain.

**Real data only.** The History and Track comparison pages read `current_weather.csv`, and the forecast pages use the live APIs. The only fake data in the repo is in `tests/` (`fake_forecast.py` and the saved sample answers), and it is used by the tests only, never by the app.

### Streamlit app (2 points)

**Runs, with several views.** `app.py` has four pages: Weekend overview, Session dashboard, History and Track comparison. `app.py` only builds the pages, and the logic lives in the `src/weather_app/` package.

**Interaction.** The user picks a track in the sidebar or adds their own, moves between sessions with previous/next buttons on the Session dashboard, scrolls through the last two hours of rain radar with a time slider, and chooses 2 to 4 tracks to compare.

**Charts.** Every chart has a title and axis labels with units (°C, mm, km/h). The main ones are the 5-day forecast on the Weekend overview (with the confidence interval and the session times marked), the rain and temperature history, and the track comparison.

**Usability.** We tried to make sure a stranger never hits a dead end or a traceback. Wherever there is no data, the app says why and what to do: no API key, a session too far ahead for any forecast, a provider that failed, or a track without enough history.

### Repository and AI collaboration record (1 point)

The code is a `src/` package with a `pyproject.toml` (installed with `uv sync`), this README explains setup and use, and no secret is committed. `PROMPTS.md` explains how we worked with the agents and then has one section per card, with what we asked, what we got, and what we kept, changed or rejected. AI-assisted commits carry a `Co-Authored-By` trailer, which you can check with `git log`.

### Team collaboration (1 point)

Each member owned one or more cards (see the checklist below), built them on their own branch, committed from their own GitHub account, and merged them into `dev` through a pull request, so the commit history and the pull requests show who did what. Before submitting, each of us walks the group through our own card (the Walkthrough step in the checklist), so that everyone can explain any part of the code, including the parts an agent wrote.

## Team and how we worked

Arthur, Minho, Diajeng Widyannisa, Cedric and Emilio. We split the app into cards, each built on its own branch and merged into `dev` through a pull request, then `dev` into `main` at the end. We used AI coding agents (Claude Code, Codex) as collaborators, guided by an `AGENTS.md` written for the assignment rules (in the git history, but no longer in the repo since further development doesn't have to follow them), [`PROMPTS.md`](PROMPTS.md) logs what we asked, what we got and what we kept or changed, and AI-assisted commits carry a `Co-Authored-By` trailer.

- [x] **0. Setup** (Arthur): shared `ForecastPoint` shape, fake forecast in `tests/`, this README.
- [x] **1. Track list** (Arthur): `data/grade1_tracks.csv` holds the 16 FIA Grade 1 circuits in EU countries (one point near the centre of each track).
- [x] **1b. Logo** (Arthur): add the logo picture.
- [x] **Everyone added to the repo and on a card.**
- [x] **2. OpenWeatherMap client and errors** (needs 0, owner: Arthur): the current weather and the 5-day forecast for a track, with the forecast as a list of `ForecastPoint`. A bad input, a bad key, a missing location, a timeout, no connection, a server error and an unreadable answer each give their own message. Done when each failure has a test with a fake response.
- [x] **3. More providers** (needs 0, owner: Arthur): Open-Meteo and MET Norway (both free, no key; MET Norway asks for a User-Agent header naming the app) as subclasses of `APIClient`, each returning `ForecastPoint`s on the same 3-hour UTC windows as OpenWeatherMap: convert units, sum hourly rain over each window, take temperature and wind at the window start. A provider that fails is skipped with its own message. Done when all three return the same windows for one track, with a test per provider on a saved sample answer.
- [x] **4. Sidebar** (needs 1, owner: Minho): pick a track, see the fixed session times and the logo, and add a track with a name, latitude and longitude. Check them first (name not empty or already used, latitude −90 to 90, longitude −180 to 180), accept the track only within 3 km of a circuit in `grade1_tracks.csv`, otherwise say "No racetrack found at these coordinates", and save accepted tracks to `data/my_tracks.csv`. Done when every check has its own message and a test.
- [x] **5. History and track comparison** (needs nothing, owner: Diajeng Widyannisa): from `data/current_weather.csv`, the rain history of the selected track (rain per day, mm, temperature range and how variable it is), and two tracks side by side over the same period, ranked with `sorted()`, with a one-line f-string summary for each (average temperature, rain days, total rain, over how many days we logged). Each with a chart with units. Done when both run on the committed data, with tests on a small slice of it.
- [x] **6. Statistics** (needs 0, owner: Cedric): for each 3-hour window, combine the three providers: mean temperature, wind and rain with a 95% confidence interval, and how many providers predict rain. Build it on `tests/fake_forecast.py` first. Done when the numbers are tested on the fake forecast.
- [x] **7. Weekend overview** (needs 0, then 2 + 6, owner: Emilio): the main page for the selected track: the weather now, one 5-day chart (temperature °C, rain mm, wind km/h) with the confidence interval and the session times marked, wind strength and direction, and the RainViewer radar on a map around the track. Fake forecast first, then the real one.
- [x] **8. Session dashboard** (needs 0, then 2 + 6, owner: Emilio): one session at a time, with previous and next buttons. For that session's window: temperature, chance of rain and wind strength and direction, per provider and combined with the confidence interval, plus a small chart. A session beyond OpenWeatherMap's 5 days uses the providers that reach it, or says "No forecast yet".
- [x] **9. Live check** (needs 2 + 3, owner: Arthur): with the real key, each error message, a failing provider, adding a good and a bad track. Fix what breaks.
- [ ] **Walkthrough (Mon 16 Nov):** each of us explains our card to the group.
- [x] **10. Refactor** (needs 2–8, owner: Arthur): move functions to where they belong, remove duplicates and unused code, make names consistent. Tests pass before and after.
- [x] **11. Polish (Mon 16 Nov)** (needs 10, owner: Arthur): cosmetic upgrades only: layout and spacing, colours, titles and labels, empty and loading states, the logo, and anything an outsider found confusing.
- [x] **12. Finish (Mon 16 Nov)** (Arthur, needs 11): user README for `main`, fresh data commit, clean-clone test, merge `dev` into `main`.
- [ ] **Submitted (Fri 20 Nov).**
