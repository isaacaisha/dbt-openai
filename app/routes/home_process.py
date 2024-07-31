import json
import os
import pytz

from flask import Blueprint, flash, render_template, request, send_file, jsonify, send_from_directory, url_for
from flask_login import current_user
from gtts import gTTS
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langdetect import detect
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from app.app_forms import TextAreaFormIndex
from app.memory import MemoryTest, db


home_conversation_bp = Blueprint('conversation_home', __name__, template_folder='templates', static_folder='static')

llm = ChatOpenAI(temperature=0.0, model="gpt-4o")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=3)

IMAGES =['siisi.jpg', 'mommy.jpg', 'corazones.jpeg', 'logo_ai.jpg', 'logo0.jpg',
         'logo3.jpg', 'space.jpg', 'a.jpg', 'c.jpg', 'd.jpg', 'b.jpg', 'o.jpg',
         'i.jpg', 'f.jpg', 's.jpg', 'o.jpg', 'k.jpg', 'p.jpg', 'n.jpg', 'i.jpg', 
         'q.jpg', 'm.jpg', 'r.jpg', 'l.jpg', 'istock5.jpg',
         ]

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)


@home_conversation_bp.route("/", methods=["GET", "POST"])
def home():
    return render_template('index.html', date=datetime.now().strftime("%a %d %B %Y"))


@home_conversation_bp.route("/conversation-test", methods=["GET", "POST"])
def home_test():
    home_form = TextAreaFormIndex()
    user_input = None
    response = None
    images = IMAGES

    try:
        if request.method == "POST" and home_form.validate_on_submit():
            # Retrieve form data using the correct key
            user_input = request.form['text_writing']

            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)

            print(f"user_input: {user_input}")
            print(f"response: {response}\n")

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        return render_template('conversation-test.html', home_form=home_form, images=images,
                               current_user=current_user, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               date=datetime.now().strftime("%a %d %B %Y"))
    except Exception as e:
        print(f"Exception occurred: {e}")
        return flash("An error occurred. Please try reformulating your question.", "error"), 500


@home_conversation_bp.route('/home/answer', methods=['POST'])
def home_answer():
    user_message = request.form['prompt']
    print(f'User Input:\n{user_message} 😎\n')

    # Detect the language of the user's message
    detected_lang = detect(user_message)

    # Extend the conversation with the user's message
    response = conversation.predict(input=user_message)

    # Check if the response is a string, and if so, use it as the assistant's reply
    if isinstance(response, str):
        assistant_reply = response
    else:
        # If it's not a string, access the assistant's reply as you previously did
        assistant_reply = response.choices[0].message['content']
            
    # Remove '#' and '*' from the response
    assistant_reply = assistant_reply.replace('#', '').replace('*', '')

    # Convert the text response to speech using gTTS
    tts = gTTS(assistant_reply, lang=detected_lang)

    # Create a temporary audio file
    audio_file_path = os.path.join(AUDIO_FOLDER_PATH, 'home_temp_audio.mp3')
    tts.save(audio_file_path)
    print(f'LLM Response:\n{assistant_reply} 😝\n')

    memory_summary.save_context({"input": f"{user_message}"}, {"output": f"{response}"})

    save_to_test_database(user_message, response)

    audio_url = url_for('conversation_home.serve_audio', filename='home_temp_audio.mp3')
    
    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_url,
        "detected_lang": detected_lang,
    })


@home_conversation_bp.route('/media/<filename>')
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER_PATH, filename)


# Function to save conversation to database
def save_to_test_database(user_message, response):
    conversations_summary = memory_summary.load_memory_variables({})
    conversations_summary_str = json.dumps(conversations_summary)

    timezone = pytz.timezone('Europe/Madrid')
    created_at = datetime.now(timezone)

    new_memory = MemoryTest(
        user_message=user_message,
        llm_response=response,
        conversations_summary=conversations_summary_str,
        created_at=created_at
    )

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
