# Known-answer tests for the reading class, validation, parsing, display helpers,
# card escaping and map maths. Hand-made values only: no API call and no key.

import io
import traceback

import pandas as pd
import pytest
from PIL import Image

from weather_app.cards import air_share_bar, air_tile, city_card, city_table, detail_tiles, feels_small, format_precipitation, header, map_legend, next_hours_strip, plan_day, pollutant_rows, radar_note
from weather_app.client import APIClient, RainViewerClient, WeatherClient, validate_city, validate_location
from weather_app.display import (
    aqi_label,
    aqi_position,
    background_for,
    BACKGROUNDS,
    compass_direction,
    display_names,
    high_low_text,
    format_local_time,
    is_night,
    rain_axis_ticks,
    range_bar,
    split_name,
    today_high_low,
    uv_label,
    weather_emoji,
)
from weather_app.maps import WEATHER_LAYER_BOOST, boost_opacity, build_map_figure, has_radar_coverage, image_to_data_uri, lat_lon_to_tile, radar_over_coverage, stitch_tiles, tile_grid, tile_to_lat_lon
from weather_app.models import WeatherReading
from weather_app.views_analytics import compare_tiles

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


# The key must not stay attached to a network error


def test_network_errors_do_not_keep_the_url_with_the_key():
    # An invalid address fails at once, with no network call. Port 9 on this machine refuses the connection.
    for url in ["notaprotocol://example", "http://127.0.0.1:9"]:
        client = APIClient(url, "secret-key", "appid", timeout=5)
        with pytest.raises(ValueError) as caught:
            client._get("path", {})
        assert caught.value.__cause__ is None
        assert caught.value.__suppress_context__ is True
        assert "secret-key" not in "".join(traceback.format_exception(caught.value))


# Input validation


def test_validate_city_strips_spaces_and_accepts_accents():
    assert validate_city("  São Paulo ") == "São Paulo"


def test_validate_city_has_a_message_for_each_problem():
    with pytest.raises(ValueError, match="Please enter a city name"):
        validate_city("   ")
    with pytest.raises(ValueError, match="contains no letters"):
        validate_city("12345")
    with pytest.raises(ValueError, match="too long"):
        validate_city("a" * 101)
    with pytest.raises(ValueError, match="must be text"):
        validate_city(None)


def test_find_city_rejects_bad_input_before_any_call():
    with pytest.raises(ValueError, match="Please enter a city name"):
        WeatherClient("not-a-real-key").find_city("")


def test_parse_city_makes_a_location_like_the_dropdown_ones():
    data = [{"name": "Bergen", "country": "NO", "lat": 60.39, "lon": 5.32}]
    assert WeatherClient("not-a-real-key")._parse_city(data, "bergen") == {
        "location": "Bergen, NO",
        "label": "Bergen, NO",
        "city": "Bergen",
        "latitude": 60.39,
        "longitude": 5.32,
    }


def test_parse_city_says_when_a_city_is_not_found():
    with pytest.raises(ValueError, match="City 'Atlantis' was not found"):
        WeatherClient("not-a-real-key")._parse_city([], "Atlantis")


def test_parse_city_with_a_missing_field_gives_a_clear_error():
    with pytest.raises(ValueError, match="unexpected format"):
        WeatherClient("not-a-real-key")._parse_city([{"name": "Bergen"}], "Bergen")


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


def test_rain_axis_ticks_are_round_and_start_at_zero():
    assert rain_axis_ticks(0) == [0, 0.5, 1]
    assert rain_axis_ticks(1.2) == [0, 0.5, 1.0, 1.5]
    assert rain_axis_ticks(4.6) == [0, 2, 4, 6]
    assert rain_axis_ticks(15.3) == [0, 5, 10, 15, 20]
    assert rain_axis_ticks(29.1) == [0, 10, 20, 30]
    assert rain_axis_ticks(400) == [0, 100, 200, 300, 400]


def test_split_name():
    assert split_name("Oslo") == ("Oslo", "")
    assert split_name("London, Canada") == ("London", "Canada")
    assert split_name("Springfield, Missouri, US") == ("Springfield", "Missouri, US")


def test_city_card_keeps_the_city_apart_from_its_country():
    reading = make_reading(temperature=12.0)
    reading.timezone_offset = 0
    html = city_card("London, Canada", reading, 13.0, 9.0, "", False, MONDAY)
    assert '<div class="city-name">London</div>' in html
    assert "00:00 · Canada" in html


def test_high_low_text():
    assert high_low_text(15.4, 11.6) == "High 15°  Low 12°"


def test_high_low_text_hides_a_misleading_equal_pair():
    # Mumbai in the evening: nothing left in the forecast, and the reading's own range is one value.
    assert high_low_text(31.2, 30.9) == ""


def test_display_names_add_the_country_only_when_needed():
    locations = [
        {"location": "London, GB", "label": "London, United Kingdom", "city": "London"},
        {"location": "London, CA", "label": "London, Canada", "city": "London"},
        {"location": "Oslo, NO", "label": "Oslo, Norway", "city": "Oslo"},
    ]
    assert display_names(locations) == ["London, United Kingdom", "London, Canada", "Oslo"]


def test_display_names_use_the_region_for_two_cities_in_one_country():
    locations = [
        {"location": "Springfield, Missouri, US", "label": "Springfield, Missouri, United States", "city": "Springfield"},
        {"location": "Springfield, Illinois, US", "label": "Springfield, Illinois, United States", "city": "Springfield"},
    ]
    assert display_names(locations) == ["Springfield, Missouri, US", "Springfield, Illinois, US"]


