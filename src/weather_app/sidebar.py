"""The sidebar: city search and the saved cities as tappable cards."""

import streamlit as st

from .cards import city_card
from .fetching import now_seconds
from .storage import load_city_list, rows_to_locations, save_cities


@st.cache_data(show_spinner=False)
def city_list():
    return load_city_list()


def select_city(name):
    st.session_state["selected_city"] = name


def add_chosen_city():
    """Runs when a city is picked in the search box. Saves it and clears the box."""
    label = st.session_state["city_search"]
    st.session_state["city_search"] = None
    if label is None:
        return

    cities = city_list()
    location = rows_to_locations(cities[cities["label"] == label])[0]
    names = [saved["location"] for saved in st.session_state["locations"]]
    if location["location"] not in names:
        st.session_state["locations"].append(location)
        save_cities(st.session_state["locations"])
    st.session_state["selected_city"] = location["location"]


def remove_city(name):
    keep = [saved for saved in st.session_state["locations"] if saved["location"] != name]
    st.session_state["locations"] = keep
    save_cities(keep)
    if st.session_state.get("selected_city") == name:
        st.session_state["selected_city"] = None


def phone_city_changed():
    st.session_state["selected_city"] = st.session_state["phone_city"]


def show_city_search(where):
    where.selectbox(
        "Add a city",
        city_list()["label"].to_list(),
        index=None,
        placeholder="🔍 Search for a city",
        key="city_search",
        on_change=add_chosen_city,
        label_visibility="collapsed",
    )


def show_sidebar(weather_by_city, selected, now):
    show_city_search(st.sidebar)
    if len(weather_by_city) == 0:
        st.sidebar.info("Search above to add your first city.")
    for number in range(len(weather_by_city)):
        weather = weather_by_city[number]
        location = weather["location"]
        name = location["location"]
        # An invisible button lies over the card (see style.py), so the whole card is tappable.
        with st.sidebar.container(key=f"city-{number}"):
            st.html(city_card(location["city"], weather["reading"], weather["high"], weather["low"], weather["note"], name == selected, now))
            st.button(f"Open {location['city']}", key=f"open-{number}", on_click=select_city, args=(name,))
            st.button("✕", key=f"remove-{number}", on_click=remove_city, args=(name,))


def show_phone_city_picker(weather_by_city, selected):
    """Only visible on narrow screens (see style.py), where the sidebar starts closed."""
    if len(weather_by_city) == 0:
        return
    names = [weather["location"]["location"] for weather in weather_by_city]
    st.session_state["phone_city"] = selected
    with st.container(key="phone-city"):
        st.selectbox("Your cities", names, key="phone_city", on_change=phone_city_changed)
