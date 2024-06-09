import pytest
from app import create_app
from app.database import db, user, password, host, port, database


TEST_DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}_test"


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = TEST_DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test_secret_key'
    WTF_CSRF_ENABLED = False


@pytest.fixture(scope='module')
def app():
    app = create_app(config=TestConfig.__dict__)
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture(scope='module')
def client(app):
    return app.test_client()
