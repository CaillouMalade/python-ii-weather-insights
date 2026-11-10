# Roadmap

What the rubric still needs, the order to build things in, and who owns which part.

Branches: `main` is the submitted racetrack app, `dev` is where we work, `data-collection` is the collector (it keeps running), and `weather-legacy` is the general weather app we started from.

## 1. Rubric status

Status of `main` on 10 November 2026. ✅ met, ⚠️ partly met, ❌ not met.

| Rubric item | Pts | Status | What is left |
|---|---:|---|---|
| Inheritance for a real shared behaviour | 0.5 | ✅ | `APIClient` → `WeatherClient` |
| public / `_protected` / `__private` | 0.5 | ✅ | `__api_key`, `_get`, `_not_found_message` |
| Special method used meaningfully | 0.5 | ✅ | `__lt__` drives the ranking; `__repr__`, `__str__` |
| `@property` | 0.5 | ✅ | `wind_kmh`, `feels_like_gap` |
| Key from env, never exposed | 0.5 | ✅ | Re-check before submitting |
| Distinct errors: bad input / key / location / network | 0.5 | ✅ | Tested with fakes, **not yet with the real API** |
| Multi-location fetch skips failures | 0.5 | ✅ | `fetch_many` |
| Input validated before the API call | 0.5 | ✅ | `validate_city` in the "add a place" box |
| Real data logged with timestamps, accumulating | 0.5 | ⚠️ | 6,013 collector readings (29 Oct–6 Nov). Refresh `data/current_weather.csv` from the collector before submitting, and use the app so its own `weather_log.csv` fills up. |
| 3 analytical views across 2+ categories | 1 | ✅ | Trend, comparison, daily range and feels-like gap |
| Analytics on real logged data | 0.5 | ✅ | Collector history plus the app's log |
| Runs cleanly with 2+ views | 0.5 | ⚠️ | Checked with Streamlit's test runner only, never with a real key |
| Meaningful interaction | 0.5 | ✅ | Pick circuits, add a place, pick the trend circuit |
| 2+ labelled charts with units | 0.5 | ✅ | Live bar chart, trend line and comparison bars (°C) |
| Usability for a stranger | 0.5 | ⚠️ | Works, but plain: no rain or forecast, which is what a track day needs |
| `src/` package, `pyproject.toml`, README, no secrets | 0.5 | ✅ | Final clean-clone check |
| PROMPTS.md and co-author trailers | 0.5 | ✅ | Keep it going: one entry per feature, by whoever asked the AI |
| Commits from every member | 0.5 | ❌ | All commits are Arthur's so far |
| Everyone can explain any part | 0.5 | ❌ | Team walkthrough of every module |

Before submitting: confirm the submission channel (the repo is public), commit fresh data, and fill in the README's Team section.

## 2. Path to a good app

One small feature at a time, with tests and a PROMPTS.md entry. `dev` goes into `main` when a step is finished.

1. **Live check.** Run with a real key: every error message, adding a place, two runs 10 minutes apart.
2. **Fresh data.** Copy the collector's latest `current_weather.csv` into `data/` every few days.
3. **Rain.** Log `rain_1h` and show rain per circuit: "wettest circuits" and a rain column in Live conditions.
4. **Forecast.** `WeatherClient.forecast()` and a 5-day forecast chart for one circuit, with the chance of rain.
5. **Track-day metric.** A derived score per circuit (for example dry, mild and calm), used to rank circuits.
6. **Usability pass.** One-line explanations under each chart, clear empty states, and the local time per circuit.
7. **Finish.** README screenshots, the Team section, a clean-clone test and the walkthrough.

## 3. Who owns what

Everyone works on `dev`. The modules follow the files, so people rarely edit the same file at once.

| Module | Files | Path steps |
|---|---|---|
| API and OOP | `client.py`, `models.py`, their tests | 1, 4 |
| Data | `storage.py`, `fetching.py`, `data/` | 2, 3 |
| Analytics | `analytics.py`, its tests | 3, 5 |
| App | `app.py` | 4, 6, 7 |

Rules for everyone:
- Commit your own work from your own GitHub account.
- When an AI agent writes code, add its co-author trailer and a PROMPTS.md entry.
- Run `uv run pytest` before pushing.
