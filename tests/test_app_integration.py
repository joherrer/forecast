from app.extensions import db
from app.models import Favorites, Users


def register(client, username="testuser", password="password123"):
    # Shared helper for tests that need an authenticated session.
    return client.post(
        "/register",
        data={
            "username": username,
            "password": password,
            "confirmation": password,
        },
        follow_redirects=True,
    )


def test_public_pages_load(client):
    home_response = client.get("/")
    spots_response = client.get("/spots")

    assert home_response.status_code == 200
    assert spots_response.status_code == 200
    assert b"Surfers Paradise" in spots_response.data


def test_register_creates_user_and_logs_them_in(client, app):
    response = register(client, username="alice")

    assert response.status_code == 200
    assert b"Account created successfully!" in response.data

    with app.app_context():
        user = Users.query.filter_by(username="alice").first()
        assert user is not None
        assert user.hash != "password123"

    with client.session_transaction() as session:
        assert session["user_id"] == user.id


def test_login_rejects_invalid_password(client):
    # Start from a real registered user so the failure is only the password check.
    register(client, username="alice", password="correct-password")
    client.post("/logout")

    response = client.post(
        "/login",
        data={"username": "alice", "password": "wrong-password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

    with client.session_transaction() as session:
        assert "user_id" not in session


def test_favorites_requires_login(client):
    response = client.get("/favorites")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_logged_in_user_can_add_and_remove_favorite(client, app):
    register(client)

    add_response = client.post(
        "/favorites",
        data={"action": "add", "spot": "Kirra"},
        follow_redirects=True,
    )

    assert add_response.status_code == 200
    assert b"Spot added to favorites" in add_response.data
    assert b"Kirra" in add_response.data

    with app.app_context():
        assert Favorites.query.filter_by(spot="Kirra").count() == 1

    remove_response = client.post(
        "/favorites",
        data={"action": "remove", "spot": "Kirra"},
        follow_redirects=True,
    )

    assert remove_response.status_code == 200
    assert b"Spot removed from favorites" in remove_response.data

    with app.app_context():
        assert Favorites.query.filter_by(spot="Kirra").count() == 0


def test_duplicate_favorite_is_not_saved_twice(client, app):
    register(client)

    client.post("/favorites", data={"action": "add", "spot": "Kirra"})

    response = client.post(
        "/favorites",
        data={"action": "add", "spot": "Kirra"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Spot already exists" in response.data

    with app.app_context():
        assert db.session.query(Favorites).filter_by(spot="Kirra").count() == 1
