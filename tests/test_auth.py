from flask import current_app, url_for
from app import User
from app.routes.auth import send_reset_email, s
from tests.config_test import app, db


def test_register_success(client):
    response = client.post(url_for('auth.register'), data={
        'email': 'newuser@example.com',
        'name': 'New User',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data  # The redirect goes to login page


def test_register_passwords_do_not_match(client):
    response = client.post(url_for('auth.register'), data={
        'email': 'newuser@example.com',
        'name': 'New User',
        'password': 'password123',
        'confirm_password': 'password456'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Passwords do not match" in response.data


def test_register_email_exists(client):
    existing_user = User(email='existinguser@example.com', name='Existing User', password='password123')
    db.session.add(existing_user)
    db.session.commit()

    response = client.post(url_for('auth.register'), data={
        'email': 'existinguser@example.com',
        'name': 'New User',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome Back" in response.data


def test_login(client):
    response = client.post(url_for('auth.login'), data={
        'email': 'user@example.com',
        'password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome Back" in response.data 

def test_logout(client):
    response = client.get(url_for('auth.logout'), follow_redirects=True)
    assert response.status_code == 200
    assert b"Register & Login" in response.data 


def test_send_reset_email(client):
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
    # Generate a token for testing
    token = s.dumps('Reset_email@example.com', salt='password-reset-salt')
    response = client.get(url_for('auth.reset_with_token', token=token))
    assert response.status_code == 200
    assert b"Reset Password Token" in response.data  
