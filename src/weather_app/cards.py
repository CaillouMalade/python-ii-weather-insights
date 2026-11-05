"""Simple HTML for the cards. Text from the API or data files always goes through escape()."""

from html import escape

from .analytics import METRES_PER_SECOND_TO_KMH
from .display import (
    aqi_label,
    aqi_position,
    background_for,
    compass_direction,
    format_local_time,
    high_low_text,
    is_night,
    range_bar,
    split_name,
    uv_label,
    weather_emoji,
)
from .findings import POLLUTANTS, pollutant_text
from .maps import LEGENDS

# CSS variables from theme.py, so these colours follow the light or dark theme.
RATING_COLORS = {"Great": "var(--great)", "Good": "var(--good)", "OK": "var(--ok)", "Poor": "var(--poor)"}
BAND_COLORS = {"Good": "var(--great)", "Fair": "var(--good)", "Moderate": "var(--ok)", "Poor": "var(--poor)", "Very poor": "var(--very-poor)"}


def city_card(name, reading, high, low, note, selected, now):
    """A sidebar entry: name, local time, temperature, conditions and high/low when available."""
    outline = " selected" if selected else ""
    city, place = split_name(name)
    if reading is None:
        place_line = f'<div class="city-small">{escape(place)}</div>' if place else ""
        return (
            f'<div class="city{outline}" style="background:var(--empty-card)">'
            f'<div class="city-name">{escape(city)}</div>{place_line}'
            f'<div class="city-small city-note">{escape(note)}</div></div>'
        )

    background = background_for(reading.weather_id, is_night(now, reading.sunrise, reading.sunset))
    high_low = ""
    if high is not None:
        high_low = high_low_text(high, low)
    time_text = format_local_time(now, reading.timezone_offset or 0)
    if place:
        time_text = f"{time_text} · {escape(place)}"
    return (
        f'<div class="city{outline}" style="background:{background}">'
        f'<div class="city-row"><div class="city-main"><div class="city-name">{escape(city)}</div>'
        f'<div class="city-small">{time_text}</div></div>'
        f'<div class="city-temp">{round(reading.temperature)}°</div></div>'
        f'<div class="city-row"><div class="city-small">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="city-small high-low">{high_low}</div></div></div>'
    )


def feels_small(delta):
    """Compare feels-like with the actual temperature, using the reading's feels_like_delta."""
    if abs(delta) < 1:
        return "About the actual temperature"
    direction = "warmer" if delta > 0 else "colder"
    return f"{round(abs(delta))}° {direction} than actual"


def stat(label, value, small=""):
    """One key figure in the header."""
    return f'<div class="stat"><div class="card-title">{label}</div><div class="stat-value">{value}</div><div class="small">{small}</div></div>'


def header(city, reading, high, low, rain_chance, now):
    """The top card: city, time and temperature on the left, key figures beside or below."""
    time_text = format_local_time(now, reading.timezone_offset or 0, "%A %H:%M")

    wind_small = ""
    if reading.wind_deg is not None:
        wind_small = f"From the {compass_direction(reading.wind_deg)}"
    if reading.wind_gust is not None:
        wind_small = f"{wind_small}, gusts {reading.wind_gust * METRES_PER_SECOND_TO_KMH:.0f} km/h".strip(", ")

    rain_value = "No data" if rain_chance is None else f"{rain_chance * 100:.0f} %"
    stats = (
        stat("Feels like", f"{round(reading.feels_like)}°", feels_small(reading.feels_like_delta))
        + stat("Wind", f"{reading.wind_speed * METRES_PER_SECOND_TO_KMH:.0f} km/h", wind_small)
        + stat("Humidity", f"{reading.humidity} %")
        + stat("Chance of rain", rain_value, "Next few hours")
    )
    return (
        '<div class="card header">'
        '<div class="header-main">'
        f'<div class="header-city">{escape(city)}</div>'
        f'<div class="small">{time_text} local time</div>'
        f'<div class="header-temp">{round(reading.temperature)}°</div>'
        f'<div class="header-line">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="header-line high-low">{high_low_text(high, low)}</div>'
        "</div>"
        f'<div class="header-stats">{stats}</div>'
        "</div>"
    )


def format_precipitation(millimetres):
    """0 mm stays whole, and anything else keeps one decimal, such as 0.4 mm."""
    if millimetres == 0:
        return "0 mm"
    return f"{millimetres:.1f} mm"


def strip_item(top, icon, value, small=""):
    """One column of the Next hours strip. Every argument is text we formatted ourselves."""
    return (
        '<div class="strip-item">'
        f"<b>{top}</b>"
        f'<div class="strip-icon">{icon}</div>'
        f'<div class="strip-value">{value}</div>'
        f'<div class="strip-small">{small}</div></div>'
    )


