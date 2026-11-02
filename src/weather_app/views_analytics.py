"""The Analytics tab: four short answers, then Plan the week, Air, Compare and History."""

from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from . import cards
from .analytics import (
    add_local_time,
    air_by_hour,
    complete_days,
    aqi_day_shares,
    city_week_summary,
    daily_log_stats,
    daily_worst_aqi,
    day_parts,
    days_over_any_guideline,
    forecast_measures,
    history_series,
    log_coverage,
    next_rain,
    who_comparison,
    windiest_moment,
)
from .config import API_KEY, SETUP_MESSAGE
from .display import aqi_label, format_local_time, rain_axis_ticks
from .fetching import fetch_air_forecast, fetch_air_history, fetch_air_now, now_seconds
from .findings import (
    air_headline,
    best_and_worst_parts,
    capitalize_first,
    coverage_sentence,
    daily_range_sentence,
    day_summary,
    guideline_days_text,
    lowest_names,
    part_name,
    rain_amount_text,
    sort_city_rows,
    time_of_day_text,
    too_little_history_text,
    trend_finding,
    week_headline,
    winner_names,
)
from .storage import load_log

AIR_HISTORY_DAYS = 90
# A line needs a few points over some real time before it can suggest anything.
MIN_TREND_READINGS = 3
MIN_TREND_HOURS = 1
# Below this much history, the chart carries a note that more data will help.
SETTLED_HISTORY_HOURS = 72

TEMPERATURE_COLOR = "#ffb86b"
RAIN_COLOR = "#7fd0f5"

# Name on the selector: (column, unit).
HISTORY_METRICS = {
    "Temperature": ("temperature", "°C"),
    "Feels like": ("feels_like", "°C"),
    "Humidity": ("humidity", "%"),
    "Wind": ("wind_kmh", "km/h"),
}
COMPARE_ORDERS = ["Warmest", "Driest", "Calmest", "Cleanest air"]


def show_finding(text):
    st.html(f'<div class="finding">{escape(text)}</div>')


