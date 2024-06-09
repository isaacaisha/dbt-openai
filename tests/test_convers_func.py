from datetime import datetime
from flask import url_for
from flask_login import login_user, logout_user
from app.memory import Memory
from app import User
from tests.config_test import app, db


# URL: pytest -v -s -x tests/test_convers_func.py

def test_unauthenticated_delete_conversation(client):
    response = client.post(url_for('conversation_function.delete_conversation'), data={'conversation_id': 1})
    assert response.status_code == 200  
    assert b'New session' in response.data


def test_unauthenticated_get_conversation(client):
    response = client.get(url_for('conversation_function.get_conversation', conversation_id=1))
    assert response.status_code == 200
    assert b'New session' in response.data


# Test the select_conversation route
def test_select_conversation(client):
    response = client.post(url_for('conversation_function.select_conversation'), data={'conversation_id': 1})
    assert response.status_code == 302  # Expecting a redirect
    expected_path = url_for('conversation_function.get_conversation', conversation_id=1)
    assert response.location.endswith(expected_path)


# Test the get_conversation route
def test_get_conversation(client):
    # Create a test user
    test_user = User(name='Test User', email='test@example.com', password='testpassword')
    db.session.add(test_user)
    db.session.commit()

    # Create a test conversation associated with the test user
    conversation = Memory(user_name=test_user.name, user_message='Test message', llm_response='Test response',
                          conversations_summary='Test summary', owner=test_user, created_at=datetime.now())
    db.session.add(conversation)
    db.session.commit()

    # Log in the test user
    login_user(test_user)

    # Now, the client is logged in as the test user
    response = client.get(url_for('conversation_function.get_conversation', conversation_id=1))
    assert response.status_code == 200
    assert b'Conversation Not Found' not in response.data
    assert b'Forbidden' not in response.data
    assert b'Test User' in response.data  # Check if user_name is present in the response


# Test the delete_conversation route
def test_delete_conversation(client):
    response = client.post(url_for('conversation_function.delete_conversation'), data={'conversation_id': 1})
    assert response.status_code == 302  # Expecting a redirect
    assert response.location == url_for('conversation_function.delete_conversation')


def test_access_conversation_or_delete_not_belonging_to_user(client):
    # Create two users
    user1 = User(name='User One', email='user1@example.com', password='password1')
    user2 = User(name='User Two', email='user2@example.com', password='password2')
    db.session.add_all([user1, user2])
    db.session.commit()

    # Create a conversation for user1
    conversation = Memory(user_name=user1.name, user_message='Message from user1', llm_response='Response for user1',
                          conversations_summary='Summary for user1', owner=user1, created_at=datetime.now())
    db.session.add(conversation)
    db.session.commit()

    # Log in as user2
    login_user(user2)

    # Test for Accessing a Conversation That Doesn't Belong to the User
    get_response = client.get(url_for('conversation_function.get_conversation', conversation_id=conversation.id))
    # Verify that user2 is denied access
    assert get_response.status_code == 200  
    assert b'Sorry Forbidden' in get_response.data in get_response.data  
    
    # Test for Deleting a Conversation That Doesn't Belong to the User
    delete_response = client.post(url_for('conversation_function.delete_conversation'), data={'conversation_id': conversation.id})
    # Verify that user2 is denied deletion
    assert get_response.status_code == 200  
    assert b'Sorry Forbidden' in delete_response.data in delete_response.data

    logout_user()
