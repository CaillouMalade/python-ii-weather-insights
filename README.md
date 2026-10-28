# Weather Insights

Python II group assignment: an object-oriented weather analytics application using OpenWeatherMap and Streamlit. This repository is initialized from the supplied scaffold; the application features and analytics remain to be implemented.

The original [assignment brief](assignment/BRIEF.md), [course reference](summary.md), and [supplied template](starter_template/) are preserved for reference. Develop the application in the root `src/`, `tests/`, and `app.py` files.

## Setup

Requires Python 3.11 or newer and uv. Run these commands from the repository root:

```bash
uv sync
```

Copy `variables.env.example` to `variables.env`, then fill in your own OpenWeatherMap key. On Windows PowerShell:

```powershell
Copy-Item variables.env.example variables.env
```

On macOS/Linux:

```bash
cp variables.env.example variables.env
```

`variables.env` is ignored by Git. Never commit or display a real key.

## Run the app

```bash
uv run streamlit run app.py
```

The supplied app currently contains two placeholder views: Live Conditions and Analytics. It does not fetch or log weather data yet.

## Run the tests

```bash
uv run pytest
```

The supplied test is a placeholder, not evidence of working weather analytics.

## Project structure

- `pyproject.toml` and `uv.lock` define the installable package and dependencies.
- `src/weather_app/` contains the supplied client, model, storage, analytics and configuration modules.
- `app.py` is the Streamlit entry point.
- `tests/` contains the supplied test scaffold.
- `variables.env.example` documents the environment variable to configure locally.
- `PROMPTS.md` records AI collaboration.

## Team

Add group members and their actual contributions as work progresses.
