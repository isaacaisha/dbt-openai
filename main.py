from flask import Flask, render_template, request, jsonify, send_file
import openai
from gtts import gTTS
import os
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
from openai.error import RateLimitError
import re
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = "any-string-you-want-just-keep-it-secret"

# Set up OpenAI API credentials
openai.api_key = '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'

# Initialize an empty conversation list
conversation = []


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


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']

    # Extend the conversation with the user's message
    conversation.append({"role": "user", "content": user_message})

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
        "answer_audio_path": audio_file_path
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

    app.run(debug=True, host='0.0.0.0')
