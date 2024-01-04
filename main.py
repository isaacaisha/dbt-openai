import json
import logging
import os
import flask_wtf
import openai
import secrets
import warnings

import pytz
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv, find_dotenv
from flask import Flask, flash, request, redirect, url_for, render_template, jsonify, abort, send_file
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, current_user
from datetime import timedelta, datetime

from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from werkzeug.exceptions import InternalServerError, BadRequest

from app.forms.app_forms import TextAreaForm, ConversationIdForm, DeleteForm
from app.routes.auth import register as auth_register, login as auth_login, logout as auth_logout
from app.databases.database import get_db
from app.models.memory import Memory, User, db
from app.routes.conversation import (home as home_conversation, conversation_answer as response_conversation,
                                     conversation as answer_conversation, serve_audio as audio_response,
                                     show_story as show_story_conversation,
                                     get_all_conversations as whole_conversations,
                                     select_conversation as conversation_selected,
                                     get_conversation as id_conversation, delete_conversation as conversation_deleted,
                                     get_conversations_jsonify as jsonify_conversation)

#logging.basicConfig(level=logging.DEBUG)
warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__, template_folder='templates')

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
siisi_conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
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


def initialize_database():
    with app.app_context():
        db.create_all()


def configure_database():
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.environ['user']}:{os.environ['password']}@"
        f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    initialize_database()


configure_database()

# Fetch memories from the database
with get_db() as db:
    # memories = db.query(Memory).all()
    test = db.query(Memory).all()


