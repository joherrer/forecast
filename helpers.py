import logging
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

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_forecast_info(forecast_type, spot_id):
    # Build the forecast URL by type (wave, wind, weather, conditions) for one spot/day.
    url = f"https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={spot_id}&days=1"
    headers = SURFLINE_HEADERS

    try:
        # Use cloudscraper to mimic browser requests on protected endpoints.
        scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        response = scraper.get(url, headers=headers, timeout=12)

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
