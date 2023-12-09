import os
import openai
import secrets
import warnings
import pytz
import json
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from datetime import datetime, timedelta
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory

from database import get_db
from models import Memory, db, User

from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from forms import RegisterForm, LoginForm, TextAreaForm, DeleteForm

import io
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__)
Bootstrap(app)
CORS(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)

openai.api_key = os.environ['OPENAI_API_KEY']
app.config['WTF_CSRF_ENABLED'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)

# Generate a random secret key
secret_key = secrets.token_hex(199)
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
#csrf = CSRFProtect(app)
#CSRFProtect(app)

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


@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']

        # Use the LLM to generate a response based on user input
        response = conversation.predict(input=user_input)

        answer = response['output'] if response else None

    memory_buffer = memory.buffer_as_str
    memory_load = memory.load_memory_variables({})
    summary_buffer = memory_summary.load_memory_variables({})

    return render_template('index.html', current_user=current_user,
                           writing_text_form=writing_text_form, answer=answer, memory_load=memory_load,
                           memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        # Check if the email is already taken
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash(f'Email: 🔥{email}🔥 is already taken. Please choose a different one.', 'danger')
            return redirect(url_for('register'))

        # Hash the password before saving it to the database
        hashed_password = generate_password_hash(password, method='sha256')

        # Create a new user
        new_user = User(email=email, password=hashed_password)

        # Add the new user to the database
        db.add(new_user)
        db.commit()

        flash('Registration successful! You can now log in.', 'success')

        # After successful registration
        login_user(new_user)

        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        #remember = form.remember_me.data

        # Find the user by username
        user = User.query.filter_by(email=email).first()

        # Check if the user exists and the password is correct
        if user and check_password_hash(user.password, password):
            # Log in the user
            login_user(user)
            #login_user(user, remember=remember)
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login failed. Please check your username and password.', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'success')
    return redirect(url_for('home'))


@app.route('/answer', methods=['GET', 'POST'])
@login_required
def answer():
    user_message = request.form['prompt']

    if current_user.is_authenticated:

        # if not current_user.is_authenticated:
        #    # If the user is not authenticated, return an appropriate response
        #    return jsonify(), 401
        # else:
        # Get conversations only for the current user
        user_conversations = Memory.query.filter_by(owner_id=current_user.id).all()

        # Create a list of JSON strings for each conversation
        conversation_strings = [memory.conversations_summary for memory in user_conversations]

        # Create a list of JSON strings for each conversation
        # conversation_strings = [memory.conversations_summary for memory in test]

        # Combine the first 1 and last 9 entries into a valid JSON array
        qdocs = f"[{','.join(conversation_strings[:1] + conversation_strings[-3:])}]"

        # Convert 'created_at' values to string
        created_at_list = [str(memory.created_at) for memory in user_conversations]

        # Include 'created_at' in the conversation context
        conversation_context = {
            "created_at": created_at_list[-3:],
            "conversations": qdocs,
            "user_message": user_message,
        }

        # Call llm ChatOpenAI
        response = conversation.predict(input=json.dumps(conversation_context))
        print(f'conversation_context:\n{conversation_context}\n')

        # Check if the response is a string, and if so, use it as the assistant's reply
        if isinstance(response, str):
            assistant_reply = response
        else:
            # If it's not a string, access the assistant's reply as you previously did
            assistant_reply = response.choices[0].message['content']

        # Convert the text response to speech using gTTS
        tts = gTTS(assistant_reply)

        # Create a temporary audio file
        audio_file_path = 'temp_audio.mp3'
        tts.save(audio_file_path)

        ## Create an in-memory file-like object to store the audio data
        # audio_data = io.BytesIO()
        # tts.write_to_fp(audio_data)
        # audio_data.seek(0)  # Reset the file pointer to the beginning

        memory_summary.save_context({"input": f"{user_message}"}, {"output": f"{response}"})
        conversations_summary = memory_summary.load_memory_variables({})
        conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

        current_time = datetime.now(pytz.timezone('Europe/Paris'))

        # Access the database session using the get_db function
        with get_db() as db:
            # Create a new Memory object with the data
            new_memory = Memory(
                user_message=user_message,
                llm_response=assistant_reply,
                conversations_summary=conversations_summary_str,
                created_at=current_time,
                owner_id=current_user.id
            )

            # Add the new memory to the session
            db.add(new_memory)

            # Commit changes to the database
            db.commit()
            db.refresh(new_memory)

        print(f'User id:\n{current_user.id} 😝\n')
        print(f'User Input: {user_message} 😎')
        print(f'LLM Response:\n{assistant_reply} 😝\n')

        # Convert current_user to JSON-serializable format
        current_user_data = {
            "id": current_user.id,
            # "username": current_user.username,
            # Include any other relevant fields
        }

        # Return the response as JSON, including both text and the path to the audio file
        return jsonify({
            "answer_text": assistant_reply,
            "answer_audio_path": audio_file_path,
            #"current_user": current_user_data,
            # "answer_audio": audio_data.read().decode('latin-1'),  # Convert binary data to string
        })
    else:
        return jsonify(), 401


@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    # Check if the file exists
    if not os.path.exists(audio_file_path):
        abort(404, description=f"Audio file not found")
    return send_file(audio_file_path, as_attachment=True)


@app.route('/show-history')
def show_story():
    summary_conversation = memory_summary.load_memory_variables({})
    memory_load = memory.load_memory_variables({})
    memory_buffer = memory.buffer_as_str

    print(f'memory_buffer_story:\n{memory_buffer}\n')
    print(f'memory_load_story:\n{memory_load}\n')
    print(f'summary_conversation_story:\n{summary_conversation}\n')

    return render_template('show-history.html', memory_load=memory_load, memory_buffer=memory_buffer,
                           summary_conversation=summary_conversation, date=datetime.now().strftime("%a %d %B %Y"))


@app.route("/private-conversations")
def get_private_conversations():
    if current_user.is_authenticated:
        # if not current_user.is_authenticated:
        #    # If the user is not authenticated, return an appropriate response
        #    # return jsonify({"error": "You must be logged in to use this feature. Please register then log in."}), 401
        #    return (f'<h1 style="color:red; text-align:center; font-size:3.7rem;">First Get Registered<br>'
        #            f'Then Log Into<br>¡!¡ 😎 ¡!¡</h1>')
        # else:
        # private:
        owner_id = current_user.id
        histories = db.query(Memory).filter_by(owner_id=owner_id).all()

        # Create a list to store serialized data for each Memory object
        serialized_histories = []

        for history in histories:
            serialized_history = {
                "id": history.id,
                "owner_id": history.owner_id,
                "user_message": history.user_message,
                "llm_response": history.llm_response,
                "created_at": history.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Convert to string
                # Add more fields as needed
            }

            serialized_histories.append(serialized_history)

        # return jsonify(serialized_histories)

        # Render an HTML template with the serialized data
        return render_template('private-conversations.html', histories=serialized_histories,
                               serialized_histories=serialized_histories, date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return (f'<h1 style="color:red; text-align:center; font-size:3.7rem;">First Get Registered<br>'
                f'Then Log Into<br>¡!¡ 😎 ¡!¡</h1>')


@app.route('/delete-conversation', methods=['GET', 'POST'])
def delete_conversation():
    if current_user.is_authenticated:
        # if not current_user.is_authenticated:
        #    # If the user is not authenticated, return an appropriate response
        #    # return jsonify({"error": "You must be logged in to use this feature. Please register then log in."}),
        #    # 401
        #    return (f'<h1 style="color:red; text-align:center; font-size:3.7rem;">First Get Registered<br>'
        #            f'Then Log Into<br>¡!¡ 😎 ¡!¡</h1>')
        # else:
        form = DeleteForm()

        if form.validate_on_submit():
            # Access the database session using the get_db function
            with get_db() as db:
                # Get the conversation_id from the form
                conversation_id = form.conversation_id.data

                # Query the database to get the conversation to be deleted
                conversation_to_delete = db.query(Memory).filter(Memory.id == conversation_id).first()

                # Check if the conversation exists
                if not conversation_to_delete:
                    abort(404, description=f"Conversation with ID 🔥{conversation_id}🔥 not found")

                # Check if the current user is the owner of the conversation
                if conversation_to_delete.owner_id != current_user.id:
                    abort(403, description=f"Not authorized to perform the requested action\n"
                                           f"Conversation with ID 🔥{conversation_id}🔥\nDoesn't belongs to you ¡!¡")

                # Delete the conversation
                db.delete(conversation_to_delete)
                print(f'conversation_to_delete:\n{conversation_to_delete}\n')
                db.commit()

                flash('Conversation deleted successfully', 'warning')

                return redirect(url_for('delete_conversation'))

        return render_template('del.html', date=datetime.now().strftime("%a %d %B %Y"), form=form)
    else:
        return (f'<h1 style="color:red; text-align:center; font-size:3.7rem;">First Get Registered<br>'
                f'Then Log Into<br>¡!¡ 😎 ¡!¡</h1>')


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
