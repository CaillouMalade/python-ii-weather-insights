# Weather Insights - Quick Reference

This project draws on everything from Sessions 1-16. This is not new material — it's a map of where to look
things up again.

## 1. API client with inheritance

A base class that knows *how* to call any JSON API; a subclass that knows *which* API and fields.

```python
class APIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self._api_key = api_key

    def _get(self, endpoint, params):
        response = requests.get(f"{self.base_url}/{endpoint}", params=params)
        if response.status_code != 200:
            raise ValueError(f"Request failed with status {response.status_code}")
        return response.json()


class WeatherClient(APIClient):
    def __init__(self, api_key):
        super().__init__("https://api.openweathermap.org/data/2.5", api_key)

    def current(self, city):
        params = {"q": city, "appid": self._api_key, "units": "metric"}
        return self._get("weather", params)
```

See [`s10_inheritance_special_methods`](../class_material/s10_inheritance_special_methods) and
[`s13_oop_apis_practice`](../class_material/s13_oop_apis_practice) for the full versions of this pattern.

## 2. Encapsulation convention

| Prefix | Convention | Enforced by Python? | Use for |
|---|---|---|---|
| `name` | Public | No | Anything callers are meant to use directly |
| `_name` | Protected | No (convention only) | Internal helpers a subclass may still need |
| `__name` | Private (name-mangled) | Partially — rewritten to `_ClassName__name` | State that should only ever be touched from inside the class |

Full explanation and runnable examples of calling each from outside the class:
[`s13_oop_apis_practice`](../class_material/s13_oop_apis_practice), Section 3.2.

## 3. Special methods and properties

```python
class LocationSnapshot:
    def __init__(self, city, temperature, humidity, wind_speed):
        self.city = city
        self.temperature = temperature
        self.humidity = humidity
        self.wind_speed = wind_speed

    @property
    def comfort_index(self):
        return self.temperature - (self.wind_speed * 0.5) - max(0, self.humidity - 60) * 0.1

    def __repr__(self):
        return f"LocationSnapshot({self.city!r}, {self.temperature}°C)"

    def __lt__(self, other):
        return self.temperature < other.temperature


snapshots = [LocationSnapshot("Madrid", 22, 40, 10), LocationSnapshot("Oslo", 4, 70, 20)]
sorted(snapshots)  # works because __lt__ is defined
```

## 4. Environment variables for the API key

Same convention as `s07_apis`, `s08_practice_apis`, and `s13_oop_apis_practice` — a `variables.env` file,
loaded with `python-dotenv`, never committed.

```python
from dotenv import load_dotenv
import os

load_dotenv("variables.env")
API_KEY = os.getenv("OPENWEATHER_API_KEY")
```

## 5. Specific error handling

```python
if response.status_code == 404:
    raise ValueError(f"City '{city}' was not found")
if response.status_code == 401:
    raise ValueError("Invalid or inactive API key")
if response.status_code != 200:
    raise ValueError(f"OpenWeatherMap returned status {response.status_code}")
```

Skip-and-continue over a batch (don't let one bad location kill the whole fetch):

```python
results = []
for city in city_names:
    try:
        results.append(WeatherClient(API_KEY).current(city))
    except ValueError as e:
        print(f"Skipping '{city}': {e}")
```

## 6. Building your own time series

The free OpenWeatherMap tier only gives current conditions. To analyze a trend, log every successful fetch
yourself, with a timestamp (see `s02_datetimes_timeseries`):

```python
import csv
from datetime import datetime, timezone

def log_snapshot(path, city, temperature, humidity, wind_speed):
    with open(path, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now(timezone.utc).isoformat(), city, temperature, humidity, wind_speed])
```

## 7. Streamlit multi-view app

```python
import streamlit as st

page = st.sidebar.radio("View", ["Live Conditions", "Analytics"])

if page == "Live Conditions":
    ...
elif page == "Analytics":
    ...
```

See [`s14_intro_to_streamlit`](../class_material/s14_intro_to_streamlit) for widgets, layout, and charts.

## 8. Packaging as a local library

```
your-repo/
├── pyproject.toml
├── src/
│   └── weather_app/
│       ├── __init__.py
│       ├── client.py
│       ├── models.py
│       ├── storage.py
│       └── analytics.py
├── app.py
└── tests/
```

Same `src/` layout as [`weather-tools`](../class_material/s16_custom_libraries/weather-tools) from Session 16.

## 9. Logging AI-agent collaboration

For each feature you ask an agent to help with, add an entry to `PROMPTS.md`:

```markdown
## Feature: multi-city comparison view

**Asked:** "Write a function that ranks a list of LocationSnapshot objects by comfort_index and returns the
top 3 and bottom 3."

**Got:** `rank_by_comfort(snapshots, n=3)` in `src/weather_app/analytics.py`.

**Checked:** ran it on 5 hand-made snapshots with known comfort scores, confirmed the ranking matched.

**Kept as-is.**
```

And tag the commit:

```
feat: add comfort-index ranking view

Co-Authored-By: Claude <noreply@anthropic.com>
```
