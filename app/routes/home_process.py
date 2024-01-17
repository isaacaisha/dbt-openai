from flask import Blueprint, render_template, flash, request, send_file, jsonify
from flask_login import current_user
from gtts import gTTS
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from datetime import datetime

from app.forms.app_forms import TextAreaFormIndex

home_conversation_bp = Blueprint('conversation_home', __name__)

llm = ChatOpenAI(temperature=0.0, model="gpt-3.5-turbo-0301")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)


@home_conversation_bp.route("/", methods=["GET", "POST"])
def home():
    home_form = TextAreaFormIndex()
    response = None
    user_input = None

    try:
        if request.method == "POST" and home_form.validate_on_submit():
            print(f"Form data: {home_form.data}\n")

            # Retrieve form data using the correct key
            user_input = request.form['text_writing']
            # Use the LLM to generate a response based on user input
            response = conversation.predict(input=user_input)

            print(f"user_input: {user_input}")
            print(f"response: {response}\n")

        memory_buffer = memory.buffer_as_str
        memory_load = memory.load_memory_variables({})

        return render_template('index.html', home_form=home_form,
                               current_user=current_user, user_input=user_input, response=response,
                               memory_buffer=memory_buffer, memory_load=memory_load,
                               date=datetime.now().strftime("%a %d %B %Y"))
    except Exception as err:
        flash(f'😭 RELOAD & RETRY Unexpected: {str(err)}, \ntype: {type(err)} 😭 ¡!¡')
        error_message = str(err)
        print(f"😭 Unexpected {err=}, {type(err)=} 😭")
        return render_template('index.html', error_message=error_message, home_form=home_form,
                               current_user=current_user, user_input=user_input, response=response,
                               date=datetime.now().strftime("%a %d %B %Y"))


@home_conversation_bp.route('/home/answer', methods=['POST'])
def home_answer():
    user_message = request.form['prompt']
    print(f'User Input:\n{user_message} 😎\n')

    # Extend the conversation with the user's message
    response = conversation.predict(input=user_message)

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
    print(f'LLM Response:\n{assistant_reply} 😝\n')

    # Return the response as JSON, including both text and the path to the audio file
    return jsonify({
        "answer_text": assistant_reply,
        "answer_audio_path": audio_file_path,
    })


@home_conversation_bp.route('/home-audio')
def home_audio():
    audio_file_path = 'temp_audio.mp3'
    try:
        return send_file(audio_file_path, as_attachment=True)
    except FileNotFoundError:
        return "File not found", 404
