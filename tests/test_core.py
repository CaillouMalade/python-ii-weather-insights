# Known-answer tests for the reading class, the clients, display helpers, cards and maps.
# Hand-made values only: no API call and no key.

import io
import math
import traceback

import pytest
from PIL import Image

from weather_app.cards import circuit_card, header, wind_legend
from weather_app.client import APIClient, RainViewerClient, WeatherClient, validate_location
from weather_app.display import BACKGROUNDS, background_for, compass_direction, format_local_time, high_low_text, is_night
from weather_app.maps import (
    WIND_BANDS,
    boost_opacity,
    has_radar_coverage,
    image_to_data_uri,
    lat_lon_to_tile,
    radar_figure,
    radar_over_coverage,
    stitch_tiles,
    tile_grid,
    tile_to_lat_lon,
    wind_arrow,
    wind_arrow_lines,
    wind_band,
    wind_figure,
    wind_grid_points,
    wind_label,
)
from weather_app.models import WeatherReading

MONDAY = 1767571200  # 2026-01-05 00:00 UTC
SPA = {"id": "spa", "location": "Spa-Francorchamps", "country": "Belgium", "latitude": 50.4372, "longitude": 5.9714, "timezone": "Europe/Brussels", "length_km": 7.004}


def make_reading(location="Spa-Francorchamps", temperature=20.0, feels_like=19.0, conditions="clear sky", wind_deg=None, wind_gust=None):
    return WeatherReading(location, 50.4, 5.97, temperature, feels_like, 50, 10.0, conditions, wind_deg=wind_deg, wind_gust=wind_gust)


# Reading class


def test_feels_like_delta_property():
    assert make_reading(temperature=20.0, feels_like=18.5).feels_like_delta == -1.5


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


def test_is_night():
    assert is_night(50, 100, 200) is True
    assert is_night(150, 100, 200) is False
    assert is_night(200, 100, 200) is True
    assert is_night(150, None, None) is False


def test_compass_direction():
    assert compass_direction(0) == "N"
    assert compass_direction(90) == "E"
    assert compass_direction(225) == "SW"
    assert compass_direction(359) == "N"


def test_background_for_conditions_and_time_of_day():
    assert background_for(800, False) == BACKGROUNDS["clear_day"]
    assert background_for(800, True) == BACKGROUNDS["clear_night"]
    assert background_for(501, False) == BACKGROUNDS["rain_day"]
    assert background_for(211, True) == BACKGROUNDS["storm"]
    assert background_for(None, False) == BACKGROUNDS["none"]


def test_high_low_text_hides_a_misleading_equal_pair():
    assert high_low_text(15.4, 11.6) == "High 15°  Low 12°"
    assert high_low_text(31.2, 30.9) == ""


# Cards


def test_circuit_card_escapes_text_and_shows_wind():
    circuit = dict(SPA, location="<b>Spa</b>")
    html = circuit_card(circuit, make_reading(wind_deg=225), "", True, MONDAY)
    assert "<b>Spa</b>" not in html
    assert "&lt;b&gt;Spa&lt;/b&gt;" in html
    assert "36 km/h SW" in html
    assert "selected" in html


def test_circuit_card_without_a_reading_shows_the_escaped_note():
    html = circuit_card(SPA, None, "Bad <key>", False, MONDAY)
    assert "Bad &lt;key&gt;" in html
    assert "Belgium" in html


def test_header_shows_the_circuit_and_units():
    html = header(SPA, make_reading(wind_gust=12.5, wind_deg=270), 22.0, 14.0, 0.4, MONDAY)
    assert "Spa-Francorchamps" in html
    assert "Belgium · 7.0 km" in html
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


# Map maths


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


def test_tile_grid_size_and_centre():
    grid = tile_grid(0.1, 0.1, 4)
    assert len(grid["rows"]) == 3
    assert len(grid["rows"][0]) == 5
    # (0.1, 0.1) is in tile x=8, y=7 at zoom 4, and that tile is the grid's middle.
    assert grid["rows"][1][2] == (8, 7)


