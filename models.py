from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.sql.sqltypes import TIMESTAMP
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class Memory(db.Model):
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True, nullable=False)
    user_message = Column(String, nullable=False)
    llm_response = Column(String, nullable=False)
    conversations_summary = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    owner_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    def __repr__(self):
        return f"<Memory {self.id}, user_message='{self.user_message}', llm_response='{self.llm_response}'>"


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.id}, email='{self.email}', password='{self.password}>"

    # Flask-Login required methods
    def get_id(self):
        return str(self.id)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False
