import os
from pathlib import Path

import pytest

from app import create_app
from app.extensions import db
from app.models import Favorites, Users


os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).resolve().parent / 'test_app.db'}",
)
os.environ.setdefault("SESSION_COOKIE_SECURE", "0")


@pytest.fixture
def app():
    # Use the real app factory with test-friendly config and a disposable database state.
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
        }
    )

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def models():
    # Expose model classes explicitly so tests can stay decoupled from import paths.
    return {
        "Users": Users,
        "Favorites": Favorites,
    }


@pytest.fixture
def database(app):
    return db
