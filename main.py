from flask import Flask, render_template, request, jsonify, send_file
from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, validators
from openai.error import RateLimitError
from datetime import datetime
import os
import re
import openai
from gtts import gTTS


app = Flask(__name__)
app.secret_key = "any-string-you-want-just-keep-it-secret"

# Set up OpenAI API credentials
openai.api_key = os.environ.get("OPENAI_API_KEY")

# ------------------------------------------------------ VARIABLES ----------------------------------------------------#
# Initialize an empty conversation list
conversation = []


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
        # writing_text_data = request.form['writing_text']  # Get the input from the textarea

        try:
            # Process the answer before passing it to the template
            answer = post_process_answer(answer)
        except RateLimitError:
            error_message = "You exceeded your current quota, please check your plan and billing details."

    return render_template('index.html', writing_text_form=writing_text_form, answer=answer,
                           date=datetime.now().strftime("%a %d %B %Y"), error_message=error_message)


@app.route('/answer', methods=['POST'])
def answer():
    user_message = request.form['prompt']
    print(f'User Input:\n{user_message} 😎\n')

    # Extend the conversation with the user's message
    conversation.append({
        "role": "user",
        "content": user_message
    })

    # Use OpenAI's GPT to generate the answer based on the conversation
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=conversation,
        temperature=0  # this is the degree of randomness model's output
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
    print(f'Chat GPT Response:\n{assistant_reply} 😝\n')

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
    })


# Serve the audio file
@app.route('/audio')
def serve_audio():
    audio_file_path = 'temp_audio.mp3'
    return send_file(audio_file_path, as_attachment=True)


# Define a function for post-processing the answer
def post_process_answer(answer):
    # You can add your post-processing logic here,
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
