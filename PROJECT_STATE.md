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
