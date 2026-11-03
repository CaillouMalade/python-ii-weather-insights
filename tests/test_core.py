# Known-answer tests for the reading class, the clients, display helpers, cards and maps.
# Hand-made values only: no API call and no key.

import io
import math
import traceback

import pytest
from PIL import Image

from weather_app.cards import circuit_card, header, light, radar_text, status_strip, wind_legend
from weather_app.client import APIClient, RainViewerClient, WeatherClient, validate_location
from weather_app.display import compass_direction, format_local_time, high_low_text
from weather_app.maps import (
    RADAR_HALF_SIZE,
    RADAR_UPSCALE,
    WIND_BANDS,
    boost_opacity,
    enlarge,
    has_radar_coverage,
    image_to_data_uri,
    lat_lon_to_tile,
    radar_area,
    radar_figure,
    radar_over_coverage,
    stitch_tiles,
    tile_to_lat_lon,
    wind_arrow,
    wind_arrow_lines,
    wind_band,
    wind_figure,
    wind_grid_points,
    wind_label,
    zoom_for_length,
    track_bounds,
    track_layer,
    track_view,
    FRAME_MARGIN,
    FRAME_WIDTH,
    MAP_HEIGHT,
)
from weather_app.storage import load_circuits, load_track
from weather_app.models import WeatherReading

MONDAY = 1767571200  # 2026-01-05 00:00 UTC
SPA = {"id": "spa", "location": "Spa-Francorchamps", "country": "Belgium", "latitude": 50.4372, "longitude": 5.9714, "timezone": "Europe/Brussels", "length_km": 7.004, "track_file": "be-1925.geojson", "track_credit": "f1-circuits (MIT)"}


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


def test_status_strip_has_three_named_lights_the_sentence_and_the_radar():
    html = status_strip(["rain", "dry", None], "Rain likely <now>.", "Radar 07:50")
    assert html.count('class="light ') == 3
    assert "Now: rain likely" in html
    assert "Next 3 hours: dry" in html
    assert "Later today: no forecast" in html
    assert "Rain likely &lt;now&gt;." in html
    assert "Radar 07:50" in html


def test_radar_text_says_why_the_radar_cannot_be_trusted():
    good = {"time": MONDAY, "complete": True, "covered": True}
    assert radar_text(good, 3600) == "Radar 01:00"
    assert radar_text(dict(good, covered=False), 0) == "No radar here"
    assert radar_text(dict(good, complete=False), 0) == "Radar incomplete"
    assert radar_text(None, 0) == "Radar unavailable"


def test_circuit_card_escapes_text_and_shows_its_light_and_wind():
    circuit = dict(SPA, location="<b>Spa</b>")
    html = circuit_card(circuit, make_reading(wind_deg=225), "rain", "", True, MONDAY)
    assert "<b>Spa</b>" not in html
    assert "&lt;b&gt;Spa&lt;/b&gt;" in html
    assert "Next 3 hours: rain likely" in html
    assert "36 km/h SW" in html
    assert "selected" in html


def test_circuit_card_without_a_reading_shows_the_escaped_note_and_an_unlit_light():
    html = circuit_card(SPA, None, None, "Bad <key>", False, MONDAY)
    assert "Bad &lt;key&gt;" in html
    assert 'class="light off"' in html
    assert "selected" not in html


def test_header_shows_the_circuit_time_and_units_but_no_subtitle():
    html = header(SPA, make_reading(wind_gust=12.5, wind_deg=270), 22.0, 14.0, 0.4, MONDAY)
    assert "Spa-Francorchamps" in html
    assert "Belgium" not in html
    assert "7.0 km" not in html
    assert "Mon 00:00" in html
    assert "36 km/h W" in html
    assert "Gusts 45 km/h" in html
    assert "40 %" in html
    assert "High 22°  Low 14°" in html


def test_header_without_a_forecast_shows_a_dash_for_rain():
    assert "–" in header(SPA, make_reading(), 20.0, 20.0, None, MONDAY)


def test_wind_legend_labels_each_band_once_with_the_unit_last():
    html = wind_legend()
    assert html.count("<span>") == len(WIND_BANDS)
    assert "<span>0</span>" in html
    assert "<span>40+ km/h</span>" in html


# Map framing and maths


def test_zoom_for_length_frames_the_circuit():
    # 13 for a 4 km track, one level out each time the length doubles.
    assert zoom_for_length(4) == 13
    assert zoom_for_length(8) == 12
    assert zoom_for_length(16) == 11
    # Real circuits: Spa 7.004 km, Le Mans 13.626 km, the Nordschleife 20.832 km.
    assert zoom_for_length(7.004) == 12.2
    assert zoom_for_length(13.626) == 11.2
    assert zoom_for_length(20.832) == 10.6
    # Kept between 10 and 13.5.
    assert zoom_for_length(1) == 13.5
    assert zoom_for_length(100) == 10


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


def test_radar_figure_without_an_outline_marks_the_circuit_and_uses_its_length():
    area = radar_area(50.4372, 5.9714)
    fig = radar_figure("data:,", area["bounds"], dict(SPA, track_file=""), [])
    assert fig.layout.map.layers[0].source == "data:,"
    assert len(fig.layout.map.layers) == 1
    assert fig.layout.map.center.lat == 50.4372
    assert fig.layout.map.zoom == 12.2
    assert list(fig.data[0].lat) == [50.4372]


