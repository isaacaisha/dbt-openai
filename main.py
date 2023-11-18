import os
import openai
import secrets
import warnings
import pytz
import json
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
from datetime import datetime
from gtts import gTTS
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryBufferMemory
from database import get_db
from models import Memory, db

warnings.filterwarnings('ignore')

_ = load_dotenv(find_dotenv())  # read local .env file

app = Flask(__name__)

openai.api_key = os.environ['OPENAI_API_KEY']

# Generate a random secret key
secret_key = secrets.token_hex(199)
# Set it as the Flask application's secret key
app.secret_key = secret_key

# Initialize an empty conversation chain
llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=19)


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


app.config[
    'SQLALCHEMY_DATABASE_URI'] = f"postgresql://{os.environ['user']}:{os.environ['password']}@{os.environ['host']}:{os.environ['port']}/{os.environ['database']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

    # Fetch memories from the database
    with get_db() as db:
        memories = db.query(Memory).all()

    # Concatenate memories for LLM input
    qdocs = "".join([memory.conversations_summary for memory in memories])
    memory_buffer = memory.buffer
    summary_conversation = memory_summary.load_memory_variables({})


@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    answer = None

    if request.method == "POST" and writing_text_form.validate_on_submit():
        user_input = request.form['writing_text']

        # Use the LLM to generate a response based on user input
        response = conversation.predict(input=user_input)

        answer = response['output'] if response else None

    # Retrieve the last entry from qdocs
    last_entry = qdocs.split("}")[-2] + "}"  # Assuming each entry ends with "}"
    print(f'last_entry_home:\n{last_entry}\n')

    memory_buffer = memory.buffer
    summary_buffer = memory_summary.load_memory_variables({})
    print(f'memory_buffer_home:\n{memory_buffer}\n')
    print(f'summary_buffer_home:\n{summary_buffer}\n')

    return render_template('index.html', writing_text_form=writing_text_form, answer=answer,
                           memory_load=last_entry, memory_buffer=memory_buffer, summary_buffer=summary_buffer,
                           date=datetime.now().strftime("%a %d %B %Y"))


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']

    # Call LLM
    response = llm.call_as_llm(f"{qdocs} Question: {user_message}")

    # Check if the response is a string, and if so, use it as the assistant's reply
    if isinstance(response, str):
        assistant_reply = response
    else:
        # If it's not a string, access the assistant's reply as you previously did
        assistant_reply = response.choices[0].message['content']

    # Convert the text response to speech using gTTS
    tts = gTTS(assistant_reply)

    # Create a temporary audio file
    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)

    memory_summary.save_context({"input": f"{user_message}"}, {"output": f"{response}"})
    conversations_summary = memory_summary.load_memory_variables({})
    conversations_summary_str = json.dumps(conversations_summary)  # Convert to string

    current_time = datetime.now(pytz.timezone('Europe/Paris'))

    # Access the database session using the get_db function
    with get_db() as db:
        # Create a new Memory object with the data
        new_memory = Memory(
            user_message=user_message,
            llm_response=assistant_reply,
            conversations_summary=conversations_summary_str,
            created_at=current_time,
        )

        # Add the new memory to the session
        db.add(new_memory)

        # Commit changes to the database
        db.commit()

    print(f'User Input: {user_message} 😎')
    print(f'LLM Response:\n{assistant_reply} 😝\n')

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
    # Retrieve the last entry from qdocs
    last_entry = qdocs.split("}")[-2] + "}"
    #print(f'qdocs:\n{qdocs}\n')
    print(f'last_entry:\n{last_entry}\n')

    print(f'memory_buffer:\n{memory_buffer}\n')
    print(f'summary_conversation:\n{summary_conversation}\n')

    return render_template('show-history.html', memory_load=last_entry, memory_buffer=memory_buffer,
                           summary_conversation=summary_conversation, date=datetime.now().strftime("%a %d %B %Y"))


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
