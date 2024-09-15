# HOME_PROCESS.PY

import json
import os
import base64
import pytz

from flask import Blueprint, flash, render_template, request, jsonify, send_from_directory, url_for

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langdetect import detect

from app.routes.utils_drawing import analyze_image, text_to_speech, generate_drawing_from, save_drawing_datas, api_context

from sqlalchemy.exc import SQLAlchemyError
from app.memory import MemoryTest, db
from app.app_forms import TextAreaFormIndex, TextAreaDrawingIndex

from gtts import gTTS
from gtts.lang import tts_langs
from datetime import datetime


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


def handle_conversation_submission(home_form):
    if home_form.validate_on_submit() and 'text_writing' in request.form:
        user_input = request.form['text_writing']
        response = conversation.predict(input=user_input)
        print(f"user_input: {user_input}")
        print(f"response: {response}\n")
        flash("Conversation generated successfully!", "success")
        return user_input, response
    return None, None


def handle_drawing_generation(drawing_form):
    if drawing_form.validate_on_submit() and 'generate_draw' in request.form:
        generate_draw = request.form.get('generate_draw')
        generation_type = request.form.get('generation_type')
        image_data = get_image_data_from_request()

        try:
            drawing_url = generate_drawing_from(generate_draw, generation_type, image_data, api_context)
            save_drawing_datas('anonymous', generate_draw, None, None, drawing_url)  # Using None for analysis and audio
            flash("Drawing successfully generated!", "success")
            return jsonify({'drawing_url': drawing_url}), 200
        except Exception as e:
            print(f"Exception occurred during drawing generation: {e}")
            flash("Failed to generate the drawing. Please try again.", "error")
    return None


def handle_image_analysis(drawing_form):
    if drawing_form.validate_on_submit() and 'analyze_image_upload' in request.files:
        file = request.files['analyze_image_upload']
        if file:
            description = analyze_image(file)
            analysis_text = description['choices'][0]['message']['content']
            audio_filename = f"image_analysis_audio.mp3"
            text_to_speech(analysis_text, audio_filename, AUDIO_FOLDER_PATH)

            audio_url = url_for('static', filename=f'media/{audio_filename}')
            print(f"Generated audio URL: {audio_url}")
            save_drawing_datas('anonymous', "Image Analysis", analysis_text, audio_url, None)
            flash("Image analysis completed!", "success")
            return jsonify({'description': description, 'audio_url': audio_url}), 200
    return None


def get_image_data_from_request():
    if 'image_upload' in request.files:
        file = request.files['image_upload']
        if file and file.filename != '':
            return base64.b64encode(file.read()).decode('utf-8')
    return None


@home_conversation_bp.route("/conversation-test", methods=["GET", "POST"])
def home_test():
    home_form = TextAreaFormIndex()
    drawing_form = TextAreaDrawingIndex()
    user_input, response = None, None
    images = IMAGES

    try:
        if request.method == "POST":
            user_input, response = handle_conversation_submission(home_form)

            drawing_response = handle_drawing_generation(drawing_form)
            if drawing_response:
                return drawing_response

            analysis_response = handle_image_analysis(drawing_form)
            if analysis_response:
                return analysis_response

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        return render_template('conversation-test.html', home_form=home_form, drawing_form=drawing_form,
                               images=images, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               date=datetime.now().strftime("%a %d %B %Y"))
    except Exception as e:
        print(f"Exception occurred: {e}")
        flash("An error occurred. Please try again.", "error")
        return render_template('conversation-test.html', home_form=home_form, drawing_form=drawing_form,
                               images=images, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               date=datetime.now().strftime("%a %d %B %Y")), 500


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

    # Initialize an empty flash message
    flash_message = None

    # Check if the language is supported
    if detected_lang not in tts_langs():
        flash_message = f"Language '{detected_lang}' not supported, falling back to English."
        detected_lang = 'en'  # Fallback to English

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
        "flash_message": flash_message,
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