def test_temperatures_just_below_zero_show_no_minus_sign():
    rows = [{"name": "Oslo", "now": -0.3, "high": 1.0, "low": -0.4, "rain_mm": 0, "wind_kmh": 5, "aqi": 1}]
    html = city_table(rows)
    assert "-0" not in html
    assert "0° to 1°" in html


def test_plan_day_escapes_and_marks_a_part_already_gone():
    parts = [{"part": "Evening", "rating": "Good", "reason": "windy"}]
    html = plan_day("Today", "01d", 20.0, 10.0, "<b>Dry</b>", parts)
    assert "&lt;b&gt;Dry" in html
    assert "High 20°  Low 10°" in html
    assert "Good" in html
    assert "part-past" in html


def test_air_share_bar_leaves_out_empty_bands():
    shares = [{"band": "Good", "days": 45, "share": 50.0}, {"band": "Fair", "days": 45, "share": 50.0}, {"band": "Poor", "days": 0, "share": 0.0}]
    html = air_share_bar(shares)
    assert "Good: 45 days" in html
    assert "Poor" not in html


def test_pollutant_rows_use_names_not_codes():
    html = pollutant_rows([{"pollutant": "o3", "guideline": 100, "days": 90, "days_over": 35}])
    assert "Ozone" in html
    assert "O3" not in html
    assert "Above the guideline on 35 of 90 days" in html


def test_city_table_shows_units_and_words():
    rows = [{"name": "<i>Oslo</i>", "now": 3.4, "high": 8.0, "low": 1.0, "rain_mm": 9.6, "wind_kmh": 12.2, "aqi": 2}]
    html = city_table(rows)
    assert "&lt;i&gt;Oslo" in html
    assert "1° to 8°" in html
    assert "10 mm" in html
    assert "12 km/h" in html
    assert "Fair" in html


def test_city_table_shows_a_dash_without_a_forecast_or_air_data():
    rows = [{"name": "Oslo", "now": 3.0, "high": None, "low": None, "rain_mm": None, "wind_kmh": None, "aqi": None}]
    html = city_table(rows)
    assert html.count("<td>–</td>") == 4
    assert "0 mm" not in html


def test_a_failed_forecast_cannot_win_driest_or_calmest():
    rows = [
        {"name": "Failed", "now": 30.0, "high": None, "low": None, "rain_mm": None, "wind_kmh": None, "aqi": None},
        {"name": "Oslo", "now": 3.0, "high": 8.0, "low": 1.0, "rain_mm": 9.6, "wind_kmh": 12.0, "aqi": 2},
        {"name": "Lima", "now": 2.0, "high": 9.0, "low": 2.0, "rain_mm": 20.0, "wind_kmh": 20.0, "aqi": 3},
    ]
    html = compare_tiles(rows)
    assert "Failed" not in html.split("Warmest")[1].split("</div></div>")[1]
    assert "About 10 mm this week" in html
    assert "Wind around 12 km/h" in html
    assert "Fair air right now" in html
    # It can still be the warmest, because that comes from its current reading.
    assert "30° right now" in html


def test_compare_tiles_when_no_city_has_a_forecast():
    rows = [
        {"name": "Oslo", "now": 3.0, "high": None, "low": None, "rain_mm": None, "wind_kmh": None, "aqi": None},
        {"name": "Lima", "now": 2.0, "high": None, "low": None, "rain_mm": None, "wind_kmh": None, "aqi": None},
    ]
    assert compare_tiles(rows).count("Not available") == 3


def test_sorted_with_a_key_compares_readings_with_lt():
    cold = {"name": "Oslo", "reading": make_reading("Oslo, NO", -2.0, -6.0)}
    warm = {"name": "Madrid", "reading": make_reading("Madrid, ES", 20.0, 19.0)}
    ordered = sorted([cold, warm], key=lambda weather: weather["reading"], reverse=True)
    assert ordered == [warm, cold]


def test_map_legend_has_documented_labels_and_unit():
    html = map_legend("Temperature")
    assert "-30" in html
    assert "°C" in html


def test_radar_note_gives_local_time_and_says_when_there_is_no_radar():
    assert "Radar at 01:00" in radar_note(MONDAY, 3600, True, "Oslo")
    assert "No radar" not in radar_note(MONDAY, 3600, True, "Oslo")
    assert "No radar reaches Oslo" in radar_note(MONDAY, 3600, False, "Oslo")
    assert "No radar" not in radar_note(MONDAY, 3600, None, "Oslo")


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


def test_weather_layers_keep_the_map_readable():
    # A tile at alpha 76 reached 228 at the old boost, which hid coasts and labels.
    image = Image.new("RGBA", (1, 1), (10, 20, 30, 76))
    assert boost_opacity(image, WEATHER_LAYER_BOOST).getpixel((0, 0))[3] == 114


def test_only_a_named_map_layer_goes_below_the_labels():
    grid = tile_grid(0.1, 0.1, 4)
    assert build_map_figure("data:,", grid["bounds"], 0.1, 0.1, "labels").layout.map.layers[0].below == "labels"
    assert build_map_figure("data:,", grid["bounds"], 0.1, 0.1).layout.map.layers[0].below is None


def test_boost_opacity_multiplies_and_keeps_colours():
    image = Image.new("RGBA", (2, 1), (10, 20, 30, 50))
    image.putpixel((1, 0), (10, 20, 30, 0))
    boosted = boost_opacity(image, 3)
    assert boosted.getpixel((0, 0)) == (10, 20, 30, 150)
    # Fully see-through stays see-through, and opacity stops at solid.
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
    uri = image_to_data_uri(Image.new("RGBA", (1, 1)))
    assert uri.startswith("data:image/png;base64,")
