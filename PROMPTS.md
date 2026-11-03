# AI collaboration log

## Repository setup — 21 October 2026

**Asked:** "just let's make a private repo with the assignments docs. linked to the group assignment's folder"

**Got:** A private GitHub repository, local Git setup in this folder, a root .gitignore, this log and PROJECT_STATE.md. Assignment documents and supplied starter code are preserved.

**Checked:** Confirmed the GitHub account and private repository in the browser. Checked local repository boundaries and the initial file list. Git status, ignored secret paths and remote synchronization are checked during setup; results are recorded in PROJECT_STATE.md.

**Kept as-is / changed / rejected:** Kept the supplied documents and starter code as-is. Added repository setup files only. No assignment implementation, dependency installation or weather fetch was requested or performed.

## Bot continuity snapshot — 23 October 2026

**Asked:** Arthur requested through COS: "Ask all bots that have a space in the vault to log a record of what they know how they work and everything about them." This bot was asked to create a comprehensive dated self-record in its existing project space, preserving historical records and distinguishing verified state from unknown capabilities.

**Got:** `BOT_SELF_RECORD_2026-10-23.md`, covering remit, assignment knowledge, relevant preferences/decisions, constraints, local project evidence, historical versus current connection checks, unresolved issues, paths and handover guidance.

**Checked:** Read applicable instructions and canonical project records; inspected local Git status, branch, origin and HEAD plus scaffold/configuration files. Re-read the saved snapshot, checked the documentation diff and confirmed that the only working-tree changes were the new snapshot and this appended log entry. No application tests or external account checks were needed for documentation.

**Kept as-is / changed / rejected:** Added a dated snapshot and appended this entry. Preserved existing records and all assignment code. No dependency installation, weather fetch, commit, push, account change or routine creation.

## Weekly bot continuity archive — 25 October 2026

**Asked:** Arthur authorized weekly self-archiving through COS: save one comprehensive dated self-record in the existing canonical project folder, preserve originals, distinguish verified from historical/unverified state, verify complete UTF-8 readback, and report quietly to COS only.

**Got:** BOT_SELF_RECORD_2026-10-25.md covering remit, knowledge, preferences/decisions, boundaries, methods, current local evidence, tool/connection limits, known routine context, unfinished work, paths and handover.

**Checked:** Read applicable AGENTS.md and PROJECT_BOT.md, canonical assignment/setup records and scaffold/configuration files. Inspected Git status/log/origin. Verified complete strict UTF-8 readback of both documentation outputs against intended text and checked documentation-only changes. No app tests or external service checks were run.

**Kept as-is / changed / rejected:** Preserved all earlier records and pre-existing changes. Added one dated snapshot and appended this entry only. No implementation, dependency installation, weather fetch, account change, routine listing/modification/testing, commit, push or submission.
## Assignment-only rollback — 28 October 2026

**Asked:** Arthur requested rollback of additions from another project, keeping only the simple assignment version.

**Got:** Restored the original assignment brief, course reference, supplied scaffold and repository setup from fc53892. Removed Pitwall implementation and its Node/React tooling from the active tree. Retained prior Git history and a local recovery bundle outside the project.

**Checked:** Compared the restored file list and scaffold against fc53892; checked the commit diff and remote synchronization. No dependencies installed, weather fetched, or assignment implementation added.

**Kept / changed / rejected:** Kept assignment sources and original starter code byte-for-byte. Preserved local AI-use documentation. Rejected unrelated Pitwall scope. Full previous Pitwall files and logs remain recoverable from the backup bundle and history.

## Repository initialization — 28 October 2026

**Asked:** Arthur requested initialization exactly as recommended by the assignment guidelines in the repository.

**Got:** Copied the supplied app.py, src/, tests/, pyproject.toml and variables.env.example to the repository root. Preserved the original starter_template and the assignment brief at assignment/BRIEF.md. Wrote the project setup README, declared pytest as a development dependency, generated uv.lock, and limited pytest discovery to the active tests/ folder to avoid duplicate template tests. Created the ignored local environment file from the example without configuring a real API key.

**Checked:** uv sync --locked succeeded; uv run pytest passed the one supplied placeholder test. Streamlit AppTest opened both supplied views without exceptions, and the installed weather_app package imported successfully. Original Python source/test files were compared by SHA-256. Git ignores variables.env, the virtual environment and generated Python metadata. No API calls were made.

**Kept as-is / changed / rejected:** Kept all supplied Python code unchanged. Changed only package/test setup and documentation. No assignment features, analytics, data collection or team details were implemented or invented.

## v0.1 general weather app — 2 November 2026

**Asked:** Arthur asked Claude Code (Opus 5.5) to build v0.1 as a simple general weather app with no racetrack features, in the style of CLASS_CONCEPTS.md plus approved exceptions: any Streamlit method (no custom CSS/HTML or multipage), any Plotly chart, OpenWeatherMap Geocoding/Current/Forecast, and pytest with small known-answer cases. Specified: a sidebar city list seeded from the log, a live card with forecast chart and sorted comparison, three log-only analytics, built-in `ValueError` for each failure mode, duplicate-safe CSV logging, and an app that opens without a key.

**Got:** `client.py`, `models.py`, `storage.py`, `analytics.py`, `config.py`, `app.py`, and 16 tests in `tests/test_analytics.py`.

**Checked:** Known-answer tests pass. With no key, AppTest ran both views without exceptions and a headless server answered its health check. In a scratch copy outside the repo (nothing committed, no real key, no real API), AppTest ran the app against a fake local server to check each error message, one failing location, no duplicate rows on rerun, and reseeding from the log. **Not checked by the agent:** the real API, and the look of the page in a browser.

**Kept / changed / rejected:**
- Kept the requested structure.
- Added beyond the literal request, each to prevent a specific failure:
  - `except requests.exceptions.RequestException`, because any other request error would otherwise reach the UI as a traceback, and its text contains the URL with the key.
  - Fixed-text network messages, for the same reason.
  - Catching `KeyError`/`IndexError` on unexpected response shapes.
  - `PermissionError` when the CSV is open in another program, which is common on Windows.
  - `encoding="utf-8"`, because the Windows default cannot write every city name and pandas reads the file back as UTF-8.
- Changed: the log stores the geocoded name, not the name `/weather` returns, because coordinates can return a nearby station's name and split one city into several.
- Changed: the header check opens the file and catches `FileNotFoundError` instead of `Path.exists()`, which is not in the class material.
- Changed: the card uses plain text lines rather than three `st.metric` columns, to avoid truncation at phone width.
- Rejected: `utc=True` timestamp parsing (only UTC timestamps are ever written), tests for storage (temporary files would need a pytest fixture, which is banned), and a persistent "removed cities" list (it would need the separate file Arthur ruled out).

### Be ready to explain: not evidenced in class material

