"""The Analytics tab: an overview strip, then Plan the week, Air, Compare and History."""

from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from . import cards
from .analytics import (
    POLLUTANT_NAMES,
    add_local_time,
    air_by_hour,
    air_calendar,
    city_day_grid,
    city_day_values,
    daily_log_stats,
    daily_worst_aqi,
    days_over_any_guideline,
    forecast_measures,
    history_series,
    log_coverage,
    next_rain,
    rank_cities,
    ranked_windows,
    week_grid,
    who_comparison,
    windiest_moment,
)
from .config import API_KEY, SETUP_MESSAGE
from .display import aqi_label
from .fetching import fetch_air_forecast, fetch_air_history, fetch_air_now, now_seconds
from .findings import comparison_finding, coverage_text, peak_hour_finding, plan_finding, too_little_history_text, trend_finding, who_finding, window_reason
from .storage import load_log

AIR_HISTORY_DAYS = 90
# A chart of a few minutes of readings would suggest a trend that is not there.
MIN_TREND_READINGS = 3
MIN_TREND_HOURS = 3

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
LINE_COLOR = "#7fd0f5"
HEAT_COLORS = ["#25405c", "#8fc7e8", "#fbe7a1"]
AQI_COLORS = ["#3ec6a8", "#8fd14f", "#f2d13c", "#ef8a3a", "#d8324a"]

# Name on the selector: (column, chart title with its unit).
PLAN_METRICS = {
    "Comfort": ("comfort", "Comfort score (0-100)"),
    "Temperature": ("temperature", "Temperature (°C)"),
    "Chance of rain": ("pop_percent", "Chance of rain (%)"),
    "Wind": ("wind_kmh", "Wind (km/h)"),
}
# Name on the selector: (how to combine a day, how to combine the days, bar axis title, heatmap title).
COMPARE_METRICS = {
    "Temperature": ("max", "mean", "Average daily high (°C)", "Daily high (°C)"),
    "Rain": ("sum", "sum", "Total rain and snow (mm)", "Daily rain and snow (mm)"),
    "Wind": ("max", "max", "Strongest wind (km/h)", "Daily strongest wind (km/h)"),
    "Air quality": ("max", "mean", "Average worst AQI (1-5)", "Worst AQI per day (1 is good, 5 is very poor)"),
}
# Name on the selector: (column, unit).
HISTORY_METRICS = {
    "Temperature": ("temperature", "°C"),
    "Feels-like difference": ("feels_delta", "°C"),
    "Humidity": ("humidity", "%"),
    "Wind": ("wind_kmh", "km/h"),
}


def show_finding(text):
    st.html(f'<div class="finding">{escape(text)}</div>')


def style_chart(fig, x_title, y_title, height=320):
    """Show a Plotly figure with the same look everywhere and both axes labelled."""
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        showlegend=False,
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, config={"displayModeBar": False})


def show_heatmap(table, title, x_title, y_title, number_format=".0f", colors=None, zmin=None, zmax=None, height=320):
    """A heatmap with the value in each cell. The title carries the unit, so no colour bar is needed."""
    fig = px.imshow(table, text_auto=number_format, aspect="auto", title=title, color_continuous_scale=colors or HEAT_COLORS, zmin=zmin, zmax=zmax)
    fig.update_xaxes(type="category")
    fig.update_yaxes(type="category")
    style_chart(fig, x_title, y_title, height)


def date_labels(dates):
    """Turn date text such as 2026-11-03 into Tue 3."""
    labels = []
    for date in dates:
        day = pd.to_datetime(date)
        labels.append(f"{day.strftime('%a')} {day.day}")
    return labels


def week_labels(dates):
    """Turn date text such as 2026-08-03 into 3 Aug, so a long calendar shows its months."""
    labels = []
    for date in dates:
        day = pd.to_datetime(date)
        labels.append(f"{day.day} {day.strftime('%b')}")
    return labels


