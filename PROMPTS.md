# AI collaboration log

One section per card, in card order. Write your entry under your own card's heading (replace the "To fill" line), never at the end of the file, so two pull requests don't edit the same lines.

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

## Card 2: OpenWeatherMap client and errors

_To fill in this card's pull request._

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

## Card 11: Polish

_To fill in this card's pull request._

## Card 12: Finish

_To fill in this card's pull request._
