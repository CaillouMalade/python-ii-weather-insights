"""Colours for the light and dark themes. Each theme has one dictionary, with the same keys.

The user picks the theme in Streamlit's own menu. Picking it there does not rerun the
script, so the page colours cannot come from Python at that moment. Instead each colour
becomes a CSS variable written with light-dark(light, dark): the browser picks the right
half from the color-scheme that Streamlit sets on the app for the chosen theme.
"""

# Page colours. The dark values are the app's original colours.
DARK_TOKENS = {
    "card": "rgba(40, 48, 58, 0.55)",
    "sidebar": "rgba(30, 36, 44, 0.92)",
    "header-bar": "#1e242c",
    "line": "rgba(255, 255, 255, 0.15)",
    "accent-text": "#7fd0f5",
    "selected": "rgba(255, 255, 255, 0.75)",
    "empty-card": "rgba(255, 255, 255, 0.08)",
    "remove-button": "rgba(0, 0, 0, 0.25)",
    "bar-fill-start": "#6fd3c7",
    "bar-fill-end": "#8fc7e8",
    "great": "#3ec6a8",
    "good": "#8fd14f",
    "ok": "#f2d13c",
    "poor": "#ef8a3a",
    "very-poor": "#d8324a",
    # Streamlit's own caption and link colours. Captions are drawn at 60 % opacity.
    "caption-text": "#ffffff",
    "caption-link": "#3d9df3",
}

# Paper background, white cards, dark text. The rating colours are darker, so text in
# them reaches the WCAG AA contrast of 4.5:1 on a white card, even at the 85 % opacity
# of small text. Captions use near-black, because Streamlit draws them at 60 % opacity.
LIGHT_TOKENS = {
    "card": "#ffffff",
    "sidebar": "#ebe6dc",
    "header-bar": "#f4f1ea",
    "line": "rgba(29, 35, 43, 0.14)",
    "accent-text": "#165488",
    "selected": "rgba(29, 35, 43, 0.6)",
    "empty-card": "rgba(29, 35, 43, 0.06)",
    "remove-button": "rgba(29, 35, 43, 0.12)",
    "bar-fill-start": "#2a9d8f",
    "bar-fill-end": "#3b82c4",
    "great": "#096b56",
    "good": "#356812",
    "ok": "#755a00",
    "poor": "#9a3a12",
    "very-poor": "#9c1a33",
    "caption-text": "#000000",
    "caption-link": "#00111f",
}

# Backgrounds that follow the weather, as gradient stops from top to bottom.
BACKGROUND_POSITIONS = {
    "clear_day": [0, 55, 100],
    "clear_night": [0, 55, 100],
    "cloud_day": [0, 50, 100],
    "cloud_night": [0, 55, 100],
    "rain_day": [0, 55, 100],
    "rain_night": [0, 55, 100],
    "snow_day": [0, 55, 100],
    "snow_night": [0, 55, 100],
    "storm": [0, 55, 100],
    "fog": [0, 55, 100],
    "none": [0, 100],
}
DARK_BACKGROUNDS = {
    "clear_day": ["#2f6fa8", "#5a93c0", "#41688a"],
    "clear_night": ["#0c1530", "#1a2747", "#243252"],
    "cloud_day": ["#5b6673", "#66717e", "#4b5561"],
    "cloud_night": ["#1c222b", "#2a323d", "#333c48"],
    "rain_day": ["#3d4a58", "#4e5c6b", "#38434f"],
    "rain_night": ["#141a22", "#222c37", "#2b3743"],
    "snow_day": ["#66788c", "#8596a8", "#5d6c7d"],
    "snow_night": ["#232d3b", "#3a4656", "#424f60"],
    "storm": ["#23222f", "#38374a", "#2c2c3b"],
    "fog": ["#6a6f75", "#7a7f85", "#55595e"],
    "none": ["#2b3440", "#35404d"],
}
# Pale tints of the same weather, so dark text reads on all of them.
LIGHT_BACKGROUNDS = {
    "clear_day": ["#d8e8f6", "#e9f2fa", "#dce8f2"],
    "clear_night": ["#dcdfec", "#e6e8f1", "#dde0ea"],
    "cloud_day": ["#e3e6ea", "#ebedf0", "#dfe2e6"],
    "cloud_night": ["#d9dce1", "#e2e5e9", "#dadde2"],
    "rain_day": ["#d9e1ea", "#e4e9ef", "#d6dee7"],
    "rain_night": ["#d3d9e1", "#dde2e8", "#d2d8e0"],
    "snow_day": ["#e9eef4", "#f2f5f8", "#e6ebf1"],
    "snow_night": ["#dfe4ec", "#e8ecf2", "#dde2ea"],
    "storm": ["#dddbe5", "#e6e4ec", "#d9d7e1"],
    "fog": ["#e8e8e6", "#efefed", "#e3e3e0"],
    "none": ["#f4f1ea", "#efebe3"],
}

# The map is drawn in Python, so it follows st.context.theme.type, which only changes on a rerun.
DARK_MAP = {"style": "carto-darkmatter", "marker": "#ffffff"}
LIGHT_MAP = {"style": "carto-positron", "marker": "#1d232b"}


def css_variables():
    """One CSS rule that defines every token as a variable, light value first."""
    lines = []
    for name in DARK_TOKENS:
        lines.append(f"--{name}: light-dark({LIGHT_TOKENS[name]}, {DARK_TOKENS[name]});")
    return ".stApp { " + " ".join(lines) + " }"


def background(name):
    """A weather background as a CSS gradient whose colours follow the theme."""
    stops = []
    for number in range(len(BACKGROUND_POSITIONS[name])):
        light = LIGHT_BACKGROUNDS[name][number]
        dark = DARK_BACKGROUNDS[name][number]
        stops.append(f"light-dark({light}, {dark}) {BACKGROUND_POSITIONS[name][number]}%")
    return f"linear-gradient(180deg, {', '.join(stops)})"


def map_look(theme_type):
    """The basemap and city dot for "light" or "dark". Anything else counts as dark, the default."""
    if theme_type == "light":
        return LIGHT_MAP
    return DARK_MAP
