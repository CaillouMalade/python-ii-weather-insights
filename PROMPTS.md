# AI collaboration log

We used AI coding agents (Claude Code mostly, Codex on a few early commits) as collaborators all along, and in loops rather than one prompt at a time: we'd point at something in the app or the brief, the agent proposed or changed it, we checked it (tests, then the page in the browser) and kept, changed or rejected it, often several rounds per feature. So listing every prompt isn't realistic, instead each section below is one feature or card, with what we asked, what the agent produced and what we kept, changed or rejected and why. The agents followed an instruction file written for the assignment rules (keep to what was taught in class, explain before and after coding, one test per feature, never commit the key or invented data), which is in the git history but no longer in the repo since further development doesn't have to follow it. The detailed entries written along the way, before this file was condensed on 16 Nov, are in the git history too.

One section per card, in card order. Write your entry under your own card's heading, never at the end of the file, so two pull requests don't edit the same lines.

## Before the racetrack app — up to 10 Nov 2026 (Arthur, with Claude Code and Codex via OpenBot)

**Asked:** Set up the repo exactly as the assignment's scaffold recommends (`src/` package, `pyproject.toml`, `variables.env.example`), then build a first version to see what the brief allows: a general city weather app, reworked a few times (a stock-style dashboard, radar map, analytics, light mode), plus a separate collector logging the current weather at 18 circuits every 30 minutes. Then, on 10 Nov, archive all of that and restart from "one SIMPLE project that fits all the guidelines", which became the racetrack app.

**Got:** The packaged scaffold with pytest; a city app with `APIClient`/`WeatherClient`, `WeatherReading`, duplicate-safe CSV logging inside `st.cache_data`, one `ValueError` message per failure and log-only analytics; the collector and its history (`current_weather.csv`); then a simplified app and a first racetrack version reading that history (archived prototypes on `archive/` branches).

**Kept / changed / rejected:** Kept the core that every card built on: the `APIClient` base class and its fixed error messages (a `requests` error contains the URL, so the key), logging inside the cache so reruns add no duplicate rows, and the collector's real history. Rejected the rest for simplicity: the stock-style theme and custom CSS, light/dark theming, air quality and UV, geocoding search, and an earlier racetrack proof of concept with wind maps and track outlines, which was more than the group could explain. We split the remaining work into the cards below.

## Card 2: OpenWeatherMap client and errors — 15 November 2026 (Arthur, with Claude Code)

**Asked:** Add the OpenWeatherMap 5-day forecast as the third provider, on the same 3-hour windows as Open-Meteo and MET Norway, and give each failure its own message with a test.

**Got:** `WeatherClient.forecast(location, now=None)` on `data/2.5/forecast`, returning `ForecastPoint`s cut with `keep_next_five_days`; OWM's `rain.3h` at 03:00 put in the 00:00 window, a missing `rain` read as 0 mm and the last window's rain left as `None` (no item after it); `WeatherClient(API_KEY)` added to `fetch_forecasts_and_log` only when the key is set; new messages in `APIClient` for 400 (bad coordinates), 429 (too many requests, easy to hit on the free key) and 5xx, so all three providers get them; 4 tests in `tests/test_client.py` with fake answers (the rain shift, the 5-day cut, one message per failure: 401, 404, 400, 429, 503, timeout, no connection, not JSON, wrong shape, and a bad location stopped before any call).

**Kept / changed:** Kept the app running without a key (Open-Meteo and MET Norway only), rather than blocking every page on a missing key. Left the `rain.3h` question to card 9's live check, which confirmed it.

## Card 3: more providers — 14 November 2026 (Arthur, with Claude Code)

**Asked:** add Open-Meteo and MET Norway as `APIClient` subclasses returning `ForecastPoint`s on OpenWeatherMap's 3-hour UTC windows, plus a way to combine the providers.

**Got:** `OpenMeteoClient`, `MetNorwayClient`, an aggregator returning one DataFrame with a `source` column and a list of failures, a forecast log `data/forecasts.csv`, and tests on two saved real answers.

**Decided / changed:** compared the APIs first in a side chat. Chose value at window start for temperature and wind, a 3-hour sum for rain, "00:00 = rain falling 00→03" for every provider, MET only where it's hourly (no 6-hour logic), 5 days max, wind direction never averaged (card 6 counts compass sectors). Rejected one CSV per provider (harder to group) and extra columns that can be calculated. Asked why a class rather than a function, and confirmed it's inheritance, not nested classes.

## Card 4: sidebar — 15 November 2026 (Minho, with Claude Code)