def next_hours_strip(steps, timezone_offset, measure, reading):
    """The current reading and the next steps for one measure: Temperature, Precipitation or Wind."""
    now_value = f"{round(reading.temperature)}°"
    if measure == "Precipitation":
        now_value = format_precipitation((reading.rain_1h or 0) + (reading.snow_1h or 0))
    elif measure == "Wind":
        now_value = f"{reading.wind_speed * METRES_PER_SECOND_TO_KMH:.0f} km/h"

    items = [strip_item("Now", weather_emoji(reading.icon), now_value)]
    for _, row in steps.iterrows():
        small = ""
        value = f'{round(row["temperature"])}°'
        if measure == "Precipitation":
            value = format_precipitation(row["rain_3h"] + row["snow_3h"])
            small = f'{row["pop"] * 100:.0f} % chance'
        elif measure == "Wind":
            value = f'{row["wind_speed"] * METRES_PER_SECOND_TO_KMH:.0f} km/h'
        items.append(strip_item(format_local_time(int(row["dt"]), timezone_offset), weather_emoji(row["icon"]), value, small))
    return '<div class="strip">' + "".join(items) + "</div>"


def daily_card(days, today, day_names, current_temperature):
    """The daily forecast. day_names holds a short name per row. Today's bar gets a dot at the current temperature."""
    overall_low = min(days["low"].to_list())
    overall_high = max(days["high"].to_list())
    rows = []
    for name, (_, row) in zip(day_names, days.iterrows()):
        left, width = range_bar(row["low"], row["high"], overall_low, overall_high)
        pop_text = f'<div class="day-pop">{row["pop"] * 100:.0f} %</div>' if row["pop"] > 0 else ""
        dot = ""
        if row["local_date"] == today:
            dot_left, _ = range_bar(current_temperature, current_temperature, overall_low, overall_high)
            dot = f'<div class="bar-dot" style="left:{max(0, min(100, dot_left))}%"></div>'
        rows.append(
            '<div class="day">'
            f"<b>{name}</b>"
            f'<div class="day-icon">{weather_emoji(row["icon"])}{pop_text}</div>'
            f'<div class="day-low">{round(row["low"])}°</div>'
            f'<div class="bar"><div class="bar-fill" style="left:{left}%;width:{width}%"></div>{dot}</div>'
            f'<b>{round(row["high"])}°</b></div>'
        )
    return f'<div class="card-title">{len(rows)}-day forecast</div><div class="days">' + "".join(rows) + "</div>"


def tile(title, value, small="", extra=""):
    """A same-size tile. value may be longer text: the tile keeps its size and wraps it."""
    return f'<div class="card"><div class="card-title">{title}</div><div class="tile-value">{value}</div>{extra}<div class="small">{small}</div></div>'


def air_tile(air_row):
    aqi = air_row.get("aqi")
    if aqi is None:
        return ""
    scale = f'<div class="scale"><div class="scale-dot" style="left:{aqi_position(aqi):.0f}%"></div></div>'
    small = ""
    if air_row.get("pm2_5") is not None:
        small = f"PM2.5 {air_row['pm2_5']:.0f} µg/m³"
    return tile("Air quality", aqi_label(aqi), small, scale)


def detail_tiles(reading, air_row, uv_value, dew_point, tendency):
    """The Details grid. Only what the header does not already show. Missing data hides its tile."""
    offset = reading.timezone_offset or 0
    tiles = []
    if air_row is not None:
        tiles.append(air_tile(air_row))
    if uv_value is not None:
        tiles.append(tile("UV index today", f"{uv_value:.0f}", uv_label(uv_value)))
    if reading.sunrise is not None:
        tiles.append(tile("Sunrise", format_local_time(reading.sunrise, offset)))
    if reading.sunset is not None:
        tiles.append(tile("Sunset", format_local_time(reading.sunset, offset)))
    if dew_point is not None:
        tiles.append(tile("Dew point", f"{round(dew_point)}°"))
    if reading.visibility is not None:
        tiles.append(tile("Visibility", f"{reading.visibility / 1000:.0f} km"))
    if reading.pressure is not None:
        tiles.append(tile("Pressure", f"{reading.pressure} hPa", tendency))
    if reading.clouds is not None:
        tiles.append(tile("Cloud cover", f"{reading.clouds} %"))
    return '<div class="grid-4">' + "".join(tiles) + "</div>"


