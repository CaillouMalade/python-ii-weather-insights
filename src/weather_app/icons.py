"""Small weather glyphs drawn as SVG: no image files and no network requests.

Every glyph is a 24 by 24 drawing in thin strokes of the text colour. Only the sun is
warm, because that is the colour the eye reads as sun in any weather app. Streamlit's
HTML cleaner removes inline <svg>, so each glyph reaches the page as an <img> whose
source is the SVG itself, as a data URI, with alt text for screen readers.
"""

import base64

TEXT = "#E8EDEA"
SUN = "#E0B878"

CLOUD = "M7 18h10a4 4 0 0 0 0-8 5.5 5.5 0 0 0-10.6-1.5A4.2 4.2 0 0 0 7 18z"
SMALL_CLOUD = "M7 15h10a4 4 0 0 0 0-8 5.5 5.5 0 0 0-10.6-1.5A4.2 4.2 0 0 0 7 15z"
SHAPES = {
    "sun": f'<circle cx="12" cy="12" r="4.2" fill="{SUN}"/><path d="M12 2.5v2.6M12 18.9v2.6M2.5 12h2.6M18.9 12h2.6M5.3 5.3l1.8 1.8M16.9 16.9l1.8 1.8M5.3 18.7l1.8-1.8M16.9 7.1l1.8-1.8" stroke="{SUN}"/>',
    "night": '<path d="M18.5 14.5A7.5 7.5 0 0 1 9.5 5.5a7.5 7.5 0 1 0 9 9z"/>',
    "cloud": f'<path d="{CLOUD}"/>',
    "rain": f'<path d="{SMALL_CLOUD}"/><path d="M8 18l-1 3M12 18l-1 3M16 18l-1 3"/>',
    "snow": f'<path d="{SMALL_CLOUD}"/><path d="M8 19h.01M12 21h.01M16 19h.01"/>',
    "fog": '<path d="M4 9h16M4 13h16M6 17h12"/>',
}
NAMES = {"sun": "Sunny", "night": "Clear night", "cloud": "Cloudy", "rain": "Rain", "snow": "Snow", "fog": "Fog"}


def svg_uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")


def icon_uri(kind):
    """One condition glyph as a data URI, for the page and for pictures inside a Plotly chart."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" '
        f'stroke="{TEXT}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{SHAPES[kind]}</svg>'
    )
    return svg_uri(svg)


def icon_img(kind, size=20):
    """One condition glyph for the page, named for screen readers."""
    return f'<img class="glyph" src="{icon_uri(kind)}" width="{size}" height="{size}" alt="{NAMES[kind]}">'


def arrow_img(from_degrees, color, label):
    """A small arrow pointing where the wind blows to, in the wind's colour. Wind direction
    says where it comes from, so the arrow is turned the other way round."""
    turn = (from_degrees + 180) % 360
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
        f'<g transform="rotate({turn:.0f} 12 12)"><path d="M12 3v18M12 3l-5 6M12 3l5 6" fill="none" stroke="{color}" '
        'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></g></svg>'
    )
    return f'<img class="glyph" src="{svg_uri(svg)}" width="14" height="14" alt="{label}">'
