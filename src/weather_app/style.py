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
.stApp, .stApp button { font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif; }

/* One card style everywhere: plain HTML cards and Streamlit containers holding widgets */
.card, .st-key-next-hours, .st-key-daily-card, .st-key-map-card, [class*="st-key-panel"] {
  background: rgba(40, 48, 58, 0.55); border-radius: 16px; padding: 16px 18px;
}
.card-title { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; opacity: 0.7; text-transform: uppercase; margin-bottom: 6px; }
.tile-value { font-size: 1.3rem; line-height: 1.25; }
.small { font-size: 0.85rem; opacity: 0.85; margin-top: 4px; }
.high-low { white-space: pre; }
.finding { font-size: 1.05rem; font-weight: 600; margin-bottom: 4px; }

/* One grid: four across, two across when the main column is narrow */
.grid-4 { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-auto-rows: 1fr; gap: 14px; }

/* Header: main block on the left, key figures on the right, wrapping below when there is no room */
.header { display: flex; flex-wrap: wrap; gap: 16px 40px; align-items: center; justify-content: space-between; }
.header-main { flex: 1 1 260px; }
.header-city { font-size: 1.9rem; font-weight: 600; line-height: 1.2; }
.header-temp { font-size: 5rem; font-weight: 200; line-height: 1.1; }
.header-line { font-size: 1.05rem; font-weight: 500; }
.header-stats { flex: 2 1 320px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.stat-value { font-size: 1.5rem; line-height: 1.25; }

/* Next hours: eight even columns, four when narrow, so no label is ever cut off */
.strip { display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 12px 6px; }
.strip-item { text-align: center; font-size: 0.86rem; }
.strip-icon { font-size: 1.5rem; margin: 2px 0; }
.strip-value { font-weight: 600; white-space: nowrap; }
.strip-small { font-size: 0.72rem; color: #7fd0f5; min-height: 1rem; white-space: nowrap; }

/* Daily forecast: the rows share the card's height, to match the map beside it */
.days { min-height: 488px; display: flex; flex-direction: column; }
.day { flex: 1; display: grid; grid-template-columns: 3.2rem 3rem 2.4rem 1fr 2.4rem; gap: 8px; align-items: center; border-top: 1px solid rgba(255,255,255,.15); }
.day-pop { font-size: 0.7rem; color: #7fd0f5; }
.day-icon { text-align: center; font-size: 1.25rem; line-height: 1.1; }
.day-low { opacity: 0.7; text-align: right; }
.bar { position: relative; height: 5px; border-radius: 3px; background: rgba(255,255,255,.15); }
.bar-fill { position: absolute; top: 0; bottom: 0; border-radius: 3px; background: linear-gradient(90deg, #6fd3c7, #8fc7e8); }
.bar-dot { position: absolute; top: -2.5px; width: 10px; height: 10px; margin-left: -5px; border-radius: 50%; background: #fff; border: 1px solid #333; }

/* Air quality scale */
.scale { position: relative; height: 6px; border-radius: 3px; margin: 10px 0 8px;
  background: linear-gradient(90deg, #3ec6a8, #8fd14f, #f2d13c, #ef8a3a, #d8324a, #8d2bd6); }
.scale-dot { position: absolute; top: -2px; width: 10px; height: 10px; margin-left: -5px; border-radius: 50%; background: #fff; border: 1px solid #333; }

/* Map notes: the same height for the legend and the radar line, so the two cards stay level */
.map-note { min-height: 2.6rem; font-size: 0.85rem; }
.legend-bar { height: 10px; border-radius: 5px; }
.legend-labels { display: flex; justify-content: space-between; font-size: 0.72rem; margin-top: 3px; }

/* Plan the week: one card per day, with three rated parts */
.plan { display: grid; gap: 14px; }
.plan-head { display: flex; align-items: center; gap: 10px; font-size: 1.05rem; }
.plan-icon { font-size: 1.3rem; }
.plan-head .high-low { margin-left: auto; font-size: 0.9rem; }
.plan-summary { margin: 2px 0 10px; }
.parts { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
.part { border-top: 3px solid; padding-top: 6px; font-size: 0.85rem; }
.part-past { border-top-color: rgba(255,255,255,.15); opacity: 0.5; }
.part-name { font-size: 0.72rem; opacity: 0.75; }
.part-rating { font-weight: 700; font-size: 1.05rem; }

/* Air: one stacked bar of days, then a row per pollutant */
.share-bar { display: flex; height: 18px; border-radius: 9px; overflow: hidden; margin: 6px 0 8px; }
.share-labels { display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 0.85rem; }
.share-labels i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
.pollutant { padding: 10px 0; border-top: 1px solid rgba(255,255,255,.15); }
.days-bar { height: 6px; border-radius: 3px; background: rgba(255,255,255,.15); margin-top: 6px; overflow: hidden; }
.days-bar div { height: 100%; background: #ef8a3a; }
.outlook-title { margin: 6px 0 8px; }

/* Compare table: wraps instead of scrolling sideways */
.cities { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.cities th { text-align: left; font-size: 0.72rem; font-weight: 600; opacity: 0.7; padding: 4px 6px 4px 0; }
.cities td { padding: 8px 6px 8px 0; border-top: 1px solid rgba(255,255,255,.15); vertical-align: top; white-space: nowrap; }
.cities td:first-child { white-space: normal; }

/* Sidebar city cards: the invisible button is stretched over the whole card */
[class*="st-key-city-"] { position: relative; }
[class*="st-key-city-"] [data-testid="stElementContainer"] { position: static; }
.city { border-radius: 14px; padding: 10px 40px 10px 14px; height: 78px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; line-height: 1.25; }
.city-row { display: flex; justify-content: space-between; gap: 6px; min-width: 0; }
.city-row + .city-row .city-small { font-size: 0.73rem; }
.city-main { min-width: 0; }
.city.selected { outline: 2px solid rgba(255,255,255,.75); }
.city-name { font-weight: 600; font-size: 1.05rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.city-temp { font-size: 1.7rem; font-weight: 300; text-align: right; }
.city-small { font-size: 0.76rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.city-small.high-low { white-space: pre; flex-shrink: 0; overflow: visible; }
.city-small.city-note { white-space: normal; }
[class*="st-key-city-"] [class*="st-key-open-"] { position: absolute; inset: 0; z-index: 1; }
[class*="st-key-open-"] button { width: 100%; height: 100%; opacity: 0; }
[class*="st-key-city-"] [class*="st-key-remove-"] { position: absolute; top: 50%; right: 8px; z-index: 2; width: auto; transform: translateY(-50%); }
[class*="st-key-remove-"] button { min-height: 0; padding: 0 7px; border: 0; background: rgba(0,0,0,.25); }

/* On a phone the sidebar starts closed, so a city picker appears in the page */
.st-key-phone-city { display: none; }
@media (max-width: 768px) { .st-key-phone-city { display: block; } }

/* Narrow main column: two tiles across, four strip columns, stacked forecast and map */
@container (max-width: 700px) {
  .grid-4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .strip { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .days { min-height: 0; }
  .cities { font-size: 0.78rem; }
  .day { padding: 9px 0; }
  .st-key-week-row [data-testid="stHorizontalBlock"] { flex-direction: column; }
  .st-key-week-row [data-testid="stColumn"] { width: 100%; flex: 1 1 100%; }
}
</style>
"""


def apply_style(background):
    """Add the CSS and the page background. background is a fixed gradient from display.py."""
    st.html(CSS + f"<style>.stApp {{ background: {background}; }}</style>")
