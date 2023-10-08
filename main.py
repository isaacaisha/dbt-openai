from flask import Flask, render_template, request, jsonify, send_file
from flask_wtf import FlaskForm
from flask_caching import Cache
from wtforms import SubmitField, TextAreaField, validators
from openai.error import RateLimitError
from datetime import datetime, timedelta
import os
import re
import time
import openai
from gtts import gTTS

app = Flask(__name__)
app.secret_key = "any-string-you-want-just-keep-it-secret"

# Set up OpenAI API credentials
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Initialize an empty conversation list
conversation = []

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Set the maximum number of messages to retain
MAX_CONVERSATION_LENGTH = 5

# ------------------------------------------------------ VARIABLES ----------------------------------------------------#
time_sec = time.localtime()
current_year = time_sec.tm_year
# getting the current date and time
current_datetime = datetime.now()
# getting the time from the current date and time in the given format
current_time = current_datetime.strftime("%a %d %B")


# -------------------------------------------------------- CLASS ------------------------------------------------------#
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


# ------------------------------------------------------- FUNCTION ----------------------------------------------------#
@app.route("/", methods=["GET", "POST"])
def home():
    writing_text_form = TextAreaForm()
    error_message = None  # Initialize an error message variable
    answer = None  # Initialize the generated text variable

    if request.method == "POST" and writing_text_form.validate_on_submit():
        writing_text_data = request.form['writing_text']  # Get the input from the textarea

        try:
            # Use the get_completion function to generate text
            answer = answer(writing_text_data)
            # Process the answer before passing it to the template
            answer = post_process_answer(answer)
        except RateLimitError:
            error_message = "You exceeded your current quota, please check your plan and billing details."

    return render_template('index.html', year=current_year, date=current_time,
                           writing_text_form=writing_text_form,
                           answer=answer,  # Pass the generated text to the template
                           error_message=error_message)  # Pass the error message if needed


# Function to remove older messages from the conversation
def trim_conversation():
    global conversation
    if len(conversation) > MAX_CONVERSATION_LENGTH:
        # Calculate the timestamp threshold to retain only recent messages
        timestamp_threshold = datetime.now() - timedelta(minutes=7)  # Adjust the time threshold as needed

        # Filter out messages that are older than the threshold
        conversation = [
            msg for msg in conversation if  datetime.fromisoformat(msg.get('timestamp')) > timestamp_threshold
        ]


@app.route('/answer', methods=['POST'])
@cache.cached(timeout=19)  # Cache the response for 19 seconds
def answer():
    user_message = request.form['prompt']

    # Trim the conversation history before adding a new message
    trim_conversation()

    # Get the current timestamp as a string
    timestamp = datetime.now().isoformat()

    # Extend the conversation with the user's message
    # Append the user's message to the conversation with a timestamp
    conversation.append({
        "role": "user",
        "content": user_message
    })

    # Use OpenAI's GPT to generate the answer based on the conversation
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=conversation
    )

    # Get the assistant's reply
    assistant_reply = response.choices[0].message['content']

    # Post-process the answer for readability (if needed)
    assistant_reply = post_process_answer(assistant_reply)

    # Convert the text response to speech using gTTS
    tts = gTTS(assistant_reply)

    # Create a temporary audio file
    audio_file_path = 'temp_audio.mp3'
    tts.save(audio_file_path)

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
        "timestamp": timestamp
    })


# Serve the audio file
@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return send_file(audio_file_path, as_attachment=True)


# Define a function for post-processing the answer
def post_process_answer(answer):
    # You can add your post-processing logic here
    # For example, you can filter out unwanted content or format the answer
    # Example post-processing:

    # Convert newlines to HTML line breaks
    answer = answer.replace('\n', '<br>')

    # Remove HTML tags
    answer = re.sub('<.*?>', '', answer)
    return answer


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    temp_audio_file = 'temp_audio.mp3'
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
