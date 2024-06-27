# from flask import url_for
# from flask_login import login_user
# from tests.conftest import login
# 
# 
# # URL: pytest -v -s -x tests/test_conversation_interface.py
# 
# def test_save_to_database(client, user1, db_session):
#     with client.application.test_request_context():
#         # Log in the user
#         login_response = login(client, user1.email, 'password1')
#         assert login_response.status_code == 200, "Login failed, expected status code 200"
#     
#         # Log in the test user
#         login_user(user1)
#     
#         user_messages = [
#             "how are you doing?",
#             # "what is your name?",
#             # "who made you?",
#             # "how do you say, hello how are you in Arabic?",
#             # "what can you tell me about the Country named Mali?",
#             # "what can you tell me about the Soninké people from Mali?",
#         ]
#     
#         for user_message in user_messages:
#             conversation_data = {
#                 "prompt": user_message
#             }
#     
#             with client.session_transaction() as sess:
#                 sess['user_id'] = user1.id
#     
#             response = client.post(url_for('conversation_interface.interface_answer'), data=conversation_data)
#     
#             # Assert that the response status code is 200 OK
#             assert response.status_code == 200, f"Expected status code 200 but got {response.status_code}"
#     
#             # Deserialize the response JSON
#             response_data = response.get_json()
#     
#             # Assert the response structure
#             assert "answer_text" in response_data
#             assert "answer_audio_path" in response_data
#             assert response_data["answer_text"] != ""  # Ensure answer_text is not empty
#             assert response_data["answer_audio_path"] != ""  # Ensure answer_audio_path is not empty
# 