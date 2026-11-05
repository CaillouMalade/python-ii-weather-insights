"""The two maps, framed the same way on the track outline: rain radar, and a field of wind arrows.

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

# Track outline. The framing assumes the narrowest map, about 340 px wide on a phone,
# and leaves this share of the map free on every side.
FRAME_WIDTH = 340
FRAME_MARGIN = 0.08
MAX_ZOOM = 16
KM_PER_DEGREE = 111.32

# Radar
TILE_SIZE = 256
# RainViewer's highest zoom: at 8 it answers with a "Zoom Level Not Supported" image.
RADAR_ZOOM = 7
# Radar pixels kept on each side of the circuit. At zoom 7 one pixel is about 1 km.
RADAR_HALF_SIZE = 24
# The kept square is enlarged this many times on the server, smoothly, so it is not blocky.
RADAR_UPSCALE = 16
RADAR_BOOST = 2
# How strongly areas without radar are shaded, out of 255.
NO_COVERAGE_OPACITY = 90

# Wind: a 3 by 3 grid of real readings (9 calls) over the outline, widened by this share of
# its size on every side, then a 3 by 3 field of large arrows interpolated from them.
WIND_GRID_SIZE = 3
WIND_GRID_MARGIN = 0.25
WIND_FIELD_SIZE = 3
# The lowest speed of each wind band, in km/h. Each band has one colour in the theme's
# wind_colors: one violet hue, standing out more when stronger, so it never reads as the
# green of dry, the red of rain or the temperature scale.
WIND_SPEEDS = [0, 10, 20, 30, 40]


# Framing


def track_bounds(segments):
    """The outline's edges: a dictionary with west, south, east and north in degrees."""
    longitudes = []
    latitudes = []
    for segment in segments:
        for point in segment:
            longitudes.append(point[0])
            latitudes.append(point[1])
    return {"west": min(longitudes), "south": min(latitudes), "east": max(longitudes), "north": max(latitudes)}


def circuit_bounds(circuit, segments):
    """The area both maps frame: the outline's edges, or without one, a box around the circuit.

    A lap of L km spans roughly L / 3 km across, so the box reaches L / 6 km each way.
    """
    if len(segments) > 0:
        return track_bounds(segments)
    half = circuit["length_km"] / 6 / KM_PER_DEGREE
    widen = 1 / math.cos(math.radians(circuit["latitude"]))
    return {
        "west": circuit["longitude"] - half * widen,
        "south": circuit["latitude"] - half,
        "east": circuit["longitude"] + half * widen,
        "north": circuit["latitude"] + half,
    }


def track_view(bounds):
    """The map centre and zoom that fit a track's bounds, with a margin on every side.

    Positions are taken on the web map's own grid (lat_lon_to_tile at zoom 0, from 0 to 1),
    because latitudes are not evenly spaced there. The basemap draws 512-pixel tiles, so
    at zoom z the whole world is 512 * 2**z pixels across.
    """
    west, north = lat_lon_to_tile(bounds["north"], bounds["west"], 0)
    east, south = lat_lon_to_tile(bounds["south"], bounds["east"], 0)
    usable = 1 - 2 * FRAME_MARGIN
    # max() keeps a single point from dividing by zero.
    zoom_across = math.log2(FRAME_WIDTH * usable / (512 * max(east - west, 1e-9)))
    zoom_down = math.log2(MAP_HEIGHT * usable / (512 * max(south - north, 1e-9)))
    latitude, longitude = tile_to_lat_lon((west + east) / 2, (north + south) / 2, 0)
    # Rounded down, so the whole track still fits.
    zoom = math.floor(min(zoom_across, zoom_down, MAX_ZOOM) * 10) / 10
    return {"latitude": latitude, "longitude": longitude, "zoom": zoom}


# Tile maths


def lat_lon_to_tile(latitude, longitude, zoom):
    """Return the (x, y) tile position as decimals, using the standard web map formula."""
    tiles_per_side = 2**zoom
    x = (longitude + 180) / 360 * tiles_per_side
    lat_radians = math.radians(latitude)
    y = (1 - math.asinh(math.tan(lat_radians)) / math.pi) / 2 * tiles_per_side
    return x, y


