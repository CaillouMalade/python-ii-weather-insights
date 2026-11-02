"""Plain-language wording computed from the data. No Streamlit and no fixed claims here."""

from datetime import datetime

import pandas as pd

# Name, what it is in a few words, and the verb forms that go with the name.
POLLUTANTS = {
    "pm2_5": {"name": "Fine particles (PM2.5)", "about": "Tiny specks from traffic and burning that reach deep into the lungs", "is": "are", "tends": "tend"},
    "pm10": {"name": "Coarse particles (PM10)", "about": "Dust, pollen and smoke that you can breathe in", "is": "are", "tends": "tend"},
    "no2": {"name": "Nitrogen dioxide", "about": "A gas mostly from traffic and burning fuel", "is": "is", "tends": "tends"},
    "o3": {"name": "Ozone", "about": "A gas formed when sunlight reacts with pollution", "is": "is", "tends": "tends"},
}

# km/h and °C limits behind the words we use.
WINDY_KMH = 28
VERY_WINDY_KMH = 40
RAIN_LIKELY = 0.5
RAIN_POSSIBLE = 0.3


def rate_comfort(score):
    """Turn a 0-100 comfort score into a word."""
    if score >= 80:
        return "Great"
    if score >= 60:
        return "Good"
    if score >= 40:
        return "OK"
    return "Poor"


def capped_comfort(score, pop, wind_kmh):
    """Limit a score so the word cannot contradict the weather. Rain likely is never "Great" or "Good"."""
    if pop >= RAIN_LIKELY or wind_kmh >= VERY_WINDY_KMH:
        return min(score, 59)
    if pop >= RAIN_POSSIBLE or wind_kmh >= WINDY_KMH:
        return min(score, 79)
    return score


def part_reason(pop, snow_mm, wind_kmh, feels_like):
    """The most important reason behind a rating, in a few words. Weather that spoils plans comes first."""
    if snow_mm > 0 and pop >= RAIN_POSSIBLE:
        return "snow likely"
    if pop >= RAIN_LIKELY:
        return "rain likely"
    if pop >= RAIN_POSSIBLE:
        return "chance of rain"
    if wind_kmh >= VERY_WINDY_KMH:
        return "very windy"
    if wind_kmh >= WINDY_KMH:
        return "windy"
    if feels_like <= 0:
        return "freezing"
    if feels_like <= 5:
        return "cold"
    if feels_like <= 10:
        return "chilly"
    if feels_like <= 15:
        return "cool"
    if feels_like >= 35:
        return "very hot"
    if feels_like >= 30:
        return "hot"
    if feels_like >= 26:
        return "warm"
    return "pleasant"


def temperature_word(high):
    """Describe a day by its highest temperature."""
    if high <= 0:
        return "freezing"
    if high <= 8:
        return "cold"
    if high <= 15:
        return "cool"
    if high <= 23:
        return "mild"
    if high <= 29:
        return "warm"
    return "hot"


def join_words(words):
    """a; a and b; a, b and c."""
    if len(words) < 2:
        return "".join(words)
    return ", ".join(words[:-1]) + " and " + words[-1]


def capitalize_first(text):
    return text[:1].upper() + text[1:]


def day_summary(parts, high):
    """One sentence for a day. parts are its day_parts rows as dictionaries, in time order."""
    temperature = temperature_word(high)
    likely = [row["part"].lower() for row in parts if row["pop"] >= RAIN_LIKELY]
    possible = [row["part"].lower() for row in parts if row["pop"] >= RAIN_POSSIBLE]
    word = "rain"
    if high <= 0:
        word = "snow"
    for row in parts:
        if row["snow"] > 0:
            word = "snow"
    windy = [row["part"] for row in parts if row["wind"] >= WINDY_KMH]

    # Rain and wind in the same single part read better said together.
    if len(likely) == 1 and windy == [likely[0].capitalize()]:
        return f"{capitalize_first(temperature)} with {word} and wind in the {likely[0]}"

    if len(parts) > 1 and len(likely) == len(parts):
        text = f"{capitalize_first(temperature)} with {word} likely all day"
    elif len(likely) > 0:
        text = f"{capitalize_first(temperature)} with {word} likely in the {join_words(likely)}"
    elif len(possible) > 0:
        text = f"{capitalize_first(temperature)} with a chance of {word} in the {join_words(possible)}"
    else:
        text = f"Dry and {temperature}"

    if len(parts) > 1 and len(windy) == len(parts):
        text = text + ", windy throughout"
    elif len(windy) > 0 and windy[0] == "Evening":
        text = text + ", windy by evening"
    elif len(windy) > 0:
        text = text + f", windy in the {windy[0].lower()}"
    return text


def part_name(row, today):
    """Say when a day_parts row is: this afternoon, or Friday afternoon."""
    if row["local_date"] == today:
        return f"this {row['part'].lower()}"
    weekday = datetime.strptime(row["local_date"], "%Y-%m-%d").strftime("%A")
    return f"{weekday} {row['part'].lower()}"


def best_and_worst_parts(parts):
    """The best and worst day_parts rows. On a tie, the earliest one wins."""
    best = parts[0]
    worst = parts[0]
    for row in parts:
        if row["comfort"] > best["comfort"]:
            best = row
        if row["comfort"] < worst["comfort"]:
            worst = row
    return best, worst


def week_headline(parts, today):
    """The one sentence above Plan the week."""
    if len(parts) == 0:
        return "There is not enough forecast to plan with yet."
    best, worst = best_and_worst_parts(parts)
    best_name = part_name(best, today)
    if best["rating"] == "Poor":
        return f"A tough week to be outside: {best_name} is the least bad."
    if worst["rating"] in ["Great", "Good"]:
        return f"{capitalize_first(best_name)} is your best bet, and the whole week looks good."
    return f"{capitalize_first(best_name)} is your best bet; avoid {part_name(worst, today)}."