@app.route('/get_csrf_token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({'csrf_token': token})


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


@app.route("/", methods=["GET", "POST"])
def home():
    form = TextAreaForm()
    response = None
    user_input = None

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}\n")

            # Retrieve form data using the correct key
            user_input = form.writing_text.data
            # Use the LLM to generate a response based on user input
            response = siisi_conversation.predict(input=user_input)

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        print(f"user_input: {user_input}")
        print(f"response: {response}\n")

        return render_template('index.html', form=form,
                               current_user=current_user, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/conversation-interface", methods=["GET", "POST"])
def conversation_interface():
    form = TextAreaForm()
    response = None
    user_input = None
    jsonify_ = None

    try:
        if request.method == "POST" and form.validate_on_submit():
            print(f"Form data: {form.data}\n")
            print(f"Request Method: {request.method}\n")

            # Retrieve form data using the correct key
            user_input = form.writing_text.data
            # Use the LLM to generate a response based on user input
            response = siisi_conversation.predict(input=user_input)

            # Convert the text response to speech using gTTS
            tts = gTTS(response)
            # Create a temporary audio file
            audio_file_path = f'temp_audio.mp3'
            tts.save(audio_file_path)

            memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})
            conversations_summary = memory_summary.load_memory_variables({})
            conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

            # Create a new Memory object with the data
            new_memory = Memory(
                user_name=current_user.name,
                owner_id=current_user.id,
                user_message=user_input,
                llm_response=response,
                conversations_summary=conversations_summary_str,
                created_at=datetime.now(pytz.timezone('Europe/Paris'))
            )
            # Add the new memory to the session
            db.add(new_memory)
            # Commit changes to the database
            db.commit()
            db.refresh(new_memory)

            # Return the response as JSON, including both text and the path to the audio file
            jsonify_ = jsonify({
                "user_input": user_input,
                "response": response,
                "conversations_summary_str": conversations_summary_str,
                "audio_path": audio_file_path,
            })
            print(f"User name: {current_user.name}\nuser_input: {user_input}\nresponse: {response}\n"
                  f"conversations_summary_str: {conversations_summary_str}")

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        return render_template('conversation-interface.html', form=form,
                               current_user=current_user, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load, jsonify_=jsonify_,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        logging.exception("Unexpected error occurred.")
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


@app.route('/show-history')
def show_story():
    try:
        # Flask-Login for user authentication
        if current_user.is_authenticated:
            owner_id = current_user.id

            # Assuming memory, llm, and memory_summary are instantiated within your Flask app context
            # Modify the query to filter records based on the current user's ID
            summary_conversation = memory_summary.load_memory_variables({'owner_id': owner_id})
            memory_load = memory.load_memory_variables({'owner_id': owner_id})

            # Assuming memory is an instance of ConversationBufferMemory
            memory_buffer = f'{current_user.name}(owner_id:{owner_id}):\n{memory.buffer_as_str}'

            print(f'memory_buffer_story:\n{memory_buffer}\n')
            print(f'memory_load_story:\n{memory_load}\n')
            print(f'summary_conversation_story:\n{summary_conversation}\n')

            return render_template('show-history.html', current_user=current_user, owner_id=owner_id,
                                   memory_load=memory_load, memory_buffer=memory_buffer,
                                   summary_conversation=summary_conversation,
                                   date=datetime.now().strftime("%a %d %B %Y"))

        # If the user is not authenticated, you may want to handle this case (redirect, show an error, etc.)
        else:
            return render_template('authentication-error.html', error_message='User not authenticated',
                                   current_user=current_user,
                                   date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        # Handle exceptions appropriately
        flash(f'Unexpected: {str(err)}, \ntype: {type(err)} 😭 ¡!¡')
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/get-all-conversations")
def get_all_conversations():
    try:
        owner_id = current_user.id
        conversations = db.query(Memory).filter_by(owner_id=owner_id).all()
        # Create a list to store serialized data for each Memory object
        serialized_conversations = []

        for conversation_ in conversations:
            serialized_history = {
                "id": conversation_.id,
                "owner_id": conversation_.owner_id,
                "user_name": conversation_.user_name,
                "user_message": conversation_.user_message,
                "llm_response": conversation_.llm_response,
                "conversations_summary": conversation_.conversations_summary,
                'created_at': conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S"),
            }

            serialized_conversations.append(serialized_history)

        return render_template('all-conversations.html',
                               current_user=current_user, owner_id=owner_id, conversations=serialized_conversations,
                               serialized_conversations=serialized_conversations,
                               date=datetime.now().strftime("%a %d %B %Y")
                               )

    except Exception as err:
        flash(f'Unexpected: {str(err)}, \ntype: {type(err)} 😭 ¡!¡')
        return render_template('authentication-error.html', error_message='User not authenticated',
                               current_user=current_user, date=datetime.now().strftime("%a %d %B %Y"))


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


@app.route('/conversation/<int:conversation_id>')
def get_conversation(conversation_id):
    conversation_ = db.query(Memory).filter_by(id=conversation_id).first()

    try:
        if not conversation_:
            # Conversation not found, return a not found message
            return render_template('conversation-not-found.html', current_user=current_user,
                                   conversation_=conversation_, conversation_id=conversation_id,
                                   date=datetime.now().strftime("%a %d %B %Y"))

        if conversation_.owner_id != current_user.id:
            # User doesn't have access, return a forbidden message
            return render_template('conversation-forbidden.html', current_user=current_user,
                                   conversation_=conversation_, conversation_id=conversation_id,
                                   date=datetime.now().strftime("%a %d %B %Y"))

        else:
            # Format created_at timestamp
            formatted_created_at = conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S")
            return render_template('conversation-details.html', current_user=current_user,
                                   conversation_=conversation_, formatted_created_at=formatted_created_at,
                                   conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/delete-conversation', methods=['GET', 'POST'])
def delete_conversation(conversation_id=None):
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
                return render_template('conversation-delete-not-found.html', current_user=current_user,
                                       conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))

            # Check if the current user is the owner of the conversation
            if conversation_to_delete.owner_id != current_user.id:
                return render_template('conversation-delete-forbidden.html', current_user=current_user,
                                       conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))

            else:
                # Delete the conversation
                db.delete(conversation_to_delete)
                db.commit()
                db.rollback()  # Rollback in case of commit failure
                flash(f'Conversation with ID: 🔥{conversation_id}🔥 deleted successfully 😎')
                return render_template('conversation-delete.html',
                                       current_user=current_user, form=form, conversation_id=conversation_id,
                                       date=datetime.now().strftime("%a %d %B %Y"))

        return render_template('conversation-delete.html', current_user=current_user, form=form,
                               conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    # Retrieve all conversations from the database
    conversations = test
    # Convert the conversations to a list of dictionaries
    serialized_conversations = []

    for conversation_ in conversations:
        conversation_dict = {
            'id': conversation_.id,
            'user_name': conversation_.user_name,
            'user_message': conversation_.user_message,
            'llm_response': conversation_.llm_response,
            'created_at': conversation_.created_at.strftime("%a %d %B %Y"),
        }

        serialized_conversations.append(conversation_dict)

    return render_template('database-conversations.html',
                           current_user=current_user,
                           serialized_conversations=serialized_conversations,
                           date=datetime.now().strftime("%a %d %B %Y")
                           )


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
