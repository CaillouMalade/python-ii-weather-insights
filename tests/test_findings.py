# The words on the Analytics tab, with known answers and the awkward edge cases.

from weather_app.findings import (
    air_headline,
    best_and_worst_parts,
    capped_comfort,
    coverage_sentence,
    daily_range_sentence,
    day_summary,
    format_duration,
    guideline_days_text,
    join_words,
    lowest_names,
    part_name,
    part_reason,
    pollutant_text,
    rain_amount_text,
    rate_comfort,
    sort_city_rows,
    temperature_word,
    time_of_day_text,
    too_little_history_text,
    trend_finding,
    week_headline,
    winner_names,
)


def part(name, comfort=90.0, pop=0.0, snow=0.0, wind=10.0, date="2026-01-09", rating="Great"):
    # 2026-01-09 is a Friday.
    return {"local_date": date, "part": name, "comfort": comfort, "pop": pop, "snow": snow, "wind": wind, "rating": rating}


def test_rate_comfort_boundaries():
    assert rate_comfort(80) == "Great"
    assert rate_comfort(79.9) == "Good"
    assert rate_comfort(60) == "Good"
    assert rate_comfort(40) == "OK"
    assert rate_comfort(39) == "Poor"


def test_capped_comfort_stops_words_contradicting_the_weather():
    assert capped_comfort(95, 0.0, 10) == 95
    assert capped_comfort(95, 0.6, 10) == 59
    assert capped_comfort(95, 0.0, 45) == 59
    assert capped_comfort(95, 0.4, 10) == 79
    assert capped_comfort(95, 0.0, 30) == 79
    assert capped_comfort(30, 0.6, 10) == 30


def test_part_reason_puts_the_plan_spoilers_first():
    assert part_reason(0.6, 0, 50, 20) == "rain likely"
    assert part_reason(0.4, 0, 50, 20) == "chance of rain"
    assert part_reason(0.4, 1.0, 10, -2) == "snow likely"
    assert part_reason(0.0, 0, 45, 20) == "very windy"
    assert part_reason(0.0, 0, 30, 20) == "windy"
    assert part_reason(0.0, 0, 10, -1) == "freezing"
    assert part_reason(0.0, 0, 10, 4) == "cold"
    assert part_reason(0.0, 0, 10, 8) == "chilly"
    assert part_reason(0.0, 0, 10, 14) == "cool"
    assert part_reason(0.0, 0, 10, 20) == "pleasant"
    assert part_reason(0.0, 0, 10, 28) == "warm"
    assert part_reason(0.0, 0, 10, 31) == "hot"
    assert part_reason(0.0, 0, 10, 36) == "very hot"


def test_temperature_word():
    assert temperature_word(-1) == "freezing"
    assert temperature_word(20) == "mild"
    assert temperature_word(35) == "hot"


def test_join_words():
    assert join_words(["a"]) == "a"
    assert join_words(["a", "b"]) == "a and b"
    assert join_words(["a", "b", "c"]) == "a, b and c"


def test_day_summary_dry_and_mild_windy_by_evening():
    parts = [part("Morning"), part("Afternoon"), part("Evening", wind=30)]
    assert day_summary(parts, 20) == "Dry and mild, windy by evening"


def test_day_summary_rain_in_one_part():
    parts = [part("Morning", pop=0.8), part("Afternoon"), part("Evening")]
    assert day_summary(parts, 12) == "Cool with rain likely in the morning"


def test_day_summary_rain_all_day_and_windy_throughout():
    parts = [part("Morning", pop=0.6, wind=30), part("Afternoon", pop=0.9, wind=30)]
    assert day_summary(parts, 25) == "Warm with rain likely all day, windy throughout"


def test_day_summary_chance_of_snow():
    parts = [part("Morning", pop=0.4, snow=0.5), part("Afternoon")]
    assert day_summary(parts, -2) == "Freezing with a chance of snow in the morning"


def test_day_summary_says_rain_and_wind_together_when_they_share_a_part():
    parts = [part("Morning", pop=0.8, wind=30), part("Afternoon")]
    assert day_summary(parts, 12) == "Cool with rain and wind in the morning"


def test_day_summary_calls_it_snow_below_freezing():
    assert day_summary([part("Morning", pop=0.4), part("Afternoon")], -1) == "Freezing with a chance of snow in the morning"


def test_day_summary_one_part_is_not_all_day():
    assert day_summary([part("Evening", pop=0.9)], 20) == "Mild with rain likely in the evening"


def test_part_name_says_this_for_today():
    assert part_name(part("Afternoon"), "2026-01-09") == "this afternoon"
    assert part_name(part("Afternoon"), "2026-01-05") == "Friday afternoon"


def test_best_and_worst_parts_prefer_the_earliest_on_a_tie():
    first = part("Morning", comfort=70)
    second = part("Afternoon", comfort=70)
    assert best_and_worst_parts([first, second]) == (first, first)


def test_week_headline_names_best_and_worst():
    parts = [part("Morning", comfort=30, rating="Poor", date="2026-01-08"), part("Afternoon", comfort=90, rating="Great")]
    assert week_headline(parts, "2026-01-05") == "Friday afternoon is your best bet; avoid Thursday morning."


def test_week_headline_uses_this_for_today():
    parts = [part("Evening", comfort=90, rating="Great", date="2026-01-05"), part("Morning", comfort=30, rating="Poor")]
    assert week_headline(parts, "2026-01-05") == "This evening is your best bet; avoid Friday morning."


