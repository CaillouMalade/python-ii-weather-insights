# Project state

## 21 October 2026 — repository setup

- Arthur authorized a private repository containing the assignment documents, linked to this folder.
- Repository: https://github.com/Arthur-Brht/python-ii-weather-insights (private, verified in GitHub browser).
- This folder is an independent Git repository, nested inside the larger AGENTIC_VAULT working tree. Run project Git commands from this folder; do not add it to the parent repository as a submodule without a separate decision.
- Assignment README.md and summary.md remain canonical; starter_template/ remains the supplied scaffold. No implementation has started.
- Root .gitignore excludes secrets, local environments and generated Python files while retaining variables.env.example.
- Correction to the bootstrap snapshot: config.py's parents[2] correctly targets starter_template/variables.env.
- Added this repository to the existing connector's selected repositories; private visibility and connector read/write permission are verified. Command-line Git has no saved authentication; the first push failed before uploading.
- Team members, deadline and app direction remain unknown.
- Next step: Arthur chooses the first assignment task. No teammate invitations or app implementation are authorized by repository setup alone.

## Verification commands

From this folder:

```powershell
git rev-parse --show-toplevel
git remote -v
git status --short --branch
git check-ignore variables.env starter_template/variables.env .venv/example
git ls-files
git ls-remote origin refs/heads/main
```

Files are uploaded through the authenticated GitHub connector. Local Git metadata is aligned to the resulting remote commit and its file tree is compared with the local index. Direct command-line pushes still require Git Credential Manager sign-in; browser sign-in and connector authentication do not provide CLI credentials.

## 28 October 2026 — assignment-only restoration

Arthur requested removal of unrelated Pitwall project additions. Restored original assignment sources and starter_template from fc53892, without implementing the assignment. The current GitHub owner/origin is CaillouMalade/python-ii-weather-insights. Earlier Arthur-Brht URLs above are historical.

The supplied scaffold is still incomplete; this rollback does not make it a finished submission. Next step awaits Arthur's assignment task. Pitwall history is preserved in Git and in C:\Users\Main\OpenBot\Shared\python-ii-recovery-2026-10-28\repository-before-rollback.bundle.

## 28 October 2026 — initialized root project

Arthur authorized initialization according to the assignment guidelines. The active app.py, src/weather_app/, tests/, pyproject.toml, uv.lock and variables.env.example now live at the repository root. The root README documents setup/run/tests; the original assignment brief is preserved at assignment/BRIEF.md, summary.md remains the course reference, and starter_template/ remains unchanged as reference material.

Verified uv sync --locked, one passing supplied placeholder test, package import and both placeholder Streamlit views via AppTest on Python 3.13.15. pytest is a development dependency; discovery targets tests/ only. The local variables.env is ignored and still needs the user's real key before future API integration. No weather data was fetched. Implementation has not started; the passing placeholder test does not validate weather functionality. Team and app direction remain unknown.

## 2 November 2026 — v0.1 general weather app (branch release/v0.1, not merged)

v0.1 is a general weather app; racetrack features are for later releases. The earlier "implementation has not started" notes are historical.

Built: `APIClient` and `WeatherClient(APIClient)` (Geocoding, Current Weather, 5-day/3-hour Forecast), `WeatherReading`, the CSV log at `data/weather_log.csv`, three log-only analyses (trend, ranking, feels-like delta), and a two-view Streamlit app. The app opens without a key, and Analytics then still works on any existing log.

Verified with no real key and no live API call: `uv run pytest` (16 passed); `uv run streamlit run app.py --server.headless true` answered its health check; AppTest ran both views without exceptions. In a scratch copy outside the repo, AppTest also ran the whole flow against a fake local server: adding, removing, one failing location, no duplicate rows on rerun, reseeding in a new session, and the error messages.

