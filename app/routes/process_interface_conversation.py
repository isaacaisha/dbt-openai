import json

import pytz

from flask import Blueprint, render_template, request, send_file, jsonify, redirect, url_for
from flask_login import current_user
from gtts import gTTS
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.forms.app_forms import TextAreaForm
from app.models.memory import Memory, db

interface_conversation_bp = Blueprint('conversation_interface', __name__)

llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)


@interface_conversation_bp.route("/conversation-interface", methods=["GET", "POST"])
def conversation_interface():
    writing_text_form = TextAreaForm()
    user_input = None
    answer = None
    error_message = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']

        # Use the LLM to generate a response based on user input
        answer = conversation.predict(input=user_input)

        print(f'User ID:{current_user.id} 😎')
        print(f'User Name: {current_user.name} 😝')
        print(f'User Input: {user_input} 😎')
        print(f'LLM Response:{answer} 😝\n')

    memory_buffer = memory.buffer_as_str
    memory_load = memory.load_memory_variables({})

    return render_template('conversation-interface.html', writing_text_form=writing_text_form,
                           user_input=user_input, answer=answer, current_user=current_user,
                           error_message=error_message, memory_buffer=memory_buffer, memory_load=memory_load,
                           date=datetime.now().strftime("%a %d %B %Y"))


def generate_conversation_context(user_input, user_conversations):
    # Create a list of JSON strings for each conversation
    conversation_strings = [memory.conversations_summary for memory in user_conversations]

    # Combine the last entry into a valid JSON array
    qdocs = f"[{','.join(conversation_strings[-1:])}]"

    # Convert 'created_at' values to string
    created_at_list = [str(memory.created_at) for memory in user_conversations]

    # Include 'created_at' in the conversation context
    conversation_context = {
        "created_at": created_at_list[-1:],
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


@interface_conversation_bp.route('/interface/answer', methods=['POST'])
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

        # Save the data to the database
        save_to_database(user_input, response)

        # Return the response as JSON, including both text and the path to the audio file
        return jsonify({
            "answer_text": assistant_reply,
            "answer_audio_path": audio_file_path,
        })
    else:
        return redirect(url_for('interface_answer')), 401


@interface_conversation_bp.route('/interface-audio')
def interface_serve_audio():
    interface_audio_file_path = 'interface_temp_audio.mp3'
    try:
        return send_file(interface_audio_file_path, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404


@interface_conversation_bp.route('/save-to-database', methods=['POST'])
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
        # Commit changes to the database session
        db.session.commit()
        # Refresh the new_memory object with the updated database state
        db.session.refresh(new_memory)

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

    except SQLAlchemyError as err:
        # Log the exception or handle it as needed
        print(f"Error saving to database: {str(err)}")
        # Rollback the changes in case of an error
        db.session.rollback()
        return jsonify({"error": "Failed to save to database"}), 500
    finally:
        # Close the database session
        db.session.close()

    return jsonify({
        "memory_buffer": memory_buffer,
        "memory_load": memory_load,
    })


@interface_conversation_bp.route('/show-history')
def show_story():
    if current_user.is_authenticated:
        owner_id = current_user.id

        # Fetch the 3 latest Memory objects for the current user
        memory_load = Memory.query.filter_by(owner_id=owner_id).order_by(Memory.created_at.desc()).limit(3).all()

        memory_buffer = f'{current_user.name}(owner_id:{owner_id}):\n\n'
        memory_buffer += '\n'.join(
            [f'{memory.user_name}: {memory.user_message}\n·SìįSí·Dbt·: {memory.llm_response}\n' for memory in
             memory_load])
        
        # Fetch the list of Memory objects for the current user
        memory_summary_list = Memory.query.filter_by(owner_id=owner_id).order_by(Memory.created_at.desc()).limit(3).all()
        # Load the summary data for the lastest 3 conversations for each memory object from memory_summary_list
        summary_conversation = '\n'.join([memory.conversations_summary for memory in memory_summary_list])

        print(f'memory_buffer_story:\n{memory_buffer}\n')
        print(f'memory_load_story:\n{memory_load}\n')
        print(f'summary_conversation_story:\n{summary_conversation}\n')
        return render_template('show-history.html', current_user=current_user, owner_id=owner_id,
                               memory_load=memory_load, memory_buffer=memory_buffer,
                               summary_conversation=summary_conversation,
                               date=datetime.now().strftime("%a %d %B %Y"))
    else:
        error_message = 'User not authenticated, RELOAD or LOGIN -¡!¡-'
        return render_template('show-history.html', error_message=error_message,
                               current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))
