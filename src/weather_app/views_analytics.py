"""The Analytics tab: logged history, the next 5 days, air quality and city comparison."""

import pandas as pd
import plotly.express as px
import streamlit as st

from .analytics import (
    METRES_PER_SECOND_TO_KMH,
    add_local_time,
    air_pattern,
    aqi_band_share,
    air_daily_means,
    city_daily_highs,
    city_forecast_summary,
    comfort_score,
    comfort_windows,
    daily_log_stats,
    feels_like_delta,
    history_coverage,
    latest_ranking,
    pressure_tendency,
    reading_counts,
    temperature_trend,
    who_comparison,
)
from .config import API_KEY, SETUP_MESSAGE
from .fetching import fetch_air_forecast, fetch_air_history, fetch_air_now
from .storage import load_log

# Clear on the dark background, and different enough to tell lines apart.
px.defaults.color_discrete_sequence = ["#7fd0f5", "#ffb86b", "#b7e36b", "#f28fb1"]

AIR_HISTORY_DAYS = 90
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def show_chart(fig, x_title, y_title):
    """Show a Plotly figure with the same look everywhere and both axes labelled."""
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=340,
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", y=-0.25, title=""),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, config={"displayModeBar": False})


def show_heatmap(table, title, unit, x_title, y_title):
    """Show a table as a heatmap. Its columns and row names are used as labels, not as a date scale."""
    fig = px.imshow(table, text_auto=True, aspect="auto", title=title, labels=dict(color=unit))
    fig.update_xaxes(type="category")
    fig.update_yaxes(type="category")
    show_chart(fig, x_title, y_title)


def show_history(log, location):
    st.subheader(f"Your logged history: {location['city']}")
    name = location["location"]
    coverage = history_coverage(log, name).to_dict("records")[0]

    if coverage["readings"] < 2:
        st.info(f"{location['city']} has {coverage['readings']} saved reading(s). A trend needs at least 2: keep the Weather tab in use to build history.")
    else:
        days = coverage["span_hours"] / 24
        if days < 3:
            st.write(f"**{coverage['readings']} readings over {coverage['span_hours']:.1f} hours.** That is an early picture, not yet a real trend.")
        else:
            st.write(f"**{coverage['readings']} readings over {days:.1f} days.**")

        trend = temperature_trend(log, name)
        trend = trend.rename(columns={"temperature": "Temperature", "feels_like": "Feels like"})
        fig = px.line(trend, x="timestamp_utc", y=["Temperature", "Feels like"], markers=True, title="Temperature and feels-like")
        show_chart(fig, "Time logged (UTC)", "Temperature (°C)")

        stats = daily_log_stats(log, name)
        table = stats[["day", "low", "high", "range", "readings"]].copy()
        table.columns = ["UTC day", "Low (°C)", "High (°C)", "Range (°C)", "Readings"]
        st.dataframe(table, hide_index=True)

    st.subheader("Feels-like minus actual temperature, all cities")
    delta = feels_like_delta(log)
    latest = delta[delta["location"] == name]["feels_like_delta"].to_list()
    if len(latest) > 0:
        st.write(f"**Latest for {location['city']}: it felt {latest[-1]:+.1f} °C compared with the actual temperature.**")
    counts = reading_counts(log)
    short_history = counts[counts["readings"] < 2]["location"].to_list()
    if len(short_history) > 0:
        st.info(f"Only one saved reading so far, so no line yet: {', '.join(short_history)}.")
    fig = px.line(delta, x="timestamp_utc", y="feels_like_delta", color="location", markers=True)
    show_chart(fig, "Time logged (UTC)", "Feels-like minus actual (°C)")


