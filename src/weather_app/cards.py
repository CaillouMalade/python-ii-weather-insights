"""Simple HTML for the cards. Text from the API or data files always goes through escape()."""

from html import escape

from .display import (
    aqi_label,
    aqi_position,
    background_for,
    compass_direction,
    format_local_time,
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
        high_low = f"H:{high:.0f}° L:{low:.0f}°"
    return (
        f'<div class="city{outline}" style="background:{background}">'
        f'<div><div class="city-name">{escape(name)}</div>'
        f'<div class="city-small">{format_local_time(now, reading.timezone_offset or 0)}</div></div>'
        f'<div class="city-temp">{reading.temperature:.0f}°</div>'
        f'<div class="city-small">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="city-small">{high_low}</div></div>'
    )


def hero(city, reading, high, low, now):
    time_text = format_local_time(now, reading.timezone_offset or 0, "%A %H:%M")
    return (
        '<div class="hero">'
        f'<div class="hero-city">{escape(city)}</div>'
        f'<div class="hero-time">{time_text} local time</div>'
        f'<div class="hero-temp">{reading.temperature:.0f}°</div>'
        f'<div class="hero-line">{escape(reading.conditions.capitalize())}</div>'
        f'<div class="hero-line">H:{high:.0f}° L:{low:.0f}°</div>'
        "</div>"
    )


def strip_item(top, icon, pop_text, value):
    """One column of the Conditions strip. Every argument is text we formatted ourselves."""
    return (
        '<div class="strip-item">'
        f"<div><b>{top}</b></div>"
        f'<div class="strip-icon">{icon}</div>'
        f'<div class="strip-pop">{pop_text}</div>'
        f'<div class="strip-value">{value}</div></div>'
    )


def conditions_strip(plan, timezone_offset, measure, reading):
    """The next 24 hours for one measure: Temperature, Precipitation or Wind."""
    now_value = f"{reading.temperature:.0f}°"
    if measure == "Precipitation":
        now_value = f"{(reading.rain_1h or 0) + (reading.snow_1h or 0):.1f} mm"
    elif measure == "Wind":
        now_value = f"{reading.wind_speed * 3.6:.0f}"

    items = [strip_item("Now", weather_emoji(reading.icon), "", now_value)]
    for _, row in plan.iterrows():
        time_text = format_local_time(int(row["dt"]), timezone_offset)
        if row["kind"] == "sunrise":
            items.append(strip_item(time_text, "🌅", "", "Sunrise"))
        elif row["kind"] == "sunset":
            items.append(strip_item(time_text, "🌇", "", "Sunset"))
        else:
            pop_text = f'{row["pop"] * 100:.0f} %' if row["pop"] > 0 else ""
            if measure == "Precipitation":
                value = f'{row["rain_3h"] + row["snow_3h"]:.1f} mm'
            elif measure == "Wind":
                value = f'{row["wind_speed"] * 3.6:.0f}'
            else:
                value = f'{row["temperature"]:.0f}°'
            items.append(strip_item(time_text, weather_emoji(row["icon"]), pop_text, value))
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
    return f'<div class="card"><div class="card-title">{len(rows)}-day forecast</div>' + "".join(rows) + "</div>"


def tile(title, big, small, extra=""):
    return f'<div class="card"><div class="card-title">{title}</div><div class="big">{big}</div>{extra}<div class="small">{small}</div></div>'


def air_tile(air_row):
    aqi = air_row.get("aqi")
    if aqi is None:
        return ""
    scale = f'<div class="scale"><div class="scale-dot" style="left:{aqi_position(aqi):.0f}%"></div></div>'

    details = []
    for key, name in [("pm2_5", "PM2.5"), ("pm10", "PM10"), ("no2", "NO₂"), ("o3", "O₃")]:
        if air_row.get(key) is not None:
            details.append(f"{name} {air_row[key]:.0f}")
    small = " · ".join(details) + " µg/m³"
    return (
        f'<div class="card wide"><div class="card-title">Air quality</div>'
        f'<div class="big">{aqi_label(aqi)}</div>{scale}<div class="small">{small}</div></div>'
    )


def wind_tile(reading):
    speed = reading.wind_speed * 3.6
    small = ""
    arrow = ""
    if reading.wind_deg is not None:
        small = f"From the {compass_direction(reading.wind_deg)}"
        # wind_deg is where the wind comes from, so the arrow head points back that way.
        arrow = f'<div class="compass-arrow" style="transform:rotate({float(reading.wind_deg):.0f}deg)"></div>'
    if reading.wind_gust is not None:
        small = f"{small} · gusts {reading.wind_gust * 3.6:.0f} km/h"
    compass = (
        '<div class="compass"><div class="compass-face"></div>'
        + arrow
        + f'<div class="compass-text"><b>{speed:.0f}</b>km/h</div></div>'
    )
    return f'<div class="card"><div class="card-title">Wind</div>{compass}<div class="small">{small}</div></div>'


def sun_tile(reading):
    if reading.sunrise is None or reading.sunset is None:
        return ""
    offset = reading.timezone_offset or 0
    sunrise = format_local_time(reading.sunrise, offset)
    sunset = format_local_time(reading.sunset, offset)
    hours = (reading.sunset - reading.sunrise) / 3600
    return tile("Sunrise and sunset", sunrise, f"Sunset {sunset} · {hours:.1f} h of daylight")


def uv_tile(uv_value):
    if uv_value is None:
        return ""
    return tile("UV index", f"{uv_value:.0f}", uv_label(uv_value))


def feels_tile(reading):
    delta = reading.feels_like_delta
    small = "About the same as the actual temperature."
    if delta >= 1:
        small = f"{delta:.0f}° warmer than the actual temperature."
    elif delta <= -1:
        small = f"{abs(delta):.0f}° colder than the actual temperature."
    return tile("Feels like", f"{reading.feels_like:.0f}°", small)


def humidity_tile(reading, dew_point):
    small = ""
    if dew_point is not None:
        small = f"Dew point in the next forecast step: {dew_point:.0f}°"
    return tile("Humidity", f"{reading.humidity} %", small)


def visibility_tile(reading):
    if reading.visibility is None:
        return ""
    return tile("Visibility", f"{reading.visibility / 1000:.0f} km", f"Cloud cover {reading.clouds or 0} %")


def pressure_tile(reading, tendency):
    if reading.pressure is None:
        return ""
    return tile("Pressure", f"{reading.pressure} hPa", tendency)
