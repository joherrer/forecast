from datetime import datetime, timedelta, timezone

from werkzeug.security import check_password_hash


TEST_TZ = timezone(timedelta(hours=10))


def _local_timestamp(hour):
    return int(datetime(2024, 4, 20, hour, tzinfo=TEST_TZ).timestamp())


def _mock_wave():
    return {
        "associated": {"utcOffset": 10},
        "data": {
            "wave": [
                {
                    "timestamp": _local_timestamp(6),
                    "surf": {"min": 2, "max": 3, "plus": False},
                    "power": 150,
                    "swells": [
                        {"height": 1.8, "period": 9, "direction": 90, "impact": 3},
                        {"height": 1.2, "period": 7, "direction": 180, "impact": 2},
                    ],
                    "probability": 65,
                },
                {
                    "timestamp": _local_timestamp(9),
                    "surf": {"min": 3, "max": 4, "plus": True},
                    "power": 220,
                    "swells": [
                        {"height": 2.4, "period": 11, "direction": 135, "impact": 4},
                        {"height": 1.0, "period": 6, "direction": 45, "impact": 1},
                    ],
                    "probability": 82,
                },
                {
                    "timestamp": _local_timestamp(12),
                    "surf": {"min": 2, "max": 3, "plus": False},
                    "power": 140,
                    "swells": [
                        {"height": 1.6, "period": 8, "direction": 120, "impact": 2},
                    ],
                    "probability": 58,
                },
                {
                    "timestamp": _local_timestamp(15),
                    "surf": {"min": 2, "max": 3, "plus": False},
                    "power": 130,
                    "swells": [
                        {"height": 1.4, "period": 8, "direction": 110, "impact": 2},
                    ],
                    "probability": 54,
                },
                {
                    "timestamp": _local_timestamp(18),
                    "surf": {"min": 2, "max": 3, "plus": False},
                    "power": 140,
                    "swells": [
                        {"height": 1.6, "period": 8, "direction": 120, "impact": 2},
                    ],
                    "probability": 58,
                },
            ]
        },
    }


def _mock_wind():
    return {
        "data": {
            "wind": [
                {"speed": 8, "direction": 45},
                {"speed": 10, "direction": 90},
                {"speed": 12, "direction": 120},
                {"speed": 14, "direction": 180},
                {"speed": 16, "direction": 225},
            ]
        }
    }


def _mock_weather():
    return {
        "data": {
            "weather": [
                {"temperature": 23, "pressure": 1015},
                {"temperature": 25, "pressure": 1013},
                {"temperature": 24, "pressure": 1011},
                {"temperature": 22, "pressure": 1010},
                {"temperature": 21, "pressure": 1009},
            ]
        }
    }


def _mock_conditions():
    return {
        "data": {
            "conditions": [
                {
                    "headline": "Clean morning windows.",
                    "observation": "Light offshore breeze early.",
                }
            ]
        }
    }


def test_register_creates_user_and_logs_them_in(app, client, database, models):
    response = client.post(
        "/register",
        data={
            "username": "grom",
            "password": "secret123",
            "confirmation": "secret123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Account created successfully!" in response.data

    with client.session_transaction() as session:
        assert session["user_id"] is not None

    with app.app_context(), database.session.no_autoflush:
        user = models["Users"].query.filter_by(username="grom").first()

    assert user is not None
    assert check_password_hash(user.hash, "secret123")


def test_favorites_requires_login(client):
    response = client.get("/favorites")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_logged_in_user_can_add_favorite(app, client, database, models):
    with app.app_context():
        user = models["Users"](username="regularfooter", hash="hashed-password")
        database.session.add(user)
        database.session.commit()
        user_id = user.id

    with client.session_transaction() as session:
        session["user_id"] = user_id

    response = client.post(
        "/favorites",
        data={"action": "add", "spot": "Kirra"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Spot added to favorites" in response.data

    with app.app_context():
        favorite = models["Favorites"].query.filter_by(user_id=user_id, spot="Kirra").first()
    assert favorite is not None


def test_spot_forecast_renders_using_mocked_forecast_data(client, monkeypatch):
    import app.routes as routes_module

    mocked_payloads = {
        "wave": _mock_wave(),
        "wind": _mock_wind(),
        "weather": _mock_weather(),
        "conditions": _mock_conditions(),
    }

    monkeypatch.setattr(
        routes_module,
        "get_forecast_info",
        lambda forecast_type, spot_id: mocked_payloads[forecast_type],
    )

    response = client.get("/spots/kirra")

    assert response.status_code == 200
    assert b"Kirra" in response.data
    assert b"Daily overview" in response.data
    assert b"Clean morning windows." in response.data
