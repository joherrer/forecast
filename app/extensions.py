from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from flask_session import Session

# Shared extension instances are initialized in create_app().
db = SQLAlchemy()
flask_session = Session()
csrf = CSRFProtect()
