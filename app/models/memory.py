from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import relationship
from flask_login import UserMixin

db = SQLAlchemy()

memory_bp = Blueprint('memory', __name__)


class Memory(db.Model):
    __tablename__ = 'test'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String(255), nullable=False)
    user_message = db.Column(db.String(255), nullable=False)
    llm_response = db.Column(db.String(255), nullable=False)
    conversations_summary = db.Column(db.String, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Add a foreign key relationship to the User model
    owner = relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f"<Memory id={self.id}>"


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User id={self.id}, email='{self.email}'>"

    # Flask-Login required methods
    def get_id(self):
        return str(self.id)
