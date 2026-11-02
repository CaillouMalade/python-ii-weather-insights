"""Analytics: each function takes a DataFrame and returns a new DataFrame."""

import pandas as pd

METRES_PER_SECOND_TO_KMH = 3.6

# WHO global air quality guidelines 2021 (ISBN 978-92-4-003422-8), in µg/m³.
# PM2.5, PM10 and NO2 are 24-hour levels; O3 is a peak 8-hour level.
WHO_GUIDELINES = {"pm2_5": 15, "pm10": 45, "no2": 25, "o3": 100}
POLLUTANT_NAMES = {"pm2_5": "PM2.5", "pm10": "PM10", "no2": "NO2", "o3": "O3"}


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
    out["feels_delta"] = (out["feels_like"] - out["temperature"]).round(1)
    out["wind_kmh"] = (out["wind_speed"] * METRES_PER_SECOND_TO_KMH).round(1)
    return out[["time", "is_local", "temperature", "feels_like", "feels_delta", "humidity", "wind_kmh"]]


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
    """Add everything Analytics shows: comfort, km/h, percent, millimetres, day and time labels."""
    out = comfort_score(steps)
    out = out.sort_values("dt")
    out["wind_kmh"] = out["wind_speed"] * METRES_PER_SECOND_TO_KMH
    out["gust_kmh"] = out["wind_gust"] * METRES_PER_SECOND_TO_KMH
    out["pop_percent"] = out["pop"] * 100
    out["precipitation_mm"] = out["rain_3h"] + out["snow_3h"]
    out["time_of_day"] = out["local_time"].dt.strftime("%H:%M")
    return out


def week_grid(measures, column):
    """A table for the Plan the week heatmap: one row per local date, one column per time of day."""
    out = measures.pivot(index="local_date", columns="time_of_day", values=column)
    return out.round(0)


def ranked_windows(measures, count=3):
    """The most comfortable six-hour daytime windows (two steps in a row) that do not overlap.

    measures comes from forecast_measures. Each row has the window's start and end,
    its mean comfort score and the reasons: mean feels-like, highest chance of rain, strongest wind.
    """
    out = measures.copy()
    out["score"] = ((out["comfort"] + out["comfort"].shift(-1)) / 2).round(0)
    out["end_time"] = out["local_time"].shift(-1) + pd.to_timedelta(3, unit="h")
    out["feels"] = (out["feels_like"] + out["feels_like"].shift(-1)) / 2
    out["rain_chance"] = pd.concat([out["pop_percent"], out["pop_percent"].shift(-1)], axis=1).max(axis=1)
    out["wind"] = pd.concat([out["wind_kmh"], out["wind_kmh"].shift(-1)], axis=1).max(axis=1)
    out = out[(out["pod"] == "d") & (out["pod"].shift(-1) == "d")]
    out = out.sort_values("score", ascending=False)

    # Take the best window, then the next best that does not overlap one already taken.
    kept = []
    for _, row in out.iterrows():
        overlaps = False
        for taken in kept:
            if row["local_time"] < taken["end_time"] and taken["local_time"] < row["end_time"]:
                overlaps = True
        if not overlaps and len(kept) < count:
            kept.append(row)

    columns = ["local_time", "end_time", "score", "feels", "rain_chance", "wind"]
    return pd.DataFrame(kept, columns=columns)


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
    """One row per pollutant: guideline, average level, and days over it, in whole numbers."""
    daily = daily_guideline_levels(air)
    rows = []
    for pollutant, guideline in WHO_GUIDELINES.items():
        levels = daily[pollutant].dropna()
        days = len(levels)
        days_over = int((levels > guideline).sum())
        average = None
        share = 0
        if days > 0:
            average = round(float(levels.mean()))
            share = round(days_over / days * 100)
        rows.append({"pollutant": POLLUTANT_NAMES[pollutant], "guideline": guideline, "average_level": average, "days": days, "days_over": days_over, "share_over": share})
    return pd.DataFrame(rows)


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


def air_calendar(air):
    """A calendar table of daily worst AQI: one row per weekday (0 is Monday), one column per week.

    Column names are the date of that week's Monday.
    """
    out = daily_worst_aqi(air)
    dates = pd.to_datetime(out["local_date"])
    out["weekday"] = dates.dt.day_of_week
    out["week"] = (dates - pd.to_timedelta(out["weekday"], unit="D")).dt.strftime("%Y-%m-%d")
    return out.pivot(index="weekday", columns="week", values="aqi")


def air_by_hour(air, pollutant):
    """Average level of one pollutant for each local hour of the day."""
    out = air.copy()
    out["hour"] = out["local_time"].dt.hour
    return out.groupby("hour").agg(level=(pollutant, "mean")).round(0).reset_index()


# City comparison


def city_day_values(df, column, per_day):
    """One value per location and local date. per_day says how to combine a day: "max" or "sum"."""
    out = df.copy()
    out = out.groupby(["location", "local_date"]).agg(value=(column, per_day)).reset_index()
    out["value"] = out["value"].round(1)
    return out


def rank_cities(city_days, overall):
    """Rank locations, highest first, by combining their days. overall is "mean", "sum" or "max"."""
    out = city_days.copy()
    out = out.groupby("location").agg(value=("value", overall)).reset_index()
    out = out.sort_values("value", ascending=False)
    out["value"] = out["value"].round(1)
    out.insert(0, "rank", list(range(1, len(out) + 1)))
    return out


def city_day_grid(city_days, order):
    """A table for the Compare heatmap: one row per location, in the given order, one column per date."""
    out = city_days.pivot(index="location", columns="local_date", values="value")
    keep = [name for name in order if name in out.index]
    return out.loc[keep]
