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