def show_forecast(weather):
    st.subheader(f"Next 5 days: {weather['location']['city']}")
    steps = comfort_score(weather["steps"])
    steps["wind_kmh"] = steps["wind_speed"] * METRES_PER_SECOND_TO_KMH
    steps["gust_kmh"] = steps["wind_gust"] * METRES_PER_SECOND_TO_KMH
    steps["pop_percent"] = steps["pop"] * 100
    steps["precipitation_mm"] = steps["rain_3h"] + steps["snow_3h"]

    warmest = steps.sort_values("temperature", ascending=False).to_dict("records")[0]
    st.write(f"**Warmest point: {warmest['temperature']:.1f} °C on {warmest['local_time'].strftime('%a at %H:%M')}.**")
    named = steps.rename(columns={"temperature": "Temperature", "feels_like": "Feels like", "dew_point": "Dew point", "wind_kmh": "Wind", "gust_kmh": "Gusts"})
    fig = px.line(named, x="local_time", y=["Temperature", "Feels like", "Dew point"], title="Temperature, feels-like and dew point")
    show_chart(fig, "Local time", "Temperature (°C)")

    total = steps["precipitation_mm"].sum()
    wettest = steps.sort_values("pop", ascending=False).to_dict("records")[0]
    st.write(f"**{total:.1f} mm of precipitation expected in total. Highest chance: {wettest['pop_percent']:.0f} % on {wettest['local_time'].strftime('%a at %H:%M')}.**")
    fig = px.bar(steps, x="local_time", y="pop_percent", title="Chance of precipitation")
    show_chart(fig, "Local time", "Chance (%)")
    fig = px.bar(steps, x="local_time", y="precipitation_mm", title="Rain and snow per 3-hour step")
    show_chart(fig, "Local time", "Precipitation (mm)")

    windiest = steps.sort_values("wind_kmh", ascending=False).to_dict("records")[0]
    st.write(f"**Windiest point: {windiest['wind_kmh']:.0f} km/h on {windiest['local_time'].strftime('%a at %H:%M')}.**")
    fig = px.line(named, x="local_time", y=["Wind", "Gusts"], title="Wind and gusts")
    show_chart(fig, "Local time", "Speed (km/h)")

    tendency = pressure_tendency(steps).to_dict("records")[0]
    st.write(f"**Pressure is {tendency['tendency']}: {tendency['change']:+.1f} hPa over the next 24 hours.**")
    fig = px.line(steps, x="local_time", y="pressure", title="Pressure")
    show_chart(fig, "Local time", "Pressure (hPa)")

    st.subheader("Comfort score")
    st.caption("Our own rule of thumb, from 0 to 100: start at 100, subtract 3 per °C the feels-like temperature is away from 21 °C, 30 × the chance of precipitation, 1 per km/h of wind above 20 km/h, and 0.3 per % of humidity above 70 %.")
    windows = comfort_windows(steps)
    if len(windows) == 0:
        st.info("The forecast has no two daytime steps in a row to compare.")
    else:
        best = windows.to_dict("records")[0]
        worst = windows.to_dict("records")[-1]
        st.write(
            f"**Best daytime window: {best['local_time'].strftime('%a %H:%M')} to {best['end_time'].strftime('%H:%M')} (score {best['score']:.0f}). "
            f"Worst: {worst['local_time'].strftime('%a %H:%M')} to {worst['end_time'].strftime('%H:%M')} (score {worst['score']:.0f}).**"
        )
    fig = px.line(steps, x="local_time", y="comfort", markers=True)
    fig.update_yaxes(range=[0, 100])
    show_chart(fig, "Local time", "Comfort score (0-100)")