def wind_text(wind_kmh, gust_kmh):
    """Wind speed, and gusts when the forecast gives them. A forecast step can lack a gust."""
    if pd.isna(gust_kmh):
        return f"{wind_kmh:.0f} km/h"
    return f"{wind_kmh:.0f} km/h, gusts up to {gust_kmh:.0f} km/h"


def rain_amount_text(millimetres):
    """Say a rain total without false precision."""
    if millimetres == 0:
        return "No rain"
    if millimetres < 1:
        return "Less than 1 mm"
    return f"About {millimetres:.0f} mm"


def guideline_days_text(days_over, days):
    """For the top card: how often air went over any health guideline."""
    if days == 0:
        return ""
    if days_over == 0:
        return "Within health guidelines over the last 3 months"
    return f"Above health guidelines on {plural(days_over, 'day')} in the last 3 months"


def pollutant_text(days_over, days):
    """How often one pollutant went over its guideline."""
    if days == 0:
        return "No data"
    if days_over == 0:
        return f"Within the guideline on all {days} days"
    if days_over == days:
        return f"Above the guideline on all {days} days"
    return f"Above the guideline on {days_over} of {days} days"


def air_headline(city, usual_band, worst_pollutant, worst_days_over):
    """The Air sentence. worst_pollutant is the key of the pollutant most often over its guideline."""
    start = f"Air in {city} is usually {usual_band.lower()}"
    if worst_days_over == 0:
        return f"{start}, and stays within health guidelines."
    pollutant = POLLUTANTS[worst_pollutant]
    return f"{start}. {pollutant['name']} {pollutant['is']} the main concern."


def time_of_day_text(pollutant_key, low_hour, low_level, high_hour, high_level):
    """Best and worst time of day for one pollutant."""
    pollutant = POLLUTANTS[pollutant_key]
    if high_level - low_level < 1:
        return f"{pollutant['name']} {pollutant['tends']} to stay about the same all day."
    return f"Best and worst time of day: {pollutant['name']} {pollutant['tends']} to be lowest around {low_hour:02d}:00 and highest around {high_hour:02d}:00."


def lowest_names(rows, key):
    """The names of the rows with the lowest value, skipping rows with no value."""
    known = [row for row in rows if row[key] is not None]
    if len(known) == 0:
        return []
    lowest = min([row[key] for row in known])
    return [row["name"] for row in known if row[key] == lowest]


def winner_names(names, total):
    """Name the winners, or count them when a long list of names would be hard to read."""
    if len(names) == total and total > 1:
        return "All your cities"
    if len(names) > 2:
        return f"{len(names)} cities tie"
    return join_words(names)


def sort_city_rows(rows, order):
    """Sort Compare's rows, lowest first. Temperature keeps the order given. A missing value goes last."""
    keys = {"Rain": "rain_mm", "Wind": "wind_kmh", "Air quality": "aqi"}
    if order not in keys:
        return rows
    key = keys[order]
    return sorted(rows, key=lambda row: float("inf") if row[key] is None else row[key])


def plural(count, word, many=None):
    """Say a count with the right word form: 1 city, 2 cities."""
    if count == 1:
        return f"{count} {word}"
    return f"{count} {many or word + 's'}"


def format_duration(hours):
    """Say a length of time in the most natural unit."""
    if hours < 1:
        return plural(round(hours * 60), "minute")
    if hours < 48:
        return plural(round(hours), "hour")
    return f"{round(hours / 24)} days"


def coverage_part(name, readings, span_hours):
    if readings < 2:
        return f"{plural(readings, 'reading')} for {name}"
    return f"{plural(readings, 'reading')} for {name} over {format_duration(span_hours)}"


def coverage_sentence(rows, selected):
    """How much history the log holds: the selected city in full, the others added up."""
    chosen = [row for row in rows if row["name"] == selected]
    others = [row for row in rows if row["name"] != selected]
    total = plural(sum([row["readings"] for row in others]), "reading")
    cities = plural(len(others), "city", "cities")
    if selected is None:
        return f"Your log has {total}."
    if len(chosen) == 0:
        return f"Your log has {total} across {cities}, but none yet for {selected}."
    text = f"Your log has {coverage_part(chosen[0]['name'], chosen[0]['readings'], chosen[0]['span_hours'])}"
    if len(others) > 0:
        other_cities = plural(len(others), "other city", "other cities")
        text = text + f", plus {total} for {other_cities}"
    return text + "."


def too_little_history_text(name, readings, span_hours):
    return f"Not enough for a trend yet: {coverage_part(name, readings, span_hours)}. A line appears at 3 readings over at least an hour."


def trend_finding(values, metric, unit):
    """The sentence above the History chart. values are in time order."""
    names = {"Temperature": "Temperature", "Feels like": "The feels-like temperature", "Humidity": "Humidity", "Wind": "Wind"}
    low = round(min(values))
    high = round(max(values))
    if low == high:
        return f"{names[metric]} has stayed at about {high} {unit}."
    return f"{names[metric]} has ranged from {low} {unit} to {high} {unit}, and the latest reading is {round(values[-1])} {unit}."


def daily_range_sentence(day_labels, ranges):
    """How much the temperature moves within a day. One or two days say too little."""
    if len(ranges) < 3:
        return ""
    biggest = max(ranges)
    biggest_day = day_labels[ranges.index(biggest)]
    typical = sum(ranges) / len(ranges)
    return f"The temperature usually moves about {typical:.0f} °C within a day; the biggest swing was {biggest:.0f} °C on {biggest_day}."
