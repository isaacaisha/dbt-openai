import os
import flask_wtf
import openai
import json
import secrets
import warnings
import pytz
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from werkzeug.exceptions import BadRequest, InternalServerError
from datetime import datetime, timedelta
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory

from app.routes.auth import register as auth_register, login as auth_login, logout as auth_logout
from app.databases.database import get_db
from app.models.memory import Memory, db, User
from app.forms.app_forms import ConversationIdForm, DeleteForm
from app.routes.conversation import (home as home_conversation, conversation_answer as answer_conversation,
                                     show_story as show_story_conversation,
                                     get_all_conversations as whole_conversations, get_conversation as id_conversation,
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


def configure_error_handlers():
    # -------------------------------------- @app.errorhandler functions ----------------------------------------------#
    @app.errorhandler(InternalServerError)
    def handle_internal_server_error(err):
        # Get the URL of the request that caused the error
        referring_url = request.referrer
        flash(f"RETRY (InternalServerError) ¡!¡")
        print(f"InternalServerError ¡!¡ Unexpected {err=}, {type(err)=}")

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

    # -------------------------------------- @app.errorhandler pages --------------------------------------------------#
    @app.route('/authentication-error', methods=['GET', 'POST'])
    def authentication_error():
        return render_template('authentication-error.html', current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y")), 401

    @app.route('/conversation-forbidden', methods=['GET', 'POST'])
    def conversation_forbidden():
        # Retrieve the selected conversation ID from the query parameter
        selected_conversation_id = request.args.get('conversation_id')

        return render_template('conversation-forbidden.html', current_user=current_user,
                               conversation_id=selected_conversation_id,
                               date=datetime.now().strftime("%a %d %B %Y")), 403

    @app.route('/conversation-not-found', methods=['GET', 'POST'])
    def conversation_not_found():
        # Retrieve the selected conversation ID from the query parameter
        selected_conversation_id = request.args.get('conversation_id')

        return render_template('conversation-not-found.html', current_user=current_user,
                               conversation_id=selected_conversation_id,
                               date=datetime.now().strftime("%a %d %B %Y")), 404

    @app.route('/conversation-delete-forbidden', methods=['GET', 'POST'])
    def conversation_delete_forbidden():
        # Retrieve the selected conversation ID from the query parameter
        selected_conversation_id = request.args.get('conversation_id')

        return render_template('conversation-delete-forbidden.html', current_user=current_user,
                               conversation_id=selected_conversation_id,
                               date=datetime.now().strftime("%a %d %B %Y")), 403

    @app.route('/conversation-delete-not-found', methods=['GET', 'POST'])
    def conversation_delete_not_found():
        # Retrieve the selected conversation ID from the query parameter
        selected_conversation_id = request.args.get('conversation_id')

        return render_template('conversation-delete-not-found.html', current_user=current_user,
                               conversation_id=selected_conversation_id,
                               date=datetime.now().strftime("%a %d %B %Y")), 404


configure_error_handlers()


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
    return home_conversation()


@app.route('/conversation-answer', methods=['GET', 'POST'])
def conversation_answer():
    return answer_conversation()


@app.route('/show-history', methods=['GET', 'POST'])
def show_story():
    return show_story_conversation()


@app.route('/get-all-conversations', methods=['GET', 'POST'])
def get_all_conversations():
    return whole_conversations()


@app.route('/conversation/<int:conversation_id>', methods=['GET', 'POST'])
def get_conversation(conversation_id):
    return id_conversation(conversation_id=conversation_id)


@app.route('/api/conversations-jsonify', methods=['GET', 'POST'])
def get_conversations_jsonify():
    return jsonify_conversation()


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']

    try:
        if current_user.is_authenticated:

            # Get conversations only for the current user
            user_conversations = Memory.query.filter_by(owner_id=current_user.id).all()

            # Create a list of JSON strings for each conversation
            conversation_strings = [memory.conversations_summary for memory in user_conversations]

            # Combine the first 1 and last 9 entries into a valid JSON array
            qdocs = f"[{','.join(conversation_strings[-3:])}]"

            # Convert 'created_at' values to string
            created_at_list = [str(memory.created_at) for memory in user_conversations]

            conversation_context = {
                "created_at": created_at_list[-3:],
                "conversations": qdocs,
                "user_name": current_user.name,
                "user_message": user_message,
            }

            # Call llm ChatOpenAI
            response = conversation.predict(input=json.dumps(conversation_context))
            print(f'conversation_context:\n{conversation_context}\n')

            # Check if the response is a string, and if so, use it as the assistant's reply
            if isinstance(response, str):
                assistant_reply = response
            else:
                # If it's not a string, access the assistant's reply appropriately
                if isinstance(response, dict) and 'choices' in response:
                    assistant_reply = response['choices'][0]['message']['content']
                else:
                    assistant_reply = None

            # Convert the text response to speech using gTTS
            tts = gTTS(assistant_reply)

            # Create a temporary audio file
            audio_file_path = 'temp_audio.mp3'
            tts.save(audio_file_path)

            memory_summary.save_context({"input": f"{user_message}"}, {"output": f"{response}"})
            conversations_summary = memory_summary.load_memory_variables({})
            conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

            current_time = datetime.now(pytz.timezone('Europe/Paris'))

            # Create a new Memory object with the data
            new_memory = Memory(
                user_name=current_user.name,
                owner_id=current_user.id,
                user_message=user_message,
                llm_response=assistant_reply,
                conversations_summary=conversations_summary_str,
                created_at=current_time
            )
            # Add the new memory to the session
            db.add(new_memory)
            # Commit changes to the database
            db.commit()
            db.refresh(new_memory)
            db.rollback()  # Rollback in case of commit failure

            # Convert current_user to JSON-serializable format
            current_user_data = {
                "id": current_user.id,
                "username": current_user.name,
                "user_email": current_user.email,
                "user_password": current_user.password,
            }

            print(f'User Name: {current_user.name} 😎')
            print(f'User ID:{current_user.id} 😝')
            print(f'User Input: {user_message} 😎')
            print(f'LLM Response:{assistant_reply} 😝\n')

            # Return the response as JSON, including both text and the path to the audio file
            return jsonify({
                "current_user": current_user_data,
                "answer_text": assistant_reply,
                "answer_audio_path": audio_file_path,
                "memory_id": new_memory.id
            })
        else:
            return redirect(url_for('authentication_error'))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    # Check if the file exists
    if not os.path.exists(audio_file_path):
        abort(404, description=f"Audio file not found")
    return send_file(audio_file_path, as_attachment=True)


@app.route('/select-conversation-id', methods=['GET', 'POST'])
def select_conversation():
    form = ConversationIdForm()

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}")

            # Retrieve the selected conversation ID
            selected_conversation_id = form.conversation_id.data

            # Construct the URL string for the 'get_conversation' route
            url = f'/conversation/{selected_conversation_id}'

            return redirect(url)

        else:
            return render_template('conversation-by-id.html', form=form, current_user=current_user,
                                   date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/delete-conversation', methods=['GET', 'POST'])
def delete_conversation():
    form = DeleteForm()

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}")

            # Get the conversation_id from the form
            conversation_id = form.conversation_id.data

            # Query the database to get the conversation to be deleted
            conversation_to_delete = db.query(Memory).filter(Memory.id == conversation_id).first()

            # Check if the conversation exists
            if not conversation_to_delete:
                return redirect(url_for('conversation_delete_not_found', conversation_id=conversation_id))

            # Check if the current user is the owner of the conversation
            if conversation_to_delete.owner_id != current_user.id:
                return redirect(url_for('conversation_delete_forbidden', conversation_id=conversation_id))

            else:
                # Delete the conversation
                db.delete(conversation_to_delete)
                db.commit()
                db.rollback()  # Rollback in case of commit failure
                flash(f'Conversation with ID: 🔥{conversation_id}🔥 deleted successfully 😎')
                return redirect(url_for('delete_conversation'))

        return render_template('conversation-delete.html', current_user=current_user, form=form,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
