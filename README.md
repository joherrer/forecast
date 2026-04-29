# Gold Coast Surf Forecast
![Python Version](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/Flask-%E2%9C%94-green)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-%E2%9C%94-green)

![Homepage Screenshot](static/images/homepage/homepage.jpeg)

## 🌊 Overview
Gold Coast Surf Forecast is a web application built using Python and Flask to offer real-time updates on surf conditions
across all the prominent surf spots along the Gold Coast. This platform is designed to provide surfers with accurate
and timely surf forecasts to enhance their surfing experience.

## ✨ Features
- Real-time surf condition updates.
- User authentication and account management.
- Save and manage favorite surf spots.
- Responsive and user-friendly design optimized for desktops, tablets, and mobile phones.

## 🖥️ Technology Stack
- **Front-End**: HTML, CSS, Jinja2
- **Back-End**: Python, Flask
- **Database**: SQLite / PostgreSQL
- **ORM**: SQLAlchemy
- **Session Management**: Flask-Session
- **Security**: Werkzeug, Flask-WTF

## 🏗️ Project Structure

```text
app/
├── __init__.py
├── __main__.py
├── data.py
├── extensions.py
├── helpers.py
├── models.py
└── routes.py
static/
├── icons/
├── images/
├── main.js
└── styles.css
templates/
├── favorites.html
├── forecast.html
├── index.html
├── layout.html
├── login.html
├── register.html
└── spots.html
tests/
├── conftest.py
├── test_app_integration.py
├── test_external_api.py
└── test_helpers.py
Dockerfile
Procfile
docker-compose.yml
pytest.ini
README.md
requirements.txt
wsgi.py
```

## 🏄 Usage
1. Register a new account or log in if you already have one.
2. Browse surf spots and save your favorites.
3. View detailed surf conditions of your favorite spots from your personalized favorites page.

## 🛠️ Development Setup

### Prerequisites
- Python 3.11+
- Flask
- SQLAlchemy

### Installation
1. Clone the repository:

    ```bash
    git clone https://github.com/joherrer/forecast.git
    ```

2. Navigate to the project directory:

    ```bash
    cd forecast
    ```

3. Create a virtual environment (optional but recommended):

    ```bash
    python3 -m venv venv
    ```

4. Activate the virtual environment:

    ```bash
    # Linux/macOS
    source venv/bin/activate
    ```

    ```bash
    # Windows
    venv\Scripts\activate
    ```

5. Install the required packages:

    ```bash
    pip install -r requirements.txt
    ```

6. Configure environment variables:

    ```bash
    touch .env
    ```

    Add at least:

    ```env
    SECRET_KEY=your-random-key
    SESSION_COOKIE_SECURE=0
    FLASK_DEBUG=0
    ```

7. Start the Flask application:

    ```bash
    python3 -m app
    ```

8. Open your browser and go to `http://127.0.0.1:5000`.

## 🧪 Testing
Run the standard test suite with:

```bash
venv/bin/python -m pytest
```

Run the external API smoke test with:

```bash
RUN_EXTERNAL_API_TESTS=1 venv/bin/python -m pytest -m external
```

## 🐳 Docker

### Prerequisites
- Docker
- Docker Compose

### Run with Docker
1. Make sure your `.env` file includes:

    ```env
    SECRET_KEY=your-random-key
    SESSION_COOKIE_SECURE=0
    FLASK_DEBUG=0
    POSTGRES_DB=forecast
    POSTGRES_USER=forecast_user
    POSTGRES_PASSWORD=your-postgres-password
    ```

2. Build and start the containers:

    ```bash
    docker compose up --build
    ```

3. Open your browser and go to `http://127.0.0.1:5000`.

## 🚀 CI/CD Pipeline
The project uses GitHub Actions for continuous integration and deployment:

- **CI** runs on pull requests and pushes to `main`, builds the Docker Compose services, and runs the test suite inside the web container.
- **Deployment** runs after a successful CI workflow on `main`, connects to an AWS EC2 instance over SSH, pulls the latest code, and restarts the app with Docker Compose.

## 🗒️ Notes
- The app uses SQLite for local development and PostgreSQL when running with Docker.

- Flask-Session provides server-side session management.

- Werkzeug handles secure password hashing, and Flask-WTF provides CSRF protection for form submissions.

- The data is fetched from an external API (Surfline).

## 📜 License
Copyright (c) 2025 Jose Herrera. All rights reserved.
