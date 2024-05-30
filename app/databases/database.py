import os
from flask import Blueprint
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


database_bp = Blueprint('database', __name__)

load_dotenv()

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{os.environ['USER']}:{os.environ['PASSWORD']}@"
    f"{os.environ['HOST']}:{os.environ['PORT_DB']}/{os.environ['DATABASE']}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
Base.metadata.create_all(bind=engine)

class DatabaseSession:
    def __enter__(self):
        self.db = SessionLocal()
        return self.db

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()


def get_db():
    return DatabaseSession()
