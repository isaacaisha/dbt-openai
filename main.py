import os

from app import create_app


from app.routes.home_process import (home as home_conversations, home_answer as answer_home,
                                     home_audio as audio_home)

from app.routes.process_interface_conversation import (conversation_interface as process_interface_llm,
                                                       interface_answer as process_answer_interface,
                                                       save_to_database as process_database,
                                                       interface_serve_audio as process_interface_audio_llm)


app = create_app()


# ------------------------------------------ @app.routes --------------------------------------------------------------#
@app.route('/', methods=['GET', 'POST'])
def home():
    return home_conversations()


@app.route('/home/answer', methods=['POST'])
def home_answer():
    return answer_home()


@app.route('/home-audio')
def home_audio():
    return audio_home()


@app.route('/conversation-interface', methods=['GET', 'POST'])
def conversation_interface():
    return process_interface_llm()


@app.route('/interface/answer', methods=['POST'])
def interface_answer():
    return process_answer_interface()


@app.route('/save-to-database', methods=['POST'])
def save_to_database(user_input, response):
    return process_database(user_input, response)


@app.route('/interface-audio')
def interface_serve_audio():
    return process_interface_audio_llm()


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    home_temp_audio_file = 'home_temp_audio.mp3'
    if os.path.exists(home_temp_audio_file):
        os.remove(home_temp_audio_file)

    interface_temp_audio_file = 'interface_temp_audio.mp3'
    if os.path.exists(interface_temp_audio_file):
        os.remove(interface_temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
