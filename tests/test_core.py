# Known-answer tests for the reading class, validation, parsing, display helpers,
# card escaping and map maths. Hand-made values only: no API call and no key.

import io

import pandas as pd
import pytest
from PIL import Image

from weather_app.cards import air_tile, city_card, detail_tiles, feels_small, format_precipitation, header, next_hours_strip
from weather_app.client import WeatherClient, validate_location
from weather_app.display import (
    aqi_label,
    aqi_position,
    background_for,
    BACKGROUNDS,
    compass_direction,
    high_low_text,
    format_local_time,
    is_night,
    range_bar,
    today_high_low,
    uv_label,
    weather_emoji,
)
from weather_app.maps import image_to_data_uri, lat_lon_to_tile, stitch_tiles, tile_grid, tile_to_lat_lon
from weather_app.models import WeatherReading

MONDAY = 1767571200  # 2026-01-05 00:00 UTC


def make_reading(location="Madrid, ES", temperature=20.0, feels_like=19.0, conditions="clear sky"):
    return WeatherReading(location, 40.4, -3.7, temperature, feels_like, 50, 10.0, conditions)


# Reading class


def test_feels_like_delta_property():
    assert make_reading(temperature=20.0, feels_like=18.5).feels_like_delta == -1.5


def test_sorted_orders_readings_by_temperature():
    cold = make_reading("Oslo, NO", -2.0, -6.0)
    warm = make_reading("Madrid, ES", 20.0, 19.0)
    assert sorted([warm, cold]) == [cold, warm]


def test_repr():
    assert repr(make_reading()) == "WeatherReading('Madrid, ES', 20.0°C)"


def test_to_dict_has_optional_fields_as_none():
    values = make_reading().to_dict()
    assert values["location"] == "Madrid, ES"
    assert values["feels_like"] == 19.0
    assert values["wind_gust"] is None


# Input validation


def test_validate_location_accepts_a_good_location():
    assert validate_location({"location": "Madrid, ES", "latitude": 40.4, "longitude": -3.7}) is None


def test_validate_location_rejects_a_blank_name():
    with pytest.raises(ValueError, match="no name"):
        validate_location({"location": "  ", "latitude": 40.4, "longitude": -3.7})


def test_validate_location_rejects_text_coordinates():
    with pytest.raises(ValueError, match="invalid coordinates"):
        validate_location({"location": "Madrid, ES", "latitude": "north", "longitude": -3.7})


def test_validate_location_rejects_out_of_range_coordinates():
    with pytest.raises(ValueError, match="outside the valid range"):
        validate_location({"location": "Madrid, ES", "latitude": 91, "longitude": -3.7})


def test_current_rejects_a_bad_location_before_any_call():
    with pytest.raises(ValueError, match="outside the valid range"):
        WeatherClient("not-a-real-key").current({"location": "Madrid, ES", "latitude": 0, "longitude": 500})


def test_tile_rejects_an_unknown_layer_before_any_call():
    with pytest.raises(ValueError, match="Unknown map layer"):
        WeatherClient("not-a-real-key").tile("bad_layer", 1, 0, 0)


# Parsing


def test_parse_current_keeps_our_location_name_and_optional_fields():
    data = {
        "name": "Some station",
        "main": {"temp": 10.0, "feels_like": 9.0, "humidity": 70},
        "wind": {"speed": 2.0},
        "weather": [{"description": "mist", "id": 701, "icon": "50d"}],
    }
    location = {"location": "Madrid, ES", "latitude": 40.4, "longitude": -3.7}
    reading = WeatherClient("not-a-real-key")._parse_current(data, location)
    assert reading.location == "Madrid, ES"
    assert reading.wind_gust is None
    assert reading.weather_id == 701


def test_parse_current_turns_a_missing_field_into_a_clear_error():
    with pytest.raises(ValueError, match="unexpected format"):
        WeatherClient("not-a-real-key")._parse_current({"main": {}}, {"location": "x", "latitude": 0, "longitude": 0})


def test_parse_forecast_treats_missing_rain_as_zero():
    data = {"list": [{"dt": 1, "main": {"temp": 5.0, "feels_like": 4.0}, "weather": [{"icon": "01d"}], "rain": {"3h": 1.5}}, {"dt": 2, "main": {"temp": 6.0, "feels_like": 5.0}, "weather": [{"icon": "01d"}]}]}
    steps = WeatherClient("not-a-real-key")._parse_forecast(data)
    assert [step["rain_3h"] for step in steps] == [1.5, 0]


def test_parse_air_skips_entries_without_a_time_and_tolerates_missing_parts():
    data = {"coord": {}, "list": [{"main": {"aqi": 1}}, {"dt": 5, "components": {"pm2_5": 7.0}}]}
    rows = WeatherClient("not-a-real-key")._parse_air(data)
    assert len(rows) == 1
    assert rows[0]["aqi"] is None
    assert rows[0]["pm2_5"] == 7.0
    assert rows[0]["o3"] is None


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


def test_weather_emoji_matches_exact_and_general_codes():
    assert weather_emoji("01n") == "🌙"
    assert weather_emoji("09d") == "🌧️"
    assert weather_emoji(None) == "☁️"


