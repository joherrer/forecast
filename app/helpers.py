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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("routes.login"))
        return f(*args, **kwargs)

    return decorated_function


def format_local_hour(timestamp, utc_offset):
    # Convert api timestamp into the spot's local hour.
    tzinfo = timezone(timedelta(hours=utc_offset or 0))
    dt = datetime.fromtimestamp(timestamp, tz=tzinfo)
    hour = dt.strftime("%I %p").lower()
    return hour[1:] if hour.startswith("0") else hour


def format_hour_label(hour):
    # Render a plain hour label for fallback rows that have no API timestamp.
    dt = datetime(2000, 1, 1, hour % 24, 0)
    formatted = dt.strftime("%I %p").lower()
    return formatted[1:] if formatted.startswith("0") else formatted


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


def format_height(height):
    # Keep swell heights clean by dropping trailing .0 values.
    if height is None:
        return "-"

    rounded = round(height, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.1f}"


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


def get_forecast_utc_offset(*payloads):
    # Use the first available forecast payload that includes a usable utc offset.
    for payload in payloads:
        utc_offset = (payload or {}).get("associated", {}).get("utcOffset")
        if utc_offset is not None:
            return utc_offset
    return 0


def has_forecast_entries(payload, key):
    # Treat a forecast source as usable only when it contains at least one entry.
    return bool((payload or {}).get("data", {}).get(key))


def build_forecast_rows(wave, wind, weather, overview_hours, forecast_hours):
    # Merge separate api responses into render-ready rows for the template.
    wave_items = (wave or {}).get("data", {}).get("wave", [])
    wind_items = (wind or {}).get("data", {}).get("wind", [])
    weather_items = (weather or {}).get("data", {}).get("weather", [])
    utc_offset = get_forecast_utc_offset(wave, wind, weather)
    tzinfo = timezone(timedelta(hours=utc_offset or 0))

    wave_by_timestamp = {
        item.get("timestamp"): item for item in wave_items if item.get("timestamp") is not None
    }
    wind_by_timestamp = {
        item.get("timestamp"): item for item in wind_items if item.get("timestamp") is not None
    }
    weather_by_timestamp = {
        item.get("timestamp"): item for item in weather_items if item.get("timestamp") is not None
    }
    timestamps = sorted(set(wave_by_timestamp) | set(wind_by_timestamp) | set(weather_by_timestamp))

    rows_by_hour = {}
    for timestamp in timestamps:
        item_wave = wave_by_timestamp.get(timestamp)
        item_wind = wind_by_timestamp.get(timestamp)
        item_weather = weather_by_timestamp.get(timestamp)

        local_dt = datetime.fromtimestamp(timestamp, tz=tzinfo)
        row = {
            "hour": local_dt.hour,
            "time": format_local_hour(timestamp, utc_offset),
            "surf_min": item_wave.get("surf", {}).get("min", "-") if item_wave else "-",
            "surf_max": item_wave.get("surf", {}).get("max", "-") if item_wave else "-",
            "surf_plus": bool(item_wave.get("surf", {}).get("plus")) if item_wave else False,
            "power": item_wave.get("power") if item_wave else None,
            "swells": build_swell_cells(item_wave.get("swells") if item_wave else None),
            "wind_speed": item_wind.get("speed") if item_wind else None,
            "wind_direction": degrees_to_cardinal(item_wind.get("direction") if item_wind else None),
            "temperature": item_weather.get("temperature") if item_weather else None,
            "pressure": item_weather.get("pressure") if item_weather else None,
            "probability": item_wave.get("probability") if item_wave else None,
        }
        if row["hour"] not in rows_by_hour:
            rows_by_hour[row["hour"]] = row

    def empty_row(hour):
        return {
            "hour": hour,
            "time": format_hour_label(hour),
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

    overview_rows = [rows_by_hour.get(hour, empty_row(hour)) for hour in overview_hours]
    forecast_rows = [rows_by_hour.get(hour, empty_row(hour)) for hour in forecast_hours]
    return {"overview_rows": overview_rows, "forecast_rows": forecast_rows}


def get_conditions_content(conditions):
    # Pull headline and observations for the forecast page.
    items = (conditions or {}).get("data", {}).get("conditions", [])
    headlines = []
    observations = []
    for item in items:
        headline = item.get("headline")
        if headline:
            headlines.append(headline)
        observation = item.get("observation")
        if observation:
            observations.append(observation)
    return {
        "headline": " ".join(headlines),
        "observation_text": " ".join(observations),
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
