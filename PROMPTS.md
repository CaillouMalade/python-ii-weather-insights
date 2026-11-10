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

## Light mode — 5 November 2026

**Asked:** Arthur wanted light mode, switched through Streamlit's own menu, with dark kept exactly as before and as the default. The ask was to use Streamlit's built-in mechanism (checked against the installed 1.66.1), keep one token dictionary per theme with identical keys, meet WCAG AA in light mode, and add no JavaScript, custom toggle or new text.

**Got:**
- `.streamlit/config.toml` with `[theme.dark]` (the old values) and `[theme.light]` (paper background, dark text).
- A new `src/weather_app/theme.py` with `DARK_TOKENS` and `LIGHT_TOKENS`, plus light versions of the weather gradients. They become CSS variables written with `light-dark(light, dark)`.
- Charts without fixed colours, so Streamlit's chart theme colours them.
- The map's basemap and city dot follow `st.context.theme.type`: `carto-positron` in light, `carto-darkmatter` in dark.

**Checked:** All tests pass, including identical token keys, WCAG ratios for light colours and known contrast answers. In real Chrome against a throwaway fake OpenWeatherMap, the agent switched themes through Streamlit's menu. It checked Weather and all four Analytics tabs in both themes at 1280 and 390 px, and audited text contrast on every page. It found no exceptions, no overflow, and no test key or `appid` in the page.

**Kept / changed / rejected:**
- **Theme switching:** checked first, in the installed Streamlit. Picking a theme in the menu re-themes the page but does not rerun the script, so `st.context.theme.type` stays stale until the next interaction (Streamlit issue #11920). As asked for that case, the page CSS uses CSS variables instead. Streamlit sets `color-scheme` on `.stApp`, and the CSS `light-dark()` function picks a colour from it, so cards, text, ratings and backgrounds switch instantly.
- **Charts:** they re-theme instantly. In dark mode they now use Streamlit's palette, a light blue line with dark blue bars, instead of the earlier fixed orange and blue.
- **Map:** the basemap is drawn in Python, so it switches on the next click.
- **Default:** dark cannot be forced as the first-visit default in 1.66.1. With two themes defined, Streamlit starts from the browser's system setting, even with `base = "dark"`, then remembers the user's choice. On a dark system, or once Dark is picked, the app looks exactly as before.
- **Contrast fixes:** the first light colours failed for captions (Streamlit draws them at 60 % opacity) and for coloured `.small` text (85 % opacity). Both were darkened, and the tests now check them at those opacities.
- **Not fixed:** in dark mode some text was already below 4.5:1, and is unchanged on purpose. That covers sidebar cards on the brighter weather gradients (about 3.0 to 3.3), the orange guideline lines (about 4.0) and the RainViewer link (about 2.5). Streamlit's own light chart axis text is grey, at about 3.6:1 on white, and is not ours to set without fixing it for both themes.

### Be ready to explain: new forms

The `[theme.light]` and `[theme.dark]` config sections; `st.context.theme.type`; CSS custom properties (`--name`, `var(--name)`); the CSS `light-dark()` function and `color-scheme`; the WCAG contrast formula in the tests.

## Simplification — 10 November 2026

**Asked:** Arthur asked for the earlier proofs of concept to be archived and for "one SIMPLE project that fits all the guidelines", built from the city app, with "a few cities" hardcoded in a CSV and no GeoNames.

**Got:**
- Archive branches `archive/city-app` (the old `main`) and `archive/racetrack-poc` (the racetrack app).
- A fixed `data/cities.csv` of 12 cities, chosen from cities already in the log so their history carries over.
- `client.py` cut down to `APIClient` and `WeatherClient` with `find_city` (geocoding) and `current`. Gone: forecast, air quality, UV, map tiles and RainViewer.
- `WeatherReading` reduced to the 8 fields the app uses, with a second property `feels_like_gap` and `__str__`.
- One `app.py` with two tabs, in Streamlit's default look. **Live conditions** shows the chosen cities ranked with `sorted()` (using `__lt__`), a bar chart of temperatures and a table. **Analytics** reads only the log and shows a trend chart, a city comparison chart with a table, the daily range and the feels-like gap.
- The log's 52 real rows were kept with their values unchanged. Only the 15 columns the app no longer uses, all blank in those rows, were dropped.
- New tests: 18, with no key and no network.

**Checked:** `uv run pytest` passes. AppTest ran the app with no key (setup message, Analytics still works) and with a fake `requests.get`. That run covered one failing city skipped with a warning, the unknown-city and empty-input messages, adding a city, and no key in the page tree. The fake run's log rows were removed afterwards. The real API was not called.

**Kept / changed / rejected:**
- Rejected: keeping the forecast. It is useful, but it is not needed for the rubric, and the ask was simplicity.
- Changed: the tests swap `requests.get` by hand and put it back in `finally`, because pytest fixtures such as `monkeypatch` are not used in this project.
- Kept: logging inside the 10-minute `st.cache_data` function, so reruns add no duplicate rows.

### Be ready to explain

`FakeGet.__call__` in `tests/test_client.py` makes an object callable like a function. `raise ... from None` hides the original `requests` error, whose text contains the URL and therefore the key. `px.bar(..., error_y=..., error_y_minus=...)` draws the lowest-to-highest bars.

## Basic racetrack app — 10 November 2026

**Asked:** Arthur wants three apps: the collector (kept active on `data-collection`), the basic weather app and a basic racetrack app. Each starts very simple, and features come back one at a time. The racetrack app gets its own branch, not a switch inside the weather app.

**Got:** Branch `racetrack-simple`, cut from the simple weather app, with the same files. The changes:
- `data/circuits.csv` holds the 18 circuits: id, name and coordinates.
- `data/current_weather.csv` is the collector's history up to 6 November, 6,013 readings, copied from Arthur's synced vault. The first 2,971 rows are byte-identical to the earlier committed snapshot, after converting Windows line endings.
- `storage.load_history` renames the collector's columns to the log's names, and `load_all_readings` combines that history with the app's own log.
- `weather_log.csv` starts empty here, because the city readings belong to the weather app.
- Analytics shows the average daily range per circuit instead of one row per day.

**Checked:** 20 tests pass. AppTest ran the app with no key and with a fake `requests.get`, covering a skipped circuit, the unknown-place and empty-input messages, adding a place, and no key in the page tree.

**Kept / changed / rejected:** The radar, wind maps, track outlines, sessions and theming of `archive/racetrack-poc` were left out, to be brought back one at a time if wanted.
