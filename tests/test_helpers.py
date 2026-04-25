from datetime import datetime, timedelta, timezone

from app.helpers import build_forecast_rows, get_conditions_content


TEST_TZ = timezone(timedelta(hours=10))


def _local_timestamp(hour):
    return int(datetime(2024, 4, 20, hour, tzinfo=TEST_TZ).timestamp())


def test_build_forecast_rows_returns_requested_forecast_hours():
    # The helper should keep the requested forecast slots in local-time order.
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
                    "swells": [{"height": 2.5, "period": 11, "direction": 135, "impact": 4}],
                    "probability": 80,
                },
            ]
        },
    }
    wind = {
        "data": {
            "wind": [
                {"timestamp": _local_timestamp(6), "speed": 12, "direction": 45},
                {"timestamp": _local_timestamp(9), "speed": 18, "direction": 225},
            ]
        }
    }
    weather = {
        "data": {
            "weather": [
                {"timestamp": _local_timestamp(6), "temperature": 24, "pressure": 1014},
                {"timestamp": _local_timestamp(9), "temperature": 25, "pressure": 1012},
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

    assert [row["time"] for row in result["forecast_rows"]] == ["6 am", "9 am"]


def test_build_forecast_rows_handles_missing_data_gracefully():
    # Missing API data should still produce placeholder rows instead of an empty table.
    result = build_forecast_rows(
        wave={"associated": {"utcOffset": 10}, "data": {"wave": []}},
        wind={"data": {"wind": []}},
        weather={"data": {"weather": []}},
        overview_hours=[6, 12, 18],
        forecast_hours=[6, 9, 12, 15, 18],
    )

    assert [row["time"] for row in result["overview_rows"]] == ["6 am", "12 pm", "6 pm"]
    assert [row["time"] for row in result["forecast_rows"]] == ["6 am", "9 am", "12 pm", "3 pm", "6 pm"]
    assert all(row["surf_min"] == "-" for row in result["forecast_rows"])


def test_build_forecast_rows_tolerates_partial_api_payloads():
    # Partial Surfline responses should leave placeholders instead of raising KeyError.
    result = build_forecast_rows(
        wave={
            "associated": {"utcOffset": 10},
            "data": {
                "wave": [
                    {"timestamp": _local_timestamp(6), "surf": {"min": 2}},
                    {"surf": {"min": 3, "max": 4}},
                ]
            }
        },
        wind={"data": {"wind": [{"speed": 12}, {"timestamp": _local_timestamp(6)}]}},
        weather={"data": {"weather": [{"timestamp": _local_timestamp(6)}]}},
        overview_hours=[6],
        forecast_hours=[6, 9],
    )

    row = result["forecast_rows"][0]
    assert row["time"] == "6 am"
    assert row["surf_min"] == 2
    assert row["surf_max"] == "-"
    assert row["wind_speed"] is None
    assert row["temperature"] is None
    assert result["forecast_rows"][1]["surf_min"] == "-"


def test_get_conditions_content_handles_missing_conditions():
    assert get_conditions_content(None) == {"headline": "", "observation_text": ""}
    assert get_conditions_content({"data": {"conditions": []}}) == {
        "headline": "",
        "observation_text": "",
    }
    assert get_conditions_content({"data": {"conditions": [{"headline": "Clean"}]}}) == {
        "headline": "Clean",
        "observation_text": "",
    }

