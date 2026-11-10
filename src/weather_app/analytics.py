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
