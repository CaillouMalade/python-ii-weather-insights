# Known-answer tests for the reading class, the clients, display helpers, cards and maps.
# Hand-made values only: no API call and no key.

import io
import math
import traceback

import pytest
from PIL import Image

from weather_app.cards import light, now_group, radar_problem, session_row
from weather_app.client import APIClient, RainViewerClient, WeatherClient, validate_location
from weather_app.display import compass_direction, format_local_time, high_low_text
from weather_app.maps import (
    FRAME_MARGIN,
    FRAME_WIDTH,
    MAP_HEIGHT,
    RADAR_HALF_SIZE,
    RADAR_UPSCALE,
    WIND_BANDS,
    WIND_FIELD_SIZE,
    boost_opacity,
    circuit_bounds,
    enlarge,
    grid_vectors,
    has_radar_coverage,
    image_to_data_uri,
    interpolate_wind,
    lat_lon_to_tile,
    outline_layers,
    radar_area,
    radar_figure,
    radar_over_coverage,
    stitch_tiles,
    tile_to_lat_lon,
    track_bounds,
    track_layer,
    track_view,
    vector_to_wind,
    wind_arrow,
    wind_arrow_lines,
    wind_band,
    wind_field,
    wind_figure,
    wind_grid_bounds,
    wind_grid_points,
    wind_label,
    wind_vector,
)
from weather_app.storage import load_circuits, load_track
from weather_app.models import WeatherReading

MONDAY = 1767571200  # 2026-01-05 00:00 UTC
SPA = {"id": "spa", "location": "Spa-Francorchamps", "country": "Belgium", "latitude": 50.4372, "longitude": 5.9714, "timezone": "Europe/Brussels", "length_km": 7.004, "track_file": "be-1925.geojson"}


def make_reading(location="Spa-Francorchamps", temperature=20.0, feels_like=19.0, conditions="clear sky", wind_deg=None, wind_gust=None):
    return WeatherReading(location, 50.4, 5.97, temperature, feels_like, 50, 10.0, conditions, wind_deg=wind_deg, wind_gust=wind_gust)


# Reading class


def test_wind_kmh_property():
    assert make_reading().wind_kmh == 36.0


def test_sorted_orders_readings_by_temperature():
    cold = make_reading("Silverstone", -2.0, -6.0)
    warm = make_reading("Jerez", 20.0, 19.0)
    assert sorted([warm, cold]) == [cold, warm]


def test_repr():
    assert repr(make_reading()) == "WeatherReading('Spa-Francorchamps', 20.0°C)"


def test_to_dict_has_optional_fields_as_none():
    values = make_reading().to_dict()
    assert values["location"] == "Spa-Francorchamps"
    assert values["wind_gust"] is None


# Providers with and without a key


def test_a_provider_without_a_key_sends_no_key_parameter():
    assert APIClient("https://example.com")._with_key({"a": 1}) == {"a": 1}
    assert RainViewerClient()._with_key({}) == {}


def test_a_provider_with_a_key_sends_it_under_its_own_name():
    assert WeatherClient("not-a-real-key")._with_key({"a": 1}) == {"a": 1, "appid": "not-a-real-key"}


def test_rainviewer_takes_the_newest_frame():
    data = {"host": "https://h", "radar": {"past": [{"path": "/old", "time": 1}, {"path": "/new", "time": 2}]}}
    assert RainViewerClient()._parse_latest_frame(data) == {"host": "https://h", "path": "/new", "time": 2}


def test_rainviewer_with_no_frames_gives_a_clear_error():
    with pytest.raises(ValueError, match="unexpected format"):
        RainViewerClient()._parse_latest_frame({"host": "https://h", "radar": {"past": []}})


def test_network_errors_do_not_keep_the_url_with_the_key():
    # An invalid address fails at once, with no network call. Port 9 on this machine refuses the connection.
    for url in ["notaprotocol://example", "http://127.0.0.1:9"]:
        client = APIClient(url, "secret-key", "appid", timeout=5)
        with pytest.raises(ValueError) as caught:
            client._get("path", {})
        assert caught.value.__cause__ is None
        assert caught.value.__suppress_context__ is True
        assert "secret-key" not in "".join(traceback.format_exception(caught.value))


# Input validation: every circuit and grid point is checked before any call


def test_validate_location_accepts_a_good_location():
    assert validate_location(SPA) is None


