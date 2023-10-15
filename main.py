from flask import Flask, render_template, request, jsonify, send_file, session
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
from openai.error import RateLimitError
from datetime import datetime
import os
import re
import openai
from gtts import gTTS
import warnings
from dotenv import load_dotenv, find_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import sqlite3

# Get the current date
current_date = datetime.now().date()

# Define the date after which the model should be set to "gpt-3.5-turbo"
target_date = datetime(2024, 6, 12).date()

# Set the model variable based on the current date
if current_date > target_date:
    llm_model = "gpt-3.5-turbo"
else:
    llm_model = "gpt-3.5-turbo-0301"

# Load environment variables from .env file
_ = load_dotenv(find_dotenv())

# Set up OpenAI API credentials
openai.api_key = os.environ['OPENAI_API_KEY']

# Initialize Flask app and SQLite database connection
app = Flask(__name__)
app.secret_key = os.urandom(25)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///conversation_history.db'

# Suppress warnings
warnings.filterwarnings('ignore')

# Initialize SQLite database
with app.app_context():
    db = sqlite3.connect('conversation_history.db')
    cursor = db.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS conversation (role TEXT, content TEXT)')
    db.commit()
    db.close()


class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    error_message = None
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_message = request.form['writing_text']

        try:
            answer = get_openai_response(user_message)
        except RateLimitError:
            error_message = "You exceeded your current quota, please check your plan and billing details."

    return render_template('index.html', writing_text_form=writing_text_form, answer=answer,
                           date=datetime.now().strftime("%a %d %B %Y"), error_message=error_message)


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']
    print(f'User Input:\n{user_message} 😎\n')

    # Store the conversation in the SQLite database
    with app.app_context():
        db = sqlite3.connect('conversation_history.db')
        cursor = db.cursor()
        cursor.execute('INSERT INTO conversation (role, content) VALUES (?, ?)', ('user', user_message))
        db.commit()
        db.close()


    # Retrieve the entire conversation history from the database
    with app.app_context():
        db = sqlite3.connect('conversation_history.db')
        cursor = db.cursor()
        cursor.execute('SELECT role, content FROM conversation')
        conversation_data = cursor.fetchall()
        db.close()

        # Debug print to check conversation data
        print(conversation_data)

    conversation = []

    for role, content in conversation_data:
        conversation.append({
            "role": role,
            "content": content
        })

    response = get_openai_response(user_message, conversation)
    response = post_process_answer(response)

    tts = gTTS(response)
    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)
    print(f'Chat GPT Response:\n{response} 😝\n')

    return jsonify({
        "answer_text": response,
        "answer_audio_path": audio_file_path,
    })


def get_openai_response(user_message, conversation):
    response = ChatOpenAI(temperature=0.0, model=llm_model)

    # Use the conversation history passed as an argument
    memory = ConversationBufferMemory(conversation=conversation)
    conversation_ = ConversationChain(
        llm=response,
        memory=memory,
        verbose=False
    )

    response = conversation_.predict(input=user_message)
    return response


# Serve the audio file
@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return send_file(audio_file_path, as_attachment=True)


def post_process_answer(answer):
    answer = answer.replace('\n', '<br>')
    answer = re.sub('<.*?>', '', answer)
    return answer


if __name__ == '__main__':
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
