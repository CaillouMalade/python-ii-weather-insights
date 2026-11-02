# The sentences on the Analytics tab, with known answers.

from weather_app.findings import (
    comparison_finding,
    coverage_text,
    feels_text,
    format_duration,
    peak_hour_finding,
    plan_finding,
    too_little_history_text,
    trend_finding,
    who_finding,
    window_reason,
)


def test_format_duration_picks_a_natural_unit():
    assert format_duration(0.3) == "18 minutes"
    assert format_duration(1) == "1 hour"
    assert format_duration(26) == "26 hours"
    assert format_duration(72) == "3 days"


def test_coverage_text():
    assert coverage_text("Madrid, ES", 3, 0.3) == "Madrid, ES: 3 readings over 18 minutes"
    assert coverage_text("Oslo, NO", 1, 0) == "Oslo, NO: 1 reading"


def test_too_little_history_text():
    assert too_little_history_text("Oslo, NO", 1, 0) == "Too little history for a trend yet. Oslo, NO: 1 reading. Readings build up as the app is used."


def test_feels_text_uses_signed_wording():
    assert feels_text(-0.2) == "felt 0.2 °C colder than the actual temperature"
    assert feels_text(1.5) == "felt 1.5 °C warmer than the actual temperature"
    assert feels_text(0.0) == "felt the same as the actual temperature"


def test_trend_finding():
    assert trend_finding([10.4, 18.0, 15.0], "Temperature", "°C") == "Logged temperature has ranged from 10 °C to 18 °C, and the latest reading is 15 °C."
    assert trend_finding([0.5, -0.2], "Feels-like difference", "°C") == "The latest reading felt 0.2 °C colder than the actual temperature."


def test_plan_finding_for_each_measure():
    assert plan_finding("Comfort", "Tuesday at 12:00", 84.0) == "The most comfortable moment is Tuesday at 12:00, scoring 84 out of 100."
    assert plan_finding("Temperature", "Tuesday at 15:00", 21.6) == "The warmest moment is Tuesday at 15:00, at 22 °C."
    assert plan_finding("Wind", "Friday at 03:00", 40.0) == "The windiest moment is Friday at 03:00, at 40 km/h."
    assert plan_finding("Chance of rain", "Friday at 03:00", 60.0) == "Rain is most likely Friday at 03:00, with a 60 % chance."


def test_plan_finding_makes_no_rain_claim_when_dry():
    assert plan_finding("Chance of rain", "Monday at 00:00", 0.0) == "No rain is expected in the forecast."


def test_window_reason():
    assert window_reason(20.6, 10.0, 14.2) == "Feels like 21 °C, 10 % chance of rain, wind up to 14 km/h"


def test_who_finding_names_the_worst_pollutant():
    rows = [{"pollutant": "PM2.5", "days_over": 3, "days": 90}, {"pollutant": "O3", "days_over": 10, "days": 90}]
    assert who_finding(rows) == "O3 went over its WHO guideline most often: on 10 of 90 days."


def test_who_finding_claims_nothing_when_all_are_within():
    rows = [{"pollutant": "PM2.5", "days_over": 0, "days": 90}, {"pollutant": "O3", "days_over": 0, "days": 90}]
    assert who_finding(rows) == "All four pollutants stayed within their WHO guidelines over these 90 days."


def test_peak_hour_finding():
    assert peak_hour_finding("PM2.5", 8, 13.6) == "PM2.5 is highest around 08:00 local time, at 14 µg/m³ on average."


def test_comparison_finding_names_each_city_once():
    text = comparison_finding("Temperature", "Madrid, ES", 20.0, "Oslo, NO", 3.0)
    assert text == "Madrid, ES looks warmest, with highs averaging 20 °C, against 3 °C in Oslo, NO, the coolest."
    assert text.count("Madrid, ES") == 1


def test_comparison_finding_rain_wind_and_air():
    assert comparison_finding("Rain", "A", 9.6, "B", 1.0) == "A expects the most rain, 9.6 mm, against 1.0 mm in B, the driest."
    assert comparison_finding("Wind", "A", 40.0, "B", 20.0) == "A gets the strongest wind, up to 40 km/h, against 20 km/h in B, the calmest."
    # A high AQI is bad, so the city at the bottom of the ranking is the cleanest.
    assert comparison_finding("Air quality", "A", 3.5, "B", 1.5) == "B looks cleanest, with an average worst AQI of 1.5, against 3.5 in A."


def test_comparison_finding_handles_no_rain_and_ties():
    assert comparison_finding("Rain", "A", 0.0, "B", 0.0) == "No rain is expected in any of your cities."
    assert comparison_finding("Wind", "A", 20.0, "B", 20.0) == "Your cities look the same on this measure."
