import os
import logging
from app import create_app
from asgiref.wsgi import WsgiToAsgi


# Create the WSGI app
app = create_app()

# Wrap the WSGI app with WsgiToAsgi
asgi_app = WsgiToAsgi(app)


if __name__ == '__main__':
    try:
        home_temp_audio_file = 'home_temp_audio.mp3'
        if os.path.exists(home_temp_audio_file):
            os.remove(home_temp_audio_file)

        interface_temp_audio_file = 'interface_temp_audio.mp3'
        if os.path.exists(interface_temp_audio_file):
            os.remove(interface_temp_audio_file)

        # This runs the Flask development server only if the script is executed directly
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    except Exception as e:
        logging.error(f"Application error: {e}") 
