import os

from . import create_app


def main():
    app = create_app()
    app.run(debug=os.getenv("FLASK_DEBUG", "0") == "1")


if __name__ == "__main__":
    main()
