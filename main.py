import os
import flask_wtf
import openai
import json
import secrets
import warnings
import pytz
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_login import LoginManager, login_user, logout_user, current_user
from werkzeug.exceptions import BadRequest, InternalServerError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory

from app.databases.database import get_db
from app.models.memory import Memory, db, User
from app.forms.conversation_id_form import ConversationIdForm
from app.forms.delete_form import DeleteForm
from app.forms.login_form import LoginForm
from app.forms.register_form import RegisterForm
from app.forms.text_area_form import TextAreaForm

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__, template_folder='templates')
csrf = CSRFProtect(app)
Bootstrap(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

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

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)

app.config[
    'SQLALCHEMY_DATABASE_URI'] = (f"postgresql://{os.environ['user']}:{os.environ['password']}@"
                                  f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()

# Fetch memories from the database
with get_db() as db:
    # memories = db.query(Memory).all()
    test = db.query(Memory).all()


@login_manager.user_loader
def load_user(user_id):
    if user_id is not None and user_id.isdigit():
        # Check if the user_id is a non-empty string of digits
        return User.query.get(int(user_id))
    return None


@app.errorhandler(InternalServerError)
def handle_internal_server_error():
    pass
    return render_template('authentication-error.html', current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))  # , 500


@app.errorhandler(BadRequest)
def handle_bad_request(err):
    pass
    return flash(f"RELOAD BadRequest ¡!¡ Unexpected {err=}, {type(err)=}")  # , 400


@app.errorhandler(flask_wtf.csrf.CSRFError)
def handle_csrf_error(err):
    pass
    return flash(f"RELOAD flask_wtf.csrf.CSRFError ¡!¡ Unexpected {err=}, {type(err)=}")  # , 400


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}")

            # Check if the passwords match
            if form.password.data != form.confirm_password.data:
                flash("Passwords do not match. Please enter matching passwords 😭.")
                return redirect(url_for('register'))

            # If user's email already exists
            if User.query.filter_by(email=form.email.data).first():
                # Send a flash message
                flash("You've already signed up with that email, log in instead! 🤣.")
                return redirect(url_for('login'))

            hash_and_salted_password = generate_password_hash(
                request.form.get('password'),
                method='pbkdf2:sha256',
                salt_length=8
            )

            new_user = User()
            new_user.email = request.form['email']
            new_user.name = request.form['name']
            new_user.password = hash_and_salted_password

            db.add(new_user)
            db.commit()
            db.refresh(new_user)

            # Log in and authenticate the user after adding details to the database.
            login_user(new_user)
            return redirect(url_for('login'))

        else:
            return render_template("register.html", form=form, current_user=current_user,
                                   date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('register'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}")

            email = request.form.get('email')
            password = request.form.get('password')
            remember_me = form.remember_me.data

            user = User.query.filter_by(email=email).first()
            # Email doesn't exist
            if not user:
                flash("That email does not exist, please try again 😭 ¡!¡")
                return redirect(url_for('login'))
            # Password incorrect
            elif not check_password_hash(user.password, password):
                flash('Password incorrect, please try again 😭 ¡!¡')
                return redirect(url_for('login'))
            # Email exists and password correct
            else:
                login_user(user, remember=remember_me)
                return redirect(url_for('conversation_answer'))

        return render_template("login.html", form=form, current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    response = None
    user_input = None

    try:
        if writing_text_form.validate_on_submit():
            print(f"Form data: {writing_text_form.data}\n")

            user_input = request.form['writing_text']
            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        print(f"user_input: {user_input}")
        print(f"response: {response}\n")

        return render_template('index.html', writing_text_form=writing_text_form,
                               current_user=current_user, response=response, memory_buffer=memory_buffer,
                               memory_load=memory_load, date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('home'))


@app.route("/conversation-answer", methods=["GET", "POST"])
def conversation_answer():
    writing_text_form = TextAreaForm()
    answer = None
    owner_id = None

    try:
        if writing_text_form.validate_on_submit():
            print(f"Form data: {writing_text_form.data}")

            user_input = request.form['writing_text']
            owner_id = current_user.id

            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)
            answer = response['output'] if response else None

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({'owner_id': owner_id})
        summary_buffer = memory_summary.load_memory_variables({'owner_id': owner_id})

        return render_template('conversation-answer.html', current_user=current_user,
                               writing_text_form=writing_text_form, answer=answer, memory_load=memory_load,
                               memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('conversation_answer'))


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
            return render_template('authentication-error.html', current_user=current_user,
                                   date=datetime.now().strftime("%a %d %B %Y")), 401

    #except flask_wtf.csrf.CSRFError as err:
    #    flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
    #    return redirect(url_for('answer'))
#
    #except BadRequest as bad_request_err:
    #    # Handle BadRequest (400) errors
    #    flash(f"RELOAD ¡!¡ Unexpected {bad_request_err=}, {type(bad_request_err)=}")
    #    return redirect(url_for('answer'))  # , 400
#
    #except InternalServerError as err:
    #    flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
    #    return redirect(url_for('answer'))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err))  # , 500


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
        owner_id = current_user.id

        # Modify the query to filter records based on the current user's ID
        summary_conversation = memory_summary.load_memory_variables({'owner_id': owner_id})
        memory_load = memory.load_memory_variables({'owner_id': owner_id})
        memory_buffer = f'{current_user.name}:\n{memory.buffer_as_str}'

        print(f'memory_buffer_story:\n{memory_buffer}\n')
        print(f'memory_load_story:\n{memory_load}\n')
        print(f'summary_conversation_story:\n{summary_conversation}\n')

        return render_template('show-history.html', current_user=current_user, memory_load=memory_load,
                               memory_buffer=memory_buffer, summary_conversation=summary_conversation,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('show_story'))


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
                               current_user=current_user,
                               conversations=serialized_conversations,
                               serialized_conversations=serialized_conversations,
                               date=datetime.now().strftime("%a %d %B %Y")
                               )

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('get_all_conversations'))


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

        return render_template('conversation-by-id.html', form=form, current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('select_conversation'))


