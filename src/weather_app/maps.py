"""Weather map helpers: tile maths, stitching tiles into one image, and the Plotly map.

The tile URLs need the API key, so the server fetches the tiles and the browser only
ever receives the finished image, as a data URI. That keeps the key out of the page.
"""

import base64
import io
import math

import plotly.graph_objects as go
from PIL import Image

RADAR_LAYER = "Rain radar"
MAP_LAYERS = {
    "Temperature": "temp_new",
    "Wind": "wind_new",
    "Clouds": "clouds_new",
    "Pressure": "pressure_new",
}

# Colour scales from OpenWeatherMap's map legend (openweathermap.org/map_legend), listed as
# (label, colour). Temperature is as published. Wind is published in m/s and pressure in Pa,
# so their labels are converted to km/h and hPa. Stops are shown evenly spaced.
LEGENDS = {
    "Temperature": ("°C", [("-30", "#8257DB"), ("-20", "#208CEC"), ("-10", "#20C4E8"), ("0", "#23DDDD"), ("10", "#C2FF28"), ("20", "#FFF028"), ("30", "#FC8014")]),
    "Wind": ("km/h", [("18", "#EECECC"), ("54", "#B364BC"), ("90", "#3F213B"), ("180", "#744CAC"), ("360", "#4600AF")]),
    "Clouds": ("%", [("10", "#FDFDFF"), ("50", "#F7F7FF"), ("80", "#E9E9DF"), ("100", "#D2D2D2")]),
    "Pressure": ("hPa", [("940", "#0073FF"), ("980", "#4BD0D6"), ("1000", "#8DE7C7"), ("1010", "#B0F720"), ("1020", "#F0B800"), ("1040", "#FB5515"), ("1080", "#C60000")]),
}

# OpenWeatherMap's tiles are mostly see-through, so low values hardly show. Multiplying
# each pixel's opacity makes them read clearly, while coasts and labels still show through.
WEATHER_LAYER_BOOST = 1.5
# The basemap's first label layer. A layer placed below it leaves the labels on top.
FIRST_LABEL_LAYER = "waterway_label"
RADAR_BOOST = 2
# How strongly areas without radar are shaded, out of 255.
NO_COVERAGE_OPACITY = 90

TILE_SIZE = 256
GRID_COLUMNS = 5
GRID_ROWS = 3
# The tiles are sharp when the map itself is one zoom level further out.
TILE_ZOOM = 6


def lat_lon_to_tile(latitude, longitude, zoom):
    """Return the (x, y) tile position as decimals, using the standard web map formula."""
    tiles_per_side = 2**zoom
    x = (longitude + 180) / 360 * tiles_per_side
    lat_radians = math.radians(latitude)
    y = (1 - math.asinh(math.tan(lat_radians)) / math.pi) / 2 * tiles_per_side
    return x, y


def tile_to_lat_lon(x, y, zoom):
    """Return the (latitude, longitude) of the top-left corner of tile (x, y)."""
    tiles_per_side = 2**zoom
    longitude = x / tiles_per_side * 360 - 180
    latitude = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / tiles_per_side))))
    return latitude, longitude


def tile_grid(latitude, longitude, zoom):
    """Return the tile grid around a point as a dictionary.

    rows: lists of (x, y) tile numbers to download. Tile numbers wrap around the
    date line. bounds: the grid's corners, in the order the Plotly image layer wants:
    top-left, top-right, bottom-right, bottom-left, each as [longitude, latitude].
    """
    tiles_per_side = 2**zoom
    x, y = lat_lon_to_tile(latitude, longitude, zoom)

    first_x = int(x) - GRID_COLUMNS // 2
    # Keep the grid on the map: there are no tiles above the top or below the bottom.
    first_y = max(0, min(int(y) - GRID_ROWS // 2, tiles_per_side - GRID_ROWS))

    rows = []
    for row_number in range(GRID_ROWS):
        row = []
        for column_number in range(GRID_COLUMNS):
            row.append(((first_x + column_number) % tiles_per_side, first_y + row_number))
        rows.append(row)

    north, west = tile_to_lat_lon(first_x, first_y, zoom)
    south, east = tile_to_lat_lon(first_x + GRID_COLUMNS, first_y + GRID_ROWS, zoom)
    bounds = [[west, north], [east, north], [east, south], [west, south]]
    return {"rows": rows, "bounds": bounds, "first_x": first_x, "first_y": first_y}


def stitch_tiles(rows_of_png_bytes):
    """Join rows of PNG bytes into one image. A tile that is None or unreadable stays clear."""
    height = len(rows_of_png_bytes) * TILE_SIZE
    width = len(rows_of_png_bytes[0]) * TILE_SIZE
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    for row_number in range(len(rows_of_png_bytes)):
        for column_number in range(len(rows_of_png_bytes[row_number])):
            png_bytes = rows_of_png_bytes[row_number][column_number]
            if png_bytes is None:
                continue
            try:
                tile = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            except OSError:
                continue
            image.paste(tile, (column_number * TILE_SIZE, row_number * TILE_SIZE))
    return image


def boost_opacity(image, factor):
    """Multiply every pixel's opacity, up to fully solid. See-through pixels stay see-through."""
    red, green, blue, alpha = image.split()
    alpha = alpha.point(lambda value: min(255, int(value * factor)))
    return Image.merge("RGBA", (red, green, blue, alpha))


def has_radar_coverage(coverage_image, latitude, longitude, zoom, grid):
    """Read the coverage image at a place. RainViewer draws it black where there is no radar."""
    x, y = lat_lon_to_tile(latitude, longitude, zoom)
    pixel_x = int((x - grid["first_x"]) * TILE_SIZE)
    pixel_y = int((y - grid["first_y"]) * TILE_SIZE)
    return coverage_image.getpixel((pixel_x, pixel_y))[3] < 128


def radar_over_coverage(radar_image, coverage_image):
    """Shade the areas with no radar lightly, and put the radar on top."""
    red, green, blue, alpha = coverage_image.split()
    alpha = alpha.point(lambda value: min(value, NO_COVERAGE_OPACITY))
    shaded = Image.merge("RGBA", (red, green, blue, alpha))
    return Image.alpha_composite(shaded, radar_image)


def image_to_data_uri(image):
    """Return an image as text the browser can show without requesting any URL."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_map_figure(image_uri, bounds, latitude, longitude, below=None):
    """A Plotly map: free dark basemap, weather image on top, and a dot on the city.

    below is the basemap layer to put the image under. None puts it on top of everything.
    """
    fig = go.Figure(go.Scattermap(lat=[latitude], lon=[longitude], mode="markers", marker=dict(size=11, color="white")))
    fig.update_layout(
        map=dict(
            style="carto-darkmatter",
            center=dict(lat=latitude, lon=longitude),
            zoom=TILE_ZOOM - 1,
            layers=[dict(sourcetype="image", source=image_uri, coordinates=bounds, opacity=1, below=below)],
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=320,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