def map_legend(layer):
    """A small colour scale for a weather layer, from OpenWeatherMap's published scale."""
    unit, stops = LEGENDS[layer]
    colors = ", ".join([color for _, color in stops])
    labels = "".join([f"<span>{label}</span>" for label, _ in stops])
    return f'<div class="map-note"><div class="legend-bar" style="background:linear-gradient(90deg, {colors})"></div><div class="legend-labels">{labels}<span>{unit}</span></div></div>'


def radar_note(radar_time, timezone_offset, covered, name):
    """When the radar image was made, and an honest note if radar does not reach this city."""
    time_text = ""
    if radar_time is not None:
        time_text = f"Radar at {format_local_time(radar_time, timezone_offset)}"
    coverage_text = ""
    if covered is False:
        coverage_text = f'<div class="small">No radar reaches {escape(name)}, so rain there will not show. Shaded areas have no radar.</div>'
    return f'<div class="map-note"><b>{time_text}</b>{coverage_text}</div>'


def plan_day(name, icon, high, low, summary, parts):
    """One day of Plan the week: name, icon, high and low, a sentence, and each part of the day rated."""
    by_part = {}
    for part in parts:
        by_part[part["part"]] = part

    chips = ""
    for part_name in ["Morning", "Afternoon", "Evening"]:
        if part_name in by_part:
            part = by_part[part_name]
            chips = chips + (
                f'<div class="part" style="border-top-color:{RATING_COLORS[part["rating"]]}"><div class="part-name">{part_name}</div>'
                f'<div class="part-rating" style="color:{RATING_COLORS[part["rating"]]}">{part["rating"]}</div><div class="part-reason">{escape(part["reason"])}</div></div>'
            )
        else:
            chips = chips + f'<div class="part part-past"><div class="part-name">{part_name}</div></div>'

    return (
        '<div class="card">'
        f'<div class="plan-head"><b>{escape(name)}</b><span class="plan-icon">{weather_emoji(icon)}</span><span class="high-low">{high_low_text(high, low)}</span></div>'
        f'<div class="plan-summary">{escape(summary)}</div>'
        f'<div class="parts">{chips}</div></div>'
    )


def air_share_bar(shares):
    """One stacked bar of the share of days per band, with the words below it. Empty bands are left out."""
    segments = ""
    labels = ""
    for row in shares:
        if row["days"] == 0:
            continue
        color = BAND_COLORS[row["band"]]
        segments = segments + f'<div style="width:{row["share"]}%;background:{color}"></div>'
        labels = labels + f'<span><i style="background:{color}"></i>{row["band"]}: {row["days"]} days</span>'
    return f'<div class="share-bar">{segments}</div><div class="share-labels">{labels}</div>'


def pollutant_rows(guidelines):
    """One plain row per pollutant: name, what it is, and how often it went over its guideline."""
    rows = ""
    for row in guidelines:
        pollutant = POLLUTANTS[row["pollutant"]]
        share = 0
        if row["days"] > 0:
            share = row["days_over"] / row["days"] * 100
        color = BAND_COLORS["Poor"] if row["days_over"] > 0 else BAND_COLORS["Good"]
        rows = rows + (
            f'<div class="pollutant"><b>{pollutant["name"]}</b><div class="small">{pollutant["about"]}</div>'
            f'<div class="days-bar"><div style="width:{share:.0f}%"></div></div>'
            f'<div class="small" style="color:{color}">{pollutant_text(row["days_over"], row["days"])}</div></div>'
        )
    return rows


def air_outlook(days):
    """The next days in words. days is a list of (day, band) pairs."""
    items = ""
    for day, band in days:
        items = items + f'<div class="card"><div class="card-title">{day}</div><div style="color:{BAND_COLORS.get(band, "inherit")}">{band}</div></div>'
    return f'<div class="card-title outlook-title">Coming days</div><div class="grid-4">{items}</div>'


def city_table(rows):
    """One row per city. Every column says its unit, air is in words, and a dash means no data."""
    body = ""
    for row in rows:
        week = "–" if row["high"] is None else f'{round(row["low"])}° to {round(row["high"])}°'
        rain = "–" if row["rain_mm"] is None else f'{row["rain_mm"]:.0f} mm'
        wind = "–" if row["wind_kmh"] is None else f'{row["wind_kmh"]:.0f} km/h'
        air = "–" if row["aqi"] is None else aqi_label(row["aqi"])
        body = body + f'<tr><td><b>{escape(row["name"])}</b></td><td>{round(row["now"])}°</td><td>{week}</td><td>{rain}</td><td>{wind}</td><td>{air}</td></tr>'
    return f'<table class="cities"><tr><th>City</th><th>Now</th><th>Low, high</th><th>Rain</th><th>Wind</th><th>Air</th></tr>{body}</table>'