def test_validate_location_rejects_a_blank_name():
    with pytest.raises(ValueError, match="no name"):
        validate_location({"location": "  ", "latitude": 40.4, "longitude": -3.7})


def test_validate_location_rejects_text_coordinates():
    with pytest.raises(ValueError, match="invalid coordinates"):
        validate_location({"location": "Jarama", "latitude": "north", "longitude": -3.7})


def test_validate_location_rejects_a_blank_csv_cell():
    with pytest.raises(ValueError, match="no coordinates"):
        validate_location({"location": "Jarama", "latitude": math.nan, "longitude": -3.7})


def test_validate_location_rejects_out_of_range_coordinates():
    with pytest.raises(ValueError, match="outside the valid range"):
        validate_location({"location": "Jarama", "latitude": 91, "longitude": -3.7})


def test_current_rejects_a_bad_location_before_any_call():
    with pytest.raises(ValueError, match="outside the valid range"):
        WeatherClient("not-a-real-key").current({"location": "Jarama", "latitude": 0, "longitude": 500})


# Parsing


def test_parse_current_keeps_our_location_name_and_optional_fields():
    data = {
        "name": "Some station",
        "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 70},
        "wind": {"speed": 2.0},
        "weather": [{"description": "mist", "id": 701, "icon": "50d"}],
    }
    reading = WeatherClient("not-a-real-key")._parse_current(data, SPA)
    assert reading.location == "Spa-Francorchamps"
    assert reading.wind_gust is None
    assert reading.weather_id == 701


def test_parse_current_turns_a_missing_field_into_a_clear_error():
    with pytest.raises(ValueError, match="unexpected format"):
        WeatherClient("not-a-real-key")._parse_current({"main": {}}, SPA)


def test_parse_forecast_treats_missing_rain_and_snow_as_zero():
    data = {"list": [{"dt": 1, "main": {"temp": 5.0}, "clouds": {"all": 40}, "pop": 0.6, "rain": {"3h": 1.5}}, {"dt": 2, "main": {"temp": 6.0}}]}
    steps = WeatherClient("not-a-real-key")._parse_forecast(data)
    assert [step["rain_3h"] for step in steps] == [1.5, 0]
    assert [step["snow_3h"] for step in steps] == [0, 0]
    assert [step["clouds"] for step in steps] == [40, None]
    assert [step["pop"] for step in steps] == [0.6, 0]


def test_parse_forecast_rejects_an_empty_forecast():
    with pytest.raises(ValueError, match="empty forecast"):
        WeatherClient("not-a-real-key")._parse_forecast({"list": []})


# Display helpers


def test_format_local_time_applies_the_offset():
    assert format_local_time(MONDAY, 3600) == "01:00"
    assert format_local_time(MONDAY, -3600, "%Y-%m-%d %H:%M") == "2026-01-04 23:00"


def test_compass_direction():
    assert compass_direction(0) == "N"
    assert compass_direction(90) == "E"
    assert compass_direction(225) == "SW"
    assert compass_direction(359) == "N"


def test_high_low_text_hides_a_misleading_equal_pair():
    assert high_low_text(15.4, 11.6) == "High 15°  Low 12°"
    assert high_low_text(31.2, 30.9) == ""


# Cards and lights


def test_light_says_its_meaning_in_words():
    assert light("dry", "Now") == '<span class="light dry" role="img" aria-label="Now: dry" title="Now: dry"></span>'
    assert 'class="light rain"' in light("rain", "Later today")
    assert 'aria-label="Later today: rain likely"' in light("rain", "Later today")
    assert 'class="light off"' in light(None, "Later today")
    assert "no forecast" in light(None, "Later today")


def test_radar_problem_only_speaks_when_the_radar_cannot_be_trusted():
    good = {"time": MONDAY, "complete": True, "covered": True}
    assert radar_problem(good) == ""
    assert radar_problem(dict(good, covered=False)) == "No radar here"
    assert radar_problem(dict(good, complete=False)) == "Radar incomplete"
    assert radar_problem(None) == "Radar unavailable"


