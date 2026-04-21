import importlib
import os
from pathlib import Path

import pytest


os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault(
    "DATABASE_URL",
    f"sqlite:///{Path(__file__).resolve().parent / 'test_app.db'}",
)
os.environ.setdefault("SESSION_COOKIE_SECURE", "0")

app_module = importlib.import_module("app")


@pytest.fixture
def app():
    app_module.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with app_module.app.app_context():
        app_module.db.session.remove()
        app_module.db.drop_all()
        app_module.db.create_all()

    yield app_module.app

    with app_module.app.app_context():
        app_module.db.session.remove()
        app_module.db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db():
    return app_module.db


@pytest.fixture
def models():
    return {
        "Users": app_module.Users,
        "Favorites": app_module.Favorites,
    }
