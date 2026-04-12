import logging
import random
from functools import wraps

import cloudscraper
import requests
from flask import redirect, session, url_for

logger = logging.getLogger(__name__)

# Browser-like user agents help reduce request blocking from the upstream API.
SURFLINE_USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]

def build_surfline_headers():
    # Randomize user agent to avoid sending an identical request fingerprint each time.
    user_agent = random.choice(SURFLINE_USER_AGENTS)
    return {
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Origin': 'https://www.surfline.com',
        'Referer': 'https://www.surfline.com/',
        'Sec-Ch-Ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
    }

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Redirect unauthenticated users to the login page.
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_forecast_info(forecast_type, spot_id):
    # Build the forecast URL by type (wave, wind, weather, conditions) for one spot/day.
    url = f"https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={spot_id}&days=1"
    headers = build_surfline_headers()

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
