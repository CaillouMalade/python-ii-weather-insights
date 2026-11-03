"""The app's one CSS block. No JavaScript. Streamlit adds a class st-key-NAME to st.container(key=NAME)."""

import streamlit as st

CSS = """
<style>
/* Page. The main column is a size container, so its layout follows the space it really has,
   whether or not the sidebar is open. The background gradient is set in apply_style. */
.stApp { background-attachment: fixed; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: rgba(30, 36, 44, 0.92); }
[data-testid="stMainBlockContainer"] { container-type: inline-size; padding-top: 1.5rem; max-width: 1400px; }
@media (max-width: 768px) { [data-testid="stMainBlockContainer"] { padding: 3.2rem 1rem 2rem; } }
/* On a phone, a solid bar behind the sidebar arrow, so content scrolls under it */
@media (max-width: 768px) { [data-testid="stHeader"] { background: #1e242c; } }
.stApp, .stApp button { font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif; }

/* One card style: plain HTML cards and Streamlit containers holding charts */
.card, [class*="st-key-panel"] { background: rgba(40, 48, 58, 0.55); border-radius: 16px; padding: 16px 18px; }
.card-title { display: flex; font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; opacity: 0.7; text-transform: uppercase; margin-bottom: 6px; }
.card-title span { margin-left: auto; font-weight: 400; }
.small { font-size: 0.85rem; opacity: 0.75; }
.high-low { white-space: pre; }
.finding { font-size: 1.05rem; font-weight: 600; }
.history-span { margin-bottom: 4px; }

/* Header: main block on the left, key figures on the right, wrapping below when there is no room */
.header { display: flex; flex-wrap: wrap; gap: 16px 40px; align-items: center; justify-content: space-between; }
.header-main { flex: 1 1 260px; }
.header-city { font-size: 1.9rem; font-weight: 600; line-height: 1.2; }
.header-temp { font-size: 5rem; font-weight: 200; line-height: 1.1; }
.header-line { font-size: 1.05rem; font-weight: 500; }
.header-stats { flex: 2 1 320px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.stat-value { font-size: 1.5rem; line-height: 1.25; }

/* Wind legend: one label at the start of each speed band */
.legend-bar { height: 8px; border-radius: 4px; margin-top: 8px; }
.legend-labels { display: flex; font-size: 0.72rem; margin-top: 3px; opacity: 0.8; }
.legend-labels span { flex: 1; }

/* Sidebar circuit cards: an invisible button is stretched over the whole card */
[class*="st-key-city-"] { position: relative; }
[class*="st-key-city-"] [data-testid="stElementContainer"] { position: static; }
.city { border-radius: 14px; padding: 10px 14px; height: 78px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; line-height: 1.25; }
.city-row { display: flex; justify-content: space-between; gap: 6px; min-width: 0; }
.city-main { min-width: 0; }
.city.selected { outline: 2px solid rgba(255,255,255,.75); }
.city-name { font-weight: 600; font-size: 1.05rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.city-temp { font-size: 1.7rem; font-weight: 300; text-align: right; }
.city-small { font-size: 0.76rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.city-small.city-note { white-space: normal; }
[class*="st-key-city-"] [class*="st-key-open-"] { position: absolute; inset: 0; z-index: 1; }
[class*="st-key-open-"] button { width: 100%; height: 100%; opacity: 0; }
.credit { font-size: 0.7rem; opacity: 0.5; text-align: center; }

/* On a phone the sidebar starts closed, so a circuit picker appears in the page */
.st-key-phone-circuit { display: none; }
@media (max-width: 768px) { .st-key-phone-circuit { display: block; } }

/* Narrow main column: the two maps stack */
@container (max-width: 700px) {
  .st-key-maps [data-testid="stHorizontalBlock"] { flex-direction: column; }
  .st-key-maps [data-testid="stColumn"] { width: 100%; flex: 1 1 100%; }
}
</style>
"""


def apply_style(background):
    """Add the CSS and the page background. background is a fixed gradient from display.py."""
    st.html(CSS + f"<style>.stApp {{ background: {background}; }}</style>")