def show_air(weather):
    location = weather["location"]
    offset = weather["reading"].timezone_offset or 0
    st.subheader(f"Air quality: {location['city']}")
    try:
        history_rows = fetch_air_history(location["latitude"], location["longitude"], AIR_HISTORY_DAYS)
    except ValueError as e:
        st.warning(f"Could not load air quality history: {e}")
        return
    if len(history_rows) == 0:
        st.info("OpenWeatherMap has no air quality history for this location.")
        return

    air = add_local_time(pd.DataFrame(history_rows), offset)
    daily = air_daily_means(air)
    st.caption(f"{len(daily)} days of modelled OpenWeatherMap data, not measurements from a local station. Times are local.")

    guidelines = who_comparison(air)
    worst = guidelines.sort_values("share_over", ascending=False).to_dict("records")[0]
    if worst["days_over"] == 0:
        st.write("**No daily level exceeded a WHO guideline in this period.**")
    else:
        st.write(f"**{worst['pollutant']} exceeded its WHO guideline most often: on {worst['days_over']} of {worst['days']} days ({worst['share_over']:.0f} %).**")
    table = guidelines.copy()
    table.columns = ["Pollutant", "WHO guideline (µg/m³)", "Average level (µg/m³)", "Days", "Days over", "Share over (%)"]
    st.dataframe(table, hide_index=True)
    st.caption("Guidelines: WHO global air quality guidelines, 2021. PM2.5, PM10 and NO2 are compared as daily means, O3 as the day's highest 8-hour mean.")

    named = daily.rename(columns={"pm2_5": "PM2.5", "pm10": "PM10", "no2": "NO2", "o3": "O3"})
    fig = px.line(named, x="local_date", y=["PM2.5", "PM10", "NO2", "O3"], title="Daily mean levels")
    show_chart(fig, "Date", "Concentration (µg/m³)")

    fig = px.bar(daily, x="local_date", y="aqi", title="Worst AQI each day")
    fig.update_yaxes(range=[0, 5])
    show_chart(fig, "Date", "AQI (1 is good, 5 is very poor)")

    bands = aqi_band_share(air)
    common = bands.sort_values("days", ascending=False).to_dict("records")[0]
    st.write(f"**The most common band is {common['band']}: {common['share']:.0f} % of days, judging each day by its worst hour.**")
    fig = px.bar(bands, x="band", y="share", title="Share of days per AQI band")
    show_chart(fig, "AQI band", "Share of days (%)")

    pollutant_names = {"PM2.5": "pm2_5", "PM10": "pm10", "NO2": "no2", "O3": "o3"}
    chosen = st.segmented_control("Pattern for", list(pollutant_names.keys()), default="PM2.5", required=True, key="air_pattern_pollutant")
    pattern = air_pattern(air, pollutant_names[chosen])
    peak = pattern.sort_values("level", ascending=False).to_dict("records")[0]
    st.write(f"**{chosen} is highest on average on {DAY_NAMES[peak['day_of_week']]} around {peak['hour']:02d}:00 ({peak['level']:.0f} µg/m³).**")
    table = pattern.pivot(index="day_of_week", columns="hour", values="level")
    table.index = [DAY_NAMES[number] for number in table.index]
    show_heatmap(table, f"{chosen} by day and hour", "µg/m³", "Local hour", "Day of week")

    st.subheader("Outlook")
    try:
        outlook_rows = fetch_air_forecast(location["latitude"], location["longitude"])
    except ValueError as e:
        st.warning(f"Could not load the air quality forecast: {e}")
        return
    if len(outlook_rows) == 0:
        st.info("OpenWeatherMap has no air quality forecast for this location.")
        return
    outlook = air_daily_means(add_local_time(pd.DataFrame(outlook_rows), offset))
    fig = px.bar(outlook, x="local_date", y="aqi", title="Forecast worst AQI per day")
    fig.update_yaxes(range=[0, 5])
    show_chart(fig, "Date", "AQI (1 is good, 5 is very poor)")


