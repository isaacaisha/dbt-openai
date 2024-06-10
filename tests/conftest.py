from datetime import datetime
import pytest
from app import create_app, User
from app.database import db, user, password, host, port, database
from app.memory import Memory


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


@pytest.fixture
def db_session(app):
    """A database session for testing."""
    with app.app_context():
        yield db.session


@pytest.fixture(scope='module')
def init_database(app):
    with app.app_context():
        yield db


def create_user(email, password, name='User'):
    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user


def create_conversation(user, message, response):
    conversation = Memory(user_name=user.name, user_message=message, llm_response=response,
                          conversations_summary=f'Summary for {user.name}', owner_id=user.id, created_at=datetime.now())
    db.session.add(conversation)
    db.session.commit()
    return conversation


def login(client, email, password):
    try:
        response = client.post('/login', data=dict(email=email, password=password), follow_redirects=True)
        if response.status_code == 200:
            print(f"User {email} logged in successfully.")
        else:
            print(f"Failed to log in user {email}. Status code: {response.status_code}")
        return response
    except Exception as e:
        print(f"An error occurred while logging in user {email}: {str(e)}")
        return None


def logout(client):
    return client.get('/logout', follow_redirects=True)


@pytest.fixture(scope='module')
def user1(init_database):
    return create_user('user1@example.com', 'password1', 'user1')


@pytest.fixture(scope='module')
def user2(init_database):
    return create_user('user2@example.com', 'password2', 'user2')


@pytest.fixture(scope='module')
def conversation_user1(user1):
    return create_conversation(user1, 'Message from user1', 'Response for user1')


@pytest.fixture(scope='module')
def conversation_user2(user2):
    return create_conversation(user2, 'Message from user2', 'Response for user2')
