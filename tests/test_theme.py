# The two themes: the same keys, AA contrast in each, and the same colours as Streamlit's config.

import tomllib
from pathlib import Path

from weather_app.display import temperature_color
from weather_app.maps import WIND_SPEEDS, outline_layers, wind_color
from weather_app.style import CSS_TOKENS, theme_css
from weather_app.theme import DARK, LIGHT, THEMES, theme_named

CONFIG = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"


def luminance(color):
    parts = []
    for start in [1, 3, 5]:
        value = int(color[start:start + 2], 16) / 255
        parts.append(value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * parts[0] + 0.7152 * parts[1] + 0.0722 * parts[2]


def contrast(first, second):
    lighter = max(luminance(first), luminance(second))
    darker = min(luminance(first), luminance(second))
    return (lighter + 0.05) / (darker + 0.05)


def test_both_themes_have_the_same_keys():
    assert sorted(DARK.keys()) == sorted(LIGHT.keys())
    for key in DARK:
        assert type(DARK[key]) == type(LIGHT[key]), key
    assert sorted(THEMES.keys()) == ["dark", "light"]


def test_both_themes_have_the_same_scales():
    for theme in [DARK, LIGHT]:
        assert len(theme["wind_colors"]) == len(WIND_SPEEDS)
        assert [stop[0] for stop in theme["temperature_stops"]] == [-5, 0, 5, 10, 15, 20, 25, 30]


def test_dark_is_the_theme_unless_light_is_asked_for():
    assert theme_named("light") is LIGHT
    assert theme_named("dark") is DARK
    assert theme_named(None) is DARK


def test_text_and_signals_meet_aa_on_both_themes():
    for theme in [DARK, LIGHT]:
        for background in [theme["background"], theme["surface"]]:
            assert contrast(theme["text"], background) >= 4.5
            assert contrast(theme["muted"], background) >= 4.5
            assert contrast(theme["green"], background) >= 4.5
        # Red is a light and a bar, never text: 3:1 is AA for graphics.
        assert contrast(theme["red"], theme["surface"]) >= 3


def test_every_temperature_colour_reads_on_its_surface():
    for theme in [DARK, LIGHT]:
        for celsius in range(-5, 31):
            assert contrast(temperature_color(celsius, theme), theme["surface"]) >= 4.5, (theme["surface"], celsius)


def test_a_cold_week_still_shows_its_range():
    # Le Mans this week, 2° to 13°: the two ends must look clearly different in both themes.
    for theme in [DARK, LIGHT]:
        cold = temperature_color(2, theme)
        mild = temperature_color(13, theme)
        difference = 0
        for start in [1, 3, 5]:
            difference = difference + abs(int(cold[start:start + 2], 16) - int(mild[start:start + 2], 16))
        assert difference > 120


def test_stronger_wind_stands_out_more_and_reads_on_its_map():
    # Dark: brighter when stronger. Light: darker when stronger. Every band at least 3:1 on its surface.
    for theme in [DARK, LIGHT]:
        contrasts = []
        for speed in WIND_SPEEDS:
            contrasts.append(contrast(wind_color(speed, theme), theme["surface"]))
        assert contrasts == sorted(contrasts)
        assert min(contrasts) >= 3, theme["surface"]


def test_outline_is_text_coloured_over_a_page_coloured_casing():
    segments = [[[0, 0], [1, 1]]]
    for theme in [DARK, LIGHT]:
        casing, line = outline_layers(segments, theme)
        assert casing["color"] == theme["background"] and line["color"] == theme["text"]
    assert LIGHT["map_style"] == "carto-positron" and DARK["map_style"] == "carto-darkmatter"


def test_css_carries_every_token_of_the_theme():
    for theme in [DARK, LIGHT]:
        css = theme_css(theme)
        for name in CSS_TOKENS:
            assert f"--{name}: {theme[name]};" in css
        # No colour is written in the rules themselves: they all come from the theme.
        rules = css[css.index("}"):]
        assert "#" not in rules and "rgba(" not in rules


def test_streamlit_config_uses_the_same_colours():
    with open(CONFIG, "rb") as file:
        config = tomllib.load(file)
    for name, theme in THEMES.items():
        section = config["theme"][name]
        assert section["backgroundColor"] == theme["background"]
        assert section["secondaryBackgroundColor"] == theme["surface"]
        assert section["textColor"] == theme["text"]
        assert section["primaryColor"] == theme["green"]
        assert section["sidebar"]["backgroundColor"] == theme["background"]
