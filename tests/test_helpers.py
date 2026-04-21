from datetime import datetime, timedelta, timezone

from app.helpers import build_forecast_rows, degrees_to_cardinal, get_conditions_content


TEST_TZ = timezone(timedelta(hours=10))


def _local_timestamp(hour):
    return int(datetime(2024, 4, 20, hour, tzinfo=TEST_TZ).timestamp())


def test_degrees_to_cardinal_returns_expected_label_and_rotation():
    result = degrees_to_cardinal(90)

    assert result == {"label": "E", "rotation": 270.0}


def test_get_conditions_content_combines_available_text():
    conditions = {
        "data": {
            "conditions": [
                {"headline": "Clean early.", "observation": "Light offshore wind."},
                {"headline": "Fun mid tide.", "observation": "Best before lunch."},
            ]
        }
    }

    result = get_conditions_content(conditions)

    assert result["headline"] == "Clean early. Fun mid tide."
    assert result["observation_text"] == "Light offshore wind. Best before lunch."


def test_build_forecast_rows_filters_requested_hours_and_formats_values():
    wave = {
        "associated": {"utcOffset": 10},
        "data": {
            "wave": [
                {
                    "timestamp": _local_timestamp(6),
                    "surf": {"min": 2, "max": 3, "plus": True},
                    "power": 180,
                    "swells": [
                        {"height": 2.0, "period": 10, "direction": 90, "impact": 3},
                        {"height": 1.5, "period": 8, "direction": 180, "impact": 2},
                    ],
                    "probability": 75,
                },
                {
                    "timestamp": _local_timestamp(9),
                    "surf": {"min": 3, "max": 4, "plus": False},
                    "power": 220,
                    "swells": [
                        {"height": 2.5, "period": 11, "direction": 135, "impact": 4},
                    ],
                    "probability": 80,
                },
            ]
        },
    }
    wind = {
        "data": {
            "wind": [
                {"speed": 12, "direction": 45},
                {"speed": 18, "direction": 225},
            ]
        }
    }
    weather = {
        "data": {
            "weather": [
                {"temperature": 24, "pressure": 1014},
                {"temperature": 25, "pressure": 1012},
            ]
        }
    }

    result = build_forecast_rows(
        wave,
        wind,
        weather,
        overview_hours=[6, 9],
        forecast_hours=[6, 9],
    )

    assert [row["hour"] for row in result["overview_rows"]] == [6, 9]
    assert [row["time"] for row in result["forecast_rows"]] == ["6 am", "9 am"]
    assert result["forecast_rows"][0]["surf_plus"] is True
    assert result["forecast_rows"][0]["swells"][0]["direction"]["label"] == "E"
    assert result["forecast_rows"][1]["wind_direction"]["label"] == "SW"


def test_build_forecast_rows_returns_empty_lists_when_any_series_is_missing():
    result = build_forecast_rows(
        wave={"associated": {"utcOffset": 10}, "data": {"wave": []}},
        wind={"data": {"wind": []}},
        weather={"data": {"weather": []}},
        overview_hours=[6, 12, 18],
        forecast_hours=[6, 9, 12, 15, 18],
    )

    assert result == {"overview_rows": [], "forecast_rows": []}
