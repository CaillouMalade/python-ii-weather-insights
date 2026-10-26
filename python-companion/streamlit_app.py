"""Optional course-facing interface; the richer Pitwall app lives one folder up."""
import json
import sqlite3
from io import StringIO
import altair as alt
import pandas as pd
import streamlit as st
from pitwall_weather.analytics import derived_metrics, latest_comparison, temperature_trends
from pitwall_weather.clients import GeocodingClient, OpenMeteoClient, OpenWeatherClient, fetch_many
from pitwall_weather.config import load_config
from pitwall_weather.errors import WeatherError
from pitwall_weather.models import Location
from pitwall_weather.storage import SnapshotStore
from pitwall_weather.tracks import TRACKS

st.set_page_config(page_title="Pitwall · Python companion", page_icon="🏁", layout="wide")
st.title("Pitwall · Weather Insights")
st.caption("Course-facing Python companion · modeled/provider current weather · metric units")
try:
    settings = load_config()
    store = SnapshotStore(settings["database"])
except (RuntimeError, OSError, sqlite3.Error):
    st.error("The local environment or data store could not be opened. Follow the Python companion README.")
    st.stop()

if "custom_locations" not in st.session_state:
    st.session_state.custom_locations = []
if "current_snapshots" not in st.session_state:
    st.session_state.current_snapshots = []

with st.sidebar:
    st.header("Locations")
    choices = list(TRACKS.values()) + st.session_state.custom_locations
    selected = st.multiselect("Circuits and saved places", choices, default=choices[:2], format_func=lambda p: p.name)
    provider = st.selectbox("Data source", ["Open-Meteo", "OpenWeather", "Both"])
    st.caption("OpenWeather reads its key from variables.env. A key is never displayed or entered in this page.")
    with st.expander("Add coordinates"):
        with st.form("coordinates", clear_on_submit=True):
            name = st.text_input("Location name")
            lat = st.number_input("Latitude (°)", min_value=-90.0, max_value=90.0, value=43.0, format="%.5f")
            lon = st.number_input("Longitude (°)", min_value=-180.0, max_value=180.0, value=0.0, format="%.5f")
            if st.form_submit_button("Save this location"):
                try:
                    location = Location(name, lat, lon)
                    if location not in st.session_state.custom_locations:
                        st.session_state.custom_locations.append(location)
                    st.rerun()
                except WeatherError as error:
                    st.error(str(error))
    with st.expander("Find a town"):
        with st.form("search"):
            query = st.text_input("Town or city")
            if st.form_submit_button("Find places"):
                try:
                    st.session_state.search_results = GeocodingClient().search(query)
                except WeatherError as error:
                    st.error(str(error))
        results = st.session_state.get("search_results", [])
        if results:
            place = st.selectbox("Matching location", results, format_func=str)
            if st.button("Save selected place"):
                if place not in st.session_state.custom_locations:
                    st.session_state.custom_locations.append(place)
                st.rerun()
    view = st.radio("View", ["Live conditions", "Analytics", "Sources & export"])
    st.caption("Custom locations persist for this Streamlit session. SQLite snapshots persist on this computer.")

if view == "Live conditions":
    st.subheader("Fetch current conditions")
    st.write("Select several circuits to compare a single source across locations, or choose Both to keep each source visible.")
    if st.button("Refresh selected locations", type="primary", disabled=not selected):
        clients = []
        if provider in ("Open-Meteo", "Both"):
            clients.append(OpenMeteoClient())
        if provider in ("OpenWeather", "Both"):
            clients.append(OpenWeatherClient(settings["openweather_api_key"]))
        with st.spinner("Fetching and logging real weather snapshots…"):
            try:
                snapshots, failures = fetch_many(clients, selected, store)
                st.session_state.current_snapshots = [item.to_record() for item in snapshots]
                st.session_state.failures = failures
            except (OSError, sqlite3.Error):
                st.error("Fetched data could not be saved to SQLite. Check that the data directory is writable.")
    for failure in st.session_state.get("failures", []):
        st.warning(f"{failure['location']} · {failure['provider']}: {failure['error']}")
    current = st.session_state.current_snapshots
    if current:
        st.dataframe(pd.DataFrame(current)[["location", "provider", "temperature_c", "humidity_pct", "wind_kmh", "gust_kmh",
                                           "precipitation_mm", "precipitation_interval_minutes", "valid_at", "fetched_at"]],
                     hide_index=True, width="stretch")
        st.caption("Temperature °C; relative humidity %; wind/gust km/h. Precipitation mm belongs to its stated interval; do not directly compare 15-minute and hourly totals. Blank means unavailable.")
    else:
        st.info("Press Refresh to fetch live data. There are no sample weather values.")
    st.info("These are provider/model conditions near the circuit centre. They do not measure tarmac temperature, local grip, standing water or corner-by-corner rain.")