def test_background_for_conditions_and_time_of_day():
    assert background_for(800, False) == BACKGROUNDS["clear_day"]
    assert background_for(800, True) == BACKGROUNDS["clear_night"]
    assert background_for(500, False) == BACKGROUNDS["rain_day"]
    assert background_for(601, True) == BACKGROUNDS["snow_night"]
    assert background_for(211, False) == BACKGROUNDS["storm"]
    assert background_for(741, False) == BACKGROUNDS["fog"]
    assert background_for(804, False) == BACKGROUNDS["cloud_day"]
    assert background_for(None, False) == BACKGROUNDS["none"]


def test_aqi_label_and_position():
    assert aqi_label(3) == "Moderate"
    assert aqi_label(9) == "Unknown"
    assert aqi_position(1) == 0
    assert aqi_position(5) == 100


def test_uv_label_boundaries():
    assert uv_label(2.9) == "Low"
    assert uv_label(3) == "Moderate"
    assert uv_label(8) == "Very high"
    assert uv_label(11) == "Extreme"


def test_range_bar():
    assert range_bar(5, 15, 0, 20) == (25.0, 50.0)
    assert range_bar(5, 5, 5, 5) == (0.0, 100.0)


def test_today_high_low_widens_the_forecast_with_the_current_values():
    days = pd.DataFrame({"local_date": ["2026-01-05"], "high": [15.0], "low": [8.0]})
    assert today_high_low(days, "2026-01-05", 18.0, 9.0) == (18.0, 8.0)


def test_today_high_low_falls_back_when_no_step_is_left_today():
    days = pd.DataFrame({"local_date": ["2026-01-06"], "high": [15.0], "low": [8.0]})
    assert today_high_low(days, "2026-01-05", 12.0, 7.0) == (12.0, 7.0)


# Cards: text from outside must never become HTML


def test_city_card_escapes_text():
    html = city_card("<b>Town</b>", make_reading(conditions="<script>x</script>"), 1.0, 0.0, "", False, MONDAY)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "<b>Town" not in html


def test_city_card_without_a_reading_shows_the_escaped_note():
    html = city_card("Town", None, None, None, "<i>failed</i>", False, MONDAY)
    assert "&lt;i&gt;failed" in html


def test_header_escapes_text_and_uses_high_low_wording():
    html = header("<b>Town</b>", make_reading(temperature=20.4, conditions="<i>rain</i>"), 21.0, 3.0, 0.5, MONDAY)
    assert "&lt;b&gt;Town" in html
    assert "<i>" not in html
    assert "20°" in html
    assert "High 21°  Low 3°" in html
    assert "50 %" in html


def test_feels_small_uses_the_delta():
    assert feels_small(-2.0) == "2° colder than actual"
    assert feels_small(3.0) == "3° warmer than actual"
    assert feels_small(0.2) == "About the actual temperature"


def test_high_low_text():
    assert high_low_text(15.4, 11.6) == "High 15°  Low 12°"


def test_format_precipitation():
    assert format_precipitation(0) == "0 mm"
    assert format_precipitation(0.42) == "0.4 mm"


def make_strip_steps():
    return pd.DataFrame({"dt": [MONDAY + 3600], "temperature": [14.2], "wind_speed": [5.0], "rain_3h": [0.4], "snow_3h": [0.0], "pop": [0.25], "icon": ["10d"]})


def test_strip_puts_the_unit_on_every_value():
    reading = make_reading()
    assert "14°" in next_hours_strip(make_strip_steps(), 0, "Temperature", reading)
    wind = next_hours_strip(make_strip_steps(), 0, "Wind", reading)
    assert "18 km/h" in wind
    assert "36 km/h" in wind
    rain = next_hours_strip(make_strip_steps(), 0, "Precipitation", reading)
    assert "0.4 mm" in rain
    assert "25 % chance" in rain
    assert "0 mm" in rain


def test_strip_shows_regular_times_only():
    html = next_hours_strip(make_strip_steps(), 0, "Temperature", make_reading())
    assert "01:00" in html
    assert "Sunrise" not in html


def test_air_tile_hidden_without_aqi():
    assert air_tile({"aqi": None}) == ""


def test_detail_tiles_show_uv_as_today_and_hide_missing_data():
    reading = make_reading()
    reading.sunrise = MONDAY + 7 * 3600
    reading.timezone_offset = 3600
    html = detail_tiles(reading, None, 3.6, None, "")
    assert "UV index today" in html
    assert "08:00" in html
    assert "Sunset" not in html
    assert "UV index today" not in detail_tiles(reading, None, None, None, "")


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
    # Near longitude 180 at zoom 2 there are only four columns, so tile numbers wrap to 0.
    rows = tile_grid(0.1, 179.0, 2)["rows"]
    assert rows[0] == [(1, 0), (2, 0), (3, 0), (0, 0), (1, 0)]


def test_tile_grid_stays_on_the_map_near_the_pole():
    rows = tile_grid(84.0, 0.0, 4)["rows"]
    assert rows[0][0][1] == 0


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


def test_image_to_data_uri():
    uri = image_to_data_uri(Image.new("RGBA", (1, 1)))
    assert uri.startswith("data:image/png;base64,")
