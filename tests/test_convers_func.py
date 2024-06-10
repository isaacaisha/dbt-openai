from flask import url_for
from flask_login import login_user, logout_user
from tests.conftest import db, create_user, create_conversation


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
    test_user = create_user('test@example.com', 'testpassword', 'Test User')

    # Create a test conversation associated with the test user
    conversation = create_conversation(test_user, 'Test message', 'Test response')

    # Log in the test user
    login_user(test_user)

    # Now, the client is logged in as the test user
    response = client.get(url_for('conversation_function.get_conversation', conversation_id=conversation.id))
    assert response.status_code == 200
    assert b'Conversation Not Found' not in response.data
    assert b'Forbidden' not in response.data
    assert b'Test User' in response.data  # Check if user_name is present in the response


# Test the delete_conversation route
def test_delete_conversation(client):
    # Create a test user
    test_user = create_user('delete@example.com', 'deletepassword', 'Delete User')

    # Create a test conversation associated with the test user
    conversation = create_conversation(test_user, 'Delete message', 'Delete response')

    # Log in the test user
    login_user(test_user)

    # Attempt to delete the conversation
    response = client.post(url_for('conversation_function.delete_conversation'), data={'conversation_id': conversation.id})
    assert response.status_code == 302  # Expecting a redirect
    assert response.location == url_for('conversation_function.delete_conversation')


def test_access_conversation_or_delete_not_belonging_to_user(client, user1, user2):
    # Create a conversation for user1
    conversation = create_conversation(user1, 'Message from user1', 'Response for user1')

    # Log in as user2
    login_user(user2)

    # Test for Accessing a Conversation That Doesn't Belong to the User
    get_response = client.get(url_for('conversation_function.get_conversation', conversation_id=conversation.id))
    # Verify that user2 is denied access
    assert get_response.status_code == 200  
    assert b'Sorry Forbidden' in get_response.data

    # Test for Deleting a Conversation That Doesn't Belong to the User
    delete_response = client.post(url_for('conversation_function.delete_conversation'), data={'conversation_id': conversation.id})
    # Verify that user2 is denied deletion
    assert delete_response.status_code == 200  
    assert b'Sorry Forbidden' in delete_response.data

    logout_user()
