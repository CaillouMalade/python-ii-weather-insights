"""Plain-language sentences computed from the data. No Streamlit and no fixed claims here."""


def format_duration(hours):
    """Say a length of time in the most natural unit."""
    if hours < 1:
        minutes = round(hours * 60)
        return f"{minutes} minute" if minutes == 1 else f"{minutes} minutes"
    if hours < 48:
        whole = round(hours)
        return f"{whole} hour" if whole == 1 else f"{whole} hours"
    return f"{round(hours / 24)} days"


def coverage_text(location, readings, span_hours):
    """How much logged history one city has."""
    word = "reading" if readings == 1 else "readings"
    if readings < 2:
        return f"{location}: {readings} {word}"
    return f"{location}: {readings} {word} over {format_duration(span_hours)}"


def too_little_history_text(location, readings, span_hours):
    return f"Too little history for a trend yet. {coverage_text(location, readings, span_hours)}. Readings build up as the app is used."


def feels_text(delta):
    """Signed wording for feels-like minus actual temperature."""
    if abs(delta) < 0.05:
        return "felt the same as the actual temperature"
    direction = "warmer" if delta > 0 else "colder"
    return f"felt {abs(delta):.1f} °C {direction} than the actual temperature"


def trend_finding(values, metric, unit):
    """The lead sentence of the History trend chart. values are in time order."""
    if metric == "Feels-like difference":
        return f"The latest reading {feels_text(values[-1])}."
    name = metric.lower()
    return f"Logged {name} has ranged from {min(values):.0f} {unit} to {max(values):.0f} {unit}, and the latest reading is {values[-1]:.0f} {unit}."


def plan_finding(metric, peak_label, peak_value):
    """The lead sentence of Plan the week, from the forecast step with the highest value."""
    if metric == "Comfort":
        return f"The most comfortable moment is {peak_label}, scoring {peak_value:.0f} out of 100."
    if metric == "Temperature":
        return f"The warmest moment is {peak_label}, at {peak_value:.0f} °C."
    if metric == "Wind":
        return f"The windiest moment is {peak_label}, at {peak_value:.0f} km/h."
    if peak_value == 0:
        return "No rain is expected in the forecast."
    return f"Rain is most likely {peak_label}, with a {peak_value:.0f} % chance."


def window_reason(feels, rain_chance, wind):
    """Why a window is ranked where it is."""
    return f"Feels like {feels:.0f} °C, {rain_chance:.0f} % chance of rain, wind up to {wind:.0f} km/h"


def who_finding(table_rows):
    """The WHO sentence. table_rows are who_comparison rows as dictionaries."""
    worst = table_rows[0]
    for row in table_rows:
        if row["days_over"] > worst["days_over"]:
            worst = row
    if worst["days_over"] == 0:
        return f"All four pollutants stayed within their WHO guidelines over these {worst['days']} days."
    return f"{worst['pollutant']} went over its WHO guideline most often: on {worst['days_over']} of {worst['days']} days."


def peak_hour_finding(pollutant, hour, level):
    return f"{pollutant} is highest around {hour:02d}:00 local time, at {level:.0f} µg/m³ on average."


def comparison_finding(metric, top, top_value, bottom, bottom_value):
    """The Compare sentence. top has the highest value and bottom the lowest."""
    if metric == "Rain" and top_value == 0:
        return "No rain is expected in any of your cities."
    if top_value == bottom_value:
        return "Your cities look the same on this measure."
    if metric == "Temperature":
        return f"{top} looks warmest, with highs averaging {top_value:.0f} °C, against {bottom_value:.0f} °C in {bottom}, the coolest."
    if metric == "Rain":
        return f"{top} expects the most rain, {top_value:.1f} mm, against {bottom_value:.1f} mm in {bottom}, the driest."
    if metric == "Wind":
        return f"{top} gets the strongest wind, up to {top_value:.0f} km/h, against {bottom_value:.0f} km/h in {bottom}, the calmest."
    return f"{bottom} looks cleanest, with an average worst AQI of {bottom_value:.1f}, against {top_value:.1f} in {top}."