def load_air_history(weather):
    """Return the selected city's air quality history as a table, or None if it is not available."""
    location = weather["location"]
    try:
        rows = fetch_air_history(location["latitude"], location["longitude"], AIR_HISTORY_DAYS)
    except ValueError:
        return None
    if len(rows) == 0:
        return None
    return add_local_time(pd.DataFrame(rows), weather["reading"].timezone_offset or 0)


# Overview strip


def best_time_tile(measures):
    windows = ranked_windows(measures, 1)
    if len(windows) == 0:
        return cards.tile("Best time outside", "No clear window")
    best = windows.to_dict("records")[0]
    return cards.tile("Best time outside", f"{best['local_time'].strftime('%a %H:%M')}–{best['end_time'].strftime('%H:%M')}", f"Comfort {best['score']:.0f} out of 100")


def next_rain_tile(measures):
    total = measures["precipitation_mm"].sum()
    first = next_rain(measures)
    if len(first) == 0:
        return cards.tile("Next rain", "None expected", "0 mm over 5 days")
    return cards.tile("Next rain", first["local_time"].to_list()[0].strftime("%a %H:%M"), f"{total:.1f} mm over 5 days")


def windiest_tile(measures):
    row = windiest_moment(measures).to_dict("records")[0]
    return cards.tile("Windiest moment", row["local_time"].strftime("%a %H:%M"), f"{row['wind_kmh']:.0f} km/h, gusts {row['gust_kmh']:.0f} km/h")


def air_overview_tile(weather):
    location = weather["location"]
    value = "Unavailable"
    small = ""
    try:
        rows = fetch_air_now(location["latitude"], location["longitude"])
        if len(rows) > 0:
            value = aqi_label(rows[0].get("aqi"))
    except ValueError:
        value = "Unavailable"
    air = load_air_history(weather)
    if air is not None:
        counts = days_over_any_guideline(air).to_dict("records")[0]
        small = f"Over a WHO guideline on {counts['days_over']} of the last {counts['days']} days"
    return cards.tile("Air quality today", value, small)


def show_overview(weather):
    if weather is None or weather["steps"] is None:
        return
    measures = forecast_measures(weather["steps"])
    st.html('<div class="grid-4">' + best_time_tile(measures) + next_rain_tile(measures) + windiest_tile(measures) + air_overview_tile(weather) + "</div>")


# Plan the week


def show_plan(weather):
    measures = forecast_measures(weather["steps"])
    with st.container(key="panel-plan"):
        metric = st.segmented_control("Show", list(PLAN_METRICS.keys()), default="Comfort", required=True, key="plan_metric", label_visibility="collapsed")
        column, title = PLAN_METRICS[metric]
        peak = measures.sort_values(column, ascending=False).to_dict("records")[0]
        show_finding(plan_finding(metric, peak["local_time"].strftime("%A at %H:%M"), peak[column]))
        table = week_grid(measures, column)
        table.index = date_labels(table.index)
        show_heatmap(table, title, "Local time", "Day", height=340)
        st.caption("Comfort starts at 100 and loses 3 per °C of feels-like away from 21 °C, 30 × the chance of rain, 1 per km/h of wind above 20, and 0.3 per % of humidity above 70.")

    windows = ranked_windows(measures, 3)
    with st.container(key="panel-windows"):
        st.html('<div class="card-title">Best windows to be outside</div>')
        if len(windows) == 0:
            st.info("The forecast has no daytime window to rank.")
        rows = ""
        number = 1
        for window in windows.to_dict("records"):
            when = f"{window['local_time'].strftime('%A %H:%M')}–{window['end_time'].strftime('%H:%M')}"
            reason = window_reason(window["feels"], window["rain_chance"], window["wind"])
            rows = rows + f'<div class="window"><b>{number}. {when}</b>, comfort {window["score"]:.0f}<div class="small">{reason}</div></div>'
            number = number + 1
        st.html(rows)


# Air


