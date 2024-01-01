import json
import os
from datetime import datetime

import pytz
from flask import Blueprint, render_template, redirect, request, jsonify, abort, send_file, flash
from flask_login import current_user
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain.chains import ConversationChain

from app.databases.database import get_db
from app.models.memory import Memory

from app.forms.app_forms import TextAreaForm, ConversationIdForm, DeleteForm

conversation_bp = Blueprint('conversation', __name__, template_folder='templates')

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
siisi_conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)

# Fetch memories from the database
with get_db() as db:
    # memories = db.query(Memory).all()
    test = db.query(Memory).all()


@conversation_bp.route("/", methods=["GET", "POST"])
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


@conversation_bp.route("/conversation", methods=["GET", "POST"])
def conversation():
    form = TextAreaForm()
    answer = None
    owner_id = None

    try:
        if form.validate_on_submit():
            print(f"Form data: {form.data}")

            user_input = form.writing_text.data
            owner_id = current_user.id

            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)
            answer = response['output'] if response else None

        elif request.method == 'POST':

            # Get conversations only for the current user
            user_conversations = Memory.query.filter_by(owner_id=current_user.id).all()

            # Call llm ChatOpenAI for additional processing
            user_message = request.form['prompt']
            response = siisi_conversation.predict(input=json.dumps({
                "created_at": [str(memory.created_at) for memory in user_conversations][-3:],
                "conversations": f"[{','.join([memory.conversations_summary for memory in user_conversations][-3:])}]",
                "user_name": current_user.name,
                "user_message": user_message,
            }))

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
            audio_file_path = f'temp_audio_{current_user.id}.mp3'
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
                "user_message": user_message,
                "answer_text": assistant_reply,
                "answer_audio_path": audio_file_path,
                "memory_id": new_memory.id,
            })

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({'owner_id': owner_id})
        summary_buffer = memory_summary.load_memory_variables({'owner_id': owner_id})

        return render_template('conversation-answer.html', current_user=current_user,
                               form=form, answer=answer, memory_load=memory_load,
                               memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                               date=datetime.now().strftime("%a %d %B %Y"))

    except Exception as err:
        print(f"RELOAD ¡!¡ Unexpected {err=}, {type(err)=}")
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@conversation_bp.route('/audio')
def serve_audio():
    audio_file_path = f'temp_audio_{current_user.id}.mp3'

    # Check if the file exists
    if not os.path.exists(audio_file_path):
        abort(404, description=f"Audio file not found")

    return send_file(audio_file_path, as_attachment=True)


@conversation_bp.route('/show-history')
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
            memory_buffer = f'\n{current_user.name}(owner_id:{owner_id}):\n{memory.buffer_as_str}'

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
        return render_template('error.html', error_message=str(err), current_user=current_user,
                               date=datetime.now().strftime("%a %d %B %Y"))


@conversation_bp.route("/get-all-conversations")
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


@conversation_bp.route('/select-conversation-id', methods=['GET', 'POST'])
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


@conversation_bp.route('/conversation/<int:conversation_id>')
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


@conversation_bp.route('/delete-conversation', methods=['GET', 'POST'])
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


@conversation_bp.route('/api/conversations-jsonify', methods=['GET'])
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
