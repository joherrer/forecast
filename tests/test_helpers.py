from datetime import datetime, timedelta, timezone

from app.helpers import build_forecast_rows


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

    assert [row["hour"] for row in result["forecast_rows"]] == [6, 9]
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

    assert [row["hour"] for row in result["overview_rows"]] == [6, 12, 18]
    assert [row["hour"] for row in result["forecast_rows"]] == [6, 9, 12, 15, 18]
    assert all(row["surf_min"] == "-" for row in result["forecast_rows"])
