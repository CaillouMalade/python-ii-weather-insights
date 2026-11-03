"""The Streamlit entry point. The real work is in the weather_app package."""

import streamlit as st

from weather_app.fetching import load_circuit
from weather_app.storage import load_circuits
from weather_app.style import apply_style
from weather_app.views import chosen_track, show_credits, show_history, show_sessions, show_today, show_track_picker

st.set_page_config(page_title="Racetrack Weather", page_icon="🏁", layout="wide")
apply_style()

circuits = load_circuits()
track = chosen_track(circuits)
show_track_picker(circuits)
circuit = circuits[[circuit["id"] for circuit in circuits].index(track)]

# Only the selected track is fetched. A failure stays inside it as a note.
loaded = load_circuit(circuit)
session = show_sessions(loaded)

today_tab, history_tab = st.tabs(["Today", "History"], key="main_tab", on_change="rerun")

# .open is True only for the tab on screen, so the other one does no work.
if today_tab.open:
    with today_tab:
        show_today(loaded, session)
if history_tab.open:
    with history_tab:
        show_history(circuit)
show_credits()
