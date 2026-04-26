import pytest
from cachelib.file import FileSystemCache

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    # Keep test state isolated from the local development database and session cache.
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
            "SESSION_CACHELIB": FileSystemCache(cache_dir=str(tmp_path / "sessions")),
        }
    )

    with test_app.app_context():
        db.drop_all()
        db.create_all()

    yield test_app

    with test_app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
