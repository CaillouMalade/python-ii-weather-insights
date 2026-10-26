"""Small explainable metrics; no wet-track diagnosis or invented confidence."""
from collections import defaultdict
from statistics import mean
from .models import optional_number


def temperature_trends(records):
    """Group by provider AND coordinates to avoid mixing sources or namesakes."""
    groups = defaultdict(list)
    for row in records:
        if optional_number(row.get("temperature_c")) is not None:
            groups[(row["latitude"], row["longitude"], row["provider"])].append(row)
    result = []
    for (_, _, provider), rows in groups.items():
        ordered = sorted(rows, key=lambda r: (r["valid_at"], r["fetched_at"]))
        # Re-fetching the same provider valid time is not a new observation.
        distinct = {row["valid_at"]: row for row in ordered}
        samples = [distinct[key] for key in sorted(distinct)]
        result.append({"location": samples[-1]["location"], "provider": provider,
            "distinct_valid_times": len(samples), "first_valid_at": samples[0]["valid_at"],
            "last_valid_at": samples[-1]["valid_at"],
            "change_c": round(samples[-1]["temperature_c"] - samples[0]["temperature_c"], 2) if len(samples) >= 2 else None,
            "min_c": min(r["temperature_c"] for r in samples),
            "max_c": max(r["temperature_c"] for r in samples),
            "mean_c": round(mean(r["temperature_c"] for r in samples), 2)})
    return result


def latest_comparison(records, provider=None):
    """Latest stored sample for each location/provider, retaining its valid time."""
    latest = {}
    for row in records:
        if provider and row["provider"] != provider:
            continue
        key = (row["latitude"], row["longitude"], row["provider"])
        if key not in latest or (row["fetched_at"], row.get("id", 0)) > (latest[key]["fetched_at"], latest[key].get("id", 0)):
            latest[key] = row
    return sorted(latest.values(), key=lambda r: (
        r["temperature_c"] is None,
        r["temperature_c"] if r["temperature_c"] is not None else 0,
        r["location"], r["provider"]))


def derived_metrics(records):
    result = []
    for row in latest_comparison(records):
        temp, dew, feels = (optional_number(row.get(field)) for field in ("temperature_c", "dewpoint_c", "feels_like_c"))
        result.append({"location": row["location"], "provider": row["provider"], "valid_at": row["valid_at"],
            "air_minus_dewpoint_c": round(temp - dew, 2) if temp is not None and dew is not None else None,
            "feels_like_minus_air_c": round(feels - temp, 2) if feels is not None and temp is not None else None})
    return result
