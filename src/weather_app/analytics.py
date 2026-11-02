"""Analytics: each function takes a DataFrame and returns a new DataFrame."""

import pandas as pd

METRES_PER_SECOND_TO_KMH = 3.6

# WHO global air quality guidelines 2021 (ISBN 978-92-4-003422-8), in µg/m³.
# PM2.5, PM10 and NO2 are 24-hour levels; O3 is a peak 8-hour level.
WHO_GUIDELINES = {"pm2_5": 15, "pm10": 45, "no2": 25, "o3": 100}
POLLUTANT_NAMES = {"pm2_5": "PM2.5", "pm10": "PM10", "no2": "NO2", "o3": "O3"}

AQI_BANDS = [(1, "Good"), (2, "Fair"), (3, "Moderate"), (4, "Poor"), (5, "Very poor")]


# Time


def add_local_time(df, timezone_offset):
    """Add local_time and local_date from dt (Unix seconds) and the city's UTC offset in seconds.

    One offset is used for the whole table, so a daylight-saving change during it is ignored.
    """
    out = df.copy()
    out["local_time"] = pd.to_datetime(out["dt"], unit="s") + pd.to_timedelta(timezone_offset, unit="s")
    out["local_date"] = out["local_time"].dt.strftime("%Y-%m-%d")
    return out


# Logged history (these work without an API key)


def temperature_trend(log, location):
    """Trend over time: one location's temperature and feels-like in time order."""
    out = log.copy()
    out = out[out["location"] == location]
    out = out.sort_values("timestamp_utc")
    return out[["timestamp_utc", "temperature", "feels_like"]]


def daily_log_stats(log, location):
    """Per UTC day: lowest, highest, range and number of readings for one location."""
    out = temperature_trend(log, location)
    out["day"] = out["timestamp_utc"].dt.strftime("%Y-%m-%d")
    out = out.groupby("day").agg(low=("temperature", "min"), high=("temperature", "max"), readings=("temperature", "count")).reset_index()
    out["range"] = (out["high"] - out["low"]).round(2)
    return out


def history_coverage(log, location):
    """One row saying how much history a location has: readings and the span in hours."""
    out = temperature_trend(log, location)
    span_hours = 0.0
    if len(out) > 0:
        span_hours = round((out["timestamp_utc"].max() - out["timestamp_utc"].min()).total_seconds() / 3600, 2)
    return pd.DataFrame([{"readings": len(out), "span_hours": span_hours}])


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


# Forecast


def daily_summary(steps):
    """Per local day, at most 5: low, high, chance of precipitation, totals and an icon.

    steps must already have local_time and local_date. The icon comes from the step
    closest to 13:00, which describes the day better than a night-time step.
    """
    out = steps.copy()
    days = out.groupby("local_date").agg(
        low=("temperature", "min"),
        high=("temperature", "max"),
        pop=("pop", "max"),
        rain=("rain_3h", "sum"),
        snow=("snow_3h", "sum"),
    ).reset_index()

    out["hours_from_midday"] = (out["local_time"].dt.hour - 13).abs()
    midday = out.sort_values("hours_from_midday").drop_duplicates(subset="local_date", keep="first")
    days = days.merge(midday[["local_date", "icon", "conditions"]], on="local_date", how="left")
    return days.sort_values("local_date").head(5)


def hourly_plan(steps, now, sunrise=None, sunset=None):
    """The next 24 hours in 3-hour steps, with sunrise and sunset placed where they fall.

    now, sunrise and sunset are Unix seconds. The API gives one sunrise and sunset per
    day, so tomorrow's are estimated by adding 24 hours (out by a minute or two at most).
    """
    window_end = now + 24 * 3600
    out = steps.copy()
    out = out[(out["dt"] > now) & (out["dt"] <= window_end)].copy()
    out["kind"] = "step"

    events = []
    for kind, time in [("sunrise", sunrise), ("sunset", sunset)]:
        if time is None:
            continue
        for candidate in [time, time + 24 * 3600]:
            if candidate > now and candidate <= window_end:
                events.append({"dt": candidate, "kind": kind})

    if len(events) > 0:
        out = pd.concat([out, pd.DataFrame(events)], ignore_index=True)
    return out.sort_values("dt")


def comfort_score(steps):
    """Add a 0-100 comfort score to each forecast step.

    score = 100
            - 3 points per °C the feels-like temperature is away from 21 °C
            - 30 points x chance of precipitation (0 to 1)
            - 1 point per km/h of wind above 20 km/h
            - 0.3 points per % of humidity above 70 %
    limited to between 0 and 100. This is our own rule of thumb, not a scientific index.
    """
    out = steps.copy()
    wind_kmh = out["wind_speed"] * METRES_PER_SECOND_TO_KMH
    score = 100 - 3 * (out["feels_like"] - 21).abs() - 30 * out["pop"]
    score = score - (wind_kmh - 20).clip(lower=0) - 0.3 * (out["humidity"] - 70).clip(lower=0)
    out["comfort"] = score.clip(lower=0, upper=100).round(1)
    return out


