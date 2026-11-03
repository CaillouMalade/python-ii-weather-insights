"""The two maps: rain radar from stitched tiles, and wind arrows from a grid of points.

The server fetches everything. The browser only receives the finished radar image, as a
data URI, and the wind figures, so no URL with the key ever reaches the page.
"""

import base64
import io
import math

import plotly.graph_objects as go
from PIL import Image

from .display import compass_direction

MAP_HEIGHT = 320

# Radar
TILE_SIZE = 256
GRID_COLUMNS = 5
GRID_ROWS = 3
# The tiles are sharp when the map itself is one zoom level further out. RainViewer stops at 7.
TILE_ZOOM = 6
RADAR_BOOST = 2
# How strongly areas without radar are shaded, out of 255.
NO_COVERAGE_OPACITY = 90

# Wind: a 3 by 3 grid, so 9 calls, 0.2 degrees of latitude (about 22 km) apart.
WIND_GRID_SIZE = 3
WIND_GRID_STEP = 0.2
# Arrow length in degrees of latitude.
ARROW_LENGTH = 0.1
WIND_MAP_ZOOM = 8.3
# (lowest speed in km/h, colour). The legend under the map is drawn from this list too.
WIND_BANDS = [(0, "#8fc7e8"), (10, "#6fd3a0"), (20, "#f2d13c"), (30, "#ef8a3a"), (40, "#e0455a")]


# Tile maths


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


# Radar image


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


# Wind arrows


def wind_grid_points(latitude, longitude):
    """A square grid of points centred on the circuit, north row first, as (latitude, longitude) pairs.

    Longitude lines get closer towards the poles, so the longitude step is widened by
    1 / cos(latitude) to keep the points about as far apart both ways. Rounding keeps
    each point identical between reruns, so the cache finds it.
    """
    longitude_step = WIND_GRID_STEP / math.cos(math.radians(latitude))
    middle = WIND_GRID_SIZE // 2
    points = []
    for row in range(WIND_GRID_SIZE):
        for column in range(WIND_GRID_SIZE):
            points.append((round(latitude + (middle - row) * WIND_GRID_STEP, 4), round(longitude + (column - middle) * longitude_step, 4)))
    return points


def wind_band(speed_kmh):
    """The position in WIND_BANDS of the band a wind speed falls in."""
    band = 0
    for number in range(len(WIND_BANDS)):
        if speed_kmh >= WIND_BANDS[number][0]:
            band = number
    return band


def wind_arrow(latitude, longitude, from_degrees):
    """One arrow centred on a place, as a list of latitudes and a list of longitudes.

    Wind direction says where the wind comes from (0 = from the north), so the arrow points
    the opposite way. The line runs from tail to tip, then along the two sides of the head;
    None lifts the pen between them.
    """
    to_radians = math.radians((from_degrees + 180) % 360)
    longitude_scale = 1 / math.cos(math.radians(latitude))
    half = ARROW_LENGTH / 2
    north = math.cos(to_radians) * half
    east = math.sin(to_radians) * half * longitude_scale
    tip_latitude = latitude + north
    tip_longitude = longitude + east

    latitudes = [latitude - north, tip_latitude, None]
    longitudes = [longitude - east, tip_longitude, None]
    for turn in [150, -150]:
        side = to_radians + math.radians(turn)
        latitudes = latitudes + [tip_latitude + math.cos(side) * half * 0.6, tip_latitude]
        longitudes = longitudes + [tip_longitude + math.sin(side) * half * 0.6 * longitude_scale, tip_longitude]
    return latitudes + [None], longitudes + [None]


def wind_arrow_lines(points):
    """Join the arrows of each speed band into one line, so each band is one colour.

    points is a list of dictionaries with latitude, longitude, speed_kmh and degrees. A point
    without a direction gets no arrow. Returns one dictionary per band that has arrows.
    """
    lines = []
    for number in range(len(WIND_BANDS)):
        latitudes = []
        longitudes = []
        for point in points:
            if point["degrees"] is None or wind_band(point["speed_kmh"]) != number:
                continue
            arrow_latitudes, arrow_longitudes = wind_arrow(point["latitude"], point["longitude"], point["degrees"])
            latitudes = latitudes + arrow_latitudes
            longitudes = longitudes + arrow_longitudes
        if len(latitudes) > 0:
            lines.append({"color": WIND_BANDS[number][1], "latitudes": latitudes, "longitudes": longitudes})
    return lines


def wind_label(point):
    """Hover text for one grid point, such as 23 km/h SW."""
    label = f"{point['speed_kmh']:.0f} km/h"
    if point["degrees"] is not None:
        label = f"{label} {compass_direction(point['degrees'])}"
    return label


# Figures


def circuit_dot(latitude, longitude):
    return go.Scattermap(lat=[latitude], lon=[longitude], mode="markers", marker=dict(size=11, color="white"), hoverinfo="skip")


def map_layout(fig, latitude, longitude, zoom, layers):
    """The look both maps share: free dark basemap, centred on the circuit, no margins."""
    fig.update_layout(
        map=dict(style="carto-darkmatter", center=dict(lat=latitude, lon=longitude), zoom=zoom, layers=layers),
        margin=dict(l=0, r=0, t=0, b=0),
        height=MAP_HEIGHT,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def radar_figure(image_uri, bounds, latitude, longitude):
    layers = [dict(sourcetype="image", source=image_uri, coordinates=bounds, opacity=1)]
    return map_layout(go.Figure(circuit_dot(latitude, longitude)), latitude, longitude, TILE_ZOOM - 1, layers)


def wind_figure(points, latitude, longitude):
    """Arrows coloured by speed. Invisible markers on the points give each one hover text."""
    fig = go.Figure()
    for line in wind_arrow_lines(points):
        fig.add_trace(go.Scattermap(lat=line["latitudes"], lon=line["longitudes"], mode="lines", line=dict(width=3, color=line["color"]), hoverinfo="skip"))
    fig.add_trace(
        go.Scattermap(
            lat=[point["latitude"] for point in points],
            lon=[point["longitude"] for point in points],
            mode="markers",
            marker=dict(size=16, opacity=0),
            hovertext=[wind_label(point) for point in points],
            hoverinfo="text",
        )
    )
    fig.add_trace(circuit_dot(latitude, longitude))
    return map_layout(fig, latitude, longitude, WIND_MAP_ZOOM, [])