def tile_to_lat_lon(x, y, zoom):
    """Return the (latitude, longitude) of a tile position. Whole numbers give a tile's top-left corner."""
    tiles_per_side = 2**zoom
    longitude = x / tiles_per_side * 360 - 180
    latitude = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / tiles_per_side))))
    return latitude, longitude


def radar_area(latitude, longitude):
    """The square of radar pixels around a place at RADAR_ZOOM, as a dictionary.

    rows: lists of (x, y) tiles that hold the square, wrapping around the date line.
    crop: the square's (left, top, right, bottom) in pixels, once those tiles are joined.
    bounds: its corners as [longitude, latitude], in the order the Plotly image layer wants:
    top-left, top-right, bottom-right, bottom-left.
    """
    x, y = lat_lon_to_tile(latitude, longitude, RADAR_ZOOM)
    # Pixel positions on the whole world map, rounded so the crop is on whole pixels.
    left = round(x * TILE_SIZE) - RADAR_HALF_SIZE
    top = round(y * TILE_SIZE) - RADAR_HALF_SIZE
    size = 2 * RADAR_HALF_SIZE
    first_x = left // TILE_SIZE
    first_y = top // TILE_SIZE

    rows = []
    for tile_y in range(first_y, (top + size - 1) // TILE_SIZE + 1):
        row = []
        for tile_x in range(first_x, (left + size - 1) // TILE_SIZE + 1):
            row.append((tile_x % 2**RADAR_ZOOM, tile_y))
        rows.append(row)

    crop_left = left - first_x * TILE_SIZE
    crop_top = top - first_y * TILE_SIZE
    north, west = tile_to_lat_lon(left / TILE_SIZE, top / TILE_SIZE, RADAR_ZOOM)
    south, east = tile_to_lat_lon((left + size) / TILE_SIZE, (top + size) / TILE_SIZE, RADAR_ZOOM)
    return {
        "rows": rows,
        "crop": (crop_left, crop_top, crop_left + size, crop_top + size),
        "bounds": [[west, north], [east, north], [east, south], [west, south]],
    }


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


def has_radar_coverage(coverage_square):
    """Read the coverage square at its centre, the circuit. RainViewer draws it black where there is no radar."""
    return coverage_square.getpixel((RADAR_HALF_SIZE, RADAR_HALF_SIZE))[3] < 128


def radar_over_coverage(radar_image, coverage_image):
    """Shade the areas with no radar lightly, and put the radar on top."""
    red, green, blue, alpha = coverage_image.split()
    alpha = alpha.point(lambda value: min(value, NO_COVERAGE_OPACITY))
    shaded = Image.merge("RGBA", (red, green, blue, alpha))
    return Image.alpha_composite(shaded, radar_image)


def enlarge(image):
    """Enlarge the radar smoothly (bicubic). In RGBa mode the colours are multiplied by their
    opacity first, so see-through pixels do not leave dark edges around the rain."""
    size = (image.width * RADAR_UPSCALE, image.height * RADAR_UPSCALE)
    return image.convert("RGBa").resize(size, Image.Resampling.BICUBIC).convert("RGBA")


def image_to_data_uri(image):
    """Return an image as text the browser can show without requesting any URL."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


# Wind field


def wind_grid_bounds(bounds):
    """The framed bounds widened by WIND_GRID_MARGIN of their size on every side."""
    across = (bounds["east"] - bounds["west"]) * WIND_GRID_MARGIN
    down = (bounds["north"] - bounds["south"]) * WIND_GRID_MARGIN
    return {"west": bounds["west"] - across, "south": bounds["south"] - down, "east": bounds["east"] + across, "north": bounds["north"] + down}


def wind_grid_points(grid_bounds):
    """The 3 by 3 points where wind is fetched, north row first, as (latitude, longitude) pairs.
    Rounding keeps each point identical between reruns, so the cache finds it."""
    last = WIND_GRID_SIZE - 1
    points = []
    for row in range(WIND_GRID_SIZE):
        for column in range(WIND_GRID_SIZE):
            latitude = grid_bounds["north"] - (grid_bounds["north"] - grid_bounds["south"]) * row / last
            longitude = grid_bounds["west"] + (grid_bounds["east"] - grid_bounds["west"]) * column / last
            points.append((round(latitude, 4), round(longitude, 4)))
    return points


def wind_vector(speed_kmh, from_degrees):
    """The wind as (east, north) parts of the way it blows, in km/h.

    Directions cannot be averaged as numbers (350° and 10° would give 180°), so the field
    is interpolated on these two parts instead. No direction counts as no wind.
    """
    if from_degrees is None:
        return 0.0, 0.0
    to_radians = math.radians(from_degrees + 180)
    return speed_kmh * math.sin(to_radians), speed_kmh * math.cos(to_radians)


def vector_to_wind(east, north):
    """Back from (east, north) parts to (speed in km/h, the direction the wind comes from)."""
    speed = math.hypot(east, north)
    if speed < 1e-9:
        return 0.0, None
    return speed, (math.degrees(math.atan2(east, north)) + 180) % 360


def grid_vectors(readings):
    """The 9 grid vectors in grid order. A failed point (None) takes the average of the others."""
    known = []
    for reading in readings:
        if reading is not None:
            known.append(wind_vector(reading["speed_kmh"], reading["degrees"]))
    east_mean = sum([vector[0] for vector in known]) / len(known)
    north_mean = sum([vector[1] for vector in known]) / len(known)
    vectors = []
    for reading in readings:
        if reading is None:
            vectors.append((east_mean, north_mean))
        else:
            vectors.append(wind_vector(reading["speed_kmh"], reading["degrees"]))
    return vectors


def interpolate_wind(vectors, grid_bounds, latitude, longitude):
    """Bilinear interpolation of the 3 by 3 grid vectors at a place inside the grid.

    The place's position is measured in grid steps from the north-west point (0 to 2 each
    way). The four grid points around it are weighted by how close they are on each axis.
    """
    last = WIND_GRID_SIZE - 1
    across = (longitude - grid_bounds["west"]) / (grid_bounds["east"] - grid_bounds["west"]) * last
    down = (grid_bounds["north"] - latitude) / (grid_bounds["north"] - grid_bounds["south"]) * last
    column = min(int(across), last - 1)
    row = min(int(down), last - 1)
    x = across - column
    y = down - row
    corners = [
        (vectors[row * WIND_GRID_SIZE + column], (1 - x) * (1 - y)),
        (vectors[row * WIND_GRID_SIZE + column + 1], x * (1 - y)),
        (vectors[(row + 1) * WIND_GRID_SIZE + column], (1 - x) * y),
        (vectors[(row + 1) * WIND_GRID_SIZE + column + 1], x * y),
    ]
    east = sum([vector[0] * weight for vector, weight in corners])
    north = sum([vector[1] * weight for vector, weight in corners])
    return east, north


def wind_field(readings, grid_bounds, area):
    """An even 3 by 3 field of arrows over the framed area, each at the centre of its cell.

    readings holds the 9 grid readings in grid order, None where a call failed; the wider
    grid only feeds the interpolation, so no arrow falls off the map. Each arrow is a
    dictionary with latitude, longitude, speed_kmh and degrees.
    """
    vectors = grid_vectors(readings)
    field = []
    for row in range(WIND_FIELD_SIZE):
        for column in range(WIND_FIELD_SIZE):
            latitude = area["north"] - (area["north"] - area["south"]) * (row + 0.5) / WIND_FIELD_SIZE
            longitude = area["west"] + (area["east"] - area["west"]) * (column + 0.5) / WIND_FIELD_SIZE
            east, north = interpolate_wind(vectors, grid_bounds, latitude, longitude)
            speed, degrees = vector_to_wind(east, north)
            field.append({"latitude": latitude, "longitude": longitude, "speed_kmh": speed, "degrees": degrees})
    return field


def wind_band(speed_kmh):
    """The position in WIND_SPEEDS of the band a wind speed falls in."""
    band = 0
    for number in range(len(WIND_SPEEDS)):
        if speed_kmh >= WIND_SPEEDS[number]:
            band = number
    return band


def wind_color(speed_kmh, theme):
    """The colour of a wind speed, from its band."""
    return theme["wind_colors"][wind_band(speed_kmh)]


def wind_arrow(latitude, longitude, from_degrees, length):
    """One arrow centred on a place, as a list of latitudes and a list of longitudes.

    Wind direction says where the wind comes from (0 = from the north), so the arrow points
    the opposite way. length is in degrees of latitude. The line runs from tail to tip, then
    along the two sides of the head; None lifts the pen between them.
    """
    to_radians = math.radians((from_degrees + 180) % 360)
    longitude_scale = 1 / math.cos(math.radians(latitude))
    half = length / 2
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


def wind_arrow_lines(points, length, theme):
    """Join the arrows of each speed band into one line, so each band is one colour.

    points is a list of dictionaries with latitude, longitude, speed_kmh and degrees. A point
    without a direction gets no arrow. Returns one dictionary per band that has arrows.
    """
    lines = []
    for number in range(len(WIND_SPEEDS)):
        latitudes = []
        longitudes = []
        for point in points:
            if point["degrees"] is None or wind_band(point["speed_kmh"]) != number:
                continue
            arrow_latitudes, arrow_longitudes = wind_arrow(point["latitude"], point["longitude"], point["degrees"], length)
            latitudes = latitudes + arrow_latitudes
            longitudes = longitudes + arrow_longitudes
        if len(latitudes) > 0:
            lines.append({"color": theme["wind_colors"][number], "latitudes": latitudes, "longitudes": longitudes})
    return lines


def wind_label(point):
    """Hover text for one arrow, such as 23 km/h SW."""
    label = f"{point['speed_kmh']:.0f} km/h"
    if point["degrees"] is not None:
        label = f"{label} {compass_direction(point['degrees'])}"
    return label


# Figures


def circuit_dot(latitude, longitude, theme):
    return go.Scattermap(lat=[latitude], lon=[longitude], mode="markers", marker=dict(size=10, color=theme["text"]), hoverinfo="skip")


def track_layer(segments, color, width):
    """One line layer drawn from the outline. Every segment stays separate, as in the file.
    below="traces" keeps it under the arrows; later layers sit above earlier ones."""
    return dict(
        sourcetype="geojson",
        source={"type": "Feature", "properties": {}, "geometry": {"type": "MultiLineString", "coordinates": segments}},
        type="line",
        color=color,
        line=dict(width=width),
        below="traces",
    )


def outline_layers(segments, theme):
    """The outline as a casing in the page colour under a crisp line in the text colour, so it
    reads over rain and arrows alike: light on the dark map, dark on the light one."""
    if len(segments) == 0:
        return []
    return [track_layer(segments, theme["background"], 6), track_layer(segments, theme["text"], 3)]


def map_layout(fig, circuit, segments, layers, theme):
    """The look and framing both maps share: the theme's basemap, no margins, the outline filling
    the map. Without an outline, a dot marks the circuit."""
    if len(segments) == 0:
        fig.add_trace(circuit_dot(circuit["latitude"], circuit["longitude"], theme))
    view = track_view(circuit_bounds(circuit, segments))
    fig.update_layout(
        map=dict(style=theme["map_style"], center=dict(lat=view["latitude"], lon=view["longitude"]), zoom=view["zoom"], layers=layers + outline_layers(segments, theme)),
        margin=dict(l=0, r=0, t=0, b=0),
        height=MAP_HEIGHT,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def radar_figure(image_uri, image_bounds, circuit, segments, theme):
    """The radar under the track outline."""
    # A map needs at least one trace, even an empty one.
    fig = go.Figure(go.Scattermap(lat=[], lon=[]))
    return map_layout(fig, circuit, segments, [dict(sourcetype="image", source=image_uri, coordinates=image_bounds, opacity=1, below="traces")], theme)


def wind_figure(field, circuit, segments, theme):
    """The field of arrows over the outline, coloured by speed. Invisible markers give each arrow hover text."""
    area = circuit_bounds(circuit, segments)
    length = (area["north"] - area["south"]) / WIND_FIELD_SIZE * 0.7
    fig = go.Figure()
    for line in wind_arrow_lines(field, length, theme):
        fig.add_trace(go.Scattermap(lat=line["latitudes"], lon=line["longitudes"], mode="lines", line=dict(width=5, color=line["color"]), hoverinfo="skip"))
    fig.add_trace(
        go.Scattermap(
            lat=[point["latitude"] for point in field],
            lon=[point["longitude"] for point in field],
            mode="markers",
            marker=dict(size=18, opacity=0),
            hovertext=[wind_label(point) for point in field],
            hoverinfo="text",
        )
    )
    return map_layout(fig, circuit, segments, [], theme)
