import os

import flask_wtf
import openai
import secrets
import warnings
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv, find_dotenv
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from datetime import timedelta, datetime
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from werkzeug.exceptions import InternalServerError, BadRequest

from app.routes.auth import register as auth_register, login as auth_login, logout as auth_logout
from app.databases.database import get_db
from app.models.memory import Memory, db, User
from app.errors_configuration.confi_errors import configure_error_handlers as configure_errors
from app.routes.conversation import (home as home_conversation, conversation_answer as answer_conversation,
                                     show_story as show_story_conversation, answer as siisi_respone,
                                     serve_audio as audio_response, get_all_conversations as whole_conversations,
                                     select_conversation as conversation_selected,
                                     get_conversation as id_conversation, delete_conversation as conversation_deleted,
                                     get_conversations_jsonify as jsonify_conversation)

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__, template_folder='templates')

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)


def initialize_app():
    CSRFProtect(app)
    Bootstrap(app)
    CORS(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        if user_id is not None and user_id.isdigit():
            # Check if the user_id is a non-empty string of digits
            return User.query.get(int(user_id))
        else:
            return None

    try:
        openai_api_key = os.environ['OPENAI_API_KEY']
    except KeyError:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    # Set the OpenAI API key
    openai.api_key = openai_api_key

    # Generate a random secret key
    secret_key = secrets.token_hex(19)
    # Set it as the Flask application's secret key
    app.secret_key = secret_key


initialize_app()


def configure_app():
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['WTF_CSRF_ENABLED'] = True


configure_app()


def configure_database():
    app.config[
        'SQLALCHEMY_DATABASE_URI'] = (f"postgresql://{os.environ['user']}:{os.environ['password']}@"
                                      f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()


configure_database()

# Fetch memories from the database
with get_db() as db:
    # memories = db.query(Memory).all()
    test = db.query(Memory).all()


# -------------------------------------- @app.errorhandler functions ----------------------------------------------#
@app.errorhandler(InternalServerError)
def handle_internal_server_error(err):
    # Get the URL of the request that caused the error
    referring_url = request.referrer
    flash(f"RETRY (InternalServerError) ¡!¡")
    print(f"InternalServerError ¡!¡ Unexpected {err=}, {type(err)=}"

    # Redirect the user back to the page that produced the error, or a default page if the referrer is not available
    return redirect(referring_url or url_for('authentication_error'))  # , 500

@app.errorhandler(BadRequest)
def handle_bad_request(err):
    # Get the URL of the request that caused the error
    referring_url = request.referrer
    flash(f"RETRY (BadRequest) ¡!¡")
    print(f"BadRequest ¡!¡ Unexpected {err=}, {type(err)=}")

     # Redirect the user back to the page that produced the error, or a default page if the referrer is not available
    return redirect(referring_url or url_for('authentication_error'))  # , 400

@app.errorhandler(flask_wtf.csrf.CSRFError)
def handle_csrf_error(err):
    # Get the URL of the request that caused the error
    referring_url = request.referrer
    flash(f"RETRY (CSRFError) ¡!¡")
    print(f"CSRFError ¡!¡ Unexpected {err=}, {type(err)=}")

    # Redirect the user back to the page that produced the error, or a default page if the referrer is not available
    return redirect(referring_url or url_for('authentication_error'))  # , 401


# ------------------------------------------ @app.routes --------------------------------------------------------------#
@app.route('/configure-error-handlers', methods=['GET', 'POST'])
def configure_error_handlers():
    return configure_errors()


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
    return home_conversation()


@app.route('/conversation-answer', methods=['GET', 'POST'])
def conversation_answer():
    return answer_conversation()


@app.route('/answer', methods=['GET', 'POST'])
def answer():
    return siisi_respone()


@app.route('/audio', methods=['GET', 'POST'])
def serve_audio():
    return audio_response()


@app.route('/show-history', methods=['GET', 'POST'])
def show_story():
    return show_story_conversation()


@app.route('/get-all-conversations', methods=['GET', 'POST'])
def get_all_conversations():
    return whole_conversations()


@app.route('/select-conversation', methods=['GET', 'POST'])
def select_conversation():
    return conversation_selected()


@app.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
def get_conversation(conversation_id):
    return id_conversation(conversation_id=conversation_id)


@app.route('/delete_conversation', methods=['GET', 'POST'])
def delete_conversation():
    return conversation_deleted()


@app.route('/api/conversations-jsonify', methods=['GET', 'POST'])
def get_conversations_jsonify():
    return jsonify_conversation()


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
