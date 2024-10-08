# MAIN.PY

import os
import logging
from app import create_app
from asgiref.wsgi import WsgiToAsgi


# Configure logging to log errors only
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

# Create the WSGI app
app = create_app()

# Wrap the WSGI app with WsgiToAsgi
asgi_app = WsgiToAsgi(app)


if __name__ == '__main__':
    try:
        # This runs the Flask development server only if the script is executed directly
        app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    except Exception as e:
        logging.error(f"Application error: {e}", exc_info=True)
