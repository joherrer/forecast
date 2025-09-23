import requests

from flask import redirect, session
from functools import wraps

# Function login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

# Function to fetch forecast info from surfline API
def get_forecast_info(forecast_type, id):

    # API endpoint URL
    url = f"https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={id}&days=1"

    try:
        # Send GET request to the API
        response = requests.get(url)

        # Check if request was successful (status code 200)
        if response.status_code == 200:
            # Extract information from the response JSON
            document_forecast = response.json()
            return document_forecast
        else:
            # If the request was not successful, print an error message
            print("Error:", response.status_code)
            return None

    except Exception as e:
        # Print any exceptions that occur during the process
        print("An error occurred:", str(e))
        return None
    