elif view == "Analytics":
    rows = store.history()
    if not rows:
        st.info("No logged weather yet. Fetch successful conditions in Live conditions first.")
        st.stop()
    providers = sorted({row["provider"] for row in rows})
    source = st.selectbox("Compare like-for-like source", providers)
    source_rows = [row for row in rows if row["provider"] == source]
    st.subheader("1 · Cross-location comparison")
    comparison = pd.DataFrame(latest_comparison(source_rows))
    st.caption("Latest stored sample per place. Check each valid time: these are not necessarily simultaneous conditions.")
    st.altair_chart(alt.Chart(comparison).mark_bar(color="#b9ef50").encode(
        x=alt.X("temperature_c:Q", title="Air temperature (°C)"),
        y=alt.Y("location:N", sort="-x", title="Location"),
        tooltip=["location", "provider", "temperature_c", "valid_at"]), use_container_width=True)
    st.dataframe(comparison[["location", "temperature_c", "wind_kmh", "valid_at", "fetched_at"]], hide_index=True)
    st.subheader("2 · Temperature trend from logged history")
    location = st.selectbox("Trend location", sorted({r["location"] for r in source_rows}))
    trend = pd.DataFrame([r for r in source_rows if r["location"] == location])
    trend = trend.sort_values(["valid_at", "fetched_at"]).drop_duplicates("valid_at", keep="last")
    trend["valid_at"] = pd.to_datetime(trend["valid_at"], utc=True)
    st.altair_chart(alt.Chart(trend).mark_line(point=True, color="#76b7ff").encode(
        x=alt.X("valid_at:T", title="Provider valid time (UTC)"),
        y=alt.Y("temperature_c:Q", title="Air temperature (°C)", scale=alt.Scale(zero=False)),
        tooltip=["valid_at:T", "temperature_c:Q"]), use_container_width=True)
    if len(trend) < 2:
        st.info("One distinct provider valid time is a starting point, not a trend. Fetch again after the provider updates.")
    st.dataframe(pd.DataFrame(temperature_trends(source_rows)), hide_index=True)
    st.subheader("3 · Computed differences")
    metrics = pd.DataFrame(derived_metrics(source_rows))
    st.dataframe(metrics, hide_index=True)
    st.caption("Air minus dewpoint is a humidity-related temperature gap in °C; dewpoint is estimated from temperature and relative humidity. Feels-like minus air is also °C. Neither metric is a calibrated grip score or a safety decision.")
else:
    st.subheader("Sources and provenance")
    st.markdown("[Open-Meteo API documentation](https://open-meteo.com/en/docs) · [OpenWeather current API](https://openweathermap.org/api/current)")
    st.write("Open-Meteo current weather is modeled, generally on a 15-minute interval. OpenWeather returns its own current-conditions product. Both are fetched over HTTPS. Every success is appended to the local SQLite file with fetch and provider-valid timestamps.")
    st.write("The main web application offers named forecast model comparisons and radar. This companion deliberately keeps current snapshot logging distinct from forecast history.")
    rows = store.history(limit=100000)
    if rows:
        csv = pd.DataFrame(rows).to_csv(index=False)
        st.download_button("Download logged snapshots (CSV)", csv, "pitwall-snapshots.csv", "text/csv")
        st.caption(f"{len(rows)} stored rows in this export. No multi-day history is fabricated.")
    else:
        st.info("No exportable snapshots yet.")