def style_chart(fig, x_title, y_title, height=300, legend=False):
    """Show a Plotly figure with the same look everywhere and both axes labelled."""
    fig.update_layout(
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=height,
        margin=dict(l=10, r=10, t=36, b=10),
        showlegend=legend,
        legend=dict(orientation="h", x=0, y=1.02, yanchor="bottom"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, config={"displayModeBar": False})


def today_text(weather):
    return format_local_time(now_seconds(), weather["reading"].timezone_offset or 0, "%Y-%m-%d")


def short_date(date):
    """Turn date text such as 2026-08-03 into Mon 3."""
    day = pd.to_datetime(date)
    return f"{day.strftime('%a')} {day.day}"


def load_air_history(weather):
    """Return the selected city's air quality history as a table, or None if it is not available."""
    location = weather["location"]
    try:
        # One day more than we show, because the first and last day in the answer are only part-days.
        rows = fetch_air_history(location["latitude"], location["longitude"], AIR_HISTORY_DAYS + 1)
    except ValueError:
        return None
    if len(rows) == 0:
        return None
    return complete_days(add_local_time(pd.DataFrame(rows), weather["reading"].timezone_offset or 0), AIR_HISTORY_DAYS)


def air_now(weather):
    """Return the current AQI (1 to 5) of a city, or None if it is not available."""
    location = weather["location"]
    try:
        rows = fetch_air_now(location["latitude"], location["longitude"])
    except ValueError:
        return None
    if len(rows) == 0:
        return None
    return rows[0].get("aqi")


# The four short answers


def best_time_tile(parts, today):
    if len(parts) == 0:
        return cards.tile("Best time outside", "Not known yet")
    best, _ = best_and_worst_parts(parts)
    return cards.tile("Best time outside", capitalize_first(part_name(best, today)), f"{best['rating']}: {best['reason']}")


def next_rain_tile(measures):
    amount = rain_amount_text(measures["precipitation_mm"].sum())
    first = next_rain(measures)
    if len(first) == 0:
        return cards.tile("Next rain", "None expected", "Dry for the next 5 days")
    return cards.tile("Next rain", first["local_time"].to_list()[0].strftime("%a %H:%M"), f"{amount} over 5 days")


def windiest_tile(measures):
    row = windiest_moment(measures).to_dict("records")[0]
    return cards.tile("Windiest moment", row["local_time"].strftime("%a %H:%M"), f"{row['wind_kmh']:.0f} km/h, gusts up to {row['gust_kmh']:.0f} km/h")


def air_tile(weather):
    aqi = air_now(weather)
    value = "Not available" if aqi is None else aqi_label(aqi)
    small = ""
    air = load_air_history(weather)
    if air is not None:
        counts = days_over_any_guideline(air).to_dict("records")[0]
        small = guideline_days_text(counts["days_over"], counts["days"])
    return cards.tile("Air quality today", value, small)


def show_overview(weather):
    if weather is None or weather["steps"] is None:
        return
    measures = forecast_measures(weather["steps"])
    parts = day_parts(measures).to_dict("records")
    st.html('<div class="grid-4">' + best_time_tile(parts, today_text(weather)) + next_rain_tile(measures) + windiest_tile(measures) + air_tile(weather) + "</div>")


# Plan the week


def show_outlook_chart(measures):
    fig = go.Figure()
    fig.add_bar(x=measures["local_time"], y=measures["precipitation_mm"], name="Rain", marker_color=RAIN_COLOR, yaxis="y2", opacity=0.45)
    fig.add_scatter(x=measures["local_time"], y=measures["temperature"], name="Temperature", mode="lines", line=dict(color=TEMPERATURE_COLOR, width=2.5))
    # Set by hand: left alone, this axis lines up with the temperature gridlines and gets odd values.
    ticks = rain_axis_ticks(measures["precipitation_mm"].max())
    fig.update_layout(yaxis2=dict(title="Rain (mm)", overlaying="y", side="right", range=[0, ticks[-1]], tickmode="array", tickvals=ticks, showgrid=False))
    style_chart(fig, "Local time", "Temperature (°C)", 260, legend=True)


def show_plan(weather):
    measures = forecast_measures(weather["steps"])
    parts = day_parts(measures)
    today = today_text(weather)
    show_finding(week_headline(parts.to_dict("records"), today))

    with st.container(key="panel-outlook"):
        show_outlook_chart(measures)

    html = ""
    for day in weather["days"].to_dict("records"):
        rows = parts[parts["local_date"] == day["local_date"]].to_dict("records")
        if len(rows) == 0:
            continue
        name = "Today" if day["local_date"] == today else short_date(day["local_date"])
        html = html + cards.plan_day(name, day["icon"], day["high"], day["low"], day_summary(rows, day["high"]), rows)
    st.html(f'<div class="plan">{html}</div>')

    with st.expander("How we rate this"):
        st.write(
            "Each part of the day gets a comfort score out of 100. It starts at 100 and loses 3 points per °C that it feels away from 21 °C, "
            "30 points times the chance of rain, 1 point per km/h of wind above 20 km/h, and 0.3 points per % of humidity above 70 %. "
            "80 and above is Great, 60 is Good, 40 is OK, and anything lower is Poor. If rain is likely or it is very windy, the most it can be is OK; "
            "with a chance of rain or some wind, the most it can be is Good. This is our own rule of thumb, not a scientific index."
        )


# Air


def show_air(weather):
    air = load_air_history(weather)
    if air is None:
        st.warning("Air quality history is not available for this city right now.")
        return

    guidelines = who_comparison(air).to_dict("records")
    shares = aqi_day_shares(air)
    usual = shares.sort_values("days", ascending=False).to_dict("records")[0]
    worst = guidelines[0]
    show_finding(air_headline(weather["name"], usual["band"], worst["pollutant"], worst["days_over"]))

    with st.container(key="panel-air-days"):
        st.html('<div class="card-title">How the last 3 months looked</div>' + cards.air_share_bar(shares.to_dict("records")))

    with st.container(key="panel-air-pollutants"):
        st.html('<div class="card-title">What is in the air</div>' + cards.pollutant_rows(guidelines))
        by_hour = air_by_hour(air, worst["pollutant"]).dropna()
        if len(by_hour) > 0:
            rows = by_hour.sort_values("level").to_dict("records")
            st.write(time_of_day_text(worst["pollutant"], int(rows[0]["hour"]), rows[0]["level"], int(rows[-1]["hour"]), rows[-1]["level"]))

    show_air_outlook(weather)
    st.caption("Modelled by OpenWeatherMap, not measured at a local station. A day counts by its worst hour, and only days with full data count. Health guidelines: WHO, 2021.")


def show_air_outlook(weather):
    location = weather["location"]
    try:
        rows = fetch_air_forecast(location["latitude"], location["longitude"])
    except ValueError:
        return
    if len(rows) == 0:
        return
    daily = daily_worst_aqi(add_local_time(pd.DataFrame(rows), weather["reading"].timezone_offset or 0)).head(4)
    days = []
    for date, aqi in zip(daily["local_date"], daily["aqi"]):
        days.append((short_date(date), aqi_label(aqi)))
    st.html(cards.air_outlook(days))


# Compare


def compare_rows(loaded):
    """One row per city. The order comes from sorted() on the reading objects: warmest first."""
    readings = sorted([weather["reading"] for weather in loaded], reverse=True)

    frames = []
    for weather in loaded:
        if weather["steps"] is not None:
            frame = forecast_measures(weather["steps"])
            frame["location"] = weather["location"]["location"]
            frames.append(frame)
    summaries = {}
    if len(frames) > 0:
        for row in city_week_summary(pd.concat(frames, ignore_index=True)).to_dict("records"):
            summaries[row["location"]] = row

    rows = []
    for reading in readings:
        for weather in loaded:
            if weather["reading"].location != reading.location:
                continue
            # A city without a forecast has no week figures, so those are left blank.
            summary = summaries.get(reading.location)
            rows.append(
                {
                    "name": weather["name"],
                    "now": reading.temperature,
                    "high": None if summary is None else summary["high"],
                    "low": None if summary is None else summary["low"],
                    "rain_mm": 0 if summary is None else summary["rain_mm"],
                    "wind_kmh": 0 if summary is None else summary["wind_kmh"],
                    "aqi": air_now(weather),
                }
            )
    return rows


def compare_tiles(rows):
    total = len(rows)
    warmest = rows[0]
    warmest_names = [row["name"] for row in rows if round(row["now"]) == round(warmest["now"])]
    driest = lowest_names(rows, "rain_mm")
    calmest = lowest_names(rows, "wind_kmh")
    cleanest = lowest_names(rows, "aqi")

    driest_value = min([row["rain_mm"] for row in rows])
    driest_text = "No rain this week" if driest_value == 0 else f"{rain_amount_text(driest_value)} this week"
    calmest_value = min([row["wind_kmh"] for row in rows])

    air_value = "Not available"
    air_small = ""
    if len(cleanest) > 0:
        air_value = winner_names(cleanest, total)
        best_aqi = min([row["aqi"] for row in rows if row["aqi"] is not None])
        air_small = f"{aqi_label(best_aqi)} air right now"

    return (
        '<div class="grid-4">'
        + cards.tile("Warmest", escape(winner_names(warmest_names, total)), f"{round(warmest['now'])}° right now")
        + cards.tile("Driest", escape(winner_names(driest, total)), driest_text)
        + cards.tile("Calmest", escape(winner_names(calmest, total)), f"Wind around {calmest_value:.0f} km/h")
        + cards.tile("Cleanest air", escape(air_value), air_small)
        + "</div>"
    )


def show_compare(weather_by_city):
    loaded = [weather for weather in weather_by_city if weather["reading"] is not None]
    if len(loaded) < 2:
        st.info("Add at least one more city in the sidebar to compare them.")
        return

    rows = compare_rows(loaded)
    st.html(compare_tiles(rows))
    with st.container(key="panel-compare"):
        order = st.segmented_control("Sort by", COMPARE_ORDERS, default="Warmest", required=True, key="compare_order", label_visibility="collapsed")
        st.html(cards.city_table(sort_city_rows(rows, order)))
        st.caption("High, low, rain and wind cover the next 5 days. Wind is the average.")


# History


def show_history(log, weather, names):
    coverage = []
    for row in log_coverage(log).to_dict("records"):
        coverage.append({"name": names.get(row["location"], row["location"]), "readings": row["readings"], "span_hours": row["span_hours"]})
    if weather is None:
        show_finding(coverage_sentence(coverage, None))
        return
    show_finding(coverage_sentence(coverage, weather["name"]))

    series = history_series(log, weather["location"]["location"])
    span_hours = 0
    if len(series) > 1:
        span_hours = (series["time"].max() - series["time"].min()).total_seconds() / 3600
    if len(series) < MIN_TREND_READINGS or span_hours < MIN_TREND_HOURS:
        st.info(too_little_history_text(weather["name"], len(series), span_hours))
        return

    with st.container(key="panel-trend"):
        metric = st.segmented_control("Show", list(HISTORY_METRICS.keys()), default="Temperature", required=True, key="history_metric", label_visibility="collapsed")
        column, unit = HISTORY_METRICS[metric]
        known = series.dropna(subset=[column])
        st.write(trend_finding(known[column].to_list(), metric, unit))
        is_local = series["is_local"].to_list()[0]
        fig = px.line(known, x="time", y=column, markers=True, color_discrete_sequence=[RAIN_COLOR])
        style_chart(fig, "Local time" if is_local else "UTC (local offset not logged yet)", f"{metric} ({unit})")
        if span_hours < SETTLED_HISTORY_HOURS:
            st.caption("This only covers a short time so far. More readings will make it clearer.")

    stats = daily_log_stats(series)
    full_days = stats[stats["readings"] >= 2]
    labels = [short_date(day) for day in full_days["day"]]
    sentence = daily_range_sentence(labels, full_days["range"].to_list())
    if sentence != "":
        st.write(sentence)


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
                names = {}
                for city in weather_by_city:
                    names[city["location"]["location"]] = city["name"]
                show_history(log, weather, names)
