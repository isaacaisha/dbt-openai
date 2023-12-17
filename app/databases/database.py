from flask import Blueprint
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


database_bp = Blueprint('database', __name__)

load_dotenv()

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{os.environ['user']}:{os.environ['password']}@"
    f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class DatabaseSession:
    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


def get_db():
    return DatabaseSession()
