# Roadmap

How we finish the project: what the rubric still needs, the order to build things in, and who owns which part.

The submission is the weather app on `main`. `racetrack-simple` (the racetrack version) and `data-collection` (the collector) are separate apps on their own branches.

## 1. Rubric status

Status of `main` on 10 November 2026. ✅ met, ⚠️ partly met, ❌ not met.

| Rubric item | Pts | Status | What is left |
|---|---:|---|---|
| Inheritance for a real shared behaviour | 0.5 | ✅ | `APIClient` → `WeatherClient` |
| public / `_protected` / `__private` | 0.5 | ✅ | `__api_key`, `_get`, `_not_found_message` |
| Special method used meaningfully | 0.5 | ✅ | `__lt__` drives the ranking; `__repr__`, `__str__` |
| `@property` | 0.5 | ✅ | `wind_kmh`, `feels_like_gap` |
| Key from env, never exposed | 0.5 | ✅ | Re-check before submitting: no key in the UI, logs or git history |
| Distinct errors: bad input / key / location / network | 0.5 | ✅ | Tested with fakes, **not yet with the real API** |
| Multi-location fetch skips failures | 0.5 | ✅ | `fetch_many` |
| Input validated before the API call | 0.5 | ✅ | `validate_city` |
| Real data logged with timestamps, **accumulating over time** | 0.5 | ⚠️ | Only 52 rows, all from 2 Nov. The log must grow over days. |
| 3 analytical views across 2+ categories | 1 | ✅ | Trend, comparison, daily range and feels-like gap |
| Analytics on real logged data | 0.5 | ⚠️ | Correct, but the data is thin, so the trend and daily range show little |
| Runs cleanly with 2+ views | 0.5 | ⚠️ | Checked with Streamlit's test runner only, never with a real key |
| Meaningful interaction | 0.5 | ✅ | Pick cities, add a city, pick the trend city |
| 2+ labelled charts with units | 0.5 | ✅ | Live bar chart, trend line and comparison bars (°C) |
| Usability for a stranger | 0.5 | ⚠️ | Works, but plain: no short explanations, no forecast |
| `src/` package, `pyproject.toml`, README, no secrets | 0.5 | ✅ | Final clean-clone check before submitting |
| PROMPTS.md specific and consistent; co-author trailers | 0.5 | ✅ | Keep it going: one entry per feature, by whoever asked the AI |
| Commits from every member | 0.5 | ❌ | All commits are Arthur's so far |
| Everyone can explain any part | 0.5 | ❌ | Team walkthrough of every module |

Submission checklist: the repo is public, so the instructor can already see it. Confirm the submission channel, commit the final log, and fill in the README's Team section.

## 2. Path to a good app

Small steps, one feature at a time. Each step is a pull request into `dev`, with tests and a PROMPTS.md entry.

1. **Live check.** Run `main` with a real key: every error message, adding a city, two runs 10 minutes apart. Fix whatever breaks.
2. **Grow the log.** Open the app every day with all cities selected (a 10-minute cache means one row per city per visit), or add a small `tools/log_now.py` that uses `WeatherClient` and `append_reading` for the 12 cities. Aim for 10+ days before submitting.
3. **Forecast view.** Add `WeatherClient.forecast()` (5-day / 3-hour) and a forecast chart for one city on Live conditions. This is the most useful thing a real user wants.
4. **One more derived metric.** For example a `comfort_index` property on `WeatherReading` (temperature, humidity and wind), shown in the ranking.
5. **Better trends.** Daily average per city and a date-range filter on Analytics, once the log has several days.
6. **Usability pass.** One-line explanations under each chart, clear empty states, and a "last updated" time.
7. **Finish.** README screenshots, the Team section, a clean-clone test following only the README, and the walkthrough.

## 3. Modules and branches

`main` holds only what is submitted. `dev` is where work comes together. Each module is a branch off `dev`, merged back by pull request. The modules match files, so people rarely edit the same file.

| Branch | Role | Files | First tasks (path step) |
|---|---|---|---|
| `feature/api` | API and OOP | `client.py`, `models.py`, `tests/test_client.py`, `tests/test_models.py` | Live check (1), `forecast()` (3), `comfort_index` (4) |
| `feature/data` | Data and logging | `storage.py`, `fetching.py`, `tools/`, `data/` | `tools/log_now.py` and the daily log (2), log sanity checks |
| `feature/analytics` | Analytics | `analytics.py`, `tests/test_storage_and_analytics.py` | Daily averages and date filter (5), comfort ranking (4) |
| `feature/ui` | Streamlit app | `app.py` | Forecast chart (3), usability pass (6), screenshots (7) |
| `docs` (no branch) | Docs and submission | `README.md`, `PROMPTS.md`, `ROADMAP.md` | Team section, walkthrough notes, submission checklist (7) |

Rules for everyone:
- Commit your own work from your own GitHub account, so the history shows every member.
- When an AI agent writes code, add its co-author trailer to the commit and a PROMPTS.md entry: what you asked, what you got, and what you kept, changed or rejected.
- Run `uv run pytest` before every pull request.
- `dev` goes into `main` at the end of each path step.
