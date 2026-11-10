"""Weather Insights: the Streamlit entry point. The logic lives in the weather_app package."""

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import city_comparison, city_trend, daily_range, feels_like_gap, rank_by_temperature
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.fetching import fetch_many, find_city
from weather_app.storage import load_cities, load_log

st.set_page_config(page_title="Weather Insights", page_icon="🌤️", layout="wide")
st.title("Weather Insights")

# The fixed list from data/cities.csv, plus any city added this session.
if "cities" not in st.session_state:
    st.session_state["cities"] = load_cities()
cities = st.session_state["cities"]
names = [city["location"] for city in cities]


# Sidebar: choose cities, or add one.


def add_city():
    """Runs when the Add button is pressed, before the page reruns."""
    try:
        city = find_city(st.session_state["new_city"])
    except ValueError as error:
        st.session_state["add_message"] = str(error)
        return
    if city["location"] in names:
        st.session_state["add_message"] = f"{city['location']} is already in the list."
    else:
        cities.append(city)
        st.session_state["chosen"] = st.session_state["chosen"] + [city["location"]]
        st.session_state["add_message"] = f"Added {city['location']}."
    st.session_state["new_city"] = ""


with st.sidebar:
    st.header("Cities")
    if "chosen" not in st.session_state:
        st.session_state["chosen"] = names[:5]
    st.multiselect("Cities to compare", names, key="chosen")

    if API_KEY:
        st.text_input("Add another city", key="new_city", placeholder="e.g. Oslo")
        st.button("Add", on_click=add_city)
        if "add_message" in st.session_state:
            st.caption(st.session_state.pop("add_message"))

chosen = []
for city in cities:
    if city["location"] in st.session_state["chosen"]:
        chosen.append(city)

live_tab, analytics_tab = st.tabs(["Live conditions", "Analytics"])


# View 1: live conditions for the chosen cities.

with live_tab:
    if not API_KEY:
        st.warning(SETUP_MESSAGE)
    elif len(chosen) == 0:
        st.info("Pick at least one city in the sidebar.")
    else:
        with st.spinner("Fetching current weather"):
            readings, failures = fetch_many(chosen)
        for failure in failures:
            st.warning(f"Skipped {failure}")

        if len(readings) > 0:
            ranked = rank_by_temperature(readings)
            warmest = ranked[0]
            coldest = ranked[-1]
            columns = st.columns(2)
            columns[0].metric(f"Warmest now: {warmest.location}", f"{warmest.temperature:.1f} °C")
            columns[1].metric(f"Coldest now: {coldest.location}", f"{coldest.temperature:.1f} °C")

            rows = []
            for reading in ranked:
                rows.append(
                    {
                        "City": reading.location,
                        "Temperature (°C)": round(reading.temperature, 1),
                        "Feels like (°C)": round(reading.feels_like, 1),
                        "Humidity (%)": reading.humidity,
                        "Wind (km/h)": round(reading.wind_kmh, 1),
                        "Conditions": reading.conditions,
                    }
                )
            table = pd.DataFrame(rows)

            fig = px.bar(table, x="City", y="Temperature (°C)", title="Current temperature by city")
            st.plotly_chart(fig)
            st.dataframe(table, hide_index=True)
            st.caption("Each successful fetch is added to data/weather_log.csv. Readings refresh every 10 minutes.")


# View 2: analytics on our own logged history. Works without a key.

with analytics_tab:
    log = load_log()
    if len(log) == 0:
        st.info("The log is empty. Open Live conditions with an API key to start collecting.")
    else:
        first = log["timestamp_utc"].min().strftime("%d %b %Y")
        last = log["timestamp_utc"].max().strftime("%d %b %Y")
        st.caption(f"{len(log)} logged readings from {first} to {last} (UTC).")

        st.subheader("Trend over time")
        # The city with the most readings is shown first, because its trend says the most.
        logged_cities = list(log["location"].value_counts().index)
        city = st.selectbox("City", logged_cities)
        trend = city_trend(log, city)
        if len(trend) < 2:
            st.info(f"Only one reading for {city} so far. The trend appears from the second one.")
        else:
            trend = trend.rename(columns={"timestamp_utc": "Time (UTC)", "temperature": "Temperature", "feels_like": "Feels like"})
            fig = px.line(trend, x="Time (UTC)", y=["Temperature", "Feels like"], markers=True, title=f"{city}: logged temperature")
            fig.update_layout(yaxis_title="°C", legend_title_text="")
            st.plotly_chart(fig)

        st.subheader("Compare cities")
        comparison = city_comparison(log)
        fig = px.bar(comparison, x="location", y="average", error_y=comparison["highest"] - comparison["average"], error_y_minus=comparison["average"] - comparison["lowest"], title="Average logged temperature, with lowest and highest")
        fig.update_layout(xaxis_title="City", yaxis_title="°C")
        st.plotly_chart(fig)
        st.dataframe(comparison.round(1), hide_index=True)

        st.subheader("Derived metrics")
        columns = st.columns(2)
        with columns[0]:
            st.markdown("**Daily range** (highest minus lowest reading in a day, °C)")
            ranges = daily_range(log)
            if len(ranges) == 0:
                st.info("Needs two readings of one city on the same day.")
            else:
                st.dataframe(ranges.round(1), hide_index=True)
        with columns[1]:
            st.markdown("**Feels-like gap** (average feels-like minus real temperature, °C)")
            st.dataframe(feels_like_gap(log).round(1), hide_index=True)
