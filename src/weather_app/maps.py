"""Weather map helpers: tile maths, stitching tiles into one image, and the Plotly map.

The tile URLs need the API key, so the server fetches the tiles and the browser only
ever receives the finished image, as a data URI. That keeps the key out of the page.
"""

import base64
import io
import math

import plotly.graph_objects as go
from PIL import Image

TILE_SIZE = 256
GRID_COLUMNS = 5
GRID_ROWS = 3


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
    return {"rows": rows, "bounds": bounds}


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


def image_to_data_uri(image):
    """Return an image as text the browser can show without requesting any URL."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_map_figure(image_uri, bounds, latitude, longitude, view_zoom):
    """A Plotly map: free dark basemap, weather image on top, and a dot on the city."""
    fig = go.Figure(go.Scattermap(lat=[latitude], lon=[longitude], mode="markers", marker=dict(size=11, color="white")))
    fig.update_layout(
        map=dict(
            style="carto-darkmatter",
            center=dict(lat=latitude, lon=longitude),
            zoom=view_zoom,
            layers=[dict(sourcetype="image", source=image_uri, coordinates=bounds, opacity=0.85)],
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=420,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig
