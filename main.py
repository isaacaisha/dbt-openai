import os
from app import create_app

app = create_app()


@app.route('/keep-alive', methods=['POST'])
def keep_alive():
    # Do nothing, just return a response
    return '', 204  # No content


if __name__ == '__main__':
    # Clean up any previous temporary audio files
    home_temp_audio_file = 'home_temp_audio.mp3'
    if os.path.exists(home_temp_audio_file):
        os.remove(home_temp_audio_file)

    interface_temp_audio_file = 'interface_temp_audio.mp3'
    if os.path.exists(interface_temp_audio_file):
        os.remove(interface_temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