def test_now_group_folds_labels_into_values_and_has_three_named_lights():
    html = now_group(make_reading(wind_gust=12.5, wind_deg=270, conditions="light <rain>"), 22.0, 14.0, MONDAY, ["rain", "dry", None], "Rain likely <now>", "")
    assert "Light &lt;rain&gt;" in html
    assert "Mon 00:00" in html
    assert '<span class="fact">High 22°  Low 14°</span> · <span class="fact">Feels 19°</span>' in html
    assert '<span class="fact">36 km/h W</span> · <span class="fact">Gusts 45</span> · <span class="fact">Humidity 50 %</span>' in html
    assert html.count('class="light ') == 3
    assert "Next 3 hours: dry" in html
    assert "Rain likely &lt;now&gt;" in html
    # No uppercase micro-labels and no radar stamp when the radar is fine.
    assert "FEELS" not in html and "Radar" not in html


def test_now_group_without_a_range_starts_with_feels_and_shows_a_radar_problem():
    html = now_group(make_reading(), 20.0, 20.0, MONDAY, [None, None, None], "Dry all week", "No radar here")
    assert '<div><span class="fact">Feels 19°</span></div>' in html
    assert "No radar here" in html


def test_session_row_shows_light_name_times_and_chance():
    session = {"track": "spa", "name": "<FP1>", "day": "2026-01-09", "start": "09:00", "end": "10:00"}
    html = session_row(session, "rain", 0.7)
    assert "&lt;FP1&gt;" in html and "<FP1>" not in html
    assert "Fri 09:00–10:00" in html
    assert "70 %" in html
    assert "&lt;FP1&gt;: rain likely" in html
    # Beyond the forecast: unlit, and no value at all.
    beyond = session_row(session, None, None)
    assert 'class="light off"' in beyond and "%" not in beyond


# Map framing and maths


def test_lat_lon_to_tile_known_points():
    # The middle of the map at zoom 1 is where the four tiles meet.
    assert lat_lon_to_tile(0, 0, 1) == (1.0, 1.0)
    x, _ = lat_lon_to_tile(0, -180, 3)
    assert x == 0.0


def test_tile_to_lat_lon_reverses_lat_lon_to_tile():
    x, y = lat_lon_to_tile(48.85, 2.35, 6)
    latitude, longitude = tile_to_lat_lon(x, y, 6)
    assert latitude == pytest.approx(48.85)
    assert longitude == pytest.approx(2.35)


def test_radar_area_is_a_square_around_the_place():
    area = radar_area(0.0, 0.0)
    # At zoom 7 the point (0, 0) is the corner of four tiles: pixel 16384 both ways.
    assert area["rows"] == [[(63, 63), (64, 63)], [(63, 64), (64, 64)]]
    size = 2 * RADAR_HALF_SIZE
    assert area["crop"] == (256 - RADAR_HALF_SIZE, 256 - RADAR_HALF_SIZE, 256 + RADAR_HALF_SIZE, 256 + RADAR_HALF_SIZE)
    assert area["crop"][2] - area["crop"][0] == size
    west, north = area["bounds"][0]
    east, south = area["bounds"][2]
    assert west == pytest.approx(-east)
    assert north == pytest.approx(-south)
    assert west < 0 < east and south < 0 < north


def test_radar_area_inside_one_tile_needs_one_tile():
    # The middle of tile (66, 43) at zoom 7.
    latitude, longitude = tile_to_lat_lon(66.5, 43.5, 7)
    area = radar_area(latitude, longitude)
    assert area["rows"] == [[(66, 43)]]
    assert area["crop"] == (128 - RADAR_HALF_SIZE, 128 - RADAR_HALF_SIZE, 128 + RADAR_HALF_SIZE, 128 + RADAR_HALF_SIZE)


def test_radar_area_wraps_at_the_date_line():
    area = radar_area(0.0, 180.0)
    assert [x for x, _ in area["rows"][0]] == [127, 0]


def solid_png(color):
    buffer = io.BytesIO()
    Image.new("RGBA", (256, 256), color).save(buffer, format="PNG")
    return buffer.getvalue()


def test_stitch_tiles_places_tiles_and_leaves_gaps_clear():
    red = solid_png((255, 0, 0, 255))
    blue = solid_png((0, 0, 255, 255))
    image = stitch_tiles([[red, None], [b"not an image", blue]])
    assert image.size == (512, 512)
    assert image.getpixel((10, 10)) == (255, 0, 0, 255)
    assert image.getpixel((300, 10)) == (0, 0, 0, 0)
    assert image.getpixel((10, 300)) == (0, 0, 0, 0)
    assert image.getpixel((300, 300)) == (0, 0, 255, 255)


