import json
import pytz

from flask import Blueprint, render_template, request, send_file, jsonify
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


home_conversation_bp = Blueprint('conversation_home', __name__)

llm = ChatOpenAI(temperature=0.0, model="gpt-4o")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=3)


@home_conversation_bp.route("/", methods=["GET", "POST"])
def home():
    return render_template('index.html', date=datetime.now().strftime("%a %d %B %Y"))


@home_conversation_bp.route("/conversation-test", methods=["GET", "POST"])
def home_test():
    home_form = TextAreaFormIndex()
    user_input = None
    response = None

    if request.method == "POST" and home_form.validate_on_submit():
        # Retrieve form data using the correct key
        user_input = request.form['text_writing']

        # Use the LLM to generate a response based on user input
        response = conversation.predict(input=user_input)

        print(f"user_input: {user_input}")
        print(f"response: {response}\n")

    memory_buffer = memory.buffer_as_str
    memory_load = memory.load_memory_variables({})

    return render_template('conversation-test.html', home_form=home_form,
                           current_user=current_user, user_input=user_input, response=response,
                           memory_buffer=memory_buffer, memory_load=memory_load,
                           date=datetime.now().strftime("%a %d %B %Y"))


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

    # Convert the text response to speech using gTTS
    tts = gTTS(assistant_reply, lang=detected_lang)

    # Create a temporary audio file
    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)
    print(f'LLM Response:\n{assistant_reply} 😝\n')

    memory_summary.save_context({"input": f"{user_message}"}, {"output": f"{response}"})

    save_to_test_database(user_message, response)

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
        "detected_lang": detected_lang,
    })


@home_conversation_bp.route('/home-audio')
def home_audio():
    audio_file_path = 'temp_audio.mp3'
    try:
        return send_file(audio_file_path, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404
    

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

    print(f'user_message: {new_memory.user_message}\nllm_response: {new_memory.llm_response}\n'
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
