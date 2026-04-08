import logging
import requests

from flask import redirect, session, url_for
from functools import wraps

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_forecast_info(forecast_type, spot_id):
    url = f"https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={spot_id}&days=1"

    try:
        response = requests.get(url, timeout=10)

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
