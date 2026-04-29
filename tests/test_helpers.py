from datetime import datetime, timezone

from app.helpers import (
    _fallback_forecast_info,
    build_forecast_rows,
    degrees_to_cardinal,
    format_height,
    format_hour,
)


def test_format_hour_uses_12_hour_labels():
    assert format_hour(0) == "12 am"
    assert format_hour(9) == "9 am"
    assert format_hour(12) == "12 pm"
    assert format_hour(18) == "6 pm"


def test_format_height_keeps_display_values_simple():
    assert format_height(None) == "-"
    assert format_height(2.0) == "2"
    assert format_height(2.25) == "2.2"


def test_degrees_to_cardinal_returns_label_and_arrow_rotation():
    assert degrees_to_cardinal(None) == {"label": "-", "rotation": None}
    assert degrees_to_cardinal(0) == {"label": "N", "rotation": 180.0}
    assert degrees_to_cardinal(90) == {"label": "E", "rotation": 270.0}


def test_build_forecast_rows_combines_wave_wind_and_weather_data():
    # Minimal Surfline-shaped payload covering matched and missing forecast slots.
    timestamp = int(datetime(2026, 1, 1, 6, tzinfo=timezone.utc).timestamp())
    wave = {
        "associated": {"utcOffset": 0},
        "data": {
            "wave": [
                {
                    "timestamp": timestamp,
                    "surf": {"min": 2, "max": 3, "plus": True},
                    "power": 120,
                    "probability": 95,
                    "swells": [
                        {"height": 1.5, "period": 10, "direction": 90, "impact": 2},
                        {"height": 0.8, "period": 8, "direction": 180, "impact": 1},
                    ],
                }
            ]
        },
    }
    wind = {"data": {"wind": [{"timestamp": timestamp, "speed": 12, "direction": 45}]}}
    weather = {"data": {"weather": [{"timestamp": timestamp, "temperature": 24, "pressure": 1015}]}}

    rows = build_forecast_rows(
        wave,
        wind,
        weather,
        overview_hours=[6, 12],
        forecast_hours=[6, 9, 12],
    )

    six_am_row = rows["overview_rows"][0]
    assert six_am_row["time"] == "6 am"
    assert six_am_row["surf_min"] == 2
    assert six_am_row["surf_max"] == 3
    assert six_am_row["surf_plus"] is True
    assert six_am_row["wind_speed"] == 12
    assert six_am_row["temperature"] == 24
    assert six_am_row["swells"][0]["direction"]["label"] == "E"

    empty_midday_row = rows["overview_rows"][1]
    assert empty_midday_row["time"] == "12 pm"
    assert empty_midday_row["surf_min"] == "-"
    assert empty_midday_row["wind_direction"]["label"] == "-"


def test_fallback_forecast_matches_page_data_shape():
    spot_id = "5842041f4e65fad6a7708be9"
    wave = _fallback_forecast_info("wave", spot_id)
    wind = _fallback_forecast_info("wind", spot_id)
    weather = _fallback_forecast_info("weather", spot_id)
    conditions = _fallback_forecast_info("conditions", spot_id)

    rows = build_forecast_rows(
        wave,
        wind,
        weather,
        overview_hours=[6, 12, 18],
        forecast_hours=[6, 9, 12, 15, 18],
    )

    assert wave["data"]["wave"]
    assert wind["data"]["wind"]
    assert weather["data"]["weather"]
    assert conditions["data"]["conditions"][0]["headline"] == "Demo forecast shown"
    assert rows["overview_rows"][0]["surf_min"] != "-"
