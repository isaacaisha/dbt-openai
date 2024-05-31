import os
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv


database_bp = Blueprint('database', __name__)

load_dotenv()

# Read environment variables
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
database = os.getenv('DB_NAME')


SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
)

# Initialize SQLAlchemy
db = SQLAlchemy()

def init_app(app):
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

