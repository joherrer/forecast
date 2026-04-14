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
    browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_local_datetime(timestamp, utc_offset):
    # Convert a Surfline timestamp into the spot's local datetime.
    tzinfo = timezone(timedelta(hours=utc_offset or 0))
    return datetime.fromtimestamp(timestamp, tz=tzinfo)

def format_local_hour(timestamp, utc_offset):
    # Convert a Surfline timestamp into the spot's local hour.
    dt = get_local_datetime(timestamp, utc_offset)
    hour = dt.strftime('%I %p').lower()
    return hour[1:] if hour.startswith('0') else hour

def degrees_to_cardinal(degrees):
    # Turn degree values into a compass label and one rotation value for a single arrow icon.
    if degrees is None:
        return {'label': '-', 'rotation': None}

    directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE',
                  'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW']
    index = round(degrees / 22.5) % 16
    label = directions[index]
    rotation = (index * 22.5 + 180) % 360
    return {'label': label, 'rotation': rotation}

def format_height(height):
    # Keep swell heights clean by dropping trailing .0 values.
    if height is None:
        return '-'

    rounded = round(height, 1)
    if rounded.is_integer():
        return str(int(rounded))
    return f'{rounded:.1f}'

def build_swell_cells(swells, limit=2):
    # Pick the most relevant swells and keep only the primary and secondary entries for display.
    usable_swells = [
        swell for swell in (swells or [])
        if swell and (swell.get('height') or swell.get('period'))
    ]
    usable_swells.sort(key=lambda swell: swell.get('impact', 0), reverse=True)

    cells = []
    for swell in usable_swells[:limit]:
        cells.append({
            'height': format_height(swell.get('height')),
            'period': swell.get('period', 0),
            'direction': degrees_to_cardinal(swell.get('direction')),
        })

    while len(cells) < limit:
        cells.append({
            'height': '-',
            'period': '-',
            'direction': {'label': '-', 'rotation': None},
        })

    return cells

def build_forecast_rows(wave, wind, weather, overview_hours, forecast_hours):
    # Merge separate Surfline responses into render-ready rows for the template.
    wave_items = (wave or {}).get('data', {}).get('wave', [])
    wind_items = (wind or {}).get('data', {}).get('wind', [])
    weather_items = (weather or {}).get('data', {}).get('weather', [])
    utc_offset = (wave or {}).get('associated', {}).get('utcOffset', 0)

    total_rows = min(len(wave_items), len(wind_items), len(weather_items))
    if total_rows == 0:
        return {'overview_rows': [], 'forecast_rows': []}

    def build_row(index):
        if index >= total_rows:
            return None

        item_wave = wave_items[index]
        item_wind = wind_items[index]
        item_weather = weather_items[index]
        timestamp = item_wave.get('timestamp')
        if timestamp is None:
            return None

        local_dt = get_local_datetime(timestamp, utc_offset)

        return {
            'hour': local_dt.hour,
            'time': format_local_hour(timestamp, utc_offset),
            'surf_min': item_wave.get('surf', {}).get('min', '-'),
            'surf_max': item_wave.get('surf', {}).get('max', '-'),
            'surf_plus': bool(item_wave.get('surf', {}).get('plus')),
            'power': item_wave.get('power'),
            'swells': build_swell_cells(item_wave.get('swells')),
            'wind_speed': item_wind.get('speed'),
            'wind_direction': degrees_to_cardinal(item_wind.get('direction')),
            'temperature': item_weather.get('temperature'),
            'pressure': item_weather.get('pressure'),
            'probability': item_wave.get('probability'),
        }

    rows_by_hour = {}
    for index in range(total_rows):
        row = build_row(index)
        if row and row['hour'] not in rows_by_hour:
            rows_by_hour[row['hour']] = row

    overview_rows = [rows_by_hour[hour] for hour in overview_hours if hour in rows_by_hour]
    forecast_rows = [rows_by_hour[hour] for hour in forecast_hours if hour in rows_by_hour]
    return {'overview_rows': overview_rows, 'forecast_rows': forecast_rows}

def get_conditions_content(conditions):
    # Pull a concise headline and the longer observations for the page.
    items = (conditions or {}).get('data', {}).get('conditions', [])
    headlines = []
    observations = []
    for item in items:
        headline = item.get('headline')
        if headline:
            headlines.append(headline)
        observation = item.get('observation')
        if observation:
            observations.append(observation)
    return {
        'headline': ' '.join(headlines),
        'observation_text': ' '.join(observations),
    }

def get_forecast_info(forecast_type, spot_id):
    # Fetch one Surfline forecast endpoint for a single spot and day.
    url = f"https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={spot_id}&days=1"
    try:
        response = SURFLINE_SCRAPER.get(url, headers=SURFLINE_HEADERS, timeout=12)

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
        logger.error("Surfline request error: forecast_type=%s spot_id=%s error=%s", forecast_type, spot_id, str(e))
        return None
