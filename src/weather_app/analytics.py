"""Analyses. The log ones take the log DataFrame and return a small DataFrame."""


def rank_by_temperature(readings):
    """Return the readings warmest first. sorted() works because WeatherReading defines __lt__."""
    return sorted(readings, reverse=True)


def city_trend(log, location):
    """Trend over time: one city's readings in time order."""
    rows = log[log["location"] == location]
    return rows.sort_values("timestamp_utc")[["timestamp_utc", "temperature", "feels_like"]]


def city_comparison(log):
    """Cross-location comparison: average, lowest and highest logged temperature per city, warmest first."""
    summary = log.groupby("location")["temperature"].agg(["mean", "min", "max", "count"]).reset_index()
    summary.columns = ["location", "average", "lowest", "highest", "readings"]
    return summary.sort_values("average", ascending=False).reset_index(drop=True)


def daily_range(log):
    """Derived metric: for each city and UTC day, the highest minus the lowest logged temperature.

    Days with a single reading are left out, because their range would always be 0.
    """
    log = log.copy()
    log["day"] = log["timestamp_utc"].dt.date
    days = log.groupby(["location", "day"])["temperature"].agg(["min", "max", "count"]).reset_index()
    days = days[days["count"] >= 2]
    days["range"] = days["max"] - days["min"]
    return days[["location", "day", "range"]].reset_index(drop=True)


def feels_like_gap(log):
    """Derived metric: on average, how much colder (negative) or warmer it felt than the real temperature."""
    log = log.copy()
    log["gap"] = log["feels_like"] - log["temperature"]
    gaps = log.groupby("location")["gap"].mean().reset_index()
    return gaps.sort_values("gap").reset_index(drop=True)


def track_rain_history(history, location_id):
    """Return daily rain totals and temperature range for one track ID."""
    track = history[history["location_id"] == location_id].copy()
    track["day"] = track["timestamp_utc"].dt.date
    daily = track.groupby("day").agg(
        temperature_min_c=("temperature", "min"),
        temperature_max_c=("temperature", "max"),
        temperature_mean_c=("temperature", "mean"),
    ).reset_index()
    rain_by_day = track.groupby("day")["rain"].sum(min_count=1).reset_index(name="rain_mm")
    daily = daily.merge(rain_by_day, on="day")
    daily["temperature_range_c"] = daily["temperature_max_c"] - daily["temperature_min_c"]
    return daily.sort_values("day").reset_index(drop=True)


def compare_track_history(history, location_ids):
    """Summarize two tracks over their logged data and rank them by average temperature."""
    summaries = []
    for location_id in location_ids:
        track = history[history["location_id"] == location_id].copy()
        if len(track) == 0:
            continue
        track["day"] = track["timestamp_utc"].dt.date
        daily_rain = track.groupby("day")["rain"].sum(min_count=1)
        summaries.append({
            "location_id": location_id,
            "location": track["location"].iloc[0],
            "average_temperature_c": track["temperature"].mean(),
            "rain_days": int((daily_rain > 0).sum()),
            "total_rain_mm": track["rain"].sum(min_count=1),
            "days_logged": int(track["day"].nunique()),
        })
    return sorted(summaries, key=lambda summary: summary["average_temperature_c"], reverse=True)
