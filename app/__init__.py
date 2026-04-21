import os
from pathlib import Path

from cachelib.file import FileSystemCache
from dotenv import load_dotenv
from flask import Flask

from .extensions import csrf, db, session


load_dotenv()

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent


def create_app(test_config=None):
    app = Flask(
        __name__,
        template_folder=str(PROJECT_ROOT / "templates"),
        static_folder=str(PROJECT_ROOT / "static"),
    )

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY"),
        SESSION_TYPE="cachelib",
        SESSION_CACHELIB=FileSystemCache(
            cache_dir=str(PROJECT_ROOT / "flask_session"),
            threshold=500,
        ),
        SESSION_SERIALIZATION_FORMAT="json",
        SESSION_PERMANENT=False,
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "0") == "1",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "DATABASE_URL",
            f"sqlite:///{PROJECT_ROOT / 'forecast.db'}",
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    if not app.config["SECRET_KEY"]:
        raise RuntimeError("SECRET_KEY is required.")

    db.init_app(app)
    session.init_app(app)
    csrf.init_app(app)

    from .routes import routes_bp

    app.register_blueprint(routes_bp)

    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

    with app.app_context():
        db.create_all()

    return app
