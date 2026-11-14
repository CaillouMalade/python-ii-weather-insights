"""Asks every forecast provider for the same location and puts the answers in one table."""

import pandas as pd

# One row per provider and 3-hour window; "source" says which provider it came from.
FORECAST_COLUMNS = ["source", "time_utc", "temperature", "wind_speed", "wind_deg", "rain"]


def points_to_frame(points):
    """Turn a list of ForecastPoints into a DataFrame with one row per point."""
    rows = []
    for point in points:
        rows.append({
            "source": point.source,
            "time_utc": point.time_utc,
            "temperature": point.temperature,
            "wind_speed": point.wind_speed,
            "wind_deg": point.wind_deg,
            "rain": point.rain,
        })
    # Giving the columns keeps the table's shape even when no provider answered.
    return pd.DataFrame(rows, columns=FORECAST_COLUMNS)


def fetch_all_forecasts(location, providers, now=None):
    """Ask every provider for a forecast and return (table, failure messages).

    A provider that fails is skipped and its message kept, so the others still load.
    """
    all_points = []
    failures = []
    for provider in providers:
        try:
            points = provider.forecast(location, now)
        except ValueError as error:
            failures.append(f"{provider.source}: {error}")
            continue
        all_points.extend(points)
    return points_to_frame(all_points), failures
