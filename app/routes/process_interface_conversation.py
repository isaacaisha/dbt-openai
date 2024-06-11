import json
import pytz

from flask import Blueprint, flash, render_template, request, send_file, jsonify, redirect, url_for
from flask_login import current_user, login_required
from gtts import gTTS
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.app_forms import TextAreaForm
from app.memory import Memory, db


interface_conversation_bp = Blueprint('conversation_interface', __name__)

llm = ChatOpenAI(temperature=0.0, model="gpt-4o")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=3)


@login_required
@interface_conversation_bp.route("/conversation-interface", methods=["GET", "POST"])
def conversation_interface():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    writing_text_form = TextAreaForm()
    user_input = None
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']
        answer = conversation.predict(input=user_input)

    memory_buffer = memory.buffer_as_str
    memory_load = memory.load_memory_variables({})

    return render_template('conversation-interface.html', writing_text_form=writing_text_form,
                           user_input=user_input, answer=answer, current_user=current_user,
                           memory_buffer=memory_buffer, memory_load=memory_load,
                           date=datetime.now().strftime("%a %d %B %Y"))


def handle_llm_response(user_input, conversation_context):
    response = conversation.predict(input=json.dumps(conversation_context))

    if isinstance(response, str):
        assistant_reply = response
    else:
        if isinstance(response, dict) and 'choices' in response:
            assistant_reply = response['choices'][0]['message']['content']
        else:
            assistant_reply = None

    tts = gTTS(assistant_reply)
    interface_audio_file_path = 'interface_temp_audio.mp3'
    tts.save(interface_audio_file_path)

    memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})

    return assistant_reply, interface_audio_file_path, response


def generate_conversation_context(user_input):
    conversation_context = {
        "user_name": current_user.name,
        "user_message": user_input,
    }
    return conversation_context


@login_required
@interface_conversation_bp.route('/interface/answer', methods=['POST'])
def interface_answer():
    if current_user.is_authenticated:
        user_input = request.form['prompt']
        conversation_context = generate_conversation_context(user_input)
        assistant_reply, audio_file_path, response = handle_llm_response(user_input, conversation_context)
        save_to_database(user_input, response)

        return jsonify({
            "answer_text": assistant_reply,
            "answer_audio_path": audio_file_path,
        })
    else:
        return redirect(url_for('conversation_interface.interface_answer')), 401
    

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
    conversations_summary_str = json.dumps(conversations_summary)

    timezone = pytz.timezone('Europe/Madrid')
    created_at = datetime.now(timezone)

    new_memory = Memory(
        user_name=current_user.name,
        owner_id=current_user.id,
        user_message=user_input,
        llm_response=response,
        conversations_summary=conversations_summary_str,
        created_at=created_at
    )

    # memory_attributes = vars(new_memory)
    print(f'owner_id: {new_memory.owner_id}\nuser_name: {new_memory.user_name}\n'
          f'user_message: {new_memory.user_message}\nllm_response: {new_memory.llm_response}\n'
          f'conversations_summary: {new_memory.conversations_summary}\ncreated_at: {created_at}') 

    try:
        db.session.add(new_memory)
        db.session.commit()
        db.session.refresh(new_memory)

        # Clear or reset the memory summary after saving
        memory_summary.clear()

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

    except SQLAlchemyError as err:
        print(f"Error saving to database: {str(err)}")
        db.session.rollback()
        return jsonify({"error": "Failed to save to database"}), 500
    finally:
        db.session.close()

    return jsonify({
        "memory_buffer": memory_buffer,
        "memory_load": memory_load,
    })
