"""The app's one CSS block. No JavaScript. Streamlit adds a class st-key-NAME to st.container(key=NAME).

The look is a pit wall's timing screen: flat graphite, green for dry and the selected item,
red only for rain and failures. The theme in .streamlit/config.toml uses the same colours.
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

/* One surface style for the header and every panel */
.header, [class*="st-key-panel"] { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px 18px; }
.label { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); margin-bottom: 6px; }
.muted { color: var(--muted); }
.small { font-size: 0.82rem; }
.high-low { white-space: pre; }
.finding { font-size: 1rem; font-weight: 600; }

/* Header: name, time and temperature on the left, key figures beside or below */
.header { display: flex; flex-wrap: wrap; gap: 16px 40px; align-items: center; justify-content: space-between; }
.header-main { flex: 1 1 240px; }
.header-name { font-size: 1.8rem; font-weight: 600; line-height: 1.2; }
.header-temp { font-size: 4.6rem; font-weight: 200; line-height: 1.1; margin-top: 4px; }
.header-stats { flex: 2 1 320px; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; }
.stat-value { font-size: 1.45rem; font-weight: 300; line-height: 1.25; }

/* Status lights: small filled circles with a faint glow, like track-status lights. No animation. */
.light { display: inline-block; flex: none; width: 12px; height: 12px; border-radius: 50%; background: var(--border); }
.light.dry { background: var(--green); box-shadow: 0 0 6px rgba(47, 210, 122, 0.55); }
.light.rain { background: var(--red); box-shadow: 0 0 6px rgba(229, 72, 77, 0.55); }

/* The track-status strip: the page's one bold element. It wraps on a phone. */
.status { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 18px; padding: 14px 18px; border: 1px solid var(--border); border-radius: 12px; }
.lights { display: flex; gap: 8px; }
.lights .light { width: 18px; height: 18px; }
.status-text { flex: 1 1 260px; font-size: 1.05rem; font-weight: 600; }

/* Map attribution: still shown, as it must be, but as quiet as the rest */
.maplibregl-ctrl.maplibregl-ctrl-attrib { background: rgba(14, 17, 16, 0.7); font-size: 0.65rem; }
.maplibregl-ctrl-attrib a { color: var(--muted); }
.maplibregl-ctrl-attrib-button { filter: invert(1) opacity(0.5); background-color: transparent; }

/* Wind legend: one label at the start of each speed band */
.legend-bar { height: 6px; border-radius: 3px; margin-top: 8px; }
.legend-labels { display: flex; font-size: 0.72rem; margin-top: 3px; }
.legend-labels span { flex: 1; }

/* Sidebar circuit cards: an invisible button is stretched over the whole card */
[class*="st-key-circuit-"] { position: relative; }
[class*="st-key-circuit-"] [data-testid="stElementContainer"] { position: static; }
.circuit { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 9px 12px; height: 64px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; }
.circuit.selected { border-color: var(--green); }
[class*="st-key-circuit-"]:has(button:focus-visible) .circuit { outline: 2px solid var(--green); outline-offset: 2px; }
.card-row { display: flex; justify-content: space-between; align-items: center; gap: 8px; min-width: 0; white-space: nowrap; }
.card-row span { overflow: hidden; text-overflow: ellipsis; }
.card-name { display: flex; align-items: center; gap: 8px; min-width: 0; font-weight: 600; }
.card-name span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.card-temp { font-size: 1.3rem; font-weight: 300; }
.circuit .small.muted { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
[class*="st-key-circuit-"] [class*="st-key-open-"] { position: absolute; inset: 0; z-index: 1; }
[class*="st-key-open-"] button { width: 100%; height: 100%; opacity: 0; }
.credit { font-size: 0.68rem; color: var(--muted); text-align: center; }

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


def apply_style():
    st.html(CSS)