**Asked:** do card 4 from the README: pick a track, show the fixed session times and the logo, and add a track by name, latitude and longitude, accepted only within 3 km of a Grade 1 circuit. Asked for simple code with a few short comments at the key steps.

**Got:** `sessions.py` (`SESSIONS` in UTC and `session_times()` for the coming weekend), `tracks.py` (`distance_km` with the haversine formula, `nearest_track`, `check_new_track` with one message per check), `load_tracks`, `load_all_tracks` and `append_track` in `storage.py`, a `show_sidebar()` function in `app.py`, and 16 tests in `tests/test_tracks_and_sessions.py`.

**Checked:** `uv run pytest` passes. Ran the app with Streamlit's AppTest: an empty name, a point in central Madrid ("No racetrack found at these coordinates"), a point at Monza (added and selected) and the same name again. The test row in `data/my_tracks.csv` was deleted afterwards.

**Decided / changed:** the tests first used `pytest.raises`; changed to `try / except ValueError as error` like `tests/test_client.py`. Coordinates are typed in `text_input` and turned into numbers with `float()`, so "north" gets its own message. The name check ignores case. The old circuit multiselect stays as it is, because moving it is card 10. The logo shows only once `assets/logo.png` exists (card 1b). From Friday to Sunday the sidebar shows the current weekend, from Monday the next one.

## Card 5: History and track comparison - 15 November 2026

**Asked:** The student asked to complete card 5.

**Got:** Track history by stable collector track ID, daily rain and temperature ranges, and a two-track comparison over their overlapping logged period. Added unit-labeled charts, summary lines, and tests using a small copy of committed collector data.

**Kept as-is / changed / rejected:** Kept the card 5 scope and the simple pandas patterns already used in the project. The student accepted the planned scope and approved the commit and PR.

## Card 5 follow-up: history fixes — 15 November 2026

**Asked:** restore the previous Analytics view, put track history in `show_track_history()`, fix dry-day rain and avoid double-counting overlapping hourly rain; optionally use the sidebar track, readable temperature legend labels, and a `TrackSummary` class with `__lt__` and `__str__`.

**Got:** restored the trend, circuit comparison and derived metrics; made track history follow the sidebar selection when available; filled missing rain with zero and estimated daily rain as the mean rolling-hour reading × 24. Added readable chart labels and ranked `TrackSummary` objects by estimated rain.

**Kept / changed:** Kept both card 4 and card 5 README/PROMPTS entries. Retained comparison track selectors because the user still needs to choose the pair being compared.

## Card 6: Statistics — 14 November 2026 (Cedric)

**Asked:** Claude (Opus 5.5) to write card 6 from the README: for each 3-hour window, combine the three providers (mean temperature, wind and rain with a 95% confidence interval, and how many providers predict rain), built and tested on `tests/fake_forecast.py`.

**Got:** `src/weather_app/forecast_stats.py` (`combine_forecasts`, `add_interval`, `t_value`, `check_forecast_table`) and `tests/test_forecast_stats.py` (13 tests). It takes the table from `aggregator.fetch_all_forecasts` and returns one row per window, ready for cards 7 and 8.

**Decided:** a t-distribution interval (mean ± t × std / √n) instead of the normal 1.96, because we only have 2–3 providers and 1.96 would make the forecast look more certain than it is; a provider "predicts rain" from 0.1 mm; the low end of rain and wind is cut at 0; a window with one provider gets no interval; wind direction is not averaged (it is an angle, so the session dashboard shows it per provider).

**Checked:** the first window's numbers by hand in a test (9.33 °C, interval 7.90 to 10.77); ran it on the saved Open-Meteo and MET Norway answers in `tests/`; `uv run pytest`: 50 passed.

**Kept / changed / rejected:** kept the module as written; rejected the normal approximation (too narrow with three values) and a 0 mm rain cutoff (counts rounding noise as rain).

## Card 6 follow-up: history fixes — 16 November 2026 (Cedric, with Claude)

**Asked:** Claude (Opus 5.5) to review the merged app, then fix three points: card 5 counted a rain day from anything above 0 mm while card 6 uses 0.1 mm; the daily rain estimate (× 24) was written both in `analytics.py` and in `app.py`; the RainViewer radar had no attribution on its map.

**Got:** `compare_track_history` now counts a rain day from 0.1 mm (`RAIN_THRESHOLD_MM`, imported from `forecast_stats`) and takes its daily rain from `track_rain_history`, so the × 24 estimate lives in one function; Track comparison builds its three charts from `track_rain_history` too; "Rain radar: RainViewer" as the radar layer's attribution; one test that a day under 0.1 mm is not a rain day.

