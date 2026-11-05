"""The two colour themes, dark and light, as one dict each with the same keys. The CSS, the
charts and the maps all read their colours from here, so each colour is written once.

Streamlit's own colours (page, sidebar, widgets) come from .streamlit/config.toml, which repeats
the background, surface, text and green of each theme. Viewers pick a theme in Streamlit's menu
(System, Light or Dark); the app reads which one is on with st.context.theme.type.

Green means dry and the selection, red only rain or a failure, in both themes. The light theme's
green and red are darker so that they keep AA contrast on white.
"""

import streamlit as st

DARK = {
    "background": "#0E1110",
    "surface": "#161A18",
    "border": "#242A27",
    "text": "#E8EDEA",
    "muted": "#8A948F",
    "green": "#2FD27A",
    "red": "#E5484D",
    "green_glow": "rgba(47, 210, 122, 0.55)",
    "red_glow": "rgba(229, 72, 77, 0.55)",
    "sun": "#E0B878",
    "cloud_band": "rgba(138, 148, 143, 0.12)",
    "rain_bar_unlikely": "rgba(138, 148, 143, 0.45)",
    "session_block": "rgba(47, 210, 122, 0.16)",
    "session_edge": "rgba(47, 210, 122, 0.6)",
    "attribution": "rgba(14, 17, 16, 0.7)",
    "attribution_button": "invert(1) opacity(0.5)",
    "chart_template": "plotly_dark",
    "map_style": "carto-darkmatter",
    # A cool-to-warm scale with a stop every 5° from -5° to 30°: (°C, red, green, blue).
    # No green or red, which keep meaning dry and rain. Light on graphite.
    "temperature_stops": [
        (-5, 138, 150, 240),
        (0, 110, 176, 232),
        (5, 120, 200, 214),
        (10, 176, 196, 206),
        (15, 218, 208, 176),
        (20, 236, 184, 112),
        (25, 242, 150, 72),
        (30, 236, 140, 60),
    ],
    # One colour per wind band in maps.WIND_SPEEDS: one violet hue, brighter when stronger.
    "wind_colors": ["#6A6488", "#7C73A6", "#9A8FD0", "#B8AEF0", "#DCD5FF"],
}

LIGHT = {
    "background": "#F6F3EC",
    "surface": "#FFFFFF",
    "border": "#E3DED3",
    "text": "#1E2321",
    "muted": "#5E6762",
    "green": "#1A7F4B",
    "red": "#C92A2F",
    "green_glow": "rgba(26, 127, 75, 0.35)",
    "red_glow": "rgba(201, 42, 47, 0.35)",
    "sun": "#B07A1C",
    "cloud_band": "rgba(94, 103, 98, 0.07)",
    "rain_bar_unlikely": "rgba(94, 103, 98, 0.35)",
    "session_block": "rgba(26, 127, 75, 0.12)",
    "session_edge": "rgba(26, 127, 75, 0.6)",
    "attribution": "rgba(246, 243, 236, 0.75)",
    "attribution_button": "opacity(0.5)",
    "chart_template": "plotly_white",
    "map_style": "carto-positron",
    # The same hues, darker, so every degree keeps 4.5:1 on white.
    "temperature_stops": [
        (-5, 82, 92, 204),
        (0, 34, 108, 188),
        (5, 18, 122, 150),
        (10, 88, 108, 128),
        (15, 142, 112, 48),
        (20, 164, 98, 16),
        (25, 182, 86, 26),
        (30, 172, 74, 36),
    ],
    # The same violet, darker when stronger, so a strong wind stands out on a pale map.
    "wind_colors": ["#9088C0", "#7C72B4", "#6656A4", "#4E3E8E", "#382A74"],
}

THEMES = {"dark": DARK, "light": LIGHT}


def theme_named(kind):
    """The light theme for "light", and the dark one otherwise: dark is the app's own look."""
    return LIGHT if kind == "light" else DARK


def current_theme():
    """The theme picked in Streamlit's menu. Switching it there repaints Streamlit's own colours
    at once; the app's colours follow at the next rerun."""
    return theme_named(st.context.theme.type)
