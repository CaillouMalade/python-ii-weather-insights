# Racetrack Weather (development)

Python II group assignment: an object-oriented Streamlit app for racetrack weather, built on OpenWeatherMap. This is the technical README for the `dev` branch: what we are building, how we work, and the checklist of cards. The user README for `main` is written at the end.

## Why this app

When racing on a track, weather plays a massive role, and three factors basically drive everything:

- **Temperature:** it has a big influence on how well we can use the tyres and on overheating, so if the temperature evolves quickly during a session it can completely change our strategy (for instance in qualifying, if we can see it gets colder later, it's in our best interest to wait for maximum performance).
- **Rain:** obviously it matters a massive amount, and having a precise idea of when it's going to rain is extremely important. The main issue we encounter is that the different weather apps on our phones or the radars often give conflicting information, and it's always difficult to compare them and to know which one to trust.
- **Wind:** the cars rely on aerodynamics, so wind in a certain direction in a corner can massively influence the car and even be a cause for errors, hence having an idea of the wind strength and direction is just as important.

Knowing that, the idea is a weather app that aggregates several APIs, so instead of giving one ungrounded likelihood of rain, we give the statistical likelihood of rain and wind with more detail, on top of the wind over the track map and the rain radar. It's an MVP (we will need more granularity later), but that's the main idea.

## How it works

Race weekends usually follow the same format and timing, so for now the session times are hardcoded, and being able to change the session hours comes later as polish. The app has four views:

1. **Weekend overview (main dashboard):** the mechanics need to prepare the car's setup a few days before, so we need the whole weekend at a glance. For instance, if we can see that tomorrow is going to rain, we need to test a few different setups, since the car is set up differently in the wet than for maximum performance in the dry.
2. **Session dashboard:** more granular, per-session information.
3. **History:** what usually happens on a given track, the temperature range and how variable things are over that particular circuit. That's a really important metric because it tells us how much we can trust the forecast there.
4. **Track comparison:** it's always interesting to compare different tracks over the same period and see how they differ rain-wise, temperature-wise and wind-wise (no track map needed here).

## What the app should do

A user can:
1. Pick a track from the list in the sidebar.
2. Add a track by typing a name, latitude and longitude. It is saved only if it lies within 3 km of an FIA Grade 1 circuit; otherwise the app says so.
3. See the weekend's session times (FP1, FP2, FP3, Qualifying, Race), fixed for now.
4. **Weekend overview:** see the weather now at that track (temperature, feels like, rain, wind strength and direction), the next 5 days on one chart (temperature °C, rain mm, wind km/h), and the rain radar on a map around the track.
5. **Session dashboard:** go through the sessions one by one and see, for each, the temperature, chance of rain and wind strength and direction during that session.
6. See how sure the forecast is: the average of three providers with a 95% confidence interval.
7. **History:** see what usually happens at a track, from our own logged data: rain, temperature range and how variable the weather is there.
8. **Track comparison:** compare two tracks over the same period, with a short summary of each (average temperature, rain days, total rain).
9. Get a clear message, never a crash, when the input is wrong, the key is bad, the network is down or a provider fails. The rest of the app keeps working.

Every successful fetch is logged with a timestamp to a CSV that grows over time and is committed with the repo.

Temperatures are air temperatures. Track (surface) temperature is measured by the race engineers on track and is not part of this MVP.

## Setup

Requires Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/CaillouMalade/python-ii-weather-insights.git
cd python-ii-weather-insights
git switch dev
uv sync
cp variables.env.example variables.env        # Windows PowerShell: Copy-Item variables.env.example variables.env
```

Put your own OpenWeatherMap key in `variables.env`. Git ignores this file; never commit a key.

```bash
uv run streamlit run app.py     # run the app
uv run pytest                   # run the tests (no key, no API calls)
```

## How we work

- Take a card from the checklist, work on your own branch from `dev`, and open a pull request into `dev`. Arthur merges.
- If you use an AI coding agent, it reads `AGENTS.md` (Claude Code reads it through `CLAUDE.md`): it will explain before and after coding and keep the code to what we saw in class.
- Commit from your own GitHub account.
- Keep it simple enough that anyone in the group could explain every line. Use what we saw in class.
- Run `uv run pytest` before pushing, and add tests for what you build.
- If an AI agent helps, add an entry to `PROMPTS.md` (what you asked, what you got, what you kept or changed) and the co-author trailer on that commit, e.g. `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Checklist

Pick an unticked card whose "needs" are done, put your name on it, and tick it when it's merged. Feature freeze Tue 17 Nov; after that, only the refactor, polish and fixes.

- [x] **0. Setup** (Arthur): shared `ForecastPoint` shape, fake forecast in `tests/`, this README.
- [x] **1. Track list** (Arthur): `data/grade1_tracks.csv` holds the 16 FIA Grade 1 circuits in EU countries (one point near the centre of each track).
- [ ] **1b. Logo** (Arthur): add the logo picture.
- [ ] **Everyone added to the repo and on a card.**
- [ ] **2. OpenWeatherMap client and errors** (needs 0, owner: ): the current weather and the 5-day forecast for a track, with the forecast as a list of `ForecastPoint`. A bad input, a bad key, a missing location, a timeout, no connection, a server error and an unreadable answer each give their own message. Done when each failure has a test with a fake response.
- [ ] **3. More providers** (needs 0, owner: ): Open-Meteo and MET Norway (both free, no key; MET Norway asks for a User-Agent header naming the app) as subclasses of `APIClient`, each returning `ForecastPoint`s on the same 3-hour UTC windows as OpenWeatherMap: convert units, sum hourly rain over each window, take temperature and wind at the window start. A provider that fails is skipped with its own message. Done when all three return the same windows for one track, with a test per provider on a saved sample answer.
- [ ] **4. Sidebar** (needs 1, owner: ): pick a track, see the fixed session times and the logo, and add a track with a name, latitude and longitude. Check them first (name not empty or already used, latitude −90 to 90, longitude −180 to 180), accept the track only within 3 km of a circuit in `grade1_tracks.csv`, otherwise say "No racetrack found at these coordinates", and save accepted tracks to `data/my_tracks.csv`. Done when every check has its own message and a test.
- [ ] **5. History and track comparison** (needs nothing, owner: ): from `data/current_weather.csv`, the rain history of the selected track (rain per day, mm, temperature range and how variable it is), and two tracks side by side over the same period, ranked with `sorted()`, with a one-line f-string summary for each (average temperature, rain days, total rain, over how many days we logged). Each with a chart with units. Done when both run on the committed data, with tests on a small slice of it.
- [ ] **6. Statistics** (needs 0, owner: ): for each 3-hour window, combine the three providers: mean temperature, wind and rain with a 95% confidence interval, and how many providers predict rain. Build it on `tests/fake_forecast.py` first. Done when the numbers are tested on the fake forecast.
- [ ] **7. Weekend overview** (needs 0, then 2 + 6, owner: ): the main page for the selected track: the weather now, one 5-day chart (temperature °C, rain mm, wind km/h) with the confidence interval and the session times marked, wind strength and direction, and the RainViewer radar on a map around the track. Fake forecast first, then the real one.
- [ ] **8. Session dashboard** (needs 0, then 2 + 6, owner: ): one session at a time, with previous and next buttons. For that session's window: temperature, chance of rain and wind strength and direction, per provider and combined with the confidence interval, plus a small chart. A session beyond OpenWeatherMap's 5 days uses the providers that reach it, or says "No forecast yet".
- [ ] **9. Live check** (needs 2 + 3, owner: ): with the real key, each error message, a failing provider, adding a good and a bad track. Fix what breaks.
- [ ] **Walkthrough (Mon 16 Nov):** each of us explains our card to the group.
- [ ] **10. Refactor (Tue 17 Nov, feature freeze)** (needs 2–8): move functions to where they belong, remove duplicates and unused code, make names consistent. Tests pass before and after.
- [ ] **11. Polish (Wed 18 Nov)** (needs 10): cosmetic upgrades only: layout and spacing, colours, titles and labels, empty and loading states, the logo, and anything an outsider found confusing.
- [ ] **12. Finish (Thu 19 Nov)** (Arthur, needs 11): user README for `main`, fresh data commit, clean-clone test, merge `dev` into `main`.
- [ ] **Submitted (Fri 20 Nov).**

Later, only if there's time after card 10: wind arrows over the track map, changing the session times, adding your own sessions, a settings view to choose providers.

## Data sources

Weather: [OpenWeatherMap](https://openweathermap.org), [Open-Meteo](https://open-meteo.com), [MET Norway](https://api.met.no). Radar: [RainViewer](https://www.rainviewer.com).

## Team

To be filled in with each member's contribution.
