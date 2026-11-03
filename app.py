"""The Streamlit entry point. The real work is in the weather_app package."""

import streamlit as st

from weather_app.fetching import load_circuit, now_seconds
from weather_app.storage import load_circuits
from weather_app.style import apply_style
from weather_app.views import show_history, show_phone_picker, show_sidebar, show_today

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")
apply_style()

circuits = load_circuits()
# Every circuit is loaded here, because each sidebar card has its own status light.
# One failure stays with its circuit.
loaded_circuits = [load_circuit(circuit) for circuit in circuits]

ids = [circuit["id"] for circuit in circuits]
if st.session_state.get("selected") not in ids:
    st.session_state["selected"] = ids[0]
selected_id = st.session_state["selected"]
selected = loaded_circuits[ids.index(selected_id)]

show_sidebar(loaded_circuits, selected_id, now_seconds())
show_phone_picker(circuits, selected_id)

today_tab, history_tab = st.tabs(["Today", "History"], key="main_tab", on_change="rerun")

# .open is True only for the tab on screen, so the other one does no work.
if today_tab.open:
    with today_tab:
        show_today(selected)
if history_tab.open:
    with history_tab:
        show_history(selected["circuit"])