**Streamlit (only `st.sidebar.radio` has a supplied example):** `st.set_page_config` and `st.title` (starter scaffold), `st.header`, `st.subheader`, `st.caption`, `st.write`, `st.metric`, `st.info`, `st.warning`, `st.container(border=True, width=420)`, `st.dataframe(hide_index=True)`, `st.plotly_chart`, `st.text_input`, `st.form_submit_button`, `st.sidebar.header`, `st.sidebar.caption`, `st.sidebar.info`, `st.sidebar.error`, `st.sidebar.success`, `st.sidebar.button`, `st.sidebar.form(clear_on_submit=True)`, `st.session_state`, `@st.cache_data(ttl=...)`, `st.rerun`.

**OpenWeatherMap:** `/geo/1.0/direct` (`q`, `limit`) and `/data/2.5/forecast` (`lat`, `lon`, `units`) are not in class material. `/data/2.5/weather` is, but with `q`; here it uses `lat` and `lon`.

**Plotly:** `px.bar`; `markers=True` and `color=` on `px.line`; `height=` and `legend_title=` in `update_layout`.

**Python and pandas:**
- `requests.exceptions.RequestException` (requested in an exercise only)
- `encoding="utf-8"` on `open`
- `str.isalpha` (list-level coverage only)
- `sorted(..., reverse=True)`
- `drop_duplicates(keep="last")` (class shows `keep="first"`)
- assigning `table.columns = [...]`
- `Path(__file__).resolve().parents[2]` (from the starter's `config.py`)
- `datetime.isoformat()` (`summary.md` only)
- `pytest.raises(..., match=...)`

## v0.1 rework into a stock-style weather app — 2 November 2026

**Asked:** Arthur tried the first v0.1 and asked Claude Code (Opus 5.5) for a rework that looks and behaves like Apple or Android Weather on phone and laptop, with his Apple Weather screenshot as the reference. His feedback: adding a city must be a searchable dropdown; Live and Analytics become tabs at the top; the sidebar keeps saved cities; the card was far too narrow; a city needs an overview, a temperature/precipitation/wind selector, the next 24 hours and a daily forecast; add a weather map; remove the "All your cities" table from the live view; and the analytics were "half-assed", so build proper ones from what the API offers. New rules he approved: one small CSS block and simple card HTML in a separate module with no JavaScript, Analytics may call the API, and the key must never reach the browser.

**Got:**
- A GeoNames-based `data/cities.csv` and the script that builds it.
- `data/saved_cities.csv` for saved cities, instead of seeding from the log.
- New modules: `maps.py`, `fetching.py`, `display.py`, `cards.py`, `style.py`, `sidebar.py`, `views_weather.py`, `views_analytics.py`.
- A wider client with air quality, UV and map tiles, and a longer log schema with a safe migration.
- Four analytics sections and 74 known-answer tests.

**Checked:**
- All 74 tests pass with no key.
- In real Chrome against a throwaway fake server, at 1280, 390 and 844 px wide, the agent looked at screenshots and clicked through search, adding, selecting, removing, refreshing, tabs, map layers and the phone picker.
- Every page's HTML, every network request and every WebSocket frame was searched for the test key and for `appid`: none found.
- The real log was migrated: 6 rows kept, all old values identical, 15 new columns blank.
- **Not checked by the agent:** the real API, real map tiles and real data. All the data in those runs was invented by the fake server and stayed outside the repo.

**Kept / changed / rejected:**
- Kept Arthur's brief, including the server-side map approach.
- Changed after looking at the screenshots:
  - The first heatmaps used `px.density_heatmap`, which binned the date strings and showed a false 0 and averaged cells. Replaced with `px.imshow` on a pivoted table.
  - The WHO takeaway claimed a pollutant "exceeded most often" on 0 days.
  - High and low both showed the current temperature late in the evening.
  - Also fixed: ✕ over the card text, the compass needle over the number, and raw column names in legends.
- Decided: emoji instead of OpenWeatherMap's icon images, so the page loads no icons from another site. Tiles stay two-column on a phone, like the stock apps, while the main cards stack into one column.
- Rejected: JavaScript to close the sidebar on phones, because it is not allowed. A city picker in the page does the job instead.
- Removed: free-text geocoding and `validate_city`, as the dropdown replaces them. `validate_location` now checks locations before any call. The team should be ready to explain this against the brief's "bad city name" and "input validation" items.

### Be ready to explain: not evidenced in class material

**Streamlit:** `st.tabs(key=..., on_change="rerun")` with `.open`, which runs only the visible tab; `st.segmented_control`; `st.selectbox` with `index=None`, `placeholder`, `on_change` and `label_visibility`; `st.container(key=...)`, which adds a CSS class `st-key-NAME`; `st.columns`; `st.html`; `st.button` with `on_click` and `args`; `st.sidebar.container`; `st.subheader`, `st.caption`, `st.info`, `st.warning`, `st.write`, `st.dataframe`, `st.plotly_chart(config=...)`; `st.session_state` (including `.get` and changing it in callbacks); `@st.cache_data(ttl=..., show_spinner=False)`; `set_page_config(layout="wide")`; `.streamlit/config.toml`.

**OpenWeatherMap:** `/data/2.5/weather` and `/forecast` by `lat`/`lon`; `/air_pollution`, `/air_pollution/forecast`, `/air_pollution/history`; `/data/2.5/uvi`; map tiles.

**Plotly:** `go.Figure`, `go.Scattermap` with `carto-darkmatter` and an image layer; `px.bar`; `px.imshow`; `px.defaults`; `update_xaxes`/`update_yaxes`.

**Pillow and standard library:** `Image.new`, `Image.open`, `paste`, `convert`, `save`; `io.BytesIO`; `base64`; `math.asinh`, `sinh`, `atan`, `tan`, `radians`, `degrees`; `html.escape`; `datetime.fromtimestamp` with `timezone(timedelta(...))`; `Path.replace`; `tempfile.TemporaryDirectory` in tests; `zip`.

**pandas:** `DataFrame.pivot`, `.rename`, `.clip`, `.equals`, `.isin`, `.to_dict("records")`, `.dt.strftime`, `.astype(int)`, `is_unique`; `to_datetime(unit="s")`; `read_csv(sep=, comment=, header=None, usecols=, keep_default_na=False)` in the build script.

**Python and CSS:** `%` to wrap tile numbers around the date line; CSS `@media`, `grid`, `conic-gradient`, `::before`; an invisible button stretched over each sidebar card to make it tappable.

## v0.1 own identity and rebuilt Analytics — 2 November 2026

**Asked:** Arthur found the main pane a slightly incoherent copy of Apple Weather and the Analytics poor. After a review, the decisions were: "High 15°  Low 12°" wording everywhere; one clear grid (header, next hours, forecast beside map, even detail tiles); a less pedantic Next hours card with units on every value and no sunrise/sunset entries or footnotes; UV labelled "UV index today"; and Analytics rebuilt as an overview strip plus Plan the week, Air, Compare and History, each leading with a computed finding, using selectors instead of stacks of charts, and showing local time throughout.

**Got:**
- Rewritten `cards.py`, `views_weather.py`, `views_analytics.py` and `style.py`.
- New `findings.py` for the sentences.
- New analytics functions: `week_grid`, `ranked_windows`, `next_rain`, `windiest_moment`, `air_calendar`, `air_by_hour`, `days_over_any_guideline`, `city_day_values`, `rank_cities`, `city_day_grid`, `log_coverage`, `history_series`.
- Known-answer tests for all of these and for the wording.

**Checked:** All tests pass with no key. In real Chrome against a throwaway fake server, at 1280, 844 and 390 px wide, every tab and selector was clicked and screenshots were read. A script checked for overflow and clipped text and searched pages, requests and WebSocket frames for the test key and `appid`. No-key mode was checked in Chrome. **Not checked by the agent:** the real API and real data; real phones.

**Kept / changed / rejected:**
- Kept the sidebar cards' look, as Arthur asked.
- Removed: the compass, the map's Region/Continent control (for less code), `hourly_plan`, `aqi_band_share`, the day-of-week air pattern, the log-based ranking chart, and the separate forecast charts.
- Changed after reading screenshots: the card title's uppercase styling turned "µg/m³" into "MG/M³"; two tables scrolled sideways on a phone; calendar week labels hid the month; "reading(s)" was clumsy; and the `feels_like_delta` property had become unused, so the header now shows it.
- Decided: History needs at least 3 readings over at least 3 hours before drawing a trend. Compare's heatmap rows follow `sorted()` on the reading objects, warmest now first. Old log rows with no UTC offset use the city's latest logged offset, and the axis says UTC if none is known.

### Be ready to explain: new forms not evidenced in class material

`@container` and `container-type` in CSS (layout follows the main column's real width); `grid-auto-rows`; `px.imshow(text_auto=..., zmin=..., zmax=...)`; `color_discrete_sequence`, `coloraxis_showscale`; `pd.concat(axis=1).max(axis=1)`; `DataFrame.pivot`, `.loc[list]`; `Series.dt.tz_localize(None)`, `.dt.total_seconds()`; `pd.to_timedelta(series, unit="D")`; combining boolean Series with `|`.

## v0.1 radar map, city search fixes and Analytics for humans — 2 November 2026

**Asked:** Arthur likes the Weather page but said Analytics "doesn't show stuff in a way a human would want to read". Decisions: real rain radar from RainViewer as the default map layer through a new `RainViewerClient(APIClient)`; stronger OpenWeatherMap layers with legends only where documented; fix the city search (London picked Canada), ambiguous sidebar names and missing capitals; fix "High 31° Low 31°"; and rewrite Analytics in plain words with no codes, keeping at least one labelled chart beyond History.

**Got:** `RainViewerClient`, a base class that works without a key, stronger map layers with documented legends, a rebuilt `data/cities.csv` (5,074 cities), `display_names`, per-day cards and word ratings in Plan the week, a plain-language Air tab, winner cards and a sortable table in Compare, and a friendlier History. 133 known-answer tests.

**Checked:**
- All tests pass with no key.
- The app ran against a throwaway fake OpenWeatherMap with varied invented weather, and the real RainViewer service, which needs no key.
- In real Chrome at 1280 and 390 px, the agent clicked through the tabs and selectors, read every generated sentence for several cities, and searched pages, requests and WebSocket frames for the test key and `appid`.
- RainViewer's coverage mask was checked against real tiles: clear over Madrid, Tokyo and Reykjavik, black over Kinshasa.
- **Not checked by the agent:** real OpenWeatherMap tiles and data.

**Kept / changed / rejected:**
- The London bug was not in our data, which was already largest first. Streamlit's default "fuzzy" search re-sorts by match score, so the shorter label won. `filter_mode="contains"` keeps our order.
- "High 31° Low 31°": the code already used `temp_min` and `temp_max`, and they can equal the current temperature. An equal pair now shows nothing rather than a misleading range.
- Changed after reading the generated text: "Great" next to "rain likely" contradicted itself, so rain or wind now caps the rating; "-0°" fixed across the app; long tie lists became "4 cities tie"; part-days no longer make counts disagree (90 vs 91 days).
- Removed: the numeric heatmaps, AQI calendar, hour-of-day chart, WHO table, ranked windows, the bar chart and heatmap in Compare, the daily range table, and OpenWeatherMap's faint precipitation layer, which radar replaces.
- Legends: OpenWeatherMap's legend page does not say which scale belongs to which `*_new` tile layer, and its values match the Weather Maps 2.0 palettes. Treat the scales as documented but unconfirmed for these tiles. There is no radar legend, because the colour values did not load from RainViewer's page.

### Be ready to explain: new forms not evidenced in class material

`PIL.Image.split`, `.merge`, `.point`, `.alpha_composite`, `.getpixel` and `Image.point` with a `lambda`; `go.Figure.add_bar` and `.add_scatter` with a second y axis; `st.expander`; `st.spinner`; `selectbox(filter_mode=...)`; `datetime.strptime`; `sorted(key=lambda ...)`; `zip` with several lists in a comprehension; `round()` to avoid "-0".

## v0.1 polish round — 2 November 2026

**Asked:** Arthur approved small fixes only: round ticks on the Plan the week rain axis; one-line sidebar names with all cards the same height; air headings saying "the last 3 months" while pollutant lines keep exact counts; and a typed-city fallback, because a grader cannot trigger the brief's bad-city and input-validation handling from a dropdown.

**Got:** `rain_axis_ticks`, `split_name`, fixed-height sidebar cards with the country on the small line, `validate_city` and `WeatherClient.find_city` back in the client, and a "Not listed? Type a city" box with distinct messages for empty input, no letters and city not found.

**Checked:** Tests pass with no key. In real Chrome at 1280 and 390 px against a throwaway fake OpenWeatherMap (including a fake geocoding endpoint), the agent looked at the chart and cards and tried each error message and a successful add. **Not checked by the agent:** the real geocoding endpoint, and the map boost on real tiles, which was left unchanged as asked.

**Kept / changed / rejected:** Kept everything else. Rejected truncating long names such as "London, United Kingdom", which would have hidden the country that tells two cities apart; the country moved to the small line instead. A typed city is identified as "Name, CC", so two places with one name in a country count as one.

### Be ready to explain: new forms not evidenced in class material

`st.form(border=False)` and `st.form_submit_button(on_click=...)`; Plotly `tickmode="array"`, `tickvals`; CSS `text-overflow: ellipsis`, flexbox; `while` loop in `rain_axis_ticks`; `str.split(", ", 1)`.

## v0.1 final fix round — 2 November 2026

**Asked:** After live testing with the real key and an independent audit, Arthur approved these fixes: softer map layers with labels on top; a clearer loading note; the daily-range sentence only from 3 days; less duplication in Compare; the typed box folded under "Not listed?"; the phone sidebar arrow no longer floating over content; High and Low agreeing everywhere; a failed forecast unable to win Compare; the key not kept in error context; no "nan km/h"; a code cleanup; a minimum Streamlit version; and accurate docs.

**Got:**
- `WEATHER_LAYER_BOOST` halved from 3 to 1.5, and weather layers placed below the basemap's first label layer. Radar is unchanged.
- `with_today_range`, so the Today row uses the same figures as the sidebar and header.
- Missing forecast values are now `None`, with a dash in the Compare table. A selectbox replaces the sort buttons that repeated the winner cards.
- `from None` on the three network errors.
- `wind_text` and `pd.to_numeric` for missing gusts. This was a real bug: a missing gust showed "nan", and a forecast with no gusts at all would have crashed.
- Removed `migrate_log` after checking that `data/weather_log.csv` already has the current header. Also removed the nested loop, repeated plural code, five unused forecast fields, and the `3.6` literals in `cards.py`.

**Checked:** All tests pass with no key. In real Chrome at 1280 and 390 px against a throwaway fake OpenWeatherMap, with a failing forecast, missing gusts and a current high above the forecast's. Pages, requests and WebSocket frames were searched for the test key and `appid`. **Not checked by the agent:** the softer layers on real tiles, or anything on a real phone.

**Kept / changed / rejected:**
- `sorted(loaded, key=lambda weather: weather["reading"], reverse=True)` replaced the nested loop. The key values are the reading objects, so `sorted` still compares them with `WeatherReading.__lt__`.
- Kept one way to sort the table, a selectbox, so the buttons no longer repeat the card names.
- The map caption says a new layer can take a few seconds to appear, because the spinner covers fetching and Streamlit cannot see when the browser finishes painting. No JavaScript was added.
- The label layer is named in `FIRST_LABEL_LAYER`. If CARTO renames it, the map may need this name updating.

### Real-key checks by the orchestrator

The agent never read a key or called OpenWeatherMap. The orchestrator ran real-key checks between rounds:
- It probed which endpoints the key can use, including the 401s on One Call, hourly, daily, history and climate data, and on Weather Maps 2.0.
- It confirmed the forecast's `dew_point` with a real request.
- It tested the app live, which found the London search result, Mumbai's equal High and Low, the Tokyo and Rio temperature layers at average alpha about 228, and Rio's 33° against 32°.
- The rows in `data/weather_log.csv` come from those live runs.

### Earlier commits by Codex

Commits `73043d4`, `387fdb0` and `b3c61e9` carry a `Co-Authored-By: Codex <noreply@openai.com>` trailer. Codex, OpenAI's coding agent, helped with those, which are the repository initialization and the earlier Pitwall work.

### Be ready to explain: forms not listed in earlier entries

`pytest.approx`; class attributes (`COLOR_SCHEME`, `OPTIONS` on `RainViewerClient`); `.pop` on `st.session_state`; `.items()` on a dictionary; `dropna(subset=...)`; the `:02d` format; `datetime.timestamp()`; `getattr` in `to_dict`; `raise ... from None`; `traceback.format_exception` in a test; `float("inf")` as a sort key; `pd.to_numeric`; `.loc[mask, column] = value`; `st.expander`; `st.selectbox(width=...)`; the `below` setting on a Plotly map layer; CSS `min-height`.

## Racetrack MVP — 3 November 2026

**Asked:** Arthur asked Claude Code (Opus 5.5) to turn v0.1 into the racetrack MVP described at the top of the README: "a clean, functional but limited MVP, not overcrowded slop", one provider done well, circuits from a CSV, a Today page (header, temperature and cloud cover, radar beside wind with direction, a precipitation histogram and a rain-timing line) and History built only on the collector's real readings, with the 2–3 November gap shown as a gap. Same class rules as v0.1, no key and no live OpenWeatherMap calls. Partway through, Arthur set a standing design bar: as finished as Linear's website or Apple Notes, no taglines, helper text, captions or footnotes, fewer modules, one way to do each thing, no dead code, and the quietest honest form wherever the earlier wording asked for sentences or notes.

**Got:**
- `data/circuits.csv`, built from the 18 circuits in `circuits.json` with the same ids. `straight_heading_deg` is blank and not used.
- `data/current_weather.csv`, a read-only snapshot of the collector's file (2,971 readings, 29 October to 3 November).
- New `forecast.py` (3-hour windows, today's high and low, `rain_timing`) and `history.py` (local time, hourly values with gaps, daily rain hours, daily extremes, one finding per section).
- Wind grid and arrows in `maps.py`: 9 cached current-weather calls around the circuit, arrows coloured by speed band, a km/h legend.
- One `views.py` for the sidebar, Today and History, replacing `sidebar.py`, `views_weather.py` and `views_analytics.py`.
- `WeatherReading.wind_kmh` as the property, replacing `feels_like_delta`, which nothing used any more.
- Tests: `test_forecast.py` and `test_history.py` are new; `test_core.py` and `test_storage.py` were rewritten. 77 tests in all.

**Checked:**
- `uv run pytest` passes with no key.
- AppTest with no key: Today shows the setup message without exceptions, and History rendered for all 18 circuits without exceptions.
- A throwaway fake OpenWeatherMap server in a scratch folder, with invented data, Monza failing and one of Spa's grid points failing, plus the real keyless RainViewer service. The agent looked at real Chrome (a visible window driven through the DevTools protocol) at 1280 px and 390 px: the sidebar, Portimão and Spa on Today, and History for Spa.
- Monza's card showed its error while every other circuit loaded. Spa's wind map showed "1 of 9 points missing" with 8 arrows.
- The test key and `appid` were not in the page HTML, the 100 resource URLs or the chart data.
- `data/weather_log.csv` was restored afterwards, so no invented rows were committed.
- **Not checked by the agent:** the real OpenWeatherMap API and key, real wind and forecast values, real phones, and Streamlit's WebSocket frames (v0.1's check covered those; this round checked what reached the page).

**Kept / changed / rejected:**
- Kept: the v0.1 header and card look, server-side radar stitching, `APIClient` and both subclasses, `validate_location`, the log schema, `__repr__` and `__lt__`, logging inside the cache.
- Removed: the city search, typed-city box, saved cities, `data/cities.csv` and its build script; air quality, UV, OpenWeatherMap's map layers and legends; Next hours, the daily forecast card and the detail tiles; Plan the week, Air, Compare and the four overview cards; `analytics.py` and `findings.py`. App code went from 2,647 to 1,463 lines.
- Sidebar cards show wind instead of high and low, so the sidebar needs one call per circuit (18) rather than two (36). With the 9 wind calls and the collector also running, two calls per circuit came close to the free key's 60 calls per minute.
- Each 3-hour step is treated as the window ending at its time, because OpenWeatherMap documents `rain.3h` as the last 3 hours. "Rain likely" means a chance of at least 50 %. "Dry until" is only said when no earlier window has any rain; otherwise it says "Rain unlikely until".
- A history day counts as full from 20 hours with data. Only full days get high and low markers, so a day the collector only half covered cannot claim a low it never saw.

**Cut under the design bar:**
- All captions: map attribution and loading notes, "How we rate this", "Next few hours", "local time", feels-like comparisons, the short-history note and the empty-tile notes.
- Sentences turned into small timestamps: "Radar 08:30" in the radar card's title, "Forecast 08:36" in the rain card's title.
- The coverage sentence is now one quiet line: readings, span and the longest stretch with no data.
- Findings were shortened to one line each, such as "Rain in 6 of 60 hours (10 %), on Sat 31 Oct, Mon 2 Nov."
- One attribution line for OpenWeatherMap and RainViewer at the foot of the sidebar; the basemap shows its own.
- The "one weather point" limit stays in the README only, not on the page.
- Kept only conditional notes that report a real failure: "No radar coverage here", "N radar tiles missing", "N of 9 points missing".

**Known gaps to resolve before submission:**
- With circuits coming from a CSV, the brief's "bad city name" and user-input validation items can no longer be triggered from the UI. `validate_location` still checks every circuit and grid point before any call, and a blank or broken row in `circuits.csv` gives a clear message on that circuit's card, but a grader cannot type bad input.
- `WeatherReading.__lt__` is kept, as Arthur asked, and tested with `sorted()`, but nothing in the app sorts readings now that comparison is out of scope.
- The README's MVP section still promises "the radar for the next hour or so" for rain timing; the app shows only the latest radar image, not a radar nowcast.

### Be ready to explain: new forms not evidenced in class material

`Series.dt.tz_convert` with a zone name and `.dt.tz_localize(None)`; `pd.to_datetime(..., utc=True)`; `DataFrame.set_index("time").resample("h").mean()` (resample is in class; on a column set as the index it is not); `Series.shift` as a whole column; `Series.value_counts().index[0]`; `math.isnan`, `math.cos`, `math.sin`; `go.Scattermap` with `mode="lines"` and `None` breaks; `fill="tozeroy"`; `add_bar(width=...)` in milliseconds; `barmode="stack"` and `"overlay"`; `hovermode="x unified"`; `st.selectbox(format_func=...)`; CSS `linear-gradient` with hard colour stops.

## Design round — 3 November 2026

**Asked:** After merging the MVP and his README rewrite (`b06083d`), the orchestrator relayed Arthur's feedback and a decided visual direction to Claude Code (Opus 5.5):
- Radar zoomed in "so that the track basically fills the map", with RainViewer's low-zoom tiles enlarged smoothly. The wind map stays regional but tighter (15–25 km spacing).
- No footnotes anywhere: the History coverage line, "Forecast 07:50" stamps and captions go. Only data attributions remain, plus the radar time inside the new status element.
- A pit-wall look: flat graphite (`#0E1110`, `#161A18`, `#242A27`, text `#E8EDEA`, muted `#8A948F`), green `#2FD27A` for dry and selection, red `#E5484D` only for rain and failures, tabular numerals, a light-weight big temperature and fewer section titles.
- One bold element, a track-status strip of three lights (now, next 3 hours, later today) with the timing sentence and radar time. Each sidebar card gets one light.
- Also cut: the header subtitle. Cloud cover becomes a quiet band. History rain becomes a sentence only when dry, or red rainy hours only.

**Got:**
- `zoom_for_length` (13 for a 4 km track, one level out per doubling, kept between 10 and 13.5).
- `radar_area`, which keeps a 48-pixel square of zoom-7 radar around the circuit, and `enlarge`, which stretches it 16 times with bicubic resampling in RGBa mode.
- `status_lights` in `forecast.py`; `light`, `status_strip` and `radar_text` in `cards.py`.
- A rewritten `style.py` with the colour tokens, the same colours in `.streamlit/config.toml`, a quieter map attribution and green focus rings.
- `load_circuit`, which fetches each circuit's forecast with its current weather for the sidebar lights.
- 84 tests in all: new known-answer tests for the lights, the zoom helper, the radar square and the smooth enlargement.

**Checked:**
- `uv run pytest` passes with no key. AppTest with no key: Today shows the setup message, and History renders for all 18 circuits without exceptions.
- RainViewer's real maximum zoom: zoom 8 answers with a "Zoom Level Not Supported" image, so the app uses 7.
- Real Chrome (a visible window driven through the DevTools protocol) at 1280 and 390 px, against the throwaway fake OpenWeatherMap with Portimão dry, Spa wet now, Monza failing and one Spa grid point failing, plus the real RainViewer service.
- Looked at Portimão (three green lights), Spa (three red lights, red card light, red bars, 8 of 9 arrows), Barcelona (real rain inside the radar square), History for Paul Ricard (rain) and Portimão (dry), the status strip wrapping at 390 px, and keyboard focus on a sidebar card.
- Contrast on the surface: text 14.8:1, muted text 5.6:1, the green focus ring 8.9:1, the red light 4.5:1.
- The fake run logged to a scratch file. The 18 real rows from the orchestrator's live check, uncommitted in `data/weather_log.csv`, were left untouched.
- **Not checked by the agent:** the real API and key, real phones, and a fresh key search of pages and requests (the key path did not change this round; the last search was in the MVP round).

**Kept / changed / rejected:**
- **What the enlarged radar looks like:** at zoom 12–13 the frame covers only about 8 by 8 radar pixels, each about 1 km. Nearby rain therefore appears as a soft, smoothly shaded wash over the track, not as detail. A side-by-side of Barcelona's real radar showed blocky squares with plain enlargement and soft patches with no dark fringes after `enlarge`. Rain more than about 24 km away is outside the kept square, as agreed.
- The sidebar light needs each circuit's forecast, so a cold start now makes 18 current-weather calls, 18 forecast calls and 9 wind calls: 45 in all, against the free key's 60 per minute, while the collector also uses the key. The MVP round had avoided this; the design needs it. Cached for 10 minutes.
- Light rule: "now" is the window running now; "next 3 hours" is the windows starting within 3 hours; "later today" is the rest of today's windows, unlit when none are left. Each light uses the 50 % rule of the sentence, and its meaning is in `aria-label` and `title`.
- Failure notes moved into the status strip's radar slot: "No radar here", "Radar incomplete" or "Radar unavailable" replace the time when they apply. The wind map no longer says how many points failed; a failed point simply has no arrow.
- `st.plotly_chart(theme=None)` with the `plotly_dark` template, because Streamlit's chart theme was replacing the muted tick colour.
- The wind scale runs from muted green-grey `#7F9A8A` to the red flag `#E5484D`.
- Removed: the per-condition gradients (`BACKGROUNDS`, `background_for`, `is_night`), `gaps` and `coverage_text`, the forecast fetch time, the "Next 5 days" title and the History section titles, the header's country and length, and the "N of 9 points missing" and "radar tiles missing" notes.

**Still open:** the bad-city rubric gap and the unused `__lt__`, both from the MVP round.

### Be ready to explain: new forms not evidenced in class material

`Image.crop`, `Image.resize` with `Image.Resampling.BICUBIC`, the `RGBa` mode (premultiplied alpha); `math.log2`; `//` floor division in pixel maths; `st.plotly_chart(theme=None)` and the `plotly_dark` template; `line_shape="spline"` with `smoothing`; `yaxis_dtick`; CSS custom properties (`--name`, `var()`), `box-shadow`, `:focus-visible` and `:has()`; `aria-label` and `role="img"`.

## Track map round — 3 November 2026

**Asked:** Arthur liked the design round ("pretty good, I like that there isn't verbose text") but said "I still don't see the track map properly." The orchestrator relayed the brief to Claude Code (Opus 5.5):
- Draw each circuit's real outline on the radar map, framed to fill it, and faintly on the wind map.
- Copy the 18 GeoJSON files read-only from the Pitwall project and check each one is the right circuit.
- Credit f1-circuits (MIT) in the map's existing attribution, and list both sources in the README.
- Fix three findings from the orchestrator's live check: the header's "Rain, next 3 h: 0 %" disagreed with a red next-3-hours light at Le Mans; History's gusts line looked broken; and the cloud band was still spiky.

**Got:**
- `data/tracks/` with the 18 files and the f1-circuits licence. `circuits.csv` gains `track_file` and `track_credit`.
- `load_track` in `storage.py`: a GeoJSON file becomes a list of line segments, and the OSM ways are not joined.
- `track_bounds`, `track_view` and `track_layer` in `maps.py`. The outline is a 3 px `#E8EDEA` line over a 6 px dark casing, drawn as map layers above the radar.
- `next_three_hours` in `forecast.py`, used by both the header and the light. `calm_clouds`, a centred 15-hour mean used only by the chart.
- History's wind chart without gusts.
- 98 tests, with new known-answer tests for loading an outline, file to segments, bounds to framing, every real track filling its map, the header and the light agreeing, and the calm cloud band.

**Checked:**
- **Each file is its circuit.** The drawn length is within 3 % of the official length for all 18, and the line passes within 0.25 km of the circuit's coordinate, or 0.9 km for the Nordschleife and Le Mans, whose coordinate sits inside the lap. A small-multiples drawing of all 18 matched each layout by eye.
- **No mismatches.** No circuit was left without an outline.
- **Tests and AppTest:** `uv run pytest` passes with no key; AppTest with no key, as before.
- **Real Chrome at 1280 px:** Spa (F1, wet now), Le Mans La Sarthe (OSM, dry now but rain likely in the next window), the Nordschleife (OSM, 53 ways) and Silverstone, all against the throwaway fake server and the real RainViewer service.
  - Each outline fills its radar map.
  - The attribution reads "f1-circuits (MIT) | © OpenStreetMap contributors © CARTO" for F1 tracks, and no f1 credit for OSM ones.
  - Le Mans' header showed 80 % beside a red next-3-hours light.
- **Real Chrome at 390 px:** Portimão's outline fills the map with no sideways scroll.
- **The log:** the fake run logged to a scratch file; the 36 real uncommitted rows in `data/weather_log.csv` were left untouched.
- **Not checked by the agent:** the real API and key, real phones, and a fresh key search (the key path is unchanged).

**Kept / changed / rejected:**
- **Layers, not traces:** the outline is drawn as map layers, because only a layer can add its source to the map's own attribution text. That keeps the f1-circuits credit without a caption.
- **Framing width:** the framing assumes a 340 by 320 pixel map, about the narrowest (a phone), so the outline fits everywhere. Desktop panels at 1280 px measured about 363 px wide. A test checks that all 18 tracks fill 78–84 % of the deciding side.
- **One definition of "next 3 hours":** the running window and the next one. In the live check, at 08:30 the header read only the running window (0 %) while the light read only the next window (80 %).
- **Light test expectations changed:** with the new definition, rain now also lights the next-3-hours light.
- **Wind map:** the outline is drawn at 1.5 px and 45 % opacity, and the map keeps zoom 8.3. At that zoom a 5 km track is a small shape at the centre, which is enough to relate the two maps.
- **Removed:** History's gusts line and the gust column from the hourly table.
- **Browser note:** Chrome pauses map drawing in a window covered by other windows. The agent's checking browser ran with `--disable-backgrounding-occluded-windows` to see the maps; the app itself is unaffected.

### Be ready to explain: new forms not evidenced in class material

`json.load`; GeoJSON (`FeatureCollection`, `LineString`, `MultiLineString`); Plotly map layers with `sourcetype="geojson"`, `type="line"`, `below="traces"` and `sourceattribution`; `math.floor` to round a zoom down; `Series.rolling(5, center=True, min_periods=1)`; `pd.isna` on a single cell.

## Sessions and legibility round — 3 November 2026

**Asked:** Arthur found the app "a bit too Claude-y verbose" and asked for more legibility through gestalt principles and core data-visualisation ideas, adding that "the small useless taglines are very annoying". The orchestrator relayed the brief to Claude Code (Opus 5.5), with these additions during the round:
- **Track picker:** a single dropdown at the top, kept in `st.query_params` and `session_state`.
- **Sidebar = my sessions** for the selected track:
  - each row has a light (green dry, red rain likely, unlit beyond the forecast) and one value, by the status rule;
  - Add, "Use default weekend" (FP1 Fri 09–10, FP2 Fri 15–16, FP3 Sat 09–10, Qualifying Sat 15–16, Race Sun 14–16, durations as one constant), and editing in place with Save and Delete;
  - a selected session shows as a band on the charts.
- **Legibility:** remove titles, legends, axis titles, micro-labels and stamps; fold labels into values; one surface per group; one shared time axis for temperature and rain; direct labels; day names; units on ticks; no wind legend; credits in one footer line where the licences allow.
- **Wind map** (added mid-round): frame it exactly like the radar, with the full outline, and use a tight 3×3 grid feeding an interpolated field of about 5×5 arrows.
- **Light/dark toggle:** asked for, then dropped by Arthur. No theme code was written; Streamlit 1.66's support was only read in the venv.

**Got:**
- **New modules and storage:**
  - `sessions.py`: `DEFAULT_WEEKEND`, `weekend_friday`, `default_weekend`, `add_default_weekend`, `check_session`, `session_windows` and `session_status`.
  - Session storage in `storage.py` (`load_sessions`, `save_sessions`, `data/sessions.csv`, git-ignored).
- **Views:** `views.py` rebuilt.
  - The track picker.
  - The sessions sidebar with in-place editing.
  - Today as three groups: `now_group` in `cards.py`, a two-row shared-x `forecast_figure`, and the maps.
  - History as one surface.
- **Wind maths in `maps.py`:** `circuit_bounds`, `wind_grid_bounds`, `wind_vector`, `vector_to_wind`, `grid_vectors`, `interpolate_wind` and `wind_field`. Both maps now share `map_layout`'s framing.
- **Status line:** `rain_timing` now gives one short line ("Dry all week", "Rain likely until Tue 19:00", "Dry until Wed 06:00, then rain until Wed 12:00").
- **Tests:** 110 in all. New known-answer tests cover:
  - default weekend dates, including inside the weekend and Sunday evening;
  - no duplicates, and input checks;
  - session overlap and the session rain rule;
  - saving sessions, and editing a row without duplicating it;
  - interpolation, and grid bounds from an outline;
  - the wind map framed like the radar;
  - the short status lines.

**Checked:**
- `uv run pytest` passes with no key.
- AppTest with no key: no exceptions, `?track=portimao` set, and the empty sessions state is the form with Add and "Use default weekend".
- **Real Chrome against the throwaway fake server** (Portimão dry, Spa raining now) and the real RainViewer service:
  - the track came from `?track=spa`;
  - "Use default weekend" added five sessions after a custom one;
  - tapping "Test day" opened the prefilled form and drew the band across both chart rows;
  - renaming it to "Shakedown" and saving changed the CSV row in place, with no duplicate;
  - Shakedown was red at 90 %, FP1–Qualifying green with their chances, and the Race unlit beyond the forecast;
  - Portimão read "Dry all week" with three green lights.
- **Widths:** 1280 px window, 500 px real window (Chrome's minimum) and 390 px emulation. At 500 px the sidebar's scroll width equals its width.
- **Key:** not in the page HTML, its 115 resource URLs or the chart data.
- **Sessions file:** the fake run wrote to a scratch file; `data/sessions.csv` was never created in the repo.
- **Not checked by the agent:** the real API and key, real phones, and Streamlit's sidebar at a true 390 px window (emulation only; the real window stops at 500).

**Visible text on Today** (Portimão, about 1280 px, counted the same way before and after):

| | Before | After |
|---|---:|---:|
| Text elements on the page | 32 | 14 |
| Chart text elements | 35 | 20 |
| **Today in all** | **67** | **34** |
| Sidebar | 89 | 13 |

What makes up the 34 after:
- the 12 high/low labels on the temperature line, which are data;
- 6 map-credit pieces;
- the footer;
- the values;
- 5 day names and 3 mm ticks.

**Kept / changed / rejected:**
- **One shared rule:** the session rule, header, lights and status line all use the same 50 % rule. A session counts every window it overlaps.
- **Status line:** dry weeks read "Dry all week", with no highest-chance clause.
- **Header chance of rain:** removed from Today. The middle light already shows it, and the bars carry the chance on hover. That also removes the old risk of the header and the light disagreeing.
- **Rain bars:** solid red where rain is likely, faint red where it is not. This replaces the dotted chance line and its second axis.
- **Temperature:** read from labels on the line (each day's high and low), so its axis has no ticks. The cloud band has no axis.
- **Wind map:**
  - It is framed like the radar: the outline's bounds plus a margin.
  - The 9 readings come from a grid a quarter wider than the outline on every side.
  - The 25 arrows sit over the framed area, so none falls off the map.
  - A failed grid point takes the average of the others.
  - Without an outline, both maps frame a box sized from `length_km`, which replaces `zoom_for_length`.
- **Sidebar rows:** two lines (name and chance, then day and times) after the one-line row overflowed the sidebar at narrow widths and scrolled it sideways. This was found in the browser.
- **Credits:** OpenStreetMap and CARTO stay on each map, because ODbL asks for attribution with the displayed map. OpenWeatherMap, RainViewer and f1-circuits (MIT) moved to one footer line. MIT asks for the licence with copies of the data, which stays in `data/tracks/`. The `track_credit` column was removed.
- **API calls:** only the selected track is fetched now, so a cold start makes 11 OpenWeatherMap calls instead of 45.
- **Removed:**
  - the 18 circuit cards and the phone circuit picker;
  - the uppercase labels, the wind legend and the radar time stamp (failure words stay in the status group);
  - the History section titles and legends;
  - `zoom_for_length`, `track_credit`, and the selected-row style.
- **Rubric note:** the session form adds real user-input validation with clear messages (empty name, name too long, end not after start). It is not the brief's bad-city item, which remains a known gap.

### Be ready to explain: new forms not evidenced in class material

`st.query_params`; `st.date_input`, `st.time_input(step=...)`, `st.form` with two submit buttons; `plotly.subplots.make_subplots(shared_xaxes=True, specs=[[{"secondary_y": True}], [{}]])`, `fig.add_vrect(row="all")`, `fig.add_annotation`, `ticklabelmode="period"`, `ticksuffix`, `hovertemplate` with `customdata`; `math.hypot`, `math.atan2`; `datetime.timedelta`, `date.isoformat()`, `datetime.weekday()`; `pd.Timestamp.now(tz=...)`; `read_csv(dtype=str)`; `list.pop(index)`; CSS `:has()` for the focus ring on a tappable row.

## Colour and history round — 3 November 2026

**Asked:** Arthur: "The graphs are pretty good. A bit more colour or weather-app-like stuff would be nice. The History visual is pretty tough to read." The orchestrator relayed it to Claude Code (Opus 5.5) with the `distinctive-frontend-design` method as the brief: ground the design in the subject and the job, define a compact direction, spend boldness in one place, let every choice encode something true, and critique the result in context. A new rule allowed colour to encode data.
- **More colour:**
  - a cool-to-warm temperature scale with no green or red, used everywhere a temperature appears;
  - inline condition glyphs, one per forecast day and one in the header;
  - wind arrows on a single-hue scale.
- **History rebuilt** as weather-app daily rows (range bar, rain dot, wind with its direction), with partial days muted and at most one sentence. The brief also asked what the flat stretches in the Le Mans chart were.
- **Pending fixes:**
  - a compact session form with a "Fri 7 Nov" day picker;
  - the session highlight as a full block;
  - rain bars red only when rain is likely.

**Direction (kept compact):**
- **Subject and job:** the pit wall; will rain hit my session, and what is the track doing.
- **Palette:** the graphite tokens, green for dry, red for rain, plus two data scales: temperature from muted blue (0°) through neutral (15°) to amber (25°), and wind in violet, brighter when stronger.
- **Signature:** the status lights stay the one bold element.
- **Weather-app cues:** monochrome condition glyphs, with only the sun warm.

**Got:**
- **Colour helpers:** `temperature_color`, `rain_bar_color` and `condition_kind` in `display.py`.
- **Glyphs:** a new `icons.py`, with six condition glyphs and the wind arrow as SVG data URIs.
- **Data:** `daily_conditions` in `forecast.py`, the forecast's `weather_id` kept by the client, `wind_color` and a violet `WIND_BANDS` in `maps.py`.
- **History:** `daily_rows` and `usual_direction` in `history.py`, and `history_rows` in `cards.py`.
- **Views:** the forecast line drawn in short coloured segments, glyphs above the days, the session as one block across both charts, the new session form, and History as rows.
- **Tests:** 117 in all, with new known-answer tests for:
  - the temperature colour mapping (stops, a mixed value, clamping, no green or red);
  - the rain-bar rule;
  - condition kinds and glyphs;
  - wind colours getting brighter;
  - the header colour and glyph;
  - the History rows' HTML;
  - `daily_rows` and `usual_direction`;
  - the day conditions;
  - the Le Mans frozen readings in the real snapshot.

**What the flat stretches were:**
- **The data:** at Le Mans La Sarthe, 40 of 165 collected readings are exactly 8.87 °C with 1.34 m/s wind from 230°; at Le Mans Bugatti, 44 are 8.8 °C with the same wind. They come mostly between midnight and 07:00, plus a few by day (for example Fri 30 Oct 17:45 and Mon 2 Nov 12:21). Humidity, pressure and cloud cover keep changing during them, and the provider's own observation times advance.
- **The cause:** a frozen value in OpenWeatherMap's data for that point. It is not a collector repeat, a fill or an interpolation in our code. No other circuit has it: the next most repeated reading, at Dijon, appears 6 times.
- **What the app does:** the data is kept as collected. Filtering it is Arthur's call. The daily ranges are barely affected, because the frozen value rarely sets a day's low or high.

**Checked:**
- `uv run pytest` passes with no key.
- **Real Chrome against the throwaway fake server** (Portimão dry, Spa raining, with condition codes added to the fake forecast) and the real RainViewer service:
  - Spa at 1280 px: blue-grey 9°, glyphs over the days, a temperature-coloured line, red bars only for likely rain, the Shakedown session as a green block across both charts, violet wind arrows, and the sidebar form reading "Tue 3 Nov" with tiny Start/End labels.
  - Portimão: "Dry all week" with no red bar.
  - History at Le Mans and Spa at 1280 px and at 390 px: no sideways scroll, partial days muted, arrows present.
- **Contrast on the surface:** temperature colours 7.0–10.2:1, the sun 9.5:1, wind bands 3.2–12.6:1 (the calmest band was lifted from 2.6:1).
- **Key:** not in the page, its 113 resources or the chart data.
- **Data files:** the fake run logged to scratch. A git-ignored `data/sessions.csv` with Le Mans's default weekend, written at 13:06 by the orchestrator's live check, was left as it was.
- **Not checked by the agent:** the real API and key, real condition codes from the real forecast, and real phones.

**Kept / changed / rejected:**
- **Glyphs as images:** Streamlit's HTML cleaner removed inline `<svg>`, which the browser check showed (no arrows, no header glyph). Glyphs are now `<img>` elements whose source is the SVG as a data URI, with alt text: still no network loads.
- **Glyph placement:** a glyph goes only on days whose midday is at least 3 hours inside the forecast, after the first and last glyphs were cut off at the chart edges.
- **Day-glyph ties:** 12:00 and 15:00 are equally far from 13:00, so the earlier window wins, which makes the choice deterministic.
- **Snow bars:** light grey, so they read apart from the neutral bars of unlikely rain.
- **The session form:** days are a select box of the next 14 days ("Fri 7 Nov"), because `st.date_input` only offers numeric formats; a saved day outside that range is still offered. The name has a placeholder; Start and End have tiny labels.
- **The session block:** one shape over the whole plotting height, with green edges. A 1-hour session on a 5-day axis is still narrow, but it now crosses both charts and the gap between them.
- **History:**
  - No hourly sparkline: with the Le Mans frozen value it would show the same flat stretches.
  - The single sentence is the rain finding, the racetrack question.
  - Day labels are "Fri 30", which fits a phone.
  - Removed: `temperature_finding`, `wind_finding`, `daily_extremes`, `moment_text` and the unused gust column.
- **Rubric charts:** the brief's two labelled charts are the forecast figure's temperature and rain rows, plus History's daily ranges with ° labels.

### Be ready to explain: new forms not evidenced in class material

The `:02X` hex format; chained assignment (`low = high = ...`); `base64.b64encode` for SVG data URIs; `fig.add_layout_image` with `xref="x"` and `yref="paper"`; `fig.add_shape(type="rect", yref="paper")`; `st.selectbox(index=..., format_func=...)` over dates; `pd.isna` on a single value; CSS grid columns for the History rows.

## Polish round — 3 November 2026

**Asked:** Arthur approved the colour and history round. The orchestrator relayed five polish items to Claude Code (Opus 5.5), keeping the design direction and method:
1. Filter the provider's stuck readings in the analysis only (a run of 3 or more with identical temperature, wind speed and direction keeps its first reading), with known-answer tests.
2. Fewer, larger wind arrows: a 3×3 field, keeping the interpolation.
3. A temperature scale that still shows a cold week: absolute, with clearer steps between -5° and 30°, checked for contrast, at Le Mans and in a warm case.
4. Hide History days with too few hours to give a real range, with the threshold as a tested constant.
5. Replace the README screenshots with current ones from the fake-server run at 1280 px.

**Got:**
- **Stuck readings:** `drop_stuck` and `STUCK_RUN = 3` in `history.py`, used by the History view only. It walks each location's readings in time order, counts runs of identical (location, temperature, wind speed, wind direction), and keeps the first reading of any run of 3 or more.
- **Thin days:** `shown_days` and `SHOWN_DAY_HOURS = 12` in `history.py`.
- **Wind:** `WIND_FIELD_SIZE = 3` and 5 px arrows in `maps.py`.
- **Temperature:** eight `TEMPERATURE_STOPS` in `display.py`, one every 5° from -5° (periwinkle) through sky, light cyan, blue-grey and sand to orange at 30°.
- **Screenshots:** three new files in `docs/screenshots/` (today, maps, history); the three older track-map images were removed.
- **Tests:** 124 in all, with new known-answer tests for:
  - a run of 3 dropped to 1;
  - a repeat of 2 kept;
  - a run that needs the same wind too;
  - other locations unaffected;
  - the raw history untouched;
  - the hidden-day threshold;
  - the new colour stops, a cold week's range, and contrast on graphite for every degree from -5° to 30°;
  - the 3×3 field.

**Checked:**
- `uv run pytest` passes with no key.
- **The filter on the real snapshot:** 86 of 2,971 readings drop (Le Mans Bugatti 38, Le Mans La Sarthe 28, Magny-Cours 8, Nürburgring GP 8, a few elsewhere), and `data/current_weather.csv` is unchanged.
- **Real Chrome against the throwaway fake server and the real RainViewer service:**
  - a 1280 px real window: Spa with a session block, Le Mans (cool) and Jerez (warm, made 14° warmer in the fake server for this check), and History at Le Mans;
  - 390 px emulation: Le Mans maps and History, with no sideways scroll.
- **Contrast on the surface:** temperature colours 6.4–11.4:1.
- **Not checked by the agent:** real data from the API, and real phones.

**Kept / changed / rejected:**
- **Le Mans History now shows Fri 30 Oct to Mon 2 Nov.** The 1-hour and 2-hour part-days at either end are hidden. Fri 30 and Mon 2 are muted, because dropping the stuck night readings leaves them under 20 hours.
- **What the rule also catches:** it removes repeats at Magny-Cours and the Nürburgring GP too (8 each): 3 or more identical readings in a row there as well. They are dropped by the same rule; Arthur may want to look at those.
- **What is kept:** a single frozen reading (the first of a run) is kept, as the rule asks.
- **Contrast pick:** the 30° stop was chosen as a deep orange that clears the "no red" check, and stays apart from the rain red.
- **Screenshot honesty:** the README notes that the screenshots come from a test run with invented forecast data and the real radar.

### Be ready to explain: new forms not evidenced in class material

`zip` over four columns in `drop_stuck`; list repetition (`[False] * (length - 1)`); `Page.captureScreenshot` with a clip, used only by the agent's checking script, not the app.
