# UTILS_INTERFACE.PY

import os
import json
import pytz
import numpy as np

from scipy.spatial.distance import cosine

from flask import jsonify
from flask_login import current_user

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langdetect import detect

from sqlalchemy.exc import SQLAlchemyError
from app.memory import Memory, db

from gtts import gTTS
from gtts.lang import tts_langs
from datetime import datetime

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

    # Initialize an empty flash message
    flash_message = None

    # Check if the language is supported
    if detected_lang not in tts_langs():
        flash_message = f"Language '{detected_lang}' not supported, falling back to English."
        detected_lang = 'en'  # Fallback to English

    tts = gTTS(assistant_reply, lang=detected_lang)
    audio_file_path = os.path.join(AUDIO_FOLDER_PATH, 'interface_temp_audio.mp3')
    tts.save(audio_file_path)

    with open(audio_file_path, 'rb') as audio_file:
        audio_data = audio_file.read()

    memory_summary.save_context({"input": f"{user_input}"}, {"output": f"{response}"})

    return assistant_reply, audio_data, response, flash_message


# Function to find the most relevant conversation based on user query
def find_most_relevant_conversation(user_query, embeddings):
    query_embedding = openai.embed_query(user_query)
    similarities = [1 - cosine(query_embedding, embedding) for embedding in embeddings]
    most_similar_index = np.argmax(similarities)
    return most_similar_index, similarities[most_similar_index]


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
