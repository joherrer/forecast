import pytest
from cachelib.file import FileSystemCache
from testcontainers.postgres import PostgresContainer

from app import create_app
from app.extensions import db


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest.fixture()
def app(tmp_path, postgres_container):
    # Keep test state isolated from the local development database and session cache.
    test_app = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": postgres_container.get_connection_url(),
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