@app.route('/conversation/<int:conversation_id>')
def get_conversation(conversation_id):
    conversation_ = db.query(Memory).filter_by(id=conversation_id).first()

    try:
        if conversation_ is not None:
            if conversation_.owner_id == current_user.id:
                # Format created_at timestamp
                formatted_created_at = conversation_.created_at.strftime("%a %d %B %Y %H:%M:%S")
                return render_template('conversation-details.html', current_user=current_user,
                                       conversation_=conversation_, formatted_created_at=formatted_created_at,
                                       date=datetime.now().strftime("%a %d %B %Y"))
            else:
                # User doesn't have access, return a forbidden message
                return render_template('conversation-forbidden.html',
                                       current_user=current_user,
                                       conversation_id=conversation_id,
                                       date=datetime.now().strftime("%a %d %B %Y"))  # , 403
        else:
            # Conversation not found, return a not found message
            return render_template('conversation-not-found.html',
                                   current_user=current_user,
                                   conversation_id=conversation_id,
                                   date=datetime.now().strftime("%a %d %B %Y"))  # , 404

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('get_conversation'))


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
                return render_template('conversation-delete-not-found.html',
                                       current_user=current_user,
                                       conversation_id=conversation_id,
                                       date=datetime.now().strftime("%a %d %B %Y"))  # , 404

            # Check if the current user is the owner of the conversation
            if conversation_to_delete.owner_id != current_user.id:
                return render_template('conversation-delete-forbidden.html',
                                       current_user=current_user,
                                       conversation_id=conversation_id,
                                       date=datetime.now().strftime("%a %d %B %Y"))  # , 403

            # Delete the conversation
            db.delete(conversation_to_delete)
            db.commit()
            flash(f'Conversation with ID: 🔥{conversation_id}🔥 deleted successfully ¡!¡ 😎 ¡!¡')
            return redirect(url_for('delete_conversation'))

        return render_template('delete.html', current_user=current_user, form=form,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        flash(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return redirect(url_for('delete_conversation'))


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
                           conversations=serialized_conversations,
                           serialized_conversations=serialized_conversations,
                           date=datetime.now().strftime("%a %d %B %Y")
                           )


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
