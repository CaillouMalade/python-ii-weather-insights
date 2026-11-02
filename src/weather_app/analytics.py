"""Analytics: each function takes a DataFrame and returns a new DataFrame."""

import pandas as pd

from .findings import capped_comfort, part_reason, rate_comfort

METRES_PER_SECOND_TO_KMH = 3.6

# WHO global air quality guidelines 2021 (ISBN 978-92-4-003422-8), in µg/m³.
# PM2.5, PM10 and NO2 are 24-hour levels; O3 is a peak 8-hour level.
WHO_GUIDELINES = {"pm2_5": 15, "pm10": 45, "no2": 25, "o3": 100}

AQI_BANDS = [(1, "Good"), (2, "Fair"), (3, "Moderate"), (4, "Poor"), (5, "Very poor")]
PART_ORDER = {"Morning": 0, "Afternoon": 1, "Evening": 2}


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


def log_coverage(log):
    """One row per location: how many readings it has and the hours between first and last."""
    out = log.copy()
    out = out.groupby("location").agg(readings=("location", "count"), first=("timestamp_utc", "min"), last=("timestamp_utc", "max")).reset_index()
    out["span_hours"] = ((out["last"] - out["first"]).dt.total_seconds() / 3600).round(2)
    return out[["location", "readings", "span_hours"]]


def history_series(log, location):
    """One location's readings in time order, with the measures the History tab can show.

    time is local when the log knows the city's UTC offset, using its latest known offset.
    Rows from before that column existed share it. Without any offset, time stays UTC and
    is_local is False, so the chart can say so.
    """
    out = log.copy()
    out = out[out["location"] == location].sort_values("timestamp_utc")
    offsets = out["timezone_offset"].dropna().to_list()
    times = out["timestamp_utc"].dt.tz_localize(None)
    out["is_local"] = len(offsets) > 0
    if len(offsets) > 0:
        times = times + pd.to_timedelta(offsets[-1], unit="s")
    out["time"] = times
    out["wind_kmh"] = (out["wind_speed"] * METRES_PER_SECOND_TO_KMH).round(1)
    return out[["time", "is_local", "temperature", "feels_like", "humidity", "wind_kmh"]]


def daily_log_stats(series):
    """Per day: lowest, highest, range and number of readings, from history_series."""
    out = series.copy()
    out["day"] = out["time"].dt.strftime("%Y-%m-%d")
    out = out.groupby("day").agg(low=("temperature", "min"), high=("temperature", "max"), readings=("temperature", "count")).reset_index()
    out["range"] = out["high"] - out["low"]
    return out.round(1)


# Forecast


def daily_summary(steps):
    """Per local day, at most 5: low, high, chance of precipitation and an icon.

    steps must already have local_time and local_date. The icon comes from the step
    closest to 13:00, which describes the day better than a night-time step.
    """
    out = steps.copy()
    days = out.groupby("local_date").agg(low=("temperature", "min"), high=("temperature", "max"), pop=("pop", "max")).reset_index()

    out["hours_from_midday"] = (out["local_time"].dt.hour - 13).abs()
    midday = out.sort_values("hours_from_midday").drop_duplicates(subset="local_date", keep="first")
    days = days.merge(midday[["local_date", "icon"]], on="local_date", how="left")
    return days.sort_values("local_date").head(5)


def next_steps(steps, now, count):
    """The next forecast steps after now (Unix seconds)."""
    out = steps.copy()
    out = out[out["dt"] > now].sort_values("dt")
    return out.head(count)


def comfort_score(steps):
    """Add a 0-100 comfort score to each forecast step.

    score = 100
            - 3 points per °C the feels-like temperature is away from 21 °C
            - 30 points x chance of rain (0 to 1)
            - 1 point per km/h of wind above 20 km/h
            - 0.3 points per % of humidity above 70 %
    limited to between 0 and 100. This is our own rule of thumb, not a scientific index.
    """
    out = steps.copy()
    wind_kmh = out["wind_speed"] * METRES_PER_SECOND_TO_KMH
    score = 100 - 3 * (out["feels_like"] - 21).abs() - 30 * out["pop"]
    score = score - (wind_kmh - 20).clip(lower=0) - 0.3 * (out["humidity"] - 70).clip(lower=0)
    out["comfort"] = score.clip(lower=0, upper=100).round(0)
    return out


def forecast_measures(steps):
    """Add what Analytics needs: comfort, km/h and millimetres."""
    out = comfort_score(steps)
    out = out.sort_values("dt")
    out["wind_kmh"] = out["wind_speed"] * METRES_PER_SECOND_TO_KMH
    out["gust_kmh"] = out["wind_gust"] * METRES_PER_SECOND_TO_KMH
    out["precipitation_mm"] = out["rain_3h"] + out["snow_3h"]
    return out


def part_of_day(hour):
    """Morning runs from 06:00 to 12:00, afternoon to 18:00, evening to midnight. Night has no name."""
    if hour < 6:
        return None
    if hour < 12:
        return "Morning"
    if hour < 18:
        return "Afternoon"
    return "Evening"


