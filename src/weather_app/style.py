"""The app's one CSS block. No JavaScript. Streamlit adds a class st-key-NAME to st.container(key=NAME)."""

import streamlit as st

CSS = """
<style>
/* Page: the background gradient is set separately, see apply_style. */
.stApp { background-attachment: fixed; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stSidebar"] { background: rgba(30, 36, 44, 0.92); }
.block-container { padding-top: 1.5rem; max-width: 1500px; }
@media (max-width: 768px) { .block-container { padding-top: 3.2rem; } }
.stApp, .stApp button { font-family: -apple-system, "SF Pro Display", "Segoe UI", Roboto, sans-serif; }

/* Hero */
.hero { text-align: center; padding: 18px 0 28px; }
.hero-city { font-size: 2.1rem; }
.hero-temp { font-size: clamp(4.5rem, 12vw, 6.5rem); font-weight: 200; line-height: 1.05; }
.hero-line { font-size: 1.15rem; font-weight: 500; }
.hero-time { opacity: 0.75; }

/* Glass cards: plain HTML ones and Streamlit containers holding widgets */
.card, .st-key-conditions-card, .st-key-map-card, [class*="st-key-panel"] {
  background: rgba(40, 48, 58, 0.55); border-radius: 18px; padding: 14px 18px;
}
.card-title { font-size: 0.72rem; font-weight: 600; letter-spacing: 0.05em; opacity: 0.65; text-transform: uppercase; margin-bottom: 8px; }
.big { font-size: 1.9rem; font-weight: 400; line-height: 1.2; }
.small { font-size: 0.86rem; opacity: 0.9; margin-top: 6px; }

/* Tiles: two columns everywhere, like a phone weather app. A last tile left alone fills its row. */
.tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.wide, .tiles > :last-child:nth-child(even) { grid-column: 1 / -1; }

/* Air quality scale */
.scale { position: relative; height: 6px; border-radius: 3px; margin: 14px 0;
  background: linear-gradient(90deg, #3ec6a8, #8fd14f, #f2d13c, #ef8a3a, #d8324a, #8d2bd6); }
.scale-dot { position: absolute; top: -2px; width: 10px; height: 10px; margin-left: -5px; border-radius: 50%; background: #fff; border: 1px solid #333; }

/* Wind compass: tick marks from a repeating conic gradient, arrow rotated inline */
.compass { position: relative; width: 120px; height: 120px; margin: 4px auto; border-radius: 50%;
  background: repeating-conic-gradient(rgba(255,255,255,.35) 0 2deg, transparent 2deg 12deg); }
.compass-face { position: absolute; inset: 9px; border-radius: 50%; background: #3d4854; }
.compass-arrow { position: absolute; left: 50%; top: 11px; bottom: 11px; width: 2px; margin-left: -1px; background: linear-gradient(#fff 24%, transparent 24% 76%, #fff 76%); }
.compass-arrow::before { content: ""; position: absolute; top: -3px; left: -4px; border: 5px solid transparent; border-top: 0; border-bottom: 9px solid #fff; }
.compass span { position: absolute; font-size: 0.68rem; }
.compass-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 0.8rem; line-height: 1.1; }
.compass-text b { font-size: 1.15rem; }

/* Conditions strip: scrolls sideways when it does not fit */
.strip { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 6px; }
.strip-item { flex: 1 0 58px; text-align: center; font-size: 0.86rem; }
.strip-icon { font-size: 1.5rem; height: 2.1rem; }
.strip-pop { font-size: 0.72rem; color: #7fd0f5; height: 1.1rem; }
.strip-value { font-weight: 600; margin-top: 4px; }

/* Daily forecast */
.day { display: grid; grid-template-columns: 3.2rem 3rem 2.6rem 1fr 2.6rem; gap: 8px; align-items: center; padding: 9px 0; border-top: 1px solid rgba(255,255,255,.15); }
.day:first-of-type { border-top: 0; }
.day-pop { font-size: 0.7rem; color: #7fd0f5; }
.day-icon { text-align: center; font-size: 1.25rem; line-height: 1.1; }
.day-low { opacity: 0.65; text-align: right; }
.bar { position: relative; height: 5px; border-radius: 3px; background: rgba(255,255,255,.15); }
.bar-dot { position: absolute; top: -2.5px; width: 10px; height: 10px; margin-left: -5px; border-radius: 50%; background: #fff; border: 1px solid #333; }
.bar-fill { position: absolute; top: 0; bottom: 0; border-radius: 3px; background: linear-gradient(90deg, #6fd3c7, #8fc7e8); }

/* Sidebar city cards: the invisible button is stretched over the whole card */
[class*="st-key-city-"] { position: relative; }
[class*="st-key-city-"] [data-testid="stElementContainer"] { position: static; }
.city { border-radius: 14px; padding: 10px 40px 10px 14px; display: grid; grid-template-columns: 1fr auto; line-height: 1.25; }
.city.selected { outline: 2px solid rgba(255,255,255,.75); }
.city-name { font-weight: 600; font-size: 1.05rem; }
.city-temp { font-size: 1.7rem; font-weight: 300; text-align: right; }
.city-small { font-size: 0.76rem; }
[class*="st-key-city-"] [class*="st-key-open-"] { position: absolute; inset: 0; z-index: 1; }
[class*="st-key-open-"] button { width: 100%; height: 100%; opacity: 0; }
[class*="st-key-city-"] [class*="st-key-remove-"] { position: absolute; top: 50%; right: 8px; z-index: 2; width: auto; transform: translateY(-50%); }
[class*="st-key-remove-"] button { min-height: 0; padding: 0 7px; border: 0; background: rgba(0,0,0,.25); }

/* Phone and small window: the sidebar is out of the way, so show a city picker in the page */
.st-key-phone-city { display: none; }
@media (max-width: 768px) { .st-key-phone-city { display: block; } }

/* Below 1000px one column, with Conditions and the daily forecast first, like a phone app */
@media (max-width: 1000px) {
  .st-key-main-grid [data-testid="stHorizontalBlock"] { flex-direction: column-reverse; }
  .st-key-main-grid [data-testid="stColumn"] { width: 100%; flex: 1 1 100%; }
}
</style>
"""


def apply_style(background):
    """Add the CSS and the page background. background is a fixed gradient from display.py."""
    st.html(CSS + f"<style>.stApp {{ background: {background}; }}</style>")
