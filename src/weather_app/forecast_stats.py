"""Combines the providers' forecasts into one estimate per 3-hour window, with a 95% confidence interval.

The input is the table from fetching.fetch_all_forecasts (one row per provider and window).
The output has one row per window: the mean of the providers, the low and high ends of the
95% confidence interval, and how many providers predict rain.
"""

import pandas as pd

from .models import METRES_PER_SECOND_TO_KMH

# A provider "predicts rain" in a window from 0.1 mm: the smallest amount a rain gauge records,
# so tiny rounding values like 0.01 mm don't count as rain.
RAIN_THRESHOLD_MM = 0.1

# Two-sided 95% t-values by number of providers (degrees of freedom = providers - 1).
# With only 2 or 3 values the normal 1.96 would make the interval look far more certain than it is.
T_VALUES_95 = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78}

# The values we average. Wind is converted to km/h first, because the pages show km/h.
COMBINED_VALUES = ["temperature", "wind_kmh", "rain"]

# These can't go below zero, so the low end of their interval is cut at 0.
NEVER_NEGATIVE = ["wind_kmh", "rain"]

NEEDED_COLUMNS = ["source", "time_utc", "temperature", "wind_speed", "rain"]

RESULT_COLUMNS = [
    "time_utc", "providers",
    "temperature", "temperature_low", "temperature_high",
    "wind_kmh", "wind_kmh_low", "wind_kmh_high",
    "rain", "rain_low", "rain_high",
    "rain_providers",
]


def t_value(providers):
    """Return the 95% t-value for this many providers, or None when there are fewer than 2."""
    if providers < 2:
        return None
    if providers in T_VALUES_95:
        return T_VALUES_95[providers]
    # Above 5 values the t-value is close to the normal one.
    return 1.96


def check_forecast_table(table):
    """Raise ValueError when the table is missing a column the statistics need."""
    missing = []
    for column in NEEDED_COLUMNS:
        if column not in table.columns:
            missing.append(column)
    if missing:
        raise ValueError(f"The forecast table is missing the columns {missing}.")


def add_interval(combined, value):
    """Add <value>_low and <value>_high: mean ± t × standard deviation / √n, for each window."""
    t_values = combined[f"{value}_count"].map(t_value).astype(float)
    margin = t_values * combined[f"{value}_std"] / combined[f"{value}_count"] ** 0.5
    low = combined[value] - margin
    if value in NEVER_NEGATIVE:
        low = low.clip(lower=0)
    combined[f"{value}_low"] = low
    combined[f"{value}_high"] = combined[value] + margin


def combine_forecasts(table):
    """Return one row per 3-hour window: provider means, 95% intervals and how many providers predict rain.

    With a single provider in a window there is nothing to compare, so its interval is left empty (NaN).
    Wind direction is not averaged; the session dashboard shows it per provider.
    """
    check_forecast_table(table)
    if len(table) == 0:
        return pd.DataFrame(columns=RESULT_COLUMNS)

    # Work on a copy so the caller's table is never changed.
    forecast = table.copy()
    forecast["wind_kmh"] = forecast["wind_speed"] * METRES_PER_SECOND_TO_KMH
    forecast["predicts_rain"] = forecast["rain"] >= RAIN_THRESHOLD_MM

    combined = forecast.groupby("time_utc").agg(
        providers=("source", "nunique"),
        temperature=("temperature", "mean"),
        temperature_std=("temperature", "std"),
        temperature_count=("temperature", "count"),
        wind_kmh=("wind_kmh", "mean"),
        wind_kmh_std=("wind_kmh", "std"),
        wind_kmh_count=("wind_kmh", "count"),
        rain=("rain", "mean"),
        rain_std=("rain", "std"),
        rain_count=("rain", "count"),
        rain_providers=("predicts_rain", "sum"),
    ).reset_index()

    for value in COMBINED_VALUES:
        add_interval(combined, value)
    return combined[RESULT_COLUMNS].sort_values("time_utc").reset_index(drop=True)
