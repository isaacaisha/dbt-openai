from flask import url_for
from flask_login import login_user
from tests.conftest import create_conversation, login


# URL: pytest -v -s -x tests/test_llm_convers.py

def test_get_all_conversations_with_data(client, user1):
    with client.application.test_request_context():
        # Log in the user
        login_response = login(client, user1.email, 'password1')
        assert login_response.status_code == 200, "Login failed, expected status code 200"
    
        # Log in the test user
        login_user(user1)
        
        assert login_response.status_code == 200
        assert b'Welcome Back' in login_response.data  # Verify successful login

        # Create a conversation
        create_conversation(user1, 'Hello', 'Hi there')

        # Access the get_all_conversations endpoint
        response = client.get(url_for('llm_conversation.get_all_conversations'))
        assert response.status_code == 200
        assert b'Your Conversations' in response.data


def test_convers_head_tail(client):
    with client.application.test_request_context():
        response = client.get(url_for('llm_conversation.convers_head_tail'))
        assert response.status_code == 200
        assert b'Conversation Not Found' not in response.data
        assert b'Your Firtest & Latest Conversations' in response.data  


def test_show_story(client):
    with client.application.test_request_context():
        response = client.get(url_for('llm_conversation.show_story'))
        assert response.status_code == 200
        assert b'Recents Conversation History' in response.data


def test_update_like(client, user1, conversation_user1):
    with client.application.test_request_context():
        login(client, user1.email, 'password1')
        conversation_id = conversation_user1.id
        response = client.post(url_for('llm_conversation.update_like', conversation_id=conversation_id), json={'liked': 1})
        assert response.status_code == 200
        assert b'Liked status updated successfully' in response.data


def test_get_conversations_jsonify(client):
    with client.application.test_request_context():
        response = client.get(url_for('llm_conversation.get_conversations_jsonify'))
        assert response.status_code == 200
        assert b'Show Database Memory' in response.data  
    