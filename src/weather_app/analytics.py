"""Analyses of the collector's logged history (data/current_weather.csv), used by the History and Track comparison pages."""

from .forecast_stats import RAIN_THRESHOLD_MM


class TrackSummary:
    """Summary of the logged weather for one track."""

    def __init__(self, location_id, location, average_temperature_c, rain_days, total_rain_mm, days_logged):
        self.location_id = location_id
        self.location = location
        self.average_temperature_c = average_temperature_c
        self.rain_days = rain_days
        self.total_rain_mm = total_rain_mm
        self.days_logged = days_logged

    def __lt__(self, other):
        """Sort wetter tracks after drier tracks."""
        return self.total_rain_mm < other.total_rain_mm

    def __str__(self):
        """Return the one-line summary shown on the page."""
        return f"{self.location}: average {self.average_temperature_c:.1f} °C, {self.rain_days} rain days, {self.total_rain_mm:.1f} mm total rain over {self.days_logged} logged days."


# A track needs readings on at least this many days before its history is drawn:
# with a single reading every chart would be one lonely dot.
MIN_DAYS_LOGGED = 2


def days_logged(history, location_id):
    """Return on how many different days a track was logged."""
    track = history[history["location_id"] == location_id]
    return track["timestamp_utc"].dt.date.nunique()


def track_rain_history(history, location_id):
    """Return daily rain estimates and temperature range for one track ID."""
    track = history[history["location_id"] == location_id].copy()
    track["rain"] = track["rain"].fillna(0)
    track["day"] = track["timestamp_utc"].dt.date
    daily = track.groupby("day").agg(
        temperature_min_c=("temperature", "min"),
        temperature_max_c=("temperature", "max"),
        temperature_mean_c=("temperature", "mean"),
    ).reset_index()
    # The collector logs a rolling one-hour total every 30 minutes, so use the daily mean × 24.
    rain_by_day = (track.groupby("day")["rain"].mean() * 24).reset_index(name="rain_mm")
    daily = daily.merge(rain_by_day, on="day")
    daily["temperature_range_c"] = daily["temperature_max_c"] - daily["temperature_min_c"]
    return daily.sort_values("day").reset_index(drop=True)


def compare_track_history(history, location_ids):
    """Summarize tracks over their logged data and rank them by estimated total rain."""
    summaries = []
    for location_id in location_ids:
        track = history[history["location_id"] == location_id]
        if len(track) == 0:
            continue
        # The daily rain comes from track_rain_history, so the estimate is written in one place only.
        daily = track_rain_history(history, location_id)
        summaries.append(TrackSummary(
            location_id,
            track["location"].iloc[0],
            track["temperature"].mean(),
            # Same threshold as the forecasts (forecast_stats): below 0.1 mm a day does not count as rainy.
            int((daily["rain_mm"] >= RAIN_THRESHOLD_MM).sum()),
            daily["rain_mm"].sum(),
            len(daily),
        ))
    return sorted(summaries, reverse=True)
