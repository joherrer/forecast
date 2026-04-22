from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import relationship

from .extensions import db


class Users(db.Model):
    # Store account credentials and the user's saved spots.
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    favorites = relationship("Favorites", back_populates="user")


class Favorites(db.Model):
    # Each user/spot pair should only appear once.
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "spot", name="uq_favorites_user_spot"),)
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    spot = db.Column(db.String(80), nullable=False)
    user = relationship("Users", back_populates="favorites")