def test_tile_grid_bounds_contain_the_point():
    grid = tile_grid(48.85, 2.35, 5)
    west, north = grid["bounds"][0]
    east, south = grid["bounds"][2]
    assert west < 2.35 < east
    assert south < 48.85 < north


def test_tile_grid_wraps_at_the_date_line():
    rows = tile_grid(0.1, 179.0, 2)["rows"]
    assert rows[0] == [(1, 0), (2, 0), (3, 0), (0, 0), (1, 0)]


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


def test_has_radar_coverage_reads_the_right_pixel():
    grid = tile_grid(0.1, 0.1, 4)
    image = Image.new("RGBA", (5 * 256, 3 * 256), (0, 0, 0, 0))
    assert has_radar_coverage(image, 0.1, 0.1, 4, grid) is True
    black = Image.new("RGBA", (5 * 256, 3 * 256), (0, 0, 0, 255))
    assert has_radar_coverage(black, 0.1, 0.1, 4, grid) is False


def test_radar_over_coverage_shades_lightly_and_keeps_radar_on_top():
    coverage = Image.new("RGBA", (2, 1), (0, 0, 0, 255))
    coverage.putpixel((1, 0), (0, 0, 0, 0))
    radar = Image.new("RGBA", (2, 1), (0, 0, 0, 0))
    result = radar_over_coverage(radar, coverage)
    assert 0 < result.getpixel((0, 0))[3] < 255
    assert result.getpixel((1, 0))[3] == 0


def test_image_to_data_uri():
    assert image_to_data_uri(Image.new("RGBA", (1, 1))).startswith("data:image/png;base64,")


def test_radar_figure_puts_the_image_on_the_map():
    grid = tile_grid(50.4, 5.97, 6)
    fig = radar_figure("data:,", grid["bounds"], 50.4, 5.97)
    assert fig.layout.map.layers[0].source == "data:,"
    assert fig.layout.map.center.lat == 50.4


# Wind grid and arrows


def test_wind_grid_is_nine_points_centred_on_the_circuit_north_row_first():
    points = wind_grid_points(0.0, 10.0)
    assert len(points) == 9
    assert points[4] == (0.0, 10.0)
    # At the equator one degree of longitude is as long as one of latitude.
    assert points[0] == (0.2, 9.8)
    assert points[8] == (-0.2, 10.2)


def test_wind_grid_widens_longitude_steps_away_from_the_equator():
    points = wind_grid_points(60.0, 0.0)
    # cos(60°) = 0.5, so 0.2 degrees of latitude match 0.4 degrees of longitude.
    assert points[3] == (60.0, -0.4)
    assert points[1] == (60.2, 0.0)


def test_wind_band_boundaries():
    assert wind_band(0) == 0
    assert wind_band(9.9) == 0
    assert wind_band(10) == 1
    assert wind_band(39.9) == 3
    assert wind_band(120) == len(WIND_BANDS) - 1


def test_wind_arrow_points_where_the_wind_blows_to():
    # Wind from the north blows south: the tip is south of the middle and the tail north.
    latitudes, longitudes = wind_arrow(0.0, 0.0, 0)
    assert latitudes[1] == pytest.approx(-0.05)
    assert latitudes[0] == pytest.approx(0.05)
    assert longitudes[1] == pytest.approx(0.0)
    # Wind from the west blows east.
    _, longitudes = wind_arrow(0.0, 0.0, 270)
    assert longitudes[1] == pytest.approx(0.05)


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
    fig = wind_figure(points, 0.0, 0.0)
    # One line for the one band with an arrow, the hover points, and the circuit dot.
    assert len(fig.data) == 3
    assert list(fig.data[1].hovertext) == ["23 km/h SW", "3 km/h"]
