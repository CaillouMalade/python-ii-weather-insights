"""Simple HTML for the cards. Text from the API or data files always goes through escape()."""

from html import escape

from .display import (
    aqi_label,
    aqi_position,
    background_for,
    compass_direction,
    format_local_time,
    high_low_text,
    is_night,
    range_bar,
    uv_label,
    weather_emoji,
)


def city_card(name, reading, high, low, note, selected, now):
    """A sidebar entry: name, local time, temperature, conditions and high/low when available."""
    outline = " selected" if selected else ""
    if reading is None:
        return (
            f'<div class="city{outline}" style="background:rgba(255,255,255,.08)">'
            f'<div><div class="city-name">{escape(name)}</div>'
            f'<div class="city-small">{escape(note)}</div></div></div>'
        )

    background = background_for(reading.weather_id, is_night(now, reading.sunrise, reading.sunset))
    high_low = ""
    if high is not None:
        high_low = high_low_text(high, low)
    return (
        f'<div class="city{outline}" style="background:{background}">'
        f'<div><div class="city-name">{escape(name)}</div>'
        f'<div class="city-small">{format_local_time(now, reading.timezone_offset or 0)}</div></div>'
        f'<div class="city-temp">{reading.temperature:.0f}°</div>'
        f'<div class="city-small">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="city-small high-low">{high_low}</div></div>'
    )


def feels_small(delta):
    """Compare feels-like with the actual temperature, using the reading's feels_like_delta."""
    if abs(delta) < 1:
        return "About the actual temperature"
    direction = "warmer" if delta > 0 else "colder"
    return f"{abs(delta):.0f}° {direction} than actual"


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
        wind_small = f"{wind_small}, gusts {reading.wind_gust * 3.6:.0f} km/h".strip(", ")

    rain_value = "No data" if rain_chance is None else f"{rain_chance * 100:.0f} %"
    stats = (
        stat("Feels like", f"{reading.feels_like:.0f}°", feels_small(reading.feels_like_delta))
        + stat("Wind", f"{reading.wind_speed * 3.6:.0f} km/h", wind_small)
        + stat("Humidity", f"{reading.humidity} %")
        + stat("Chance of rain", rain_value, "Next few hours")
    )
    return (
        '<div class="card header">'
        '<div class="header-main">'
        f'<div class="header-city">{escape(city)}</div>'
        f'<div class="small">{time_text} local time</div>'
        f'<div class="header-temp">{reading.temperature:.0f}°</div>'
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
    now_value = f"{reading.temperature:.0f}°"
    if measure == "Precipitation":
        now_value = format_precipitation((reading.rain_1h or 0) + (reading.snow_1h or 0))
    elif measure == "Wind":
        now_value = f"{reading.wind_speed * 3.6:.0f} km/h"

    items = [strip_item("Now", weather_emoji(reading.icon), now_value)]
    for _, row in steps.iterrows():
        small = ""
        value = f'{row["temperature"]:.0f}°'
        if measure == "Precipitation":
            value = format_precipitation(row["rain_3h"] + row["snow_3h"])
            small = f'{row["pop"] * 100:.0f} % chance'
        elif measure == "Wind":
            value = f'{row["wind_speed"] * 3.6:.0f} km/h'
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
            f'<div class="day-low">{row["low"]:.0f}°</div>'
            f'<div class="bar"><div class="bar-fill" style="left:{left}%;width:{width}%"></div>{dot}</div>'
            f'<b>{row["high"]:.0f}°</b></div>'
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
        tiles.append(tile("Dew point", f"{dew_point:.0f}°"))
    if reading.visibility is not None:
        tiles.append(tile("Visibility", f"{reading.visibility / 1000:.0f} km"))
    if reading.pressure is not None:
        tiles.append(tile("Pressure", f"{reading.pressure} hPa", tendency))
    if reading.clouds is not None:
        tiles.append(tile("Cloud cover", f"{reading.clouds} %"))
    return '<div class="grid-4">' + "".join(tiles) + "</div>"