def test_week_headline_when_everything_is_good():
    parts = [part("Morning", comfort=70, rating="Good"), part("Afternoon", comfort=95, rating="Great")]
    assert week_headline(parts, "2026-01-05") == "Friday afternoon is your best bet, and the whole week looks good."


def test_week_headline_when_everything_is_poor():
    parts = [part("Morning", comfort=10, rating="Poor"), part("Afternoon", comfort=30, rating="Poor")]
    assert week_headline(parts, "2026-01-05") == "A tough week to be outside: Friday afternoon is the least bad."


def test_week_headline_without_a_forecast():
    assert week_headline([], "2026-01-05") == "There is not enough forecast to plan with yet."


def test_rain_amount_text():
    assert rain_amount_text(0) == "No rain"
    assert rain_amount_text(0.4) == "Less than 1 mm"
    assert rain_amount_text(9.6) == "About 10 mm"


def test_guideline_days_text():
    assert guideline_days_text(37, 90) == "Above health guidelines on 37 of the last 90 days"
    assert guideline_days_text(0, 90) == "Within health guidelines on all of the last 90 days"
    assert guideline_days_text(0, 0) == ""


def test_pollutant_text():
    assert pollutant_text(35, 90) == "Above the guideline on 35 of 90 days"
    assert pollutant_text(0, 90) == "Within the guideline on all 90 days"
    assert pollutant_text(90, 90) == "Above the guideline on all 90 days"
    assert pollutant_text(0, 0) == "No data"


def test_air_headline_says_names_not_codes():
    assert air_headline("Tokyo", "Fair", "o3", 35) == "Air in Tokyo is usually fair. Ozone is the main concern."
    assert air_headline("Tokyo", "Moderate", "pm2_5", 3) == "Air in Tokyo is usually moderate. Fine particles (PM2.5) are the main concern."


def test_air_headline_with_nothing_over_a_guideline():
    assert air_headline("Oslo", "Good", "o3", 0) == "Air in Oslo is usually good, and stays within health guidelines."


def test_time_of_day_text():
    assert time_of_day_text("o3", 4, 40.0, 15, 90.0) == "Best and worst time of day: Ozone tends to be lowest around 04:00 and highest around 15:00."
    assert time_of_day_text("pm10", 4, 30.0, 15, 30.0) == "Coarse particles (PM10) tend to stay about the same all day."


def test_lowest_names_includes_ties_and_skips_missing_values():
    rows = [{"name": "A", "aqi": 2}, {"name": "B", "aqi": 1}, {"name": "C", "aqi": 1}, {"name": "D", "aqi": None}]
    assert lowest_names(rows, "aqi") == ["B", "C"]
    assert lowest_names([{"name": "A", "aqi": None}], "aqi") == []


def test_winner_names():
    assert winner_names(["Oslo"], 3) == "Oslo"
    assert winner_names(["Oslo", "Lima"], 3) == "Oslo and Lima"
    assert winner_names(["Oslo", "Lima"], 2) == "All your cities"
    assert winner_names(["A", "B", "C"], 5) == "3 cities tie"


def test_sort_city_rows():
    rows = [
        {"name": "Warm", "rain_mm": 9.0, "wind_kmh": 5.0, "aqi": None},
        {"name": "Dry", "rain_mm": 0.0, "wind_kmh": 20.0, "aqi": 3},
        {"name": "Clean", "rain_mm": 4.0, "wind_kmh": 10.0, "aqi": 1},
    ]
    names = lambda ordered: [row["name"] for row in ordered]
    assert names(sort_city_rows(rows, "Warmest")) == ["Warm", "Dry", "Clean"]
    assert names(sort_city_rows(rows, "Driest")) == ["Dry", "Clean", "Warm"]
    assert names(sort_city_rows(rows, "Calmest")) == ["Warm", "Clean", "Dry"]
    assert names(sort_city_rows(rows, "Cleanest air")) == ["Clean", "Dry", "Warm"]


def test_format_duration_picks_a_natural_unit():
    assert format_duration(0.3) == "18 minutes"
    assert format_duration(1) == "1 hour"
    assert format_duration(26) == "26 hours"
    assert format_duration(72) == "3 days"


def test_coverage_sentence():
    rows = [{"name": "Madrid", "readings": 7, "span_hours": 2.0}, {"name": "Oslo", "readings": 1, "span_hours": 0.0}]
    assert coverage_sentence(rows) == "Your log has 7 readings for Madrid over 2 hours and 1 reading for Oslo."
    assert coverage_sentence(list(reversed(rows))) == coverage_sentence(rows)


def test_too_little_history_text():
    assert too_little_history_text("Oslo", 2, 0.25) == "Not enough for a trend yet: 2 readings for Oslo over 15 minutes. A line appears at 3 readings over at least an hour."


def test_trend_finding():
    assert trend_finding([10.4, 18.0, 15.0], "Temperature", "°C") == "Temperature has ranged from 10 °C to 18 °C, and the latest reading is 15 °C."
    assert trend_finding([9.0, 11.0], "Feels like", "°C") == "The feels-like temperature has ranged from 9 °C to 11 °C, and the latest reading is 11 °C."
    assert trend_finding([50, 50], "Humidity", "%") == "Humidity has stayed at about 50 %."


def test_daily_range_sentence():
    assert daily_range_sentence(["Mon 3", "Tue 4"], [4.0, 8.0]) == "The temperature usually moves about 6 °C within a day; the biggest swing was 8 °C on Tue 4."
    assert daily_range_sentence(["Mon 3"], [4.0]) == ""