def show_air(weather):
    air = load_air_history(weather)
    if air is None:
        st.warning("Air quality history is not available for this city right now.")
        return

    with st.container(key="panel-calendar"):
        table_rows = who_comparison(air).to_dict("records")
        show_finding(who_finding(table_rows))
        calendar = air_calendar(air)
        calendar.index = [WEEKDAYS[number] for number in calendar.index]
        calendar.columns = week_labels(calendar.columns)
        show_heatmap(calendar, "Worst AQI each day (1 is good, 5 is very poor)", "Week starting", "Weekday", colors=AQI_COLORS, zmin=1, zmax=5, height=340)
        st.caption("Modelled OpenWeatherMap data, not readings from a local station. Guidelines: WHO 2021.")

    with st.container(key="panel-hours"):
        names = {}
        for key, name in POLLUTANT_NAMES.items():
            names[name] = key
        chosen = st.segmented_control("Pollutant", list(names.keys()), default="PM2.5", required=True, key="air_pollutant", label_visibility="collapsed")
        by_hour = air_by_hour(air, names[chosen])
        peak = by_hour.sort_values("level", ascending=False).to_dict("records")[0]
        show_finding(peak_hour_finding(chosen, int(peak["hour"]), peak["level"]))
        fig = px.line(by_hour, x="hour", y="level", markers=True, title=f"{chosen} through the day (µg/m³)", color_discrete_sequence=[LINE_COLOR])
        style_chart(fig, "Local hour", "Average level (µg/m³)", 280)

    with st.container(key="panel-who"):
        st.html('<div class="card-title">Against the WHO guidelines</div><div class="small">Levels in µg/m³</div>')
        table = pd.DataFrame(table_rows)[["pollutant", "guideline", "average_level", "days_over"]]
        table.columns = ["Pollutant", "Guideline", "Average", "Days over"]
        st.dataframe(table, hide_index=True)
        show_air_outlook(weather)


def show_air_outlook(weather):
    location = weather["location"]
    try:
        rows = fetch_air_forecast(location["latitude"], location["longitude"])
    except ValueError:
        return
    if len(rows) == 0:
        return
    daily = daily_worst_aqi(add_local_time(pd.DataFrame(rows), weather["reading"].timezone_offset or 0)).head(4)
    parts = []
    for label, aqi in zip(date_labels(daily["local_date"]), daily["aqi"]):
        parts.append(f"{label}: {aqi_label(aqi)}")
    st.write("**Outlook, worst of each day.** " + ", ".join(parts))


# Compare


def compare_data(metric, loaded):
    """Return one table of forecast steps or air rows from every loaded city, with a location column."""
    frames = []
    for weather in loaded:
        name = weather["location"]["location"]
        if metric == "Air quality":
            try:
                rows = fetch_air_forecast(weather["location"]["latitude"], weather["location"]["longitude"])
            except ValueError:
                continue
            if len(rows) == 0:
                continue
            frame = add_local_time(pd.DataFrame(rows), weather["reading"].timezone_offset or 0)
        elif weather["steps"] is None:
            continue
        else:
            frame = forecast_measures(weather["steps"])
        frame["location"] = name
        frames.append(frame)
    return frames


