import os
import openai
from dotenv import load_dotenv, find_dotenv
import secrets
from flask import Flask, render_template, request, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
from datetime import datetime
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
import warnings

from pydantic import BaseModel
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor
import pytz
import json

warnings.filterwarnings('ignore')

app = Flask(__name__)
_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
# Generate a random secret key
secret_key = secrets.token_hex(199)

# Set it as the Flask application's secret key
app.secret_key = secret_key

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")  # Set your desired LLM model here
memory = ConversationBufferMemory()
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


class Memory(BaseModel):
    user_message: str
    llm_response: str
    conversations_summary: str
    published: bool = True
    rating: Optional[int] = None
    created_at: str


try:
    # Connect to your postgres DB
    conn = psycopg2.connect(host='localhost', database='dbt_openai_api', port=5433,
                            user='postgres', password='touremedina', cursor_factory=RealDictCursor)
    # Open a cursor to perform database operations
    cursor = conn.cursor()
    print('Database connection was successful 😎')
except Exception as error:
    print(f'Connection with the database failed 😭\nError: {error} 😝')


@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']

        # Use the LLM to generate a response based on user input
        response = conversation.predict(input=user_input)

        answer = response['output'] if response else None

    memory_load = memory.load_memory_variables({})
    memory_buffer = memory.buffer

    memory_summary.save_context({"input": f"Summarize the memory.buffer:"}, {"output": f"{memory_buffer}"})
    summary_buffer = memory_summary.load_memory_variables({})
    print(f'Summary Buffer:\n{summary_buffer}\n')

    return render_template('index.html', writing_text_form=writing_text_form, answer=answer,
                           memory_load=memory_load, memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']

    # Use the LLM to generate a response based on the user's message
    response = conversation.predict(input=user_message)

    current_time = datetime.now(pytz.timezone('Europe/Paris'))

    if isinstance(response, str):
        # If the response is a string, use it directly as the assistant's reply
        assistant_reply = response
        llm_response = response  # Store the response to be saved in the database
    else:
        # Access the assistant's reply from the response object
        assistant_reply = response['output']
        llm_response = response.choices[0].message['content']  # Save the response content for the database

    # Save the conversation summary
    memory_buffer = memory.buffer
    memory_summary.save_context({"input": f"Summarize the memory.buffer:"}, {"output": f"{memory_buffer}"})
    conversations_summary = memory_summary.load_memory_variables({})
    conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

    # Insert the conversation data into the database
    insert_query = """
    INSERT INTO memory (user_message, llm_response, conversations_summary, published, rating, created_at)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    cursor.execute(insert_query, (user_message, llm_response, conversations_summary_str, True, 5, current_time))
    conn.commit()

    # Convert the text response to speech using gTTS
    tts = gTTS(assistant_reply)

    # Create a temporary audio file
    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)
    print(f'User Input:\n{user_message} 😎\n')
    print(f'LLM Response:\n{llm_response} 😝\n')
    print(f'conversations:\n{conversations_summary_str}')

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
    })


@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return send_file(audio_file_path, as_attachment=True)


@app.route('/show-history')
def show_story():
    memory_load = memory.load_memory_variables({})
    memory_buffer = memory.buffer
    print(f'Memory Buffer:\n{memory_buffer}\n')
    print(f'Memory Load:\n{memory_load}\n')
    print(f'Conversation:\n{conversation}\n')

    memory_summary.save_context({"input": f"Summarize the conversation:"}, {"output": f"{conversation}"})
    summary_conversation = memory_summary.load_memory_variables({})
    print(f'Summary Conversation:\n{summary_conversation}\n')

    return render_template('show-history.html', memory_load=memory_load, memory_buffer=memory_buffer,
                           conversation=conversation, summary_conversation=summary_conversation,
                           date=datetime.now().strftime("%a %d %B %Y"))


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
