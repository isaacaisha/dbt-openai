# memory.py

from flask import Blueprint
from sqlalchemy import func
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from app.database import db


memory_bp = Blueprint('memory', __name__)


class Memory(db.Model):
    __tablename__ = 'memories'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String(73), nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    llm_response = db.Column(db.Text, nullable=False)
    conversations_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    liked = db.Column(db.Integer, default=0)
    embedding = db.Column(db.LargeBinary, nullable=True)

    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Add a foreign key relationship to the User model
    owner = relationship('User', foreign_keys=[owner_id])

    def __repr__(self):
        return f"<Memory id={self.id}>"


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(73), nullable=False)
    email = db.Column(db.String(73), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    # Define the relationship to the BlogPost model
    blog_posts = relationship('BlogPost', back_populates='user', cascade='all, delete')

    # Define the relationship to the PortfolioReview model
    website_reviews = relationship('WebsiteReview', back_populates='user', cascade='all, delete')

    def __repr__(self):
        return f"<User id={self.id}, email='{self.email}'>"

    # Flask-Login required methods
    def get_id(self):
        return str(self.id)


class Theme(db.Model):
    __tablename__ = 'themes'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    theme_name = db.Column(db.String(73), nullable=False)

    def __repr__(self):
        return f"<Theme id={self.id}, theme_name='{self.theme_name}'>"


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    value = db.Column(db.String(999991), nullable=False)
    date = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    user = db.Column(db.String(999991), nullable=False)
    theme = db.Column(db.String(999991), nullable=False)

    def __repr__(self):
        return f"<Message id={self.id}, user='{self.user}'>"

    def get_id(self):
        return str(self.id)


class MemoryTest(db.Model):
    __tablename__ = 'memories_test'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_message = db.Column(db.Text, nullable=False)
    llm_response = db.Column(db.Text, nullable=False)
    conversations_summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Memory id={self.id}>"
    

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    youtube_title = db.Column(db.String(255), nullable=False)
    youtube_link = db.Column(db.String(255), nullable=False)
    generated_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)

    # Define the relationship to the User model
    user = relationship('User', back_populates='blog_posts')

    def __repr__(self):
        return f"<BlogPost id={self.id}, title='{self.youtube_title}'>"
    

class WebsiteReview(db.Model):
    __tablename__ = 'website_reviews'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    site_url = db.Column(db.String(9991), nullable=False)
    site_image_url = db.Column(db.Text, nullable=False)
    feedback = db.Column(db.Text, default=None, nullable=False)
    liked = db.Column(db.Integer, default=0)
    user_rating = db.Column(db.String(5))
    created_at = db.Column(db.TIMESTAMP(timezone=True), default=func.now(), nullable=False)
    
    # Define the relationship to the User model
    user = relationship('User', back_populates='website_reviews')

    def __repr__(self):
        return f"<WebsiteReview id={self.id}, title='{self.site_url}'>"
    