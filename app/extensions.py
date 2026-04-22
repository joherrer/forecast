from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Shared extension instances are initialized in create_app().
db = SQLAlchemy()
flask_session = Session()
csrf = CSRFProtect()