Not verified yet: the real OpenWeatherMap API and real key (Arthur's orchestrator does this check next), and how the page looks in a browser, since AppTest does not render the layout.

Known limits:
- `data/weather_log.csv` does not exist until the first live fetch. No rows are committed yet, and the brief requires real accumulated history at submission.
- Removing a city lasts until the page is refreshed, because the list is reseeded from the log and log rows are never deleted.
- Cities are identified by "Name, CC", so two places with the same name in one country count as one.
- Team members remain unknown. The brief requires commits from every member.

## 2 November 2026 — v0.1 rework (branch release/v0.1, not merged)

Arthur's feedback turned v0.1 into a stock-style weather app: top tabs, saved-city cards in the sidebar, a searchable city dropdown from `data/cities.csv` (GeoNames, CC BY 4.0), a server-side stitched weather map, and four analytics sections. Saved cities now live in `data/saved_cities.csv` (ignored by Git), not in the log. The earlier note that a removed city returns after a refresh no longer applies.

The log schema grew from 9 to 24 columns. `migrate_log` upgrades older files automatically; the 6 real rows in this worktree were migrated with every old value unchanged and the new columns blank. `data/weather_log.csv` is still uncommitted, by decision.

Verified without a real key or live API call: 74 tests pass; real Chrome against a throwaway fake server at 1280, 390 and 844 px wide; no test key or `appid` found in page HTML, network requests or WebSocket frames; no-key mode opens, and log analytics work on a copy of the real log.

Not verified yet: the real API (including field names, the UV endpoint and real tile appearance); the 90-day history size; a real phone (only narrow desktop Chrome windows).

Known limits:
- The free-text "bad city name" path is gone because the dropdown replaced it, which needs explaining against the brief.
- Only the roughly 5,000 largest cities can be added.
- On wide windows, or when panning, the map's weather layer ends at its fixed 5-by-3 tile area.
- Team members remain unknown, and the brief requires commits from every member.

## 2 November 2026 — v0.1 own identity and rebuilt Analytics (branch release/v0.1, not merged)

The main pane is now one grid: header, Next hours, forecast beside map, then eight same-size detail tiles. Analytics is an overview strip plus Plan the week, Air, Compare and History. This replaces the Apple-style layout and the Analytics sections described in the earlier entry. The map's Region/Continent control and the wind compass are gone.

Verified without a real key or live API call: all tests pass; real Chrome against a throwaway fake server at 1280, 844 and 390 px, with every tab and selector; no overflow or clipped text found; no test key or `appid` in pages, requests or WebSocket frames; no-key mode works.

Not verified yet: the real API, including the UV endpoint's meaning. "UV index today" is a cautious label based on what was seen, not on anything confirmed by the agent. Findings have only run on invented data. Real phones are also untested.

Known limits: at about 844 px wide with the sidebar open, the main column uses its narrow layout. Comparison ties are reported only when the top and bottom values are equal.

## 2 November 2026 — v0.1 radar map and Analytics for humans (branch release/v0.1, not merged)

The map now opens on real RainViewer radar, with OpenWeatherMap's temperature, wind, clouds and pressure as other layers. Analytics has been rewritten in plain words; this replaces the Analytics description in the earlier entry. `data/cities.csv` now holds 5,074 cities: the 5,000 largest plus national capitals. The search keeps largest-first order.

Weather Maps 2.0 returned 401 on our key (checked by the orchestrator), so the fainter 1.0 tiles stay and are boosted on the server.

Verified without a real OpenWeatherMap key or call: all tests pass; real Chrome at 1280 and 390 px against a throwaway fake OpenWeatherMap and the real RainViewer service; no test key or `appid` in pages, requests or WebSocket frames.

Not verified yet: real OpenWeatherMap tiles (including how the boost looks and whether the legends match them), and real forecast and air data. Real phones are also untested.

Known limits: RainViewer's API is for personal and educational use. The first map load fetches 30 tiles one at a time, so it can take several seconds; a spinner shows meanwhile. A capital missing from GeoNames' `cities15000` file cannot be added. High and low are hidden when they would be equal.

## 2 November 2026 — v0.1 polish round (branch release/v0.1, not merged)

Rain axis ticks are round, sidebar cards are one fixed height, air headings say "the last 3 months", and a typed-city box covers cities missing from the dropdown. This restores input validation and a city-not-found message a grader can trigger, which closes the rubric risk noted earlier. The box needs an API key, so it is hidden without one.

Not verified yet: the real geocoding endpoint through this box, and the map boost on real tiles (the orchestrator is checking the boost; it was not changed).

## 2 November 2026 — final v0.1 round (branch release/v0.1, not merged)

This round softened the map's weather layers and put labels above them, made High and Low agree everywhere, stopped a failed forecast winning Compare, fixed a "nan km/h" bug, folded the typed-city box, added a bar behind the phone's sidebar arrow, and simplified the code (app code is 22 lines shorter overall, because the fixes added code as well). Streamlit now has a minimum version of 1.66.1, matching the lock file.

**Correction to earlier entries:** `migrate_log` no longer exists. `data/weather_log.csv` already had the current header when it was removed, but an older-format log would no longer be upgraded automatically.

Verified: all tests pass with no key; real Chrome at 1280 and 390 px against a throwaway fake OpenWeatherMap; no test key or `appid` in pages, requests or WebSocket frames.

Not verified by the agent: the softer layers on real tiles, whether CARTO keeps the layer name `waterway_label`, and real phones.

Still open at the time: `data/weather_log.csv` was uncommitted and the orchestrator handled it. The brief requires commits from every team member, and Team is still to be filled in. `PROJECT_BOT.md` is staying for now.

## 3 November 2026 — v0.1 merged into main

The orchestrator committed the real log (tag `v0.1` holds 45 rows; later real rows were added before the merge), pushed `release/v0.1` and tag `v0.1`, and, with Arthur's approval, fast-forwarded `main` to it. The README clone line now uses the default branch. An independent re-audit of `v0.1` found no banned construct, no secret and no regression, and estimated 9–9.5/10. Open: commits from every team member, the Team section, a team walkthrough of the README's hardest parts, and more logged days. The racetrack collector still lives untracked in the main checkout and on the `data-collection` branch; it comes into the app in V2.

## 3 November 2026 — racetrack MVP (branch racetrack-mvp-build, not merged)

The app is now circuit-only: 18 circuits from `data/circuits.csv` (same ids as the collector), a Today view (header, next 5 days of temperature and cloud cover, radar beside wind arrows from a 3 by 3 grid, rain and snow per 3-hour window with a rain-timing sentence) and a History view built on `data/current_weather.csv`, a committed snapshot of the collector's file taken 3 November. Everything about cities, air quality, UV, map layers, Plan the week and Compare is gone. App code: 2,647 lines before, 1,463 after.

Verified without a real key or live OpenWeatherMap call: 77 tests pass; AppTest with no key (Today shows the setup message, History renders for all 18 circuits); real Chrome at 1280 and 390 px against a throwaway fake server, with one failing circuit and one failing grid point, and the real RainViewer service; no test key or `appid` in the page, its resource URLs or its chart data. `data/weather_log.csv` was restored after the fake run.

Not verified yet: the real API and key, real wind-grid values, real phones. Maps only paint while the Chrome window is in front, which is normal browser throttling, not an app bug.

Known gaps: the bad-city input rubric item cannot be reached from the UI any more; `__lt__` has no caller in the app; the README's MVP section still mentions a radar nowcast the app does not have. `straight_heading_deg` is blank and waiting for Arthur. The collector, `circuits.json` and the main checkout were not touched.

## 3 November 2026 — design round (branch racetrack-mvp-build, not merged)

Built on `b06083d` (the MVP plus Arthur's README rewrite).
- **Look:** a pit-wall look, with flat graphite, green for dry and selection, and red only for rain and failures.
- **Status:** a three-light track-status strip under the header, and one light on each sidebar card.
- **Radar:** framed on the circuit, at zoom 10 to 13.5 from `length_km`. RainViewer's zoom-7 tiles are cropped and enlarged 16 times, bicubic.
- **Wind:** the grid is 17 km apart.
- **Cut:** footnotes, gradients and the header subtitle.
- **Size:** app code is 1,519 lines (1,463 after the MVP round).

Verified without a real key or live OpenWeatherMap call:
- 84 tests pass.
- AppTest with no key.
- Real Chrome at 1280 and 390 px against a throwaway fake server (one dry circuit, one wet, one failing, one failing grid point) and the real RainViewer service.
- Contrast is AA for text and muted text, and keyboard focus is visible on the sidebar cards.

Not verified yet: the real API and key, real phones, and a fresh key search (unchanged code path, last searched in the MVP round).

Watch: a cold start now makes 45 OpenWeatherMap calls (18 current, 18 forecast, 9 wind), against 60 per minute on the free key, shared with the collector.

`data/weather_log.csv` still has 18 real, uncommitted rows from the orchestrator's live check at 07:50 UTC. They were left as they were.

Still open from the MVP round: the bad-city rubric gap, `__lt__` without a caller, and blank `straight_heading_deg`.

## 3 November 2026 — track map round (branch racetrack-mvp-build, not merged)

Built on `cdf10d4`.
- **Outlines:** every circuit's outline is drawn on the radar map and framed to fill it, and drawn faintly on the wind map. The files are in `data/tracks/`: 9 from f1-circuits (MIT), 9 from OpenStreetMap (ODbL), all 18 checked against their circuits.
- **Header and lights:** the header's chance of rain and the next-3-hours light now share one definition.
- **History:** the wind chart has no gusts line.
- **Cloud band:** smoothed.
- **Size:** app code is 1,644 lines.

Verified without a real key or live OpenWeatherMap call: 98 tests pass; real Chrome at 1280 px (Spa, Le Mans, the Nordschleife, Silverstone) and 390 px (Portimão) against a throwaway fake server and the real RainViewer service.

Not verified yet: the real API and key, and real phones.

`data/weather_log.csv` holds 36 real, uncommitted rows from the orchestrator's live checks, left as they were. Still open: the bad-city rubric gap, `__lt__` without a caller, a blank `straight_heading_deg`, and the 45-call cold start.

## 3 November 2026 — sessions and legibility round (branch racetrack-mvp-build, not merged)

Built on `6be16b3`.
- **Track:** a dropdown at the top picks the track (`?track=`), and only that track is fetched (11 calls).
- **Sidebar:** my sessions for that track, each with a status light. They can be added, filled with the default weekend, and edited in place; the selected one shows as a band on the charts. Sessions are saved in git-ignored `data/sessions.csv`.
- **Today:** three groups, with one shared-time-axis forecast figure and direct labels.
- **Wind map:** framed like the radar, with an interpolated 5×5 arrow field.
- **Less text:** the Today page's visible text elements went from 67 to 34.
- **Size:** app code is 1,882 lines.

Verified without a real key or live OpenWeatherMap call:
- 110 tests pass.
- AppTest with no key.
- Real Chrome against a throwaway fake server (dry Portimão, wet Spa) at a 1280 px window, a 500 px real window and 390 px emulation: sessions added, edited and highlighted; no key in the page.

Not verified yet: the real API and key, and real phones.

The README screenshots in `docs/screenshots/` show the previous design and should be retaken with real data.

`data/weather_log.csv` has 54 real, uncommitted rows from the orchestrator's live checks, left as they were. Still open: the bad-city rubric gap, `__lt__` without a caller, and a blank `straight_heading_deg`.

## 3 November 2026 — colour and history round (branch racetrack-mvp-build, not merged)

Built on `cc1daa0`.
- **Colour:** colour now encodes data. One cool-to-warm temperature scale (no green or red) colours the header, the forecast line and the History ranges; wind is violet, brighter when stronger.
- **Glyphs:** condition glyphs (SVG data URIs) sit in the header and above each forecast day.
- **Rain bars:** red only when rain is likely.
- **History:** one row per collected day (rain dot, low-to-high range, wind with its direction), partial days muted, one sentence.
- **Sessions:** the form picks days as "Fri 7 Nov"; the selected session is one block across both charts.
- **Size:** app code is 2,061 lines.

The flat stretches in Le Mans's History were a frozen OpenWeatherMap value at that point (8.87 °C at La Sarthe, 8.8 °C at Bugatti, both with 1.34 m/s from 230°), in about a quarter of the readings, mostly overnight. It is kept as collected; filtering is Arthur's decision.

Verified without a real key or live OpenWeatherMap call:
- 117 tests pass.
- Real Chrome at 1280 and 390 px against a throwaway fake server (dry Portimão, wet Spa), plus History at Le Mans and Spa.
- Contrast checked.
- No key in the page.

Not verified yet: the real API's condition codes and real phones.

`data/weather_log.csv` (real, uncommitted) and the git-ignored `data/sessions.csv` come from the orchestrator's live checks and were left as they were. The README screenshots still show an older design.

## 3 November 2026 — polish round (branch racetrack-mvp-build, not merged)

Built on `40d3454`.
- **Stuck readings:** History drops them (3 or more in a row with the same temperature, wind speed and direction keep only the first), so 86 of 2,971 readings leave the analysis. `data/current_weather.csv` is unchanged.
- **Thin days:** days with fewer than 12 hours are hidden.
- **Wind:** a 3×3 field of large arrows.
- **Temperature:** the scale now has a stop every 5° from -5° to 30°.
- **Screenshots:** the README shows current screenshots from a fake-data run.
- **Size:** app code is 2,111 lines.

Verified without a real key or live OpenWeatherMap call: 124 tests pass; real Chrome at a 1280 px window and 390 px emulation, cold and warm cases.

Not verified yet: real API data and real phones.

`data/weather_log.csv` (real, uncommitted) and the git-ignored `data/sessions.csv` come from the orchestrator's live checks and were left as they were.

## 5 November 2026 — light mode (branch racetrack-mvp-build, not merged)

Built on `783ef1c`.
- **Themes:** Streamlit's menu offers System, Light and Dark. Dark is unchanged. Light has warm paper, white panels, graphite text, a darker green and red, darker temperature and wind colours, and the pale CARTO map with a dark outline.
- **One source:** `theme.py` holds one dictionary per theme with the same keys; CSS, charts, glyphs and maps read from it.
- **Default:** System, so a device set to light opens light. Streamlit 1.66 has no setting to start on Dark when it offers both themes.
- **Switching:** Streamlit repaints its own colours at once; the app's panels, charts and maps follow at the next rerun (any click, or a reload). Panels stay readable in between.
- **Size:** app code is 2,190 lines.

Verified without a real key or live OpenWeatherMap call: 132 tests pass; real Chrome against the fake server, Today and History, both themes, at a 1280 px window and 390 px emulation, with no sideways scroll; the switch from the menu and the rerun after it.

Not verified yet: real API data and real phones.

`data/weather_log.csv` (real, uncommitted) and the git-ignored `data/sessions.csv` were left as they were. The README screenshots show the dark theme.