def comfort_windows(steps):
    """Six-hour daytime windows (two steps in a row), most comfortable first.

    steps must have comfort, local_time and pod ("d" is day, "n" is night).
    """
    out = steps.copy()
    out = out.sort_values("dt")
    out["score"] = ((out["comfort"] + out["comfort"].shift(-1)) / 2).round(1)
    out["end_time"] = out["local_time"].shift(-1) + pd.to_timedelta(3, unit="h")
    out = out[(out["pod"] == "d") & (out["pod"].shift(-1) == "d")]
    out = out.sort_values("score", ascending=False)
    return out[["local_time", "end_time", "score"]]


def pressure_tendency(steps):
    """One row: the pressure change over the next 24 hours and whether it is rising or falling."""
    out = steps.copy()
    # Nine steps three hours apart span 24 hours.
    values = out.sort_values("dt").head(9)["pressure"].to_list()
    change = round(values[-1] - values[0], 1)
    tendency = "steady"
    if change >= 3:
        tendency = "rising"
    elif change <= -3:
        tendency = "falling"
    return pd.DataFrame([{"start": values[0], "end": values[-1], "change": change, "tendency": tendency}])


# Air quality


def who_comparison(air):
    """Compare air quality with the WHO guidelines: one row per pollutant.

    PM2.5, PM10 and NO2 use each local day's mean. O3 uses each day's highest
    8-hour rolling mean, because its guideline is an 8-hour level. air must be
    hourly and have local_date.
    """
    out = air.copy()
    out = out.sort_values("dt")
    rows = []
    for pollutant, guideline in WHO_GUIDELINES.items():
        values = out[["local_date", pollutant]].copy()
        if pollutant == "o3":
            values["o3"] = values["o3"].rolling(8).mean()
            daily = values.groupby("local_date").agg(level=("o3", "max")).reset_index()
        else:
            daily = values.groupby("local_date").agg(level=(pollutant, "mean")).reset_index()
        daily = daily.dropna()

        days = len(daily)
        days_over = int((daily["level"] > guideline).sum())
        average_level = None
        share_over = 0.0
        if days > 0:
            average_level = round(float(daily["level"].mean()), 1)
            share_over = round(days_over / days * 100, 1)
        rows.append(
            {
                "pollutant": POLLUTANT_NAMES[pollutant],
                "guideline": guideline,
                "average_level": average_level,
                "days": days,
                "days_over": days_over,
                "share_over": share_over,
            }
        )
    return pd.DataFrame(rows)


def air_daily_means(air):
    """Daily mean of the main pollutants and the day's worst AQI. air must have local_date."""
    out = air.copy()
    out = out.groupby("local_date").agg(
        aqi=("aqi", "max"),
        pm2_5=("pm2_5", "mean"),
        pm10=("pm10", "mean"),
        no2=("no2", "mean"),
        o3=("o3", "mean"),
    ).round(1).reset_index()
    return out


def air_pattern(air, pollutant):
    """Average level of one pollutant by day of week (0 is Monday) and local hour."""
    out = air.copy()
    out["day_of_week"] = out["local_time"].dt.day_of_week
    out["hour"] = out["local_time"].dt.hour
    out = out.groupby(["day_of_week", "hour"]).agg(level=(pollutant, "mean")).round(1).reset_index()
    return out


def aqi_band_share(air):
    """Share of days per AQI band, judging each day by its worst hour. All five bands appear."""
    daily = air_daily_means(air)
    counts = daily.groupby("aqi").agg(days=("aqi", "count")).reset_index()

    out = pd.DataFrame(AQI_BANDS, columns=["aqi", "band"])
    out = out.merge(counts, on="aqi", how="left")
    out["days"] = out["days"].fillna(0).astype(int)
    out["share"] = 0.0
    if len(daily) > 0:
        out["share"] = (out["days"] / len(daily) * 100).round(1)
    return out


# City comparison


def city_forecast_summary(steps):
    """One row per location from combined forecast steps: temperature, rain and wind ahead."""
    out = steps.copy()
    out["wind_kmh"] = out["wind_speed"] * METRES_PER_SECOND_TO_KMH
    out = out.groupby("location").agg(
        low=("temperature", "min"),
        high=("temperature", "max"),
        average=("temperature", "mean"),
        rain_mm=("rain_3h", "sum"),
        highest_pop=("pop", "max"),
        wind_kmh=("wind_kmh", "mean"),
    ).reset_index()
    out = out.sort_values("average", ascending=False)
    return out.round(1)


def city_daily_highs(steps):
    """Each location's high temperature and total rain per local date, for the heatmaps."""
    out = steps.copy()
    out = out.groupby(["location", "local_date"]).agg(high=("temperature", "max"), rain_mm=("rain_3h", "sum")).round(1).reset_index()
    return out