def show_compare(weather_by_city):
    loaded = [weather for weather in weather_by_city if weather["reading"] is not None]
    if len(loaded) < 2:
        st.info("A comparison needs at least 2 saved cities that have loaded.")
        return

    # sorted() uses WeatherReading.__lt__. This sets the row order of the heatmap: warmest now first.
    readings = sorted([weather["reading"] for weather in loaded], reverse=True)
    order = [reading.location for reading in readings]

    with st.container(key="panel-compare"):
        metric = st.segmented_control("Compare", list(COMPARE_METRICS.keys()), default="Temperature", required=True, key="compare_metric", label_visibility="collapsed")
        frames = compare_data(metric, loaded)
        if len(frames) < 2:
            st.info("This comparison needs data from at least 2 cities.")
            return

        columns = {"Temperature": "temperature", "Rain": "precipitation_mm", "Wind": "wind_kmh", "Air quality": "aqi"}
        per_day, overall, bar_title, heat_title = COMPARE_METRICS[metric]
        city_days = city_day_values(pd.concat(frames, ignore_index=True), columns[metric], per_day)
        ranking = rank_cities(city_days, overall)

        top = ranking.to_dict("records")[0]
        bottom = ranking.to_dict("records")[-1]
        show_finding(comparison_finding(metric, top["location"], top["value"], bottom["location"], bottom["value"]))
        fig = px.bar(ranking, x="location", y="value", color_discrete_sequence=[LINE_COLOR], text_auto=".1f")
        style_chart(fig, "City", bar_title, 280)

        grid = city_day_grid(city_days, order)
        grid.columns = date_labels(grid.columns)
        number_format = ".1f" if metric == "Rain" else ".0f"
        height = 120 + 60 * len(grid)
        if metric == "Air quality":
            show_heatmap(grid, heat_title, "Local date", "City", colors=AQI_COLORS, zmin=1, zmax=5, height=height)
        else:
            show_heatmap(grid, heat_title, "Local date", "City", number_format=number_format, height=height)


# History


def show_history(log, location):
    with st.container(key="panel-coverage"):
        st.html('<div class="card-title">What your log holds</div>')
        lines = []
        for row in log_coverage(log).to_dict("records"):
            lines.append(escape(coverage_text(row["location"], row["readings"], row["span_hours"])))
        st.html('<div class="small">' + "<br>".join(lines) + "</div>")

    if location is None:
        return

    name = location["location"]
    series = history_series(log, name)
    span_hours = 0
    if len(series) > 1:
        span_hours = (series["time"].max() - series["time"].min()).total_seconds() / 3600
    if len(series) < MIN_TREND_READINGS or span_hours < MIN_TREND_HOURS:
        st.info(too_little_history_text(location["city"], len(series), span_hours))
        return

    with st.container(key="panel-trend"):
        metric = st.segmented_control("Show", list(HISTORY_METRICS.keys()), default="Temperature", required=True, key="history_metric", label_visibility="collapsed")
        column, unit = HISTORY_METRICS[metric]
        show_finding(trend_finding(series[column].to_list(), metric, unit))
        is_local = series["is_local"].to_list()[0]
        fig = px.line(series, x="time", y=column, markers=True, title=f"{metric} ({unit})", color_discrete_sequence=[LINE_COLOR])
        style_chart(fig, "Local time" if is_local else "UTC (local offset not logged yet)", f"{metric} ({unit})")

    stats = daily_log_stats(series)
    if len(stats) >= 2:
        with st.container(key="panel-range"):
            st.html('<div class="card-title">Daily range</div>')
            table = stats[["day", "low", "high", "range"]].copy()
            table["day"] = week_labels(table["day"])
            table.columns = ["Day", "Low °C", "High °C", "Range °C"]
            st.dataframe(table, hide_index=True)


def show_analytics_tab(weather, weather_by_city):
    if API_KEY:
        show_overview(weather)

    plan_tab, air_tab, compare_tab, history_tab = st.tabs(["Plan the week", "Air", "Compare", "History"], key="analytics_tab", on_change="rerun")

    # .open is True only for the tab on screen, so the others make no API calls.
    if plan_tab.open:
        with plan_tab:
            if not API_KEY:
                st.info(SETUP_MESSAGE)
            elif weather is None or weather["steps"] is None:
                st.info("The forecast for this city is not available right now.")
            else:
                show_plan(weather)

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
                show_compare(weather_by_city)

    if history_tab.open:
        with history_tab:
            log = load_log()
            if len(log) == 0:
                st.info("Your log is empty. Open the Weather tab with an API key to start building history.")
            else:
                show_history(log, None if weather is None else weather["location"])
