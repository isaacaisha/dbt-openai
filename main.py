import json
import os
import warnings
import pytz

from dotenv import load_dotenv, find_dotenv
from flask import flash, request, render_template, jsonify
from flask_login import current_user, login_required
from gtts import gTTS
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory

from app import create_app
from app.models.memory import Memory, db
from app.routes.auth import register as auth_register, login as auth_login, logout as auth_logout

from app.routes.home_process import (home as home_conversations, home_answer as answer_home,
                                     home_audio as audio_home)

from app.routes.llm_conversation import (conversation_interface as interface_llm,
                                         get_all_conversations as all_conversation_llm,
                                         interface_serve_audio as interface_audio_llm,
                                         get_conversations_jsonify as conversation_jsonify_llm)

from app.routes.convers_functions import (select_conversation as conversation_selected,
                                          get_conversation as access_conversation,
                                          delete_conversation as conversation_deleted)

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = create_app()

llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)


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
    return home_conversations()


@app.route('/home/answer', methods=['POST'])
def home_answer():
    return answer_home()


@app.route('/home-audio')
def home_audio():
    return audio_home()


@app.route('/conversation-interface', methods=['GET', 'POST'])
def conversation_interface():
    return interface_llm()


def generate_conversation_context(user_input, user_conversations):
    # Create a list of JSON strings for each conversation
    conversation_strings = [memory.conversations_summary for memory in user_conversations]

    # Combine the first 1 and last 9 entries into a valid JSON array
    qdocs = f"[{','.join(conversation_strings[-3:])}]"

    # Convert 'created_at' values to string
    created_at_list = [str(memory.created_at) for memory in user_conversations]

    # Include 'created_at' in the conversation context
    conversation_context = {
        "created_at": created_at_list[-3:],
        "conversations": json.loads(qdocs),
        "user_name": current_user.name,
        "user_message": user_input,
    }

    return conversation_context


def handle_llm_response(user_input, conversation_context):
    # Call llm ChatOpenAI
    response = conversation.predict(input=json.dumps(conversation_context))
    print(f'conversation_context:\n{conversation_context} 😇\n')

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
    interface_audio_file_path = 'interface_temp_audio.mp3'
    tts.save(interface_audio_file_path)

    memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})

    print(f'User ID:{current_user.id} 😎')
    print(f'User Name: {current_user.name} 😝')
    print(f'User Input: {user_input} 😎')
    print(f'LLM Response:{response} 😝\n')

    return assistant_reply, interface_audio_file_path, response


@app.route('/interface/answer', methods=['POST'])
def interface_answer():
    # Check if the user is authenticated
    if current_user.is_authenticated:
        user_input = request.form['prompt']

        # Get conversations only for the current user
        user_conversations = Memory.query.filter_by(owner_id=current_user.id).all()

        # Generate conversation context
        conversation_context = generate_conversation_context(user_input, user_conversations)

        # Handle llm response and save data to the database
        assistant_reply, audio_file_path, response = handle_llm_response(user_input, conversation_context)

        memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})

        # Save the data to the database
        save_to_database(user_input, response)

        # Return the response as JSON, including both text and the path to the audio file
        return jsonify({
            "answer_text": assistant_reply,
            "answer_audio_path": audio_file_path,
        })


@app.route('/save-to-database', methods=['POST'])
def save_to_database(user_input, response):
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
    try:
        # Add the new memory to the session
        db.session.add(new_memory)
        # Commit changes to the database
        db.session.commit()

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

    except Exception as err:
        # Log the exception or handle it as needed
        # Refresh the new_memory object with the updated database state
        db.refresh(new_memory)
        flash(f"Error saving to database: {str(err)}")
        print(f"Error saving to database: {str(err)}")
        return jsonify({"error": "Failed to save to database"}), 500

    return jsonify({
        "memory_buffer": memory_buffer,
        "memory_load": memory_load,
    })


@app.route('/interface-audio')
def interface_serve_audio():
    return interface_audio_llm()


@login_required
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
        flash(f'😭 Unexpected: {str(err)}, \ntype: {type(err)} 😭 ¡!¡')
        print(f'😭 Unexpected: {str(err)}, \ntype: {type(err)} 😭 ¡!¡')
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


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
