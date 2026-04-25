import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

import cloudscraper
import requests
from flask import redirect, session, url_for


logger = logging.getLogger(__name__)

SURFLINE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Origin": "https://www.surfline.com",
    "Referer": "https://www.surfline.com/",
}

SURFLINE_SCRAPER = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)


def login_required(f):
    # Redirect anonymous users before they access protected routes.
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)

    return decorated_function


def format_hour(hour):
    # Convert a 24-hour value into a label shown in forecast tables.
    period = "am" if hour < 12 else "pm"
    display_hour = hour % 12 or 12
    return f"{display_hour} {period}"


def format_height(height):
    # Keep swell heights clean by dropping trailing .0 values.
    if height is None:
        return "-"

    rounded = round(height, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


def degrees_to_cardinal(degrees):
    # Turn degree values into a compass label and one rotation value for a single arrow icon.
    if degrees is None:
        return {"label": "-", "rotation": None}

    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW",
    ]
    index = round(degrees / 22.5) % 16
    label = directions[index]
    rotation = (index * 22.5 + 180) % 360
    return {"label": label, "rotation": rotation}


def build_swell_cells(swells, limit=2):
    # Identify the most relevant swells and keep only the primary and secondary entries for display.
    usable_swells = [
        swell for swell in (swells or []) if swell and (swell.get("height") or swell.get("period"))
    ]
    usable_swells.sort(key=lambda swell: swell.get("impact", 0), reverse=True)

    cells = []
    for swell in usable_swells[:limit]:
        cells.append(
            {
                "height": format_height(swell.get("height")),
                "period": swell.get("period", 0),
                "direction": degrees_to_cardinal(swell.get("direction")),
            }
        )

    while len(cells) < limit:
        cells.append(
            {
                "height": "-",
                "period": "-",
                "direction": {"label": "-", "rotation": None},
            }
        )

    return cells


def build_forecast_rows(wave, wind, weather, overview_hours, forecast_hours):
    # Wave entries define the forecast rows; wind and weather add matching details.
    wave_entries = (wave or {}).get("data", {}).get("wave", []) or []
    wind_entries = (wind or {}).get("data", {}).get("wind", []) or []
    weather_entries = (weather or {}).get("data", {}).get("weather", []) or []

    utc_offset = (wave or {}).get("associated", {}).get("utcOffset", 0) or 0
    tzinfo = timezone(timedelta(hours=utc_offset))
    requested_hours = set(overview_hours + forecast_hours)

    wind_by_timestamp = {
        entry["timestamp"]: entry for entry in wind_entries if entry.get("timestamp") is not None
    }
    weather_by_timestamp = {
        entry["timestamp"]: entry for entry in weather_entries if entry.get("timestamp") is not None
    }

    rows_by_hour = {}
    for wave_entry in wave_entries:
        timestamp = wave_entry.get("timestamp")
        if timestamp is None:
            continue

        local_dt = datetime.fromtimestamp(timestamp, tz=tzinfo)
        hour = local_dt.hour
        if hour not in requested_hours:
            continue

        wind_entry = wind_by_timestamp.get(timestamp)
        weather_entry = weather_by_timestamp.get(timestamp)

        row = {
            "time": format_hour(hour),
            "surf_min": wave_entry.get("surf", {}).get("min", "-"),
            "surf_max": wave_entry.get("surf", {}).get("max", "-"),
            "surf_plus": bool(wave_entry.get("surf", {}).get("plus")),
            "power": wave_entry.get("power"),
            "swells": build_swell_cells(wave_entry.get("swells")),
            "wind_speed": wind_entry.get("speed") if wind_entry else None,
            "wind_direction": degrees_to_cardinal(wind_entry.get("direction") if wind_entry else None),
            "temperature": weather_entry.get("temperature") if weather_entry else None,
            "pressure": weather_entry.get("pressure") if weather_entry else None,
            "probability": wave_entry.get("probability"),
        }
        if hour not in rows_by_hour:
            rows_by_hour[hour] = row

    def empty_row(hour):
        return {
            "time": format_hour(hour),
            "surf_min": "-",
            "surf_max": "-",
            "surf_plus": False,
            "power": None,
            "swells": build_swell_cells(None),
            "wind_speed": None,
            "wind_direction": degrees_to_cardinal(None),
            "temperature": None,
            "pressure": None,
            "probability": None,
        }

    overview_rows = [rows_by_hour.get(hour) or empty_row(hour) for hour in overview_hours]
    forecast_rows = [rows_by_hour.get(hour) or empty_row(hour) for hour in forecast_hours]
    return {"overview_rows": overview_rows, "forecast_rows": forecast_rows}


def get_conditions_content(conditions):
    # Conditions are secondary content, so the page should still render if this request fails.
    items = (conditions or {}).get("data", {}).get("conditions", []) or []
    condition = next(iter(items), None)
    if not condition:
        return {"headline": "", "observation_text": ""}

    return {
        "headline": condition.get("headline", ""),
        "observation_text": condition.get("observation", ""),
    }


def get_forecast_info(forecast_type, spot_id):
    # Reuse the shared scraper so Surfline requests keep consistent headers/cookies.
    url = f"https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={spot_id}&days=1"
    try:
        response = SURFLINE_SCRAPER.get(url, headers=SURFLINE_HEADERS, timeout=10)

        if response.status_code == 200:
            return response.json()

        logger.warning(
            "Surfline request failed: forecast_type=%s spot_id=%s status=%s",
            forecast_type,
            spot_id,
            response.status_code,
        )
        return None

    except requests.RequestException as e:
        logger.error(
            "Surfline request error: forecast_type=%s spot_id=%s error=%s",
            forecast_type,
            spot_id,
            str(e),
        )
        return None
