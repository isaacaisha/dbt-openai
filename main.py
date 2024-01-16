import os
import warnings

from dotenv import load_dotenv, find_dotenv

from app import create_app

from app.routes.auth import register as auth_register, login as auth_login, logout as auth_logout

from app.routes.process_home_conversation import (home as process_home_llm, home_answer as process_answer_home,
                                                  home_serve_audio as process_home_audio_llm)

from app.routes.process_interface_conversation import (conversation_interface as process_interface_llm,
                                                       generate_conversation_context as process_context_conversation,
                                                       handle_llm_response as process_response_llm,
                                                       interface_answer as process_answer_interface,
                                                       save_to_database as process_database,
                                                       interface_serve_audio as process_interface_audio_llm)

from app.routes.conversation_functionality import (select_conversation as conversation_selected,
                                                   get_conversation as access_conversation,
                                                   delete_conversation as conversation_deleted)

from app.routes.llm_conversation import (show_story as process_history, get_all_conversations as all_conversation_llm,
                                         get_conversations_jsonify as conversation_jsonify_llm)

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = create_app()


# ------------------------------------------ @app.routes --------------------------------------------------------------#
@app.route('/register', methods=['GET', 'POST'])
def register():
    return auth_register()


@app.route('/login', methods=['GET', 'POST'])
def login():
    return auth_login()


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    return auth_logout()


@app.route('/', methods=['GET', 'POST'])
def home():
    return process_home_llm()


@app.route('/home/answer', methods=['POST'])
def home_answer():
    return process_answer_home()


@app.route('/home-audio')
def home_serve_audio():
    return process_home_audio_llm()


@app.route('/conversation-interface', methods=['GET', 'POST'])
def conversation_interface():
    return process_interface_llm()


def generate_conversation_context(user_input, user_conversations):
    return process_context_conversation(user_input, user_conversations)


def handle_llm_response(user_input, conversation_context):
    return process_response_llm(user_input, conversation_context)


@app.route('/interface/answer', methods=['POST'])
def interface_answer():
    return process_answer_interface()


@app.route('/save-to-database', methods=['POST'])
def save_to_database(user_input, response):
    return process_database(user_input, response)


@app.route('/interface-audio')
def interface_serve_audio():
    return process_interface_audio_llm()


@app.route('/show-history')
def show_story():
    return process_history()


@app.route("/get-all-conversations")
def get_all_conversations():
    return all_conversation_llm()


@app.route('/select-conversation-id', methods=['GET', 'POST'])
def select_conversation():
    return conversation_selected()


@app.route('/conversation/<int:conversation_id>')
def get_conversation(conversation_id):
    return access_conversation(conversation_id)


@app.route('/delete-conversation', methods=['GET', 'POST'])
def delete_conversation():
    return conversation_deleted()


@app.route("/api/conversations-jsonify")
def get_conversations_jsonify():
    return conversation_jsonify_llm()


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    home_temp_audio_file = 'home_temp_audio.mp3'
    if os.path.exists(home_temp_audio_file):
        os.remove(home_temp_audio_file)

    interface_temp_audio_file = 'interface_temp_audio.mp3'
    if os.path.exists(interface_temp_audio_file):
        os.remove(interface_temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
