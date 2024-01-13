import json
import os
import openai
import secrets
import warnings

import pytz
from dotenv import load_dotenv, find_dotenv
from flask import Flask, flash, request, redirect, url_for, render_template, send_file, jsonify
from flask_login import LoginManager, current_user
from flask_bootstrap import Bootstrap
from datetime import datetime

from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory

from app.forms.app_forms import TextAreaFormIndex, TextAreaForm, ConversationIdForm, DeleteForm
from app.routes.auth import register as auth_register, login as auth_login, logout as auth_logout
from app.databases.database import get_db
from app.models.memory import Memory, User, db

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__, template_folder='templates')
Bootstrap(app)


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

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.environ['user']}:{os.environ['password']}@"
    f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
siisi_conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)

with app.app_context():
    db.create_all()

# Fetch memories from the database
with get_db() as db:
    # memories = db.query(Memory).all()
    test = db.query(Memory).all()


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
    home_form = TextAreaFormIndex()
    response = None
    user_input = None

    try:
        if request.method == "POST" and home_form.validate_on_submit():
            print(f"Form data: {home_form.data}\n")

            # Retrieve form data using the correct key
            user_input = request.form['text_writing']
            # Use the LLM to generate a response based on user input
            response = siisi_conversation.predict(input=user_input)

            print(f"user_input: {user_input}")
            print(f"response: {response}\n")

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        return render_template('index.html', home_form=home_form,
                               current_user=current_user, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/home/answer', methods=['POST'])
def home_answer():
    user_message = request.form['prompt']
    print(f'User Input:\n{user_message} 😎\n')

    # Extend the conversation with the user's message
    response = siisi_conversation.predict(input=user_message)

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
    print(f'LLM Response:\n{assistant_reply} 😝\n')

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
    })


@app.route("/conversation-interface", methods=["GET", "POST"])
def conversation_interface():
    writing_text_form = TextAreaForm()
    error_message = None
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']

        # Use the LLM to generate a response based on user input
        response = siisi_conversation.predict(input=user_input)
        answer = response['output']

        print(f'User ID:{current_user.id} 😎')
        print(f'User Name: {current_user.name} 😝')
        print(f'User Input: {user_input} 😎')
        print(f'LLM Response:{answer} 😝\n')

    memory_buffer = memory.buffer_as_str
    memory_load = memory.load_memory_variables({})

    return render_template('conversation-interface.html', writing_text_form=writing_text_form,
                           answer=answer, date=datetime.now().strftime("%a %d %B %Y"), error_message=error_message,
                           current_user=current_user, memory_buffer=memory_buffer, memory_load=memory_load)


@app.route('/answer', methods=['POST'])
def answer():
    global memory

    try:
        # Check if the user is authenticated
        if current_user.is_authenticated:
            user_input = request.form['prompt']
            print(f'User Input:\n{user_input} 😎\n')

            # Get conversations only for the current user
            user_conversations = Memory.query.filter_by(owner_id=current_user.id).all()

            # Create a list of JSON strings for each conversation
            conversation_strings = [memory.conversations_summary for memory in user_conversations]

            # Combine the first 1 and last 9 entries into a valid JSON array
            qdocs = f"[{','.join(conversation_strings[-3:])}]"

            # Convert 'created_at' values to string
            created_at_list = [str(memory.created_at) for memory in user_conversations]

            # Include 'created_at' in the conversation context
            conversation_context = {
                "created_at": created_at_list[-3:],
                "conversations": qdocs,
                "user_name": current_user.name,
                "user_message": user_input,
            }

            # Call llm ChatOpenAI
            response = siisi_conversation.predict(input=json.dumps(conversation_context))
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

            memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})
            conversations_summary = memory_summary.load_memory_variables({})
            conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

            created_at = datetime.now(pytz.timezone('Europe/Paris'))

            # Create a new Memory object with the data
            new_memory = Memory(
                user_name=current_user.name,
                owner_id=current_user.id,
                user_message=user_input,
                llm_response=response,
                conversations_summary=conversations_summary_str,
                created_at=created_at
            )
            # Add the new memory to the session
            db.add(new_memory)
            # Commit changes to the database
            db.commit()
            db.refresh(new_memory)

            print(f'User ID:{current_user.id} 😎')
            print(f'User Name: {current_user.name} 😝')
            print(f'User Input: {user_input} 😎')
            print(f'LLM Response:{response} 😝\n')

            memory_buffer = memory.buffer_as_str
            memory_load = memory.load_memory_variables({})

            # Return the response as JSON, including both text and the path to the audio file
            return jsonify({
                "answer_text": assistant_reply,
                "answer_audio_path": audio_file_path,
                "memory_buffer": memory_buffer,
                "memory_load": memory_load,
            })
        else:
            # Handle the case where the user is not authenticated
            return flash("User not authenticated. Please log in.", "info")

    except AttributeError as e:
        flash("An error occurred. Please reload & retry...", "info")
        print(f"AttributeError: {e}")
        return redirect(url_for('conversation_interface'))


@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return send_file(audio_file_path, as_attachment=True)


@app.route('/show-history')
def show_story():
    try:
        if current_user.is_authenticated:
            owner_id = current_user.id

            summary_conversation = memory_summary.load_memory_variables({'owner_id': owner_id})
            memory_load = memory.load_memory_variables({'owner_id': owner_id})

            memory_buffer = f'{current_user.name}(owner_id:{owner_id}):\n{memory.buffer_as_str}'

            print(f'memory_buffer_story:\n{memory_buffer}\n')
            print(f'memory_load_story:\n{memory_load}\n')
            print(f'summary_conversation_story:\n{summary_conversation}\n')

            return render_template('show-history.html', current_user=current_user, owner_id=owner_id,
                                   memory_load=memory_load, memory_buffer=memory_buffer,
                                   summary_conversation=summary_conversation,
                                   date=datetime.now().strftime("%a %d %B %Y"))

        else:
            return render_template('authentication-error.html', error_message='User not authenticated',
                                   current_user=current_user,
                                   date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
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
    select_conversation_form = ConversationIdForm()

    try:
        if select_conversation_form.validate_on_submit():
            print(f"Form data: {select_conversation_form.data}")

            # Retrieve the selected conversation ID
            selected_conversation_id = select_conversation_form.conversation_id.data

            # Construct the URL string for the 'get_conversation' route
            url = url_for('get_conversation', conversation_id=selected_conversation_id)

            return redirect(url)

        else:
            return render_template('conversation-by-id.html',
                                   select_conversation_form=select_conversation_form, current_user=current_user,
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
            # Conversation isn't found, return a not found message
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
def delete_conversation():
    delete_conversation_form = DeleteForm()

    try:
        if delete_conversation_form.validate_on_submit():
            print(f"Form data: {delete_conversation_form.data}")

            # Get the conversation_id from the form
            conversation_id = delete_conversation_form.conversation_id.data

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
                                       current_user=current_user, delete_conversation_form=delete_conversation_form,
                                       conversation_id=conversation_id, date=datetime.now().strftime("%a %d %B %Y"))

        return render_template('conversation-delete.html', date=datetime.now().strftime("%a %d %B %Y"),
                               current_user=current_user, delete_conversation_form=delete_conversation_form,)

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/api/conversations-jsonify', methods=['GET'])
def get_conversations_jsonify():
    # Retrieve all conversations from the database
    conversations = db.query(Memory).all()
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

    return render_template('database-conversations.html', date=datetime.now().strftime("%a %d %B %Y"),
                           current_user=current_user, serialized_conversations=serialized_conversations)


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
