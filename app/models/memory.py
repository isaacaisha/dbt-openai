from flask import Blueprint
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime


memory_bp = Blueprint('memory', __name__)

db = SQLAlchemy()


class Memory(db.Model):
    __tablename__ = 'test'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String, nullable=False)
    user_message = db.Column(db.String, nullable=False)
    llm_response = db.Column(db.String, nullable=False)
    conversations_summary = db.Column(db.String, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Add a foreign key relationship to the User model
    owner = relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f"<Memory id={self.id}>"


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<User id={self.id}, email='{self.email}'>"

    # Flask-Login required methods
    def get_id(self):
        return str(self.id)

    # @property
    # def is_authenticated(self):
    #     return True
#
    # @property
    # def is_active(self):
    #     return True
#
    # @property
    # def is_anonymous(self):
    #     return False
#