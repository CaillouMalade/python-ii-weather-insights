"""The app's one CSS block. No JavaScript. Streamlit adds a class st-key-NAME to st.container(key=NAME).

The look is a pit wall's timing screen: flat graphite, green for dry and the selection,
red only for rain and failures. The theme in .streamlit/config.toml uses the same colours.
Groups are separated by space and one surface each, not by borders and labels.
"""

import streamlit as st

CSS = """
<style>
:root {
  --background: #0E1110; --surface: #161A18; --border: #242A27;
  --text: #E8EDEA; --muted: #8A948F; --green: #2FD27A; --red: #E5484D;
}

/* Page: flat graphite everywhere. The main column is a size container, so its layout
   follows the space it really has, whether or not the sidebar is open. */
.stApp { background: var(--background); color: var(--text); font-variant-numeric: tabular-nums; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: var(--background); border-right: 1px solid var(--border); }
[data-testid="stMainBlockContainer"] { container-type: inline-size; padding-top: 1.5rem; max-width: 1400px; }
@media (max-width: 768px) {
  [data-testid="stMainBlockContainer"] { padding: 3.2rem 1rem 2rem; }
  /* A solid bar behind the sidebar arrow, so content scrolls under it */
  [data-testid="stHeader"] { background: var(--background); }
}
:focus-visible { outline: 2px solid var(--green); outline-offset: 2px; }

/* One surface per group */
[class*="st-key-panel"] { background: var(--surface); border-radius: 12px; padding: 16px 18px; }
.muted { color: var(--muted); }
.finding { font-size: 1rem; font-weight: 600; margin-top: 4px; }
.credit { font-size: 0.68rem; color: var(--muted); text-align: center; margin-top: 8px; }

/* Now: the big temperature with its facts close beside it, then the status lights below */
.now { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 20px; }
.now-temp { font-size: 4.2rem; font-weight: 200; line-height: 1; }
.now-facts { flex: 1 1 240px; line-height: 1.5; }
.now-facts div:first-child { font-weight: 600; }
.now-facts div + div { color: var(--muted); }
.fact { white-space: pre; }

.now-facts .glyph { vertical-align: -4px; margin-right: 4px; }

/* History: one row per collected day, like a weather app's daily forecast. A partial day is muted. */
.days { display: grid; gap: 2px; margin-top: 10px; }
.day-row { display: grid; grid-template-columns: 5.2rem 3.4rem 2.4rem minmax(40px, 1fr) 2.4rem 5.6rem; align-items: center; gap: 10px; padding: 7px 0; }
.day-row.partial { opacity: 0.45; }
.day-rain, .day-wind { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.day-wind { justify-content: flex-end; color: var(--muted); }
.range { position: relative; height: 6px; border-radius: 3px; background: var(--border); }
.range-fill { position: absolute; top: 0; bottom: 0; border-radius: 3px; }
@container (max-width: 520px) {
  .day-row { grid-template-columns: 3.6rem 2.6rem 2rem minmax(30px, 1fr) 2rem 4.2rem; gap: 6px; font-size: 0.9rem; }
  .day-wind { font-size: 0.8rem; }
}

/* Sidebar form: only the two times carry a label, and it is tiny */
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { font-size: 0.7rem; color: var(--muted); }

/* Status lights: small filled circles with a faint glow, like track-status lights. No animation. */
.light { display: inline-block; flex: none; width: 12px; height: 12px; border-radius: 50%; background: var(--border); }
.light.dry { background: var(--green); box-shadow: 0 0 6px rgba(47, 210, 122, 0.55); }
.light.rain { background: var(--red); box-shadow: 0 0 6px rgba(229, 72, 77, 0.55); }
.status { flex: 1 1 100%; display: flex; flex-wrap: wrap; align-items: center; gap: 8px 16px; margin-top: 12px; }
.lights { display: flex; gap: 8px; }
.lights .light { width: 18px; height: 18px; }
.status-text { font-size: 1.05rem; font-weight: 600; }

/* Map attribution: still shown on the map, as OpenStreetMap and CARTO require, but quiet */
.maplibregl-ctrl.maplibregl-ctrl-attrib { background: rgba(14, 17, 16, 0.7); font-size: 0.62rem; }
.maplibregl-ctrl-attrib a { color: var(--muted); }
.maplibregl-ctrl-attrib-button { filter: invert(1) opacity(0.5); background-color: transparent; }

/* Session rows: an invisible button is stretched over the whole row, so it is tappable */
[class*="st-key-session-"] { position: relative; }
[class*="st-key-session-"] [data-testid="stElementContainer"] { position: static; }
/* Two short lines, so a row always fits the sidebar: name and chance, then day and times */
.session { display: flex; align-items: center; gap: 10px; padding: 7px 10px; border-radius: 8px; background: var(--surface); line-height: 1.3; }
.session-main { flex: 1 1 auto; min-width: 0; }
.session-name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.session-main .muted { font-size: 0.85rem; white-space: nowrap; }
.session-value { flex: none; }
[class*="st-key-session-"]:has(button:focus-visible) .session { outline: 2px solid var(--green); outline-offset: 2px; }
[class*="st-key-session-"] [class*="st-key-open-"] { position: absolute; inset: 0; z-index: 1; }
[class*="st-key-open-"] button { width: 100%; height: 100%; opacity: 0; }

/* Narrow main column: the two maps stack */
@container (max-width: 700px) {
  .st-key-panel-maps [data-testid="stHorizontalBlock"] { flex-direction: column; }
  .st-key-panel-maps [data-testid="stColumn"] { width: 100%; flex: 1 1 100%; }
}
</style>
"""


def apply_style():
    st.html(CSS)