def day_parts(measures):
    """One row per day and part of day, in time order, rated in words with a short reason."""
    out = measures.copy()
    out["part"] = [part_of_day(hour) for hour in out["local_time"].dt.hour]
    out = out.dropna(subset=["part"])
    out = out.groupby(["local_date", "part"]).agg(
        comfort=("comfort", "mean"),
        pop=("pop", "max"),
        snow=("snow_3h", "sum"),
        wind=("wind_kmh", "max"),
        feels=("feels_like", "mean"),
    ).reset_index()
    out["comfort"] = [capped_comfort(score, pop, wind) for score, pop, wind in zip(out["comfort"], out["pop"], out["wind"])]
    out["order"] = [PART_ORDER[part] for part in out["part"]]
    out = out.sort_values(["local_date", "order"])
    out["rating"] = [rate_comfort(score) for score in out["comfort"]]
    out["reason"] = [part_reason(pop, snow, wind, feels) for pop, snow, wind, feels in zip(out["pop"], out["snow"], out["wind"], out["feels"])]
    return out[["local_date", "part", "comfort", "pop", "snow", "wind", "feels", "rating", "reason"]]


def next_rain(measures):
    """The first forecast step with rain or snow: zero rows if none is expected."""
    out = measures.copy()
    out = out[out["precipitation_mm"] > 0]
    return out.head(1)


def windiest_moment(measures):
    """The forecast step with the strongest wind, as one row."""
    out = measures.copy()
    return out.sort_values("wind_kmh", ascending=False).head(1)


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
    return pd.DataFrame([{"change": change, "tendency": tendency}])


# Air quality


def complete_days(air, count):
    """Keep the latest count local days with at least 20 hours of data, so part-days do not skew the counts."""
    out = air.copy()
    counts = out.groupby("local_date").agg(hours=("dt", "count")).reset_index()
    full = counts[counts["hours"] >= 20]["local_date"].to_list()[-count:]
    return out[out["local_date"].isin(full)]


def daily_guideline_levels(air):
    """Each local day's level for comparing with the WHO guidelines.

    PM2.5, PM10 and NO2 use the day's mean. O3 uses the day's highest 8-hour rolling
    mean, because its guideline is an 8-hour level. air must be hourly with local_date.
    """
    out = air.copy()
    out = out.sort_values("dt")
    out["o3_8h"] = out["o3"].rolling(8).mean()
    return out.groupby("local_date").agg(pm2_5=("pm2_5", "mean"), pm10=("pm10", "mean"), no2=("no2", "mean"), o3=("o3_8h", "max")).reset_index()


def who_comparison(air):
    """One row per pollutant, most often over its guideline first: days over and days measured."""
    daily = daily_guideline_levels(air)
    rows = []
    for pollutant, guideline in WHO_GUIDELINES.items():
        levels = daily[pollutant].dropna()
        rows.append({"pollutant": pollutant, "guideline": guideline, "days": len(levels), "days_over": int((levels > guideline).sum())})
    return pd.DataFrame(rows).sort_values("days_over", ascending=False)


def days_over_any_guideline(air):
    """One row: the number of days, and the days with at least one pollutant over its guideline."""
    daily = daily_guideline_levels(air)
    over = daily["pm2_5"] > WHO_GUIDELINES["pm2_5"]
    for pollutant in ["pm10", "no2", "o3"]:
        over = over | (daily[pollutant] > WHO_GUIDELINES[pollutant])
    return pd.DataFrame([{"days": len(daily), "days_over": int(over.sum())}])


def daily_worst_aqi(air):
    """Each local day's worst AQI. air must have local_date."""
    out = air.copy()
    return out.groupby("local_date").agg(aqi=("aqi", "max")).reset_index()


def aqi_day_shares(air):
    """Share of days per air quality band, judging each day by its worst hour. All five bands appear."""
    daily = daily_worst_aqi(air)
    counts = daily.groupby("aqi").agg(days=("aqi", "count")).reset_index()

    out = pd.DataFrame(AQI_BANDS, columns=["aqi", "band"])
    out = out.merge(counts, on="aqi", how="left")
    out["days"] = out["days"].fillna(0).astype(int)
    out["share"] = 0.0
    if len(daily) > 0:
        out["share"] = (out["days"] / len(daily) * 100).round(1)
    return out


def air_by_hour(air, pollutant):
    """Average level of one pollutant for each local hour of the day."""
    out = air.copy()
    out["hour"] = out["local_time"].dt.hour
    return out.groupby("hour").agg(level=(pollutant, "mean")).round(0).reset_index()


# City comparison


def city_week_summary(measures):
    """One row per location from combined forecasts: high, low, total rain and average wind."""
    out = measures.copy()
    out = out.groupby("location").agg(
        high=("temperature", "max"),
        low=("temperature", "min"),
        rain_mm=("precipitation_mm", "sum"),
        wind_kmh=("wind_kmh", "mean"),
    ).reset_index()
    return out.round(1)
