# Weather Insights: group capstone project

Your group will build a small but real software project: an **object-oriented Python application** that
pulls live data from the [OpenWeatherMap API](https://openweathermap.org/api), turns it into **analytics that
are actually useful** (not just a number on a page), and presents it through a **Streamlit** web app. You will
work in a shared **GitHub repository**, using an AI coding agent as a collaborator the way you've used Claude
throughout this course — and you will document that collaboration the same way your work is documented: as
part of the repo's history, not as a separate essay.

This is a capstone: it combines almost everything from PDA2 — APIs, error handling, OOP (classes, inheritance,
encapsulation, special methods), datetimes, and Streamlit — into one project you design yourselves.

See [`summary.md`](summary.md) for a quick reference of the concepts this project draws on, and
[`starter_template/`](starter_template) for a ready-to-use project scaffold (packaging, `.env` loading,
folder layout) your group can copy into its own repo so you can start on the actual design work right away.

## The brief

"Analytics in any shape that is useful" is intentionally open — you choose what story your app tells and how
it tells it. But every submission must meet the **minimum requirements** below. Think of these as the floor,
not the ceiling: a group that does exactly the minimum, correctly, passes; a group that builds something a
real user would actually want to open gets the higher grades.

### 1. Object-oriented design

- **Inheritance, used for a real reason.** At minimum, a base class that knows how to call a JSON API
  generically (handle the request, check the status code, raise on failure) and a subclass specific to
  OpenWeatherMap that knows the actual endpoint and fields. Don't inherit just to tick a box — the base
  class should capture behavior that a *different* weather or data provider could also reuse.
- **Encapsulation applied with intent.** Use the public / `_protected` / `__private` convention correctly
  (see [`s11_advanced_oop`](../class_material/s11_advanced_oop) and
  [`s13_oop_apis_practice`](../class_material/s13_oop_apis_practice)) — public attributes for what callers
  need, `_protected` for internal helpers subclasses may still touch, `__private` only where name-mangling
  genuinely protects something.
- **At least one special method** beyond `__init__` — `__str__`/`__repr__` at minimum, and ideally something
  that makes your objects more useful in Python itself (`__eq__`, `__lt__` so locations can be `sorted()` by
  temperature, etc.).
- **At least one `@property`** where it makes sense (e.g. a computed value derived from stored attributes,
  not just a renamed attribute).

### 2. API integration and robustness

- The API key is read from an environment variable via `python-dotenv` (`variables.env`, never hardcoded,
  never committed, never shown in the UI).
- **Specific error handling per failure mode** — a bad city name, an invalid/expired key, and a network or
  server error should each produce a clear, distinct message, not a raw traceback. No bare `except:`.
- Fetching data for **multiple locations** must degrade gracefully — one bad location should not stop the
  rest from loading (same pattern as the batch loop in `s13_oop_apis_practice`).
- Basic input validation before calling the API (empty string, obviously invalid input).

### 3. Data and analytics

OpenWeatherMap's free tier gives you *current* conditions, not history — so to analyze anything "over time"
your app has to **build its own dataset** by logging what it fetches.

- Every successful fetch is appended to a local data file (CSV or SQLite) with a timestamp — this is your own
  mini time series, and it should accumulate as your group tests the app over the following days/weeks.
- Your app must implement **at least three distinct analytical views**, drawing on at least two of these
  categories:
  - **Trend over time** for at least one location, using your own logged history.
  - **Cross-location comparison** (ranking, sorting, highlighting extremes among tracked locations).
  - **A derived/computed metric** that the API does not return directly — e.g. a simple comfort index from
    temperature + humidity + wind, a "feels colder/warmer than actual" delta, a daily range.
- Analytics must run on real fetched/logged data, not hardcoded or fabricated numbers.

### 4. Streamlit app

- At least **two views** (e.g. "Live Conditions" and "Analytics") — a single page dumping everything is not
  enough.
- Meaningful user interaction: adding/selecting locations, not just static output.
- At least **two charts**, labeled with units, built from real data.
- The API key must never appear in the UI, in `st.write`/print output, or in the repo.

### 5. Repository, packaging, and AI collaboration

- A real **GitHub repository**, structured as an installable local package (`src/` layout, `pyproject.toml`)
  the way [`weather-tools`](../class_material/s16_custom_libraries/weather-tools) did in Session 16 — not one
  giant script.
- **Commit history from every group member.** A repo with one commit from one person does not show group
  work, regardless of who wrote the README.
- A `PROMPTS.md` log at the repo root: for each feature or class you asked an AI agent to help with, record
  what you asked, what it produced, and what you kept / changed / rejected and why. Keep this file running —
  don't write it retroactively from memory.
- Any commit where an AI agent substantially authored the code must carry a co-author trailer, exactly the
  way this course's own repository does it:
  ```
  Co-Authored-By: Claude <noreply@anthropic.com>
  ```
  (or the equivalent for whichever tool/model your group used — name it).
- A top-level `README.md` in your submitted repo (not this one) with setup instructions, how to run the app,
  and a short description of what your app does.

## What to submit

Submit the **URL of your group's GitHub repository**. Make sure:

- the repo is either public, or private with the instructor added as a collaborator (confirm the exact
  submission channel — Blackboard / email / other — with the instructor);
- it runs from a clean clone following only your own `README.md` instructions;
- `variables.env` (or any file holding a real API key) is **not** committed — only the course `.gitignore`
  pattern or your own `.env.example` should be;
- the data log file your app has been building *is* committed, so the grader can see real accumulated history,
  not an empty database.

## Grading rubric (10 points)

Graded by cloning the repo fresh and running it. Points are awarded in **0.5-point increments** — partial,
correct work earns partial credit; a missing or broken piece loses credit only for that piece, not the whole
project.

| Criterion | Points | What earns the points |
|---|---:|---|
| **OOP design** | **2** | **0.5**: inheritance used for a genuine shared behavior. **0.5**: public/`_protected`/`__private` applied correctly and deliberately. **0.5**: at least one special method beyond `__init__` used meaningfully. **0.5**: at least one `@property` used where appropriate. |
| **API integration & robustness** | **2** | **0.5**: API key via environment variable, never hardcoded or exposed. **0.5**: distinct, specific handling for bad input / bad key / bad location / network failure. **0.5**: multi-location fetches skip failures instead of crashing. **0.5**: user input validated before the API call. |
| **Data & analytics** | **2** | **0.5**: real fetched data is logged with timestamps and accumulates over time. **1**: at least three distinct, correctly computed analytical views spanning at least two categories (trend / comparison / derived metric). **0.5**: analytics run on real logged data, not fabricated numbers. |
| **Streamlit app** | **2** | **0.5**: runs cleanly with at least two views. **0.5**: real, meaningful user interaction. **0.5**: at least two labeled, correct charts. **0.5**: overall usability — a stranger could use it without reading the code. |
| **Repository & AI collaboration record** | **1** | **0.5**: proper `src/` package structure, `pyproject.toml`, working `README.md`, no secrets committed. **0.5**: `PROMPTS.md` is specific and consistent with the commit history, and AI-assisted commits carry the co-author trailer. |
| **Team collaboration evidence** | **1** | **0.5**: commit history shows real contributions from every group member. **0.5**: the group can explain any part of the code when asked — including the parts an agent wrote. |
| **Total** | **10** | |

A failing component (e.g. a broken API call, an empty `PROMPTS.md`, analytics computed on fake numbers) loses
credit only for that row — it does not zero out the rest of the project.
