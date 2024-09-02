# PROCESS_INTERFACE_CONVERSATION.PY

import io
import base64
import os
import numpy as np

from flask import Blueprint, Response, flash, render_template, request, jsonify, redirect, send_file, url_for
from flask_login import current_user

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langdetect import detect

from app.routes.utils_interface import find_most_relevant_conversation, generate_conversation_context, handle_llm_response, save_to_database 

from app.memory import Memory
from app.app_forms import TextAreaForm, TextAreaDrawingIndex

from datetime import datetime


interface_conversation_bp = Blueprint('conversation_interface', __name__, template_folder='templates', static_folder='static')

openai = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
llm = ChatOpenAI(temperature=0.0, model="gpt-4o")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=3)

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)


@interface_conversation_bp.route("/conversation-interface", methods=["GET", "POST"])
def conversation_interface():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    writing_text_form = TextAreaForm()
    drawing_form = TextAreaDrawingIndex()
    user_input = None
    answer = None
    latest_conversation = []

    try:
        if request.method == "POST":
            # Handle conversation form submission
            if writing_text_form.validate_on_submit() and 'text_writing' in request.form:
                user_input = request.form['writing_text']
                answer = conversation.predict(input=user_input)
                latest_conversation = Memory.query.filter_by(owner_id=current_user.id).order_by(Memory.created_at.desc()).all()
            else:
                latest_conversation = Memory.query.filter_by(owner_id=current_user.id).order_by(Memory.created_at.desc()).all()

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        return render_template('conversation-interface.html', writing_text_form=writing_text_form, drawing_form=drawing_form,
                               user_input=user_input, answer=answer, current_user=current_user,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               latest_conversation=latest_conversation, date=datetime.now().strftime("%a %d %B %Y"))
    except Exception as e:
        print(f"Exception occurred: {e}")
        flash("An error occurred. Please try again.", "error")
        return render_template('conversation-interface.html', writing_text_form=writing_text_form, drawing_form=drawing_form,
                               user_input=user_input, answer=answer, current_user=current_user,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               latest_conversation=latest_conversation, date=datetime.now().strftime("%a %d %B %Y")), 500


# Route to handle answering user input
@interface_conversation_bp.route('/interface/answer', methods=['POST'])
def interface_answer():
    if current_user.is_authenticated:
        user_input = request.form['prompt']

        # Detect the language of the user's message
        detected_lang = detect(user_input)

        if current_user.email == 'medusadbt@gmail.com':
            print("Using embedding method for medusadbt@gmail.com")
            # Limit to 91 most recent conversations
            user_conversations = Memory.query.filter_by(
                owner_id=current_user.id).order_by(Memory.created_at.desc()).limit(91).all()
            
            # Generate embeddings from the stored binary data
            embeddings = [
                np.frombuffer(memory.embedding, dtype=float) for memory in user_conversations if memory.embedding is not None
            ]

            if not embeddings:
                # Handle new users with no embeddings
                assistant_reply, audio_data, response, flash_message = handle_llm_response(user_input, conversation_context, detected_lang)
                save_to_database(user_input, response, audio_data)

                return jsonify({
                    "answer_text": assistant_reply,
                    "detected_lang": detected_lang,
                    "flash_message": flash_message
                })

            index, similarity = find_most_relevant_conversation(user_input, embeddings)
            most_relevant_memory = user_conversations[index]

            conversation_context = {
                "user_name": current_user.name,
                "user_message": user_input,
                "most_relevant_conversation": {
                    "user_message": most_relevant_memory.user_message,
                    "llm_response": most_relevant_memory.llm_response,
                    "created_at": str(most_relevant_memory.created_at), 
                    "similarity": similarity
                },
                "previous_conversations": [
                    {
                        "user_message": memory.user_message,
                        "llm_response": memory.llm_response,
                        "created_at": str(memory.created_at) 
                    } for memory in user_conversations
                ]
            }

        else:
            print(f"User {current_user.email} is not using the embedding method")
            # For all other users, use generate_conversation_context
            user_conversations = Memory.query.filter_by(
                owner_id=current_user.id).order_by(Memory.created_at.desc()).limit(3).all()
            conversation_context = generate_conversation_context(user_input, user_conversations)

        assistant_reply, audio_data, response, flash_message = handle_llm_response(user_input, conversation_context, detected_lang)
        save_to_database(user_input, response, audio_data)

        return jsonify({
            "answer_text": assistant_reply,
            "detected_lang": detected_lang,
            "flash_message": flash_message
        })
    else:
        return jsonify({"error": "User not authenticated"}), 401


@interface_conversation_bp.route('/audio/<int:conversation_id>')
def serve_audio_from_db(conversation_id):
    memory = Memory.query.get(conversation_id)
    if memory and memory.audio_datas:
        audio_data = io.BytesIO(memory.audio_datas)
        return send_file(
            audio_data,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=f"audio_{conversation_id}.mp3"
        )
    else:
        return Response("Audio not found", status=404)


@interface_conversation_bp.route("/latest-audio-url", methods=["GET"])
def latest_audio_url():
    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 403

    # Fetch the latest conversation
    latest_conversation = Memory.query.filter_by(owner_id=current_user.id).order_by(Memory.created_at.desc()).first()
    
    if latest_conversation:
        audio_url = url_for('conversation_interface.serve_audio_from_db', conversation_id=latest_conversation.id)
        return jsonify({"audio_url": audio_url})
    else:
        return jsonify({"error": "No audio found"}), 404
    