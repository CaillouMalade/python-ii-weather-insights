"""The Streamlit entry point. The real work is in the weather_app package."""

import streamlit as st

from weather_app.display import background_for, is_night
from weather_app.fetching import load_current, now_seconds
from weather_app.storage import load_circuits
from weather_app.style import apply_style
from weather_app.views import show_history, show_phone_picker, show_sidebar, show_today

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")

circuits = load_circuits()
# Every circuit is fetched here, because the sidebar shows them all. One failure stays with its circuit.
current_by_circuit = [load_current(circuit) for circuit in circuits]

ids = [circuit["id"] for circuit in circuits]
if st.session_state.get("selected") not in ids:
    st.session_state["selected"] = ids[0]
selected_id = st.session_state["selected"]
selected = current_by_circuit[ids.index(selected_id)]

now = now_seconds()
background = background_for(None, False)
if selected["reading"] is not None:
    reading = selected["reading"]
    background = background_for(reading.weather_id, is_night(now, reading.sunrise, reading.sunset))
apply_style(background)

show_sidebar(current_by_circuit, selected_id, now)
show_phone_picker(circuits, selected_id)

today_tab, history_tab = st.tabs(["Today", "History"], key="main_tab", on_change="rerun")

# .open is True only for the tab on screen, so the other one does no work.
if today_tab.open:
    with today_tab:
        show_today(selected)
if history_tab.open:
    with history_tab:
        show_history(selected["circuit"])
