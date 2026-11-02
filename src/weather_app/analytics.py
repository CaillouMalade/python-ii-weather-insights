"""Small analytics functions: each takes the log DataFrame and returns a new DataFrame."""


def temperature_trend(log, location):
    """Trend over time: one location's temperatures in time order."""
    out = log.copy()
    out = out[out["location"] == location]
    out = out.sort_values("timestamp_utc")
    return out[["timestamp_utc", "temperature"]]


def latest_ranking(log):
    """Cross-location comparison: each location's latest reading, warmest first, with a rank."""
    out = log.copy()
    out = out.sort_values("timestamp_utc")
    out = out.drop_duplicates(subset="location", keep="last")
    out = out.sort_values("temperature", ascending=False)
    out = out[["location", "temperature", "timestamp_utc"]].copy()
    out.insert(0, "rank", list(range(1, len(out) + 1)))
    return out


def feels_like_delta(log):
    """Derived metric: feels-like minus actual temperature, per location over time."""
    out = log.copy()
    out["feels_like_delta"] = (out["feels_like"] - out["temperature"]).round(2)
    out = out.sort_values("timestamp_utc")
    return out[["timestamp_utc", "location", "feels_like_delta"]]


def reading_counts(log):
    """Number of logged readings per location, used to spot too little history."""
    out = log.copy()
    out = out.groupby("location").agg(readings=("location", "count")).reset_index()
    return out