def test_boost_opacity_multiplies_and_keeps_colours():
    image = Image.new("RGBA", (2, 1), (10, 20, 30, 50))
    image.putpixel((1, 0), (10, 20, 30, 0))
    boosted = boost_opacity(image, 3)
    assert boosted.getpixel((0, 0)) == (10, 20, 30, 150)
    assert boosted.getpixel((1, 0))[3] == 0
    assert boost_opacity(image, 10).getpixel((0, 0))[3] == 255


def test_has_radar_coverage_reads_the_centre():
    size = 2 * RADAR_HALF_SIZE
    assert has_radar_coverage(Image.new("RGBA", (size, size), (0, 0, 0, 0))) is True
    assert has_radar_coverage(Image.new("RGBA", (size, size), (0, 0, 0, 255))) is False


def test_radar_over_coverage_shades_lightly_and_keeps_radar_on_top():
    coverage = Image.new("RGBA", (2, 1), (0, 0, 0, 255))
    coverage.putpixel((1, 0), (0, 0, 0, 0))
    radar = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    result = radar_over_coverage(radar, coverage)
    assert 0 < result.getpixel((0, 0))[3] < 255
    assert result.getpixel((1, 0))[3] == 0


def test_enlarge_is_smooth_and_leaves_no_dark_edge():
    image = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    image.putpixel((0, 0), (0, 120, 255, 255))
    big = enlarge(image)
    assert big.size == (2 * RADAR_UPSCALE, RADAR_UPSCALE)
    # Smooth: the middle is part-way see-through, not a hard step from solid to clear.
    middle = big.getpixel((RADAR_UPSCALE, RADAR_UPSCALE // 2))
    assert 0 < middle[3] < 255
    # No dark edge: where it fades, the colour stays the rain's blue instead of turning black.
    assert middle[2] > 200


def test_image_to_data_uri():
    assert image_to_data_uri(Image.new("RGBA", (1, 1))).startswith("data:image/png;base64,")


def test_circuit_bounds_from_the_outline_or_from_the_length():
    segments = [[[5.96, 50.43], [5.98, 50.44]]]
    assert circuit_bounds(SPA, segments) == track_bounds(segments)
    # Without an outline, a box reaching length / 6 km each way: 7.004 / 6 / 111.32 degrees north and south.
    box = circuit_bounds({"latitude": 0.0, "longitude": 10.0, "length_km": 6.6792}, [])
    assert box["north"] == pytest.approx(0.01)
    assert box["west"] == pytest.approx(9.99)


def test_radar_figure_without_an_outline_marks_the_circuit():
    area = radar_area(50.4372, 5.9714)
    fig = radar_figure("data:,", area["bounds"], dict(SPA, track_file=""), [])
    assert fig.layout.map.layers[0].source == "data:,"
    assert len(fig.layout.map.layers) == 1
    assert list(fig.data[-1].lat) == [50.4372]


def test_radar_figure_with_an_outline_frames_it_over_the_radar():
    segments = [[[5.96, 50.43], [5.98, 50.44]], [[5.98, 50.44], [5.97, 50.45]]]
    area = radar_area(50.4372, 5.9714)
    fig = radar_figure("data:,", area["bounds"], SPA, segments)
    layers = fig.layout.map.layers
    # The radar first, then the dark casing, then the crisp line on top.
    assert [layer.sourcetype for layer in layers] == ["image", "geojson", "geojson"]
    assert layers[1].line.width == 6 and layers[2].line.width == 3
    assert layers[2].color == "#E8EDEA"
    view = track_view(track_bounds(segments))
    assert fig.layout.map.zoom == view["zoom"]
    assert fig.layout.map.center.lat == pytest.approx(view["latitude"])
    # No dot where there is an outline.
    assert len(fig.data[0].lat) == 0


# Track outlines


def test_track_bounds():
    segments = [[[1.0, 40.0], [1.5, 40.2]], [[0.8, 39.9], [1.2, 40.1]]]
    assert track_bounds(segments) == {"west": 0.8, "south": 39.9, "east": 1.5, "north": 40.2}


def test_track_view_fits_a_square_track_by_its_height():
    # 0.02 degrees square on the equator. The map is 340 by 320 pixels, so the height decides:
    # log2(320 * 0.84 / (512 * 0.02 / 360)) = 13.21, rounded down.
    view = track_view({"west": -0.01, "south": -0.01, "east": 0.01, "north": 0.01})
    assert view["zoom"] == 13.2
    assert view["latitude"] == pytest.approx(0.0, abs=1e-9)
    assert view["longitude"] == pytest.approx(0.0, abs=1e-9)


def test_track_view_fits_a_wide_track_by_its_width():
    # log2(340 * 0.84 / (512 * 0.08 / 360)) = 11.29, rounded down.
    view = track_view({"west": 2.0, "south": -0.005, "east": 2.08, "north": 0.005})
    assert view["zoom"] == 11.2
    assert view["longitude"] == pytest.approx(2.04)


def test_track_view_stops_at_the_maximum_zoom():
    assert track_view({"west": 0.0, "south": 0.0, "east": 0.0, "north": 0.0})["zoom"] == 16


def test_every_real_track_fills_its_map():
    for circuit in load_circuits():
        segments = load_track(circuit["track_file"])
        assert len(segments) > 0, circuit["id"]
        bounds = track_bounds(segments)
        view = track_view(bounds)
        west, north = lat_lon_to_tile(bounds["north"], bounds["west"], view["zoom"])
        east, south = lat_lon_to_tile(bounds["south"], bounds["east"], view["zoom"])
        # In map pixels (512 per tile at this zoom), as a share of the map's width and height.
        filled = max((east - west) * 512 / FRAME_WIDTH, (south - north) * 512 / MAP_HEIGHT)
        assert 0.78 <= filled <= 1 - 2 * FRAME_MARGIN, (circuit["id"], filled)


def test_track_layer_keeps_every_segment():
    segments = [[[0, 0], [1, 1]], [[2, 2], [3, 3]]]
    layer = track_layer(segments, "#E8EDEA", 3)
    assert layer["source"]["geometry"] == {"type": "MultiLineString", "coordinates": segments}
    assert layer["below"] == "traces"
    assert outline_layers([]) == []
    assert len(outline_layers(segments)) == 2


# Wind field


BOX = {"west": 0.0, "south": 0.0, "east": 1.0, "north": 1.0}


def test_wind_grid_bounds_widen_the_outline_by_a_quarter_each_side():
    assert wind_grid_bounds(BOX) == {"west": -0.25, "south": -0.25, "east": 1.25, "north": 1.25}


def test_wind_grid_points_span_the_grid_bounds_north_row_first():
    points = wind_grid_points(wind_grid_bounds(BOX))
    assert len(points) == 9
    assert points[0] == (1.25, -0.25)
    assert points[4] == (0.5, 0.5)
    assert points[8] == (-0.25, 1.25)


def test_wind_grid_from_a_real_outline_surrounds_it():
    circuit = load_circuits()[[circuit["id"] for circuit in load_circuits()].index("lemans")]
    bounds = circuit_bounds(circuit, load_track(circuit["track_file"]))
    points = wind_grid_points(wind_grid_bounds(bounds))
    assert points[0][0] > bounds["north"] and points[8][0] < bounds["south"]
    assert points[0][1] < bounds["west"] and points[8][1] > bounds["east"]


def test_wind_vector_and_back():
    # From the west at 10 km/h: it blows east.
    east, north = wind_vector(10, 270)
    assert east == pytest.approx(10) and north == pytest.approx(0, abs=1e-9)
    assert vector_to_wind(east, north) == (pytest.approx(10), pytest.approx(270))
    assert wind_vector(10, None) == (0.0, 0.0)
    assert vector_to_wind(0.0, 0.0) == (0.0, None)


def test_interpolation_is_exact_on_grid_points_and_bilinear_between():
    grid = {"west": 0.0, "south": 0.0, "east": 2.0, "north": 2.0}
    # East parts 0..8 across the grid, north parts all 1.
    vectors = [(value, 1.0) for value in [0, 1, 2, 3, 4, 5, 6, 7, 8]]
    assert interpolate_wind(vectors, grid, 2.0, 0.0) == (0, 1)
    assert interpolate_wind(vectors, grid, 0.0, 2.0) == (8, 1)
    # Halfway between the four north-west points (0, 1, 3, 4): their average, 2.
    assert interpolate_wind(vectors, grid, 1.5, 0.5) == (pytest.approx(2.0), pytest.approx(1.0))
    # A quarter of the way east from the centre point (4) towards the next (5).
    assert interpolate_wind(vectors, grid, 1.0, 1.25)[0] == pytest.approx(4.25)


def test_interpolating_two_directions_averages_their_vectors_not_their_angles():
    grid = {"west": 0.0, "south": 0.0, "east": 2.0, "north": 2.0}
    west_wind = {"speed_kmh": 10, "degrees": 270}
    south_wind = {"speed_kmh": 10, "degrees": 180}
    readings = [west_wind, west_wind, west_wind, south_wind, south_wind, south_wind, south_wind, south_wind, south_wind]
    east, north = interpolate_wind(grid_vectors(readings), grid, 1.5, 1.0)
    speed, degrees = vector_to_wind(east, north)
    # Halfway between a west and a south wind is a south-west wind, slower than either.
    assert degrees == pytest.approx(225)
    assert speed == pytest.approx(10 / 2**0.5)


def test_a_failed_grid_point_takes_the_average_of_the_others():
    readings = [{"speed_kmh": 10, "degrees": 270}] * 8 + [None]
    assert grid_vectors(readings)[8] == (pytest.approx(10), pytest.approx(0, abs=1e-9))


def test_wind_field_is_an_even_five_by_five_over_the_framed_area():
    readings = [{"speed_kmh": 20, "degrees": 0}] * 9
    field = wind_field(readings, wind_grid_bounds(BOX), BOX)
    assert len(field) == WIND_FIELD_SIZE * WIND_FIELD_SIZE
    assert field[0]["latitude"] == pytest.approx(0.9) and field[0]["longitude"] == pytest.approx(0.1)
    assert field[24]["latitude"] == pytest.approx(0.1) and field[24]["longitude"] == pytest.approx(0.9)
    # A uniform wind stays the same everywhere.
    assert field[12]["speed_kmh"] == pytest.approx(20) and field[12]["degrees"] == pytest.approx(0)


def test_wind_band_boundaries():
    assert wind_band(0) == 0
    assert wind_band(9.9) == 0
    assert wind_band(10) == 1
    assert wind_band(39.9) == 3
    assert wind_band(120) == len(WIND_BANDS) - 1


def test_wind_arrow_points_where_the_wind_blows_to():
    # Wind from the north blows south: the tip is south of the middle and the tail north.
    latitudes, longitudes = wind_arrow(0.0, 0.0, 0, 0.1)
    assert latitudes[1] == pytest.approx(-0.05)
    assert latitudes[0] == pytest.approx(0.05)
    assert longitudes[1] == pytest.approx(0.0)
    # Wind from the west blows east.
    _, longitudes = wind_arrow(0.0, 0.0, 270, 0.1)
    assert longitudes[1] == pytest.approx(0.05)


def test_wind_arrow_lines_group_by_band_and_skip_points_without_direction():
    points = [
        {"latitude": 0.0, "longitude": 0.0, "speed_kmh": 5, "degrees": 0},
        {"latitude": 0.2, "longitude": 0.0, "speed_kmh": 7, "degrees": 90},
        {"latitude": 0.4, "longitude": 0.0, "speed_kmh": 45, "degrees": 180},
        {"latitude": 0.6, "longitude": 0.0, "speed_kmh": 25, "degrees": None},
    ]
    lines = wind_arrow_lines(points, 0.05)
    assert [line["color"] for line in lines] == [WIND_BANDS[0][1], WIND_BANDS[4][1]]
    assert len(lines[0]["latitudes"]) == 16
    assert len(lines[1]["latitudes"]) == 8


def test_wind_label():
    assert wind_label({"speed_kmh": 23.4, "degrees": 225}) == "23 km/h SW"
    assert wind_label({"speed_kmh": 3, "degrees": None}) == "3 km/h"


def test_wind_figure_is_framed_exactly_like_the_radar_with_the_full_outline():
    segments = [[[5.96, 50.43], [5.98, 50.44]], [[5.98, 50.44], [5.97, 50.45]]]
    grid = wind_grid_bounds(circuit_bounds(SPA, segments))
    field = wind_field([{"speed_kmh": 12, "degrees": 90}] * 9, grid, circuit_bounds(SPA, segments))
    wind = wind_figure(field, SPA, segments)
    radar = radar_figure("data:,", radar_area(50.4372, 5.9714)["bounds"], SPA, segments)
    assert wind.layout.map.zoom == radar.layout.map.zoom
    assert wind.layout.map.center.lat == radar.layout.map.center.lat
    # The same full-strength outline as the radar, not a faint one.
    assert [layer.line.width for layer in wind.layout.map.layers] == [6, 3]
    # One arrow line for the one speed band, then the 25 hover points.
    assert len(wind.data) == 2
    assert len(wind.data[1].hovertext) == 25


# Colour that encodes data


def test_temperature_color_known_answers():
    from weather_app.display import temperature_color
    assert temperature_color(-5) == "#6FA8DC"
    assert temperature_color(0) == "#6FA8DC"
    assert temperature_color(15) == "#C9C5B9"
    # Halfway between the 10° and 15° stops: (159+201)/2, (183+197)/2, (201+185)/2.
    assert temperature_color(12.5) == "#B4BEC1"
    assert temperature_color(25) == "#F0A040"
    assert temperature_color(40) == "#F0A040"


def test_temperature_scale_has_no_green_or_red():
    from weather_app.display import TEMPERATURE_STOPS
    for _, red, green, blue in TEMPERATURE_STOPS:
        # Never a green-dominant or a red-dominant colour: those mean dry and rain.
        assert not (green > red + 30 and green > blue + 30)
        assert not (red > green + 100 and red > blue + 100)


def test_rain_bar_is_red_only_when_rain_is_likely():
    from weather_app.display import RAIN_BAR_LIKELY, RAIN_BAR_UNLIKELY, rain_bar_color
    assert rain_bar_color(0.5, 0.5) == RAIN_BAR_LIKELY
    assert rain_bar_color(0.9, 0.5) == RAIN_BAR_LIKELY
    assert rain_bar_color(0.49, 0.5) == RAIN_BAR_UNLIKELY
    assert rain_bar_color(0.0, 0.5) == RAIN_BAR_UNLIKELY
    assert "229" not in RAIN_BAR_UNLIKELY


def test_condition_kind_and_glyphs():
    from weather_app.display import condition_kind
    from weather_app.icons import arrow_img, icon_img, icon_uri
    assert [condition_kind(code, False) for code in [211, 310, 501, 601, 741, 800, 801, 803, None]] == ["rain", "rain", "rain", "snow", "fog", "sun", "sun", "cloud", "cloud"]
    assert condition_kind(800, True) == "night"
    assert 'alt="Rain"' in icon_img("rain")
    # Drawn inline as a data URI: nothing is loaded from the network.
    assert icon_uri("cloud").startswith("data:image/svg+xml;base64,")
    assert 'src="data:image/svg+xml;base64,' in icon_img("sun")
    assert 'alt="From the SW"' in arrow_img(225, "#9A8FD0", "From the SW")


def test_wind_colour_is_one_hue_getting_brighter():
    from weather_app.maps import wind_color
    levels = []
    for speed in [0, 10, 20, 30, 40]:
        color = wind_color(speed)
        levels.append(int(color[1:3], 16) + int(color[3:5], 16) + int(color[5:7], 16))
    assert levels == sorted(levels)
    assert wind_color(5) == wind_color(0)


def test_now_group_colours_the_temperature_and_shows_a_glyph():
    reading = make_reading(temperature=25.0)
    html = now_group(reading, 26.0, 18.0, MONDAY, ["dry", "dry", "dry"], "Dry all week", "")
    assert 'style="color:#F0A040"' in html
    assert 'alt="Cloudy"' in html


def test_history_rows_draw_ranges_rain_and_wind_and_mute_partial_days():
    import pandas as pd
    from weather_app.cards import history_rows
    rows = pd.DataFrame(
        {
            "day": ["2026-11-01", "2026-11-02"],
            "low": [5.0, 10.0],
            "high": [15.0, 25.0],
            "wind_kmh": [12.0, 3.0],
            "direction": [225, float("nan")],
            "hours": [24, 6],
            "rain_hours": [3, 0],
            "full": [True, False],
        }
    )
    html = history_rows(rows)
    assert html.count('class="day-row') == 2
    assert html.count('class="day-row partial"') == 1
    assert "Sun 1" in html and "Mon 2" in html
    # On one shared scale from 5° to 25°: the first bar starts at 0 % and covers half.
    assert "left:0.0%;width:50.0%" in html
    assert "left:25.0%;width:75.0%" in html
    assert 'aria-label="Rain: rain likely"' in html and "<span>3 h</span>" in html
    assert 'aria-label="Dry: dry"' in html
    assert 'alt="From the SW"' in html and "12 km/h" in html
