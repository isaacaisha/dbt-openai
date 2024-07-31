# PROCESS_INTERFACE_CONVERSATION.PY

import io
import json
import pytz
import os
import numpy as np
from scipy.spatial.distance import cosine

from flask import Blueprint, Response, flash, render_template, request, jsonify, redirect, send_file, send_from_directory, url_for
from flask_login import current_user
from gtts import gTTS

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langdetect import detect
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.app_forms import TextAreaForm
from app.memory import Memory, db
import logging

# Get the logger instance
logger = logging.getLogger(__name__)

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
    logger.debug("Entering conversation_interface route")
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated access attempt to conversation_interface")
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    writing_text_form = TextAreaForm()
    user_input = None
    answer = None
    latest_conversation = []
    try:
        if request.method == "POST" and writing_text_form.validate_on_submit():
            user_input = request.form['writing_text']
            logger.debug(f"Received user input: {user_input}")
            answer = conversation.predict(input=user_input)
            logger.debug(f"Generated answer: {answer}")
            latest_conversation = Memory.query.filter_by(owner_id=current_user.id).order_by(Memory.created_at.desc()).all()
        else:
            latest_conversation = Memory.query.filter_by(owner_id=current_user.id).order_by(Memory.created_at.desc()).all()

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        logger.debug(f"Rendering template with user input: {user_input}, answer: {answer}, memory buffer: {memory_buffer}, memory load: {memory_load}")
        return render_template('conversation-interface.html', writing_text_form=writing_text_form,
                               user_input=user_input, answer=answer, current_user=current_user,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               latest_conversation=latest_conversation, date=datetime.now().strftime("%a %d %B %Y"))
    except Exception as e:
        print(f"Exception occurred: {e}")
        return flash("An error occurred. Please try reformulating your question.", "error"), 500


@interface_conversation_bp.route('/audio/<int:conversation_id>')
def serve_audio_from_db(conversation_id):
    logger.debug(f"Requested audio for conversation ID: {conversation_id}")
    memory = Memory.query.get(conversation_id)
    if memory and memory.audio_datas:
        audio_data = io.BytesIO(memory.audio_datas)
        logger.debug("Audio data found and served.")
        return send_file(
            audio_data,
            mimetype='audio/mpeg',
            as_attachment=False,
            download_name=f"audio_{conversation_id}.mp3"
        )
    else:
        logger.warning(f"Audio not found for conversation ID: {conversation_id}")
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


def generate_conversation_context(user_input, user_conversations):
    # Create a list of JSON strings for each conversation
    conversation_strings = [memory.conversations_summary for memory in user_conversations]

    # Combine the last entry into a valid JSON array
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


# Function to handle the response from the language model
def handle_llm_response(user_input, conversation_context, detected_lang):
    logger.debug(f"Handling LLM response with user_input: {user_input}, conversation_context: {conversation_context}, detected_lang: {detected_lang}")
    if conversation_context and 'previous_conversations' in conversation_context:
        conversation_context['previous_conversations'] = conversation_context['previous_conversations'][-3:]  

    if not conversation_context:
        response = conversation.predict(input=user_input)
    else:
        response = conversation.predict(input=json.dumps(conversation_context))

    if isinstance(response, str):
        assistant_reply = response
    else:
        if isinstance(response, dict) and 'choices' in response:
            assistant_reply = response['choices'][0]['message']['content']
        else:
            assistant_reply = None
            
    assistant_reply = assistant_reply.replace('#', '').replace('*', '')

    tts = gTTS(assistant_reply, lang=detected_lang)
    audio_file_path = os.path.join(AUDIO_FOLDER_PATH, 'interface_temp_audio.mp3')
    tts.save(audio_file_path)

    with open(audio_file_path, 'rb') as audio_file:
        audio_data = audio_file.read()

    memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})

    logger.debug(f"Generated assistant reply: {assistant_reply}, saved audio data, response: {response}")
    return assistant_reply, audio_data, response


# Function to find the most relevant conversation based on user query
def find_most_relevant_conversation(user_query, embeddings):
    query_embedding = openai.embed_query(user_query)
    similarities = [1 - cosine(query_embedding, embedding) for embedding in embeddings]
    most_similar_index = np.argmax(similarities)
    return most_similar_index, similarities[most_similar_index]


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
                assistant_reply, audio_data, response = handle_llm_response(user_input, {}, detected_lang)
                save_to_database(user_input, response, audio_data)

                return jsonify({
                    "answer_text": assistant_reply,
                    "detected_lang": detected_lang,
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

        assistant_reply, audio_data, response = handle_llm_response(user_input, conversation_context, detected_lang)
        save_to_database(user_input, response, audio_data)

        return jsonify({
            "answer_text": assistant_reply,
            "detected_lang": detected_lang,
        })
    else:
        return jsonify({"error": "User not authenticated"}), 401


# Function to save conversation to database
def save_to_database(user_input, response, audio_data):
    # Generate embedding for the user message
    embedding = openai.embed_query(user_input)

    # Convert embedding to bytes for storage
    embedding_bytes = np.array(embedding).tobytes()

    conversations_summary = memory_summary.load_memory_variables({})
    conversations_summary_str = json.dumps(conversations_summary)

    timezone = pytz.timezone('Europe/Madrid')
    created_at = datetime.now(timezone)

    new_memory = Memory(
        user_name=current_user.name,
        owner_id=current_user.id,
        user_message=user_input,
        llm_response=response,
        audio_datas=audio_data,
        embedding=embedding_bytes,
        conversations_summary=conversations_summary_str,
        created_at=created_at
    )

    print(f'Saving to database:\n'
          f'owner_id: {new_memory.owner_id}\n'
          f'user_name: {new_memory.user_name}\n'
          f'user_message: {new_memory.user_message}\n'
          f'llm_response: {new_memory.llm_response}\n'
          f'conversations_summary: {new_memory.conversations_summary}\n'
          f'created_at: {created_at}') 
    
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
