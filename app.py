"""The Streamlit entry point. The real work is in the weather_app package."""

import streamlit as st

from weather_app.display import background_for, display_names, is_night
from weather_app.fetching import load_city_weather, now_seconds
from weather_app.sidebar import show_phone_city_picker, show_sidebar
from weather_app.storage import load_saved_cities
from weather_app.style import apply_style
from weather_app.views_analytics import show_analytics_tab
from weather_app.views_weather import show_weather_tab

st.set_page_config(page_title="Weather Insights", page_icon="\U0001F324️", layout="wide")

if "locations" not in st.session_state:
    st.session_state["locations"] = load_saved_cities()

# Every saved city is fetched here, because the sidebar shows them all. One failure stays with its city.
weather_by_city = [load_city_weather(location) for location in st.session_state["locations"]]
shown_names = display_names(st.session_state["locations"])
for number in range(len(weather_by_city)):
    weather_by_city[number]["name"] = shown_names[number]
names = [weather["location"]["location"] for weather in weather_by_city]

# The selection can point to a city that was just removed.
if st.session_state.get("selected_city") not in names:
    st.session_state["selected_city"] = names[0] if len(names) > 0 else None
selected = st.session_state["selected_city"]

selected_weather = None
for weather in weather_by_city:
    if weather["location"]["location"] == selected:
        selected_weather = weather

now = now_seconds()
background = background_for(None, False)
if selected_weather is not None and selected_weather["reading"] is not None:
    reading = selected_weather["reading"]
    background = background_for(reading.weather_id, is_night(now, reading.sunrise, reading.sunset))
apply_style(background)

show_sidebar(weather_by_city, selected, now)
show_phone_city_picker(weather_by_city, selected)

weather_tab, analytics_tab = st.tabs(["Weather", "Analytics"], key="main_tab", on_change="rerun")

# .open is True only for the tab on screen, so the other one does no work.
if weather_tab.open:
    with weather_tab:
        show_weather_tab(selected_weather)
if analytics_tab.open:
    with analytics_tab:
        show_analytics_tab(selected_weather, weather_by_city)