def show_comparison(weather_by_city):
    st.subheader("Your cities side by side")
    loaded = [weather for weather in weather_by_city if weather["reading"] is not None]
    if len(loaded) < 2:
        st.info("A comparison needs at least 2 saved cities that have loaded.")
        return

    # Ranked with sorted() on the reading objects, which uses WeatherReading.__lt__.
    ranked = sorted([weather["reading"] for weather in loaded], reverse=True)
    rows = []
    for reading in ranked:
        air_text = None
        try:
            air_rows = fetch_air_now(reading.latitude, reading.longitude)
            if len(air_rows) > 0:
                air_text = air_rows[0].get("aqi")
        except ValueError:
            air_text = None
        rows.append({"City": reading.location, "Now (°C)": round(reading.temperature, 1), "Feels like (°C)": round(reading.feels_like, 1), "Wind now (km/h)": round(reading.wind_speed * METRES_PER_SECOND_TO_KMH, 1), "AQI (1-5)": air_text})
    st.write(f"**Warmest right now: {ranked[0].location} at {ranked[0].temperature:.1f} °C. Coldest: {ranked[-1].location} at {ranked[-1].temperature:.1f} °C.**")
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    frames = []
    for weather in loaded:
        if weather["steps"] is not None:
            steps = weather["steps"].copy()
            steps["location"] = weather["location"]["location"]
            frames.append(steps)
    if len(frames) < 2:
        st.info("A forecast comparison needs forecasts for at least 2 cities.")
        return
    combined = pd.concat(frames, ignore_index=True)

    summary = city_forecast_summary(combined)
    wettest = summary.sort_values("rain_mm", ascending=False).to_dict("records")[0]
    windiest = summary.sort_values("wind_kmh", ascending=False).to_dict("records")[0]
    rain_text = f"{wettest['location']} expects the most rain ({wettest['rain_mm']:.1f} mm)"
    if wettest["rain_mm"] == 0:
        rain_text = "no city expects rain"
    st.write(f"**Over the next 5 days, {summary['location'].to_list()[0]} is warmest on average, {rain_text} and {windiest['location']} has the most wind ({windiest['wind_kmh']:.0f} km/h on average).**")
    fig = px.bar(summary, x="location", y="average", title="Average forecast temperature")
    show_chart(fig, "City", "Temperature (°C)")

    table = summary.copy()
    table.columns = ["City", "Low (°C)", "High (°C)", "Average (°C)", "Rain (mm)", "Highest chance of precipitation (0-1)", "Average wind (km/h)"]
    st.dataframe(table, hide_index=True)

    daily = city_daily_highs(combined)
    highs = daily.pivot(index="location", columns="local_date", values="high")
    show_heatmap(highs, "Daily high", "°C", "Local date", "City")
    rain = daily.pivot(index="location", columns="local_date", values="rain_mm")
    show_heatmap(rain, "Daily rain", "mm", "Local date", "City")


def show_logged_ranking(log):
    st.subheader("From your log: cities ranked by latest temperature")
    ranking = latest_ranking(log)
    if len(ranking) < 2:
        st.info("Only one city has saved readings. A comparison needs at least 2 cities.")
    else:
        top = ranking.to_dict("records")[0]
        st.write(f"**{top['location']} had the highest latest logged temperature: {top['temperature']:.1f} °C.**")
    fig = px.bar(ranking, x="location", y="temperature")
    show_chart(fig, "City", "Latest logged temperature (°C)")


def show_analytics_tab(weather, weather_by_city):
    log = load_log()
    history_tab, forecast_tab, air_tab, compare_tab = st.tabs(["Your history", "Next 5 days", "Air quality", "Compare cities"], key="analytics_tab", on_change="rerun")

    # .open is True only for the tab on screen, so the others make no API calls.
    if history_tab.open:
        with history_tab:
            if len(log) == 0:
                st.info("The weather log is empty. Open the Weather tab with an API key to start building history.")
            elif weather is None:
                st.info("Add a city in the sidebar to see its history.")
            else:
                show_history(log, weather["location"])

    if forecast_tab.open:
        with forecast_tab:
            if not API_KEY:
                st.info(SETUP_MESSAGE)
            elif weather is None or weather["steps"] is None:
                st.info("The forecast for this city is not available right now.")
            else:
                show_forecast(weather)

    if air_tab.open:
        with air_tab:
            if not API_KEY:
                st.info(SETUP_MESSAGE)
            elif weather is None or weather["reading"] is None:
                st.info("Air quality for this city is not available right now.")
            else:
                show_air(weather)

    if compare_tab.open:
        with compare_tab:
            if not API_KEY:
                st.info(SETUP_MESSAGE)
            else:
                show_comparison(weather_by_city)
            if len(log) > 0:
                show_logged_ranking(log)