def test_radar_figure_with_an_outline_frames_it_over_the_radar():
    segments = [[[5.96, 50.43], [5.98, 50.44]], [[5.98, 50.44], [5.97, 50.45]]]
    area = radar_area(50.4372, 5.9714)
    fig = radar_figure("data:,", area["bounds"], SPA, segments)
    layers = fig.layout.map.layers
    # The radar first, then the dark casing, then the crisp line on top.
    assert [layer.sourcetype for layer in layers] == ["image", "geojson", "geojson"]
    assert layers[1].line.width == 6 and layers[2].line.width == 3
    assert layers[2].color == "#E8EDEA"
    assert layers[1].sourceattribution == "f1-circuits (MIT)"
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


def test_track_layer_keeps_every_segment_and_credits_only_when_asked():
    segments = [[[0, 0], [1, 1]], [[2, 2], [3, 3]]]
    layer = track_layer(segments, "#E8EDEA", 3, 1, "")
    assert layer["source"]["geometry"] == {"type": "MultiLineString", "coordinates": segments}
    assert layer["below"] == "traces"
    assert "sourceattribution" not in layer
    assert track_layer(segments, "#E8EDEA", 3, 1, "f1-circuits (MIT)")["sourceattribution"] == "f1-circuits (MIT)"


# Wind grid and arrows


def test_wind_grid_is_nine_points_centred_on_the_circuit_north_row_first():
    points = wind_grid_points(0.0, 10.0)
    assert len(points) == 9
    assert points[4] == (0.0, 10.0)
    # At the equator one degree of longitude is as long as one of latitude.
    assert points[0] == (0.15, 9.85)
    assert points[8] == (-0.15, 10.15)


def test_wind_grid_widens_longitude_steps_away_from_the_equator():
    points = wind_grid_points(60.0, 0.0)
    # cos(60°) = 0.5, so 0.15 degrees of latitude match 0.3 degrees of longitude.
    assert points[3] == (60.0, -0.3)
    assert points[1] == (60.15, 0.0)


def test_wind_band_boundaries():
    assert wind_band(0) == 0
    assert wind_band(9.9) == 0
    assert wind_band(10) == 1
    assert wind_band(39.9) == 3
    assert wind_band(120) == len(WIND_BANDS) - 1


def test_wind_scale_runs_from_green_grey_to_the_red_flag():
    assert WIND_BANDS[-1][1] == "#E5484D"


def test_wind_arrow_points_where_the_wind_blows_to():
    # Wind from the north blows south: the tip is south of the middle and the tail north.
    # Arrows are half a grid step long, so the tip is a quarter step from the middle.
    latitudes, longitudes = wind_arrow(0.0, 0.0, 0)
    assert latitudes[1] == pytest.approx(-0.0375)
    assert latitudes[0] == pytest.approx(0.0375)
    assert longitudes[1] == pytest.approx(0.0)
    # Wind from the west blows east.
    _, longitudes = wind_arrow(0.0, 0.0, 270)
    assert longitudes[1] == pytest.approx(0.0375)


def test_wind_arrow_breaks_the_line_between_shaft_and_head():
    latitudes, longitudes = wind_arrow(45.0, 7.0, 90)
    assert len(latitudes) == len(longitudes) == 8
    assert latitudes[2] is None and latitudes[7] is None
    # Both sides of the head end at the tip.
    assert latitudes[4] == latitudes[1] and latitudes[6] == latitudes[1]


def test_wind_arrow_lines_group_by_band_and_skip_points_without_direction():
    points = [
        {"latitude": 0.0, "longitude": 0.0, "speed_kmh": 5, "degrees": 0},
        {"latitude": 0.2, "longitude": 0.0, "speed_kmh": 7, "degrees": 90},
        {"latitude": 0.4, "longitude": 0.0, "speed_kmh": 45, "degrees": 180},
        {"latitude": 0.6, "longitude": 0.0, "speed_kmh": 25, "degrees": None},
    ]
    lines = wind_arrow_lines(points)
    assert [line["color"] for line in lines] == [WIND_BANDS[0][1], WIND_BANDS[4][1]]
    assert len(lines[0]["latitudes"]) == 16
    assert len(lines[1]["latitudes"]) == 8


def test_wind_label_and_figure():
    points = [{"latitude": 0.0, "longitude": 0.0, "speed_kmh": 23.4, "degrees": 225}, {"latitude": 0.2, "longitude": 0.0, "speed_kmh": 3, "degrees": None}]
    assert wind_label(points[0]) == "23 km/h SW"
    assert wind_label(points[1]) == "3 km/h"
    circuit = {"latitude": 0.0, "longitude": 0.0, "track_credit": ""}
    fig = wind_figure(points, circuit, [])
    # One line for the one band with an arrow, the hover points, and the circuit dot.
    assert len(fig.data) == 3
    assert list(fig.data[1].hovertext) == ["23 km/h SW", "3 km/h"]
    assert len(fig.layout.map.layers) == 0


def test_wind_figure_draws_the_outline_faintly_instead_of_the_dot():
    points = [{"latitude": 0.0, "longitude": 0.0, "speed_kmh": 12, "degrees": 90}]
    circuit = {"latitude": 0.0, "longitude": 0.0, "track_credit": "f1-circuits (MIT)"}
    fig = wind_figure(points, circuit, [[[0, 0], [0.01, 0.01]]])
    assert len(fig.data) == 2
    layer = fig.layout.map.layers[0]
    assert layer.opacity < 0.5 and layer.line.width < 3
    assert layer.sourceattribution == "f1-circuits (MIT)"
    # The wind map keeps its regional framing.
    assert fig.layout.map.zoom == 8.3
