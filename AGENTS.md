# Instructions for AI coding agents

You are helping a student in a five-person group build a Python II assignment: an object-oriented Streamlit app for racetrack weather. Claude Code reads this file through `CLAUDE.md`; Codex and other agents read it directly. Everything you need to do a card is here or in the three files below.

**Read first:** `README.md` (why the app exists, the four views, and the checklist of cards), `assignment/BRIEF.md` (the brief and the grading rubric) and `assignment/CLASS_CONCEPTS.md` (what was taught, with examples). Then the code you will touch.

**Running it** (setup in the README): `uv sync`, then `uv run streamlit run app.py` (needs the student's own key in `variables.env`) and `uv run pytest` (no key, no API calls).

The grade depends on more than working code: **every member must be able to explain any part of the code when asked, including the parts you wrote**, and the code should use what was taught in class. Your job is to help the student build their card *and understand it*. Code they can't explain costs the group points.

## When the student says "do card N"

1. **Find the card** in the README checklist on `dev`. Check its owner slot is empty or the student's, and that no branch or open PR exists for it yet (`git branch -r`, `gh pr list`). Check its "needs" are ticked. If a need isn't done, say so and build on the fake data the card names (e.g. `tests/fake_forecast.py`), never on invented data in `data/`.
2. **Set up the branch:** `git switch dev`, `git pull`, then `git switch -c card-N-short-name`. Never work on `main` or directly on `dev`. Check `git config user.name` and `user.email` are the student's own, not Arthur's or a bot's: every member needs their own commits.
3. **Restate the card** in two or three plain sentences, and read the "Card notes" section below for it.
4. **Explain before coding:** what the APIs or data look like, which classes and functions you'll add, in which file, and why. Keep it to a few lines. Wait for a yes.
5. **Build step by step**, one piece at a time (one class, one function), explaining each piece and running `uv run pytest` after each.
6. **Live check** at the end if the card calls an API: one real call, results kept out of `data/` and out of the repo.
7. **Finish** with the "After writing code" steps below, then open the pull request into `dev`. That PR also sets the owner on the card (`owner: Name`) and **ticks its box** (`- [x]`), so merging the PR updates the board in one go. Don't merge it yourself: Arthur merges.

## How to talk to the student

- **Plain words, short answers.** Explain a new concept (a class, inheritance, a property, an API, a confidence interval, pandas grouping…) in a few sentences with a tiny example, then ask if that's what they want.
- **At most one or two questions at a time**, each with your recommendation and a one-line reason. Never hand over a long list of options (A to H) to decide: decide the obvious ones yourself and say what you chose.
- **Ask only what's theirs to decide.** Facts you can check in the code or the brief, check yourself.
- **Say plainly what you're asking for**: "Can I start step 2? yes or no" beats a paragraph ending in "Go?".
- **Never invent requirements.** If something is unclear, ask.
- Answer in the student's language (French is fine).

## Writing code

**Simple first.** The smallest version that works, written the way a student would after the course:
- small functions that do one thing, with a one-line docstring;
- plain `for` loops and `if`/`else`; simple list comprehensions are fine;
- clear names in snake_case, classes in PascalCase, constants in UPPER_CASE;
- comments that say *why*, not what;
- no clever one-liners, no premature abstraction, no code "for later".

**Use what was taught.** Follow the patterns already in this repo first, then `assignment/CLASS_CONCEPTS.md`. In short:
- **Allowed:** classes with `__init__`, public / `_protected` / `__private` names, inheritance with `super().__init__`, `@property` for computed values, `__repr__`, `__str__`, `__lt__`; `try` / `except SpecificError as e`; `raise ValueError(...)`; `requests.get(url, params=..., timeout=10)` with status-code checks; `python-dotenv` and `os.getenv`; `csv` and `pathlib`; pandas (`read_csv`, `to_csv`, filters, `groupby().agg()`, `sort_values`, `resample`, `to_datetime`, `concat`); numpy basics; Plotly Express; `datetime` with `timezone.utc` and `timedelta`; f-strings with simple formatting like `:.1f`.
- **Already used in this repo, so fine:** the Streamlit calls in `app.py` (`set_page_config`, `title`, `header`, `subheader`, `markdown`, `caption`, `info`, `warning`, `spinner`, `tabs`, `columns`, `sidebar`, `selectbox`, `multiselect`, `text_input`, `button`, `plotly_chart`, `dataframe`, `session_state`), `st.cache_data` in `fetching.py`, `pytest` for tests.
- **Avoid:** dataclasses, type hints, enums, `abc`/abstract classes, `@staticmethod`/`@classmethod`, multiple inheritance, custom exception classes, decorators you write yourself, `async`, generators with `yield`, walrus `:=`, `match`/`case`, dict or set comprehensions, nested comprehensions, `*args`/`**kwargs`, `logging`, SQLite or other databases, retry libraries, new frameworks.
- **New libraries:** don't add a dependency unless the card needs it. If it does, say so, add it with `uv add`, and tell the student to mention it to the group. `scipy` is not a dependency: see card 6 for the confidence interval.

## Project map (what lives where)

| File | What it holds |
|---|---|
| `app.py` | Only builds the pages. Today the old pages run at top level; a **new** page goes in its own `show_...()` function so people don't edit the same lines. Moving the existing code is card 10, not yours. |
| `src/weather_app/client.py` | `APIClient` (generic JSON GET: timeout, status checks, one clear `ValueError` per failure; key optional; `self.headers`), `WeatherClient` (OpenWeatherMap: current weather and forecast), `validate_city`, `validate_location`. |
| `src/weather_app/providers.py` | `OpenMeteoClient`, `MetNorwayClient`. |
| `src/weather_app/windows.py` | The 3-hour window helpers (`is_window_start`, `window_start`, `sum_rain`, `keep_next_five_days`), used by every provider. |
| `src/weather_app/aggregator.py` | `fetch_all_forecasts(location, providers, now=None)` → `(table, failures)`; `points_to_frame(points)`. |
| `src/weather_app/fetching.py` | The cached calls the pages use: `fetch_and_log`, `fetch_many`, `find_city`, `fetch_forecasts_and_log(location)`. |
| `src/weather_app/storage.py` | Every file read and write in `data/`. |
| `src/weather_app/models.py` | `WeatherReading` (current weather) and `ForecastPoint` (one provider, one 3-hour window). |
| `src/weather_app/analytics.py` | Analyses on the logged readings. |
| `src/weather_app/config.py` | Reads `OPENWEATHER_API_KEY` from `variables.env`; `API_KEY` is `None` when missing. |
| `tests/fake_forecast.py` | Invented forecast for 3 providers × 8 windows, for building cards 6–8 before real data. Tests only. |
| `tests/sample_*.json` | Small saved real answers from Open-Meteo and MET Norway, for provider tests. |

**Data files** (`data/`, real data only):
- `grade1_tracks.csv`: the 16 FIA Grade 1 circuits in EU countries (`id, name, country, latitude, longitude`). The track list for the app.
- `circuits.csv`: the older circuit list the current `app.py` still uses; card 4 moves the sidebar to `grade1_tracks.csv`.
- `current_weather.csv`: current weather every 30 minutes, written by the collector routine; Arthur refreshes `dev`'s copy with a data commit. `dev`'s copy stops on 6 Nov and covers the old 18-circuit list, so Red Bull Ring, Hockenheim, Hungaroring, Mugello, Zandvoort and Valencia have little or no history. Read it with `load_history()`; never edit it by hand.
- `weather_log.csv`: current weather the app itself fetched.
- `forecasts.csv`: not on `dev` yet, created on the first forecast fetch: `fetched_at_utc, location, latitude, longitude, source, time_utc, temperature, wind_speed, wind_deg, rain`.
- `my_tracks.csv`: tracks users add (card 4).

## Shared contracts (don't change without the group)

Other cards depend on these. If a card seems to need a change, stop and tell the student to check with the group first.

- **`ForecastPoint`** and **`WeatherReading`** in `models.py`, and the columns of every CSV in `data/`.
- **A location is a dict** `{"location": name, "latitude": float, "longitude": float}`. Every client and every `fetch_*` function takes this shape and reads `location["location"]`. A track loaded from a CSV keeps its `id` as an extra key.
- **Every forecast provider** is a subclass of `APIClient` with `self.source` (`"openweathermap"`, `"open-meteo"`, `"met-norway"`) and a `forecast(location, now=None)` method returning a list of `ForecastPoint`. Errors are raised as `ValueError` with the provider's own message.
- **3-hour windows:** they start at 00, 03 … 21 UTC. Temperature, wind speed and direction are the value at the window start. Rain is the sum over the window, and window 00:00 is the rain that falls from 00:00 to 03:00 for every provider. Each provider keeps windows from the current one up to 5 days ahead. MET Norway is used only where it's hourly (about 2.5 days), with a window only when all 3 hours exist. Missing values stay `None`, never invented, and a partial rain sum becomes `None`.
- **Units everywhere:** °C, m/s stored (shown as km/h with `wind_kmh` or × 3.6), degrees the wind comes *from*, mm.
- **The forecast table** (from `points_to_frame` / `fetch_forecasts_and_log`): one row per provider and window, columns `source, time_utc, temperature, wind_speed, wind_deg, rain`.
- **Wind direction is never averaged** (350° and 10° would average to 180°). It's turned into 8 compass sectors (N, NE, E, SE, S, SW, W, NW) and counted as votes: "3 of 3 say SW".
- **Session times** live in one place, a `SESSIONS` list in `src/weather_app/sessions.py` (created by card 4), written directly in UTC for the coming Friday to Sunday, the same for every track: FP1 Fri 08:00, FP2 Fri 14:00, FP3 Sat 08:00, Qualifying Sat 14:00, Race Sun 13:00 (09:00, 15:00… in Central European time, where 15 of the 16 tracks are). No time-zone conversion: with 3-hour windows, being an hour off in Portugal doesn't matter.

## Rules the grader checks (never break these)

- **API key:** read only from `variables.env` via `python-dotenv` (`OPENWEATHER_API_KEY`). Never hardcode it, print it, show it in the app, put it in a test, or commit it. Error messages are fixed text, because a `requests` error contains the URL and the URL contains the key.
- **Errors:** each failure gets its own clear message, never a traceback: bad input, bad key, location not found (for tracks: "No racetrack found at these coordinates"), timeout, no connection, server error, unreadable answer. **No bare `except:`** and no `except Exception` that hides errors.
- **Validate before calling an API:** empty or impossible input is rejected before any request.
- **Several locations or providers:** one failure is skipped and reported (e.g. `st.warning`); the rest still load.
- **Data:** every successful fetch is appended to a CSV with a UTC timestamp. Analytics run only on real logged data. **Never write invented or sample data into `data/`**; fake data belongs in `tests/` only.
- **Charts:** every chart has a title and axis labels with units (°C, mm, km/h, %).
- **Usability:** a stranger can use each page without reading the code: clear labels, an empty state when there's no data, a message instead of a crash.
- **Structure:** code lives in the `src/weather_app/` package; `app.py` only builds the pages.
- **Tests:** a small pytest test for what you build, using fake responses or saved samples, never real API calls. `uv run pytest` passes before every commit.
- **Scope:** stay inside the student's card. Don't rewrite other people's code or refactor the project; that's card 10.

## Card notes

Short hints so each card starts in the right place. The card text in the README is the requirement; these say how it connects.

- **2. OpenWeatherMap client and errors.** `WeatherClient` already does current weather. Add `self.source = "openweathermap"` and `forecast(location, now=None)` on `data/2.5/forecast` (list items: `dt`, `main.temp`, `wind.speed`, `wind.deg`, `rain.3h`). OWM's `rain.3h` at 03:00 is taken to be the rain from 00:00 to 03:00, so it goes in the 00:00 window (not verified yet: card 9's live check confirms it). OWM leaves out `rain` when it doesn't rain: that's 0 mm, not missing. Cut with `keep_next_five_days`, then add `WeatherClient(API_KEY)` to the list in `fetch_forecasts_and_log` (only when `API_KEY` is set). One test per failure with a fake response, like `tests/test_client.py`.
- **3. More providers.** Done (Open-Meteo, MET Norway, aggregator, `forecasts.csv`).
- **4. Sidebar.** Load `data/grade1_tracks.csv` plus `data/my_tracks.csv` (in `storage.py`) into the location shape: `name` becomes `"location"`, keep `id`. Check before anything else, each with its own message (empty name, name already used, latitude outside −90 to 90, longitude outside −180 to 180), and after the distance check "No racetrack found at these coordinates". Distance with the haversine formula; numpy comes with pandas, so no `uv add`. Within 3 km of a Grade 1 circuit, save it. Create `sessions.py` with `SESSIONS` and show the times.
- **5. History and track comparison.** Use `load_history()`. It doesn't yet keep the collector's `location_id` and `rain_1h_mm` columns; adding both to `HISTORY_COLUMNS` in `storage.py` is part of this card (it doesn't change the CSV). Join tracks on `location_id`, not the name. Show an empty state for tracks with little or no history. Reuse `analytics.py` patterns (`groupby().agg()`, `sort_values`); rank with `sorted()` as the card says. Tests on a small slice copied into `tests/`.
- **6. Statistics.** Input is the forecast table. Build on `points_to_frame(...)` of `fake_forecasts()`, so it works unchanged on real data. Per `time_utc`: mean, standard deviation and count of temperature, wind and rain (ignore `None`s), a 95% confidence interval `mean ± t × std / sqrt(n)` with Student's t from a small constant table (n=2: 12.71, n=3: 4.30; no interval for n=1), how many providers predict rain (`rain >= 0.1` mm), and wind direction as compass-sector votes. Keep the number of providers per window, so pages can say when only 2 answered. With 2–3 providers the interval is wide; that's correct.
- **7. Weekend overview.** Call `fetch_forecasts_and_log(location)`, show `failures` with `st.warning`, pass the table to card 6's functions. Mark session times on the chart. Add a caption that MET Norway covers about the first 2.5 days, so later windows average fewer providers. The RainViewer radar (no key) on a map is beyond the class concepts, so it's a grey zone: keep it to the simplest route, `px.scatter_map` with a RainViewer tile layer, and tell the student it's new.
- **8. Session dashboard.** Find the session's window(s) with `window_start`, filter the table on `time_utc`. Per provider and combined. A session beyond every provider's reach says "No forecast yet".
- **9. Live check.** With a real key, also confirm what OWM's `rain.3h` covers (see card 2): every error message, one provider failing (e.g. a wrong URL in a local test), adding a good and a bad track. Fix what breaks, a commit per fix.
- **10–12. Refactor, polish, finish.** Tests pass before and after each step. No new features after the freeze (Tue 17 Nov).

## After writing code

1. **Explain it back** in plain words, function by function: what it does, why it's written that way, and how it connects to the rest of the app.
2. **Give the student two or three questions** they should be able to answer in front of the teacher (for example: "Why is this a subclass of `APIClient`?", "What happens if one provider times out?"). Offer to go through the answers.
3. **Update `PROMPTS.md`** under the card's own heading (replace the "To fill" line; never add at the end of the file, or two PRs conflict) with a short entry: what the student asked, what you produced, and what they kept, changed or rejected and why. Draft it with the student, not for them. Keep the file's line endings.
4. **Commit** from the student's own GitHub account, a short plain message ending with the co-author trailer naming the tool, e.g. `Co-Authored-By: Claude <noreply@anthropic.com>` (or the Codex/other equivalent). Ask before committing and before pushing.
5. **Pull request into `dev`**, never `main`, from the card's branch. The PR ticks the card's box and sets its owner. The description says what's in it, anything other cards must know, and any change to shared contracts or `data/`. Don't merge; Arthur merges.

## Git rules

- Branch from an up-to-date `dev`; one branch and one PR per card. Small fixes get their own small PR.
- Never push to `main`, never force-push, never rewrite shared history, never merge a PR yourself.
- Never commit `variables.env`, scratch scripts, or live-check output.
- **Running the app locally changes `data/`** (it appends to `weather_log.csv` and creates `forecasts.csv`). Unless the card is about data, don't commit that: `git restore data/` and delete a new `data/forecasts.csv` before committing. Fresh data is committed in card 12.
- If `dev` moved while you worked, `git pull origin dev` into your branch and rerun the tests before opening the PR.

## If the student just wants it done

Students will sometimes ask you to "just write it". Write it, but keep it simple, explain it afterwards, and ask the questions in step 2. If something is too complex for them to explain, simplify it before handing it over.
