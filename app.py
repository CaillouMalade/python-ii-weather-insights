"""Streamlit UI only. Weather logic lives in the weather_app package."""

import pandas as pd
import plotly.express as px
import streamlit as st

from weather_app.analytics import feels_like_delta, latest_ranking, reading_counts, temperature_trend
from weather_app.client import WeatherClient
from weather_app.config import API_KEY, SETUP_MESSAGE
from weather_app.storage import append_reading, load_log, load_saved_locations

TEN_MINUTES = 600


# Logging happens inside the cached function, so ordinary Streamlit reruns reuse
# the cached reading and cannot append duplicate rows. Failures are not cached.
@st.cache_data(ttl=TEN_MINUTES)
def fetch_and_log_current(location):
    reading = WeatherClient(API_KEY).current(location)
    append_reading(reading)
    return reading


@st.cache_data(ttl=TEN_MINUTES)
def fetch_forecast(latitude, longitude):
    return WeatherClient(API_KEY).forecast(latitude, longitude)


def add_city(city):
    """Geocode the typed city and add its top match to the sidebar list."""
    try:
        location = WeatherClient(API_KEY).find_city(city)
    except ValueError as e:
        st.sidebar.error(str(e))
        return

    names = [saved["name"] for saved in st.session_state["locations"]]
    if location["name"] in names:
        st.sidebar.info(f"{location['name']} is already in your list.")
    else:
        st.session_state["locations"].append(location)
        st.sidebar.success(f"Added {location['name']}.")
    st.session_state["selected_city"] = location["name"]


def show_sidebar():
    """Draw the sidebar and return the chosen view and the selected city name."""
    view = st.sidebar.radio("View", ["Live Conditions", "Analytics"])

    st.sidebar.header("Your cities")
    if API_KEY:
        with st.sidebar.form("add_city_form", clear_on_submit=True):
            city = st.text_input("Add a city", placeholder="e.g. Madrid")
            submitted = st.form_submit_button("Add")
        if submitted:
            add_city(city)
    else:
        st.sidebar.caption("Adding cities needs an API key.")

    names = [location["name"] for location in st.session_state["locations"]]
    if len(names) == 0:
        st.sidebar.info("No cities yet.")
        return view, None

    # The selection can point to a city that was just removed.
    if st.session_state.get("selected_city") not in names:
        st.session_state["selected_city"] = names[0]
    selected = st.sidebar.radio("Selected city", names, key="selected_city")

    if st.sidebar.button("Remove selected city"):
        keep = [location for location in st.session_state["locations"] if location["name"] != selected]
        st.session_state["locations"] = keep
        st.rerun()
    st.sidebar.caption("Removing lasts until you refresh the page: saved history stays in the log.")

    return view, selected


def show_weather_card(reading):
    """A phone-style card made of ordinary Streamlit elements."""
    with st.container(border=True, width=420):
        st.subheader(reading.location)
        st.metric("Temperature", f"{reading.temperature:.1f} °C")
        st.write(reading.conditions.capitalize())
        st.write(f"Feels like: {reading.feels_like:.1f} °C")
        st.write(f"Humidity: {reading.humidity} %")
        st.write(f"Wind: {reading.wind_speed:.1f} m/s")
        show_forecast_chart(reading)


def show_forecast_chart(reading):
    try:
        forecast = pd.DataFrame(fetch_forecast(reading.latitude, reading.longitude))
    except ValueError as e:
        st.warning(f"Could not load the forecast: {e}")
        return

    forecast["time"] = pd.to_datetime(forecast["time"])
    fig = px.line(forecast, x="time", y="temperature", title="Forecast")
    fig.update_layout(xaxis_title="Time (UTC)", yaxis_title="Temperature (°C)", height=260)
    st.plotly_chart(fig)


def show_comparison(readings):
    """All sidebar cities, warmest first. sorted() uses WeatherReading.__lt__."""
    st.subheader("All your cities")
    rows = [reading.to_dict() for reading in sorted(readings, reverse=True)]
    table = pd.DataFrame(rows)[["location", "temperature", "feels_like", "humidity", "wind_speed", "conditions"]]
    table.columns = ["City", "Temperature (°C)", "Feels like (°C)", "Humidity (%)", "Wind (m/s)", "Conditions"]
    st.dataframe(table, hide_index=True)


def show_live_view(selected):
    st.header("Live Conditions")
    if not API_KEY:
        st.warning(SETUP_MESSAGE)
        return
    if selected is None:
        st.info("Add a city in the sidebar to get started.")
        return

    # One bad location shows a warning and the others still load.
    readings = []
    for location in st.session_state["locations"]:
        try:
            readings.append(fetch_and_log_current(location))
        except ValueError as e:
            st.warning(f"Could not load {location['name']}: {e}")

    for reading in readings:
        if reading.location == selected:
            show_weather_card(reading)

    if len(readings) > 0:
        show_comparison(readings)
    st.caption("Readings refresh at most every 10 minutes.")


def show_trend(log, selected):
    st.subheader("Temperature trend")
    if selected is None:
        st.info("Select a city in the sidebar to see its trend.")
        return

    trend = temperature_trend(log, selected)
    if len(trend) < 2:
        st.info(f"{selected} has {len(trend)} saved reading(s). A trend needs at least 2.")
        return

    fig = px.line(trend, x="timestamp_utc", y="temperature", markers=True, title=selected)
    fig.update_layout(xaxis_title="Time logged (UTC)", yaxis_title="Temperature (°C)")
    st.plotly_chart(fig)


def show_ranking(log):
    st.subheader("Cities ranked by latest temperature")
    ranking = latest_ranking(log)
    if len(ranking) < 2:
        st.info("Only one city has saved readings. A comparison needs at least 2 cities.")

    fig = px.bar(ranking, x="location", y="temperature")
    fig.update_layout(xaxis_title="City", yaxis_title="Latest temperature (°C)")
    st.plotly_chart(fig)

    table = ranking.copy()
    table.columns = ["Rank", "City", "Latest temperature (°C)", "Logged at (UTC)"]
    st.dataframe(table, hide_index=True)


def show_feels_like_delta(log):
    st.subheader("Feels-like minus actual temperature")
    st.caption("Above 0 it feels warmer than the thermometer says; below 0 it feels colder.")

    counts = reading_counts(log)
    short_history = counts[counts["readings"] < 2]["location"].to_list()
    if len(short_history) > 0:
        names = ", ".join(short_history)
        st.info(f"Only one saved reading so far, so no line yet: {names}.")

    fig = px.line(feels_like_delta(log), x="timestamp_utc", y="feels_like_delta", color="location", markers=True)
    fig.update_layout(xaxis_title="Time logged (UTC)", yaxis_title="Feels-like minus actual (°C)", legend_title="City")
    st.plotly_chart(fig)


def show_analytics_view(selected):
    """Reads only the saved log and makes no API calls."""
    st.header("Analytics")
    log = load_log()
    if len(log) == 0:
        st.info("The weather log is empty. Open Live Conditions with an API key to start building history.")
        return

    show_trend(log, selected)
    show_ranking(log)
    show_feels_like_delta(log)


st.set_page_config(page_title="Weather Insights", page_icon="\U0001F324️")
st.title("Weather Insights")

# Seed once per session. A refresh starts a new session, so cities come back from the log.
if "locations" not in st.session_state:
    st.session_state["locations"] = load_saved_locations()

chosen_view, chosen_city = show_sidebar()

if chosen_view == "Live Conditions":
    show_live_view(chosen_city)
elif chosen_view == "Analytics":
    show_analytics_view(chosen_city)
