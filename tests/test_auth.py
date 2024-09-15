from flask import current_app, url_for
from app import User
from app.routes.auth import send_reset_email, s
from tests.conftest import db
import pytest

# URL: pytest -v -s -x tests/test_auth.py

def register_user(client, user_data):
    """Helper function to register a user."""
    return client.post(url_for('auth.register'), data=user_data, follow_redirects=True)

def login_user(client, login_data):
    """Helper function to login a user."""
    return client.post(url_for('auth.login'), data=login_data, follow_redirects=True)

@pytest.mark.parametrize("user_data, expected_status, expected_message", [
    ({'email': 'newuser@example.com', 'name': 'New User', 'password': 'password123', 'confirm_password': 'password123'}, 200, b"Login"),
    ({'email': 'newuser@example.com', 'name': 'New User', 'password': 'password123', 'confirm_password': 'password456'}, 200, b"Passwords do not match")
])
def test_register(client, user_data, expected_status, expected_message):
    with client.application.test_request_context():
        response = register_user(client, user_data)
        assert response.status_code == expected_status
        assert expected_message in response.data

def test_register_email_exists(client, user1):
    with client.application.test_request_context():
        user_data = {'email': user1.email, 'name': user1.name, 'password': 'password1', 'confirm_password': 'password1'}
        response = register_user(client, user_data)
        assert response.status_code == 200
        assert b"Welcome Back" in response.data

def test_login(client, user1):
    with client.application.test_request_context():
        login_data = {'email': user1.email, 'password': user1.password}
        response = login_user(client, login_data)
        assert response.status_code == 200
        assert b"Welcome Back" in response.data

def test_logout(client):
    with client.application.test_request_context():
        response = client.get(url_for('auth.logout'), follow_redirects=True)
        assert response.status_code == 200
        assert b"To Use All Features" in response.data 

def test_send_reset_email(client):
    with client.application.test_request_context():
        user = User(email='Reset_email@example.com', name='Reset_email User', password='password123')
        db.session.add(user)
        db.session.commit()

        mail = current_app.extensions['mail']

        with mail.record_messages() as outbox:
            send_reset_email(user, 'token')
            assert len(outbox) == 1
            assert outbox[0].subject == 'Password Reset Request'
            assert outbox[0].recipients == ['Reset_email@example.com']

def test_reset_with_token(client):
    with client.application.test_request_context():
        # Generate a token for testing
        token = s.dumps('Reset_email@example.com', salt='password-reset-salt')
        response = client.get(url_for('auth.reset_with_token', token=token))
        assert response.status_code == 200
        assert b"Reset Password Token" in response.data  