**Checked:** `pytest`: 80 passed. Ran `compare_track_history` on the committed history before and after: average temperature, total rain and days logged are identical for all 24 tracks, only rain days drop where a day had under 0.1 mm (e.g. Imola 9 → 8). Rendered Track comparison with Streamlit's AppTest: no error, same three charts.

**Kept / changed / rejected:** kept "Spa" for a user track sharing Spa-Francorchamps' id (people call it Spa), the session dashboard's wide two-provider interval (it is honest there, in a table rather than a chart), and every logged circuit in Track comparison, including those not in the sidebar (Silverstone, Le Mans…).

## Card 7: Weekend overview — 15 November 2026 (Emilio, with Claude)

**Asked:** I began with an exploration phase together with Claude (Opus 5.5): we went through the card's requirements in the README and `AGENTS.md`, the code the group had already merged (cards 2 to 6), and the class material on Streamlit (s14) and Plotly (s18). From there I decided on the page layout and on an approach that reuses the group's existing functions and stays within the concepts covered in class. Claude then helped me structure and draft the code one piece at a time; I reviewed, tested and adjusted each piece before committing it.

**Got:** `dashboard.py` with small page helpers shared with card 8 (wind compass sector and provider votes, chance of rain, a session's 3-hour window, and the "session over / no forecast yet" message), with 8 tests; `radar.py` with `RainViewerClient(APIClient)`, a cached `fetch_radar_url()` in `fetching.py`, and 3 tests; and in `app.py`, `forecast_chart()`, `show_radar()`, `show_weekend_overview()` and a first tab, "Weekend overview".

**Checked:** `uv run pytest` passes (84 tests). The page was run with Streamlit's AppTest on fake forecasts, with and without an API key: setup message, a skipped provider, metrics and four charts, no errors. One live RainViewer request and one radar tile confirmed the image address. I also reviewed the page in the browser.

**Decided / changed:**
- Three line charts (°C, mm, km/h) instead of one chart split into panels, so each chart keeps its own unit and the code stays within what was covered in class.
- The 95% confidence interval is shown as Low / Average / High lines (`px.line` with three columns) rather than error bars.
- Wind direction is shown as a vote over eight compass sectors ("SW (3 of 3 providers)") rather than an average, since averaging angles is misleading (350° and 10° average to 180°).
- Rain and wind direction for the current window come from the forecast, so `WeatherReading` and the log columns stay unchanged.
- The radar client lives in its own file because it is not a forecast provider. The earlier archived radar code was not reused, to keep the implementation simple.
- During my review, the radar showed "Zoom Level Not Supported" tiles at close zoom. RainViewer's free images stop at zoom 7 and the map requests one level ahead, so the radar layer is hidden from map zoom 6.5 onwards (`maxzoom`), with a caption explaining the limit.
- Beyond the class material: `fig.add_vline`, `px.scatter_map` and `map_layers`, each used once and documented in the code.

## Card 8: Session dashboard — 15 November 2026 (Emilio, with Claude)

**Asked:** Building on the exploration done for card 7, I defined the session page: one session at a time with Previous and Next buttons, the combined forecast with its 95% interval, the chance of rain and the wind for that session, a per-provider comparison, and a clear message when a session is over or not yet forecast. Claude helped me structure and draft the code one piece at a time; I reviewed, tested and adjusted each piece before committing it.

**Got:** in `dashboard.py`, `provider_table()` (one readable row per provider, wind in km/h and as a compass direction), `direction_label()` and `interval_text()` (the texts shown on both pages), with 5 more tests; in `app.py`, `previous_session()`, `next_session()`, `session_chart()`, `show_session_dashboard()` and a second tab, "Session dashboard". The Weekend overview now uses `direction_label()` too, so the direction text is written in one place.

**Checked:** `uv run pytest` passes (89 tests). The page was run with Streamlit's AppTest on fake forecasts and fake session times, clicking through every case: a session that is over, two sessions with a forecast (values checked by hand against the fake data), a session six days ahead ("No forecast yet."), and the buttons disabled at the first and last session. I also reviewed the page in the browser with next weekend's sessions and real forecasts.

**Decided / changed:**
- The session shown is kept in `st.session_state`, because a button is only pressed for one run; the buttons use `on_click`, the same pattern as "Add track" in the sidebar, so the page always redraws with the right session and button states.
- The forecast is fetched with the same cached call as the Weekend overview, so switching tabs or sessions downloads and logs nothing twice.
- The statistics are computed on the session's window only, by reusing `combine_forecasts()` unchanged.
- The small chart is a bar per provider plus a "Combined" bar whose error bar shows the 95% interval, the same `error_y` already used in the Analytics tab.
- A session beyond the providers' 5 days shows "No forecast yet."; one that has already started keeps its forecast until its 3-hour window ends.

## Card 9: Live check — 15 November 2026 (Arthur, with Claude Code)

**Asked:** Run the card 9 live check with my real key: every error message, one provider failing, adding a good and a bad track, and whether OpenWeatherMap's `rain.3h` lands in the right window. Fix only what breaks.

**Got:** Scratch scripts outside the repo that triggered each failure for real (bad key, not found, bad request, timeout, no connection, 429, 503, an answer that isn't JSON, bad input before any request), one provider pointed at a wrong URL, and the add-track form driven in the app with Streamlit's AppTest. For `rain.3h`, OpenWeatherMap was compared with Open-Meteo's hourly rain on all 16 tracks: they agree best (correlation 0.64, against 0.27 for the 3 hours after) when `rain.3h` is the rain of the 3 hours before its timestamp, which is what `WeatherClient.forecast` already assumes. One bug: "nan" typed as a latitude passed every check, the track was saved, and every provider then refused it.

**Kept / changed:** Every message and the failing-provider case worked, so they stay as they are. Fixed the `nan` hole in two places, one commit each, with a test each: `validate_location` (client.py) and `read_coordinate` (tracks.py) now check "not inside the range" instead of "below or above", so `nan` is rejected. Also translated the 10 comments in Chinese into English (sidebar, sessions, storage, tracks and their tests), keeping their meaning, so every member can read them. Left the "Spa" id follow-up to card 4. No live-check output was kept in the repo or in `data/`.

## Card 10: Refactor — 15 November 2026 (Arthur, with Claude Code)

**Asked:** Remove everything left over from the old city app so each page holds only what the README says, keep the code simple, close to the class and well commented, and keep each member's code recognisable. While checking the app in the browser I also asked for a few changes: the race weekend always starting tomorrow (the presentation is on a Monday and the forecasts only reach a few days ahead), "Add a track" folded, a zoomed-in track map, a time slider on the radar, one rain and temperature chart like the one in our first prototype, the charts cut to the 3 race days right under "Weather now", the pages in a bar that stays at the top, and the app name in the sidebar.

**Got:**
- Removed the old city app: the "Circuits" box and "Add a place" in the sidebar, the Live conditions tab, the old analytics (`city_trend`, `city_comparison`, `daily_range`, `feels_like_gap`, `rank_by_temperature`), `find_city`, `validate_city`, `fetch_many`, `load_circuits`, `load_log`, `load_all_readings` and `data/circuits.csv`, with their tests. Also `direction_label`, `WeatherReading.__lt__` and `WeatherReading.feels_like_gap`, which nothing used any more.
- Four pages, matching the README: Weekend overview, Session dashboard, History and Track comparison (card 5's page split in two, its code unchanged). They are `st.Page`s in `st.navigation(position="top")`, so the bar stays visible and only the open page runs.
- `sessions.py`: `weekend_start()` (tomorrow at 00:00 UTC) replaces `weekend_friday()`.
- Weekend overview: "Wind from" in "Weather now"; `rain_and_temperature_chart()` (rain bars, temperature line and its 95% band on a second axis) and `wind_chart()`, both for the 3 race days, with the band drawn only where all 3 providers answered (with 2, Student's t is 12.7 and the band flattened the line); a satellite map of the track next to the radar; `RainViewerClient.radar_frames()` and a slider over the last 2 hours of radar.
- Structure: `aggregator.py` moved into `fetching.py`, `radar.py` into `providers.py` (15 modules to 13), docstrings on the page functions, the `AGENTS.md` project map updated.

**Checked:** `uv run pytest` passes (78 tests: 9 removed with the old city code, 3 with the unused pieces, 2 added for the weekend start and the radar list). Every page opened in the browser and with Streamlit's AppTest on real data, with no errors; `data/` restored before each commit.

**Kept / changed:** Every member's functions were moved, not rewritten: card 5's history and comparison, card 6's statistics, card 7's radar and card 8's session page work as before. I rejected removing the radar: it only shows the last 2 hours, but that is what tells you whether rain reaches the track within the hour. I kept `weather_log.csv` and `forecasts.csv` being written, but the history pages read only the collector's `current_weather.csv`, since the app's own log has no track id.

### Be ready to explain: new forms
- `st.navigation` with `st.Page` (the top bar), `st.select_slider` (radar time), `st.expander` (Add a track).
- `fig.add_scatter` with `fill="tonexty"` (the shaded band) and `yaxis="y2"` (temperature on a second axis), and `pandas.Series.where` (hiding the band where only 2 providers answered).
- A satellite tile layer (Esri World Imagery, free, no key) in `px.scatter_map`, the same way the radar is drawn.

## Card 11: Polish — 16 November 2026 (Arthur, with Claude Code)

**Asked:** Going through the app in the browser and pointing at what looked wrong, page by page: align the track map and the radar, shorter captions, the session dashboard reorganised (cards, charts for the session's own 3-hour slot, then a "Per provider detail" section), a confidence view for rain that is actually readable, the History charts fixed (negative rain axis, red for the highest temperature, a gradient on the temperature swing), more in Track comparison (variability, any number of tracks), the logo in the sidebar in light and dark mode, and why History showed almost no rain.

**Got:**
- Weekend overview: the radar slider moved above both maps, so the track map and the radar line up at the same height and size; shorter captions ("MVP preview using free APIs…", "Note: MET Norway API is limited to 2.5 days.").
- Session dashboard: the weekend charts reused for the session's 3-hour slot only, split into temperature, rain and wind (`wind_chart` became a general `line_chart`, plus `temperature_chart` and `rain_chart`); rain shows one flat line per provider and their mean as a bar, with a footnote on why the lines are flat; a "Per provider detail" section with the table and three bar charts (temperature, rain, wind), each with the combined value and its 95% interval as an error bar (`session_chart` now takes the value to draw).
- History: rain axis starts at 0, "Highest" in red, the temperature swing as bars coloured from blue to red; tracks logged on fewer than 2 days say "Not enough logged history" instead of drawing one dot (`days_logged` and `MIN_DAYS_LOGGED` in `analytics.py`, with a test).
- Track comparison: 2 to 4 tracks with `st.multiselect`; the `TrackSummary` ranking shown as metric cards, wettest on the left; a grouped bar chart of the daily temperature swing reusing `track_rain_history`; an "MVP preview" callout at the top. The "logged readings" line removed from both history pages.
- Sidebar: the logo (`assets/logo.png`, and `assets/logo_dark.png` picked with `st.context.theme.type` in dark mode) in place of the title.
- Rain in History: the committed `current_weather.csv` stopped on 6 Nov (174 rainy readings out of 6,013). The collector had kept running until 13 Nov, so its newer copy replaced it: 11,591 readings, 892 with rain. The collector stopped after the switch to the 16-track list, so the 6 new tracks have one reading each.

**Checked:** `uv run pytest` passes after every change (79 tests). Each page checked in the browser on real data.

**Kept / changed:** I rejected the gradient line, then kept the gradient bars for the swing. I rejected the rain error bar in the session chart (too wide to read with 3 providers) for one line per provider. I wanted to remove the one-line track summaries, but they are the only visible use of `TrackSummary.__lt__` with `sorted()`, so they became metric cards instead. I kept 3-hour windows rather than hourly: OpenWeatherMap's free forecast is 3-hourly and the group's `ForecastPoint` contract is built on them.

### Be ready to explain: new forms
- `st.context.theme.type` (light or dark logo), `st.multiselect` with `max_selections`.
- `px.bar` with `error_y` and `error_y_minus` (an interval that is not symmetric because rain and wind never go below 0), and `color_continuous_scale` (the blue-to-red bars).

## Card 12: Finish — 16 November 2026 (Arthur, with Claude Code)

**Asked:** What the submitted repo must contain according to the brief, then a user README for `main`, the fresh data committed, and a clean-clone check before merging `dev` into `main`.

**Got:** A checklist of the brief's repository requirements against the repo (all met except the user README and the data, which was 10 days old); `README.md` rewritten for a user and the grader (what the app does, setup, how to run it and the tests, the data files, how the forecasts are combined, the project structure, the team), with the card checklist kept at the end; `current_weather.csv`, `weather_log.csv` and `forecasts.csv` committed as real logged data; `AGENTS.md` and `CLAUDE.md` taken out of the repo and added to `.gitignore`; this file condensed (an intro on how we worked with the agents, and the ~290 lines of prototype history before the cards summed up in one section, the card entries kept as written).

**Checked:** A fresh clone, `uv sync` and `uv run pytest` following only the README; the app started from it; no key in any committed file.

**Kept / changed:** I took `AGENTS.md` and `CLAUDE.md` out of the repo: they were written for the assignment rules, and now that the MVP is done further development doesn't have to follow them. They stay in the git history and `PROMPTS.md` stays. I kept three CSVs rather than one: forecasts and observations don't mix, and the app's `WeatherReading` has no track id or rain, so its log can't join the collector's history without changing a shared contract on freeze day.
