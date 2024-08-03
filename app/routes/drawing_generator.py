# DRAWING_GENERATOR.PY

import os
from venv import logger
from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import current_user
import openai
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.app_forms import TextAreaDrawingIndex
from app.memory import DrawingDatabase, db

generator_drawing_bp = Blueprint('drawing_generator', __name__, template_folder='templates', static_folder='static')

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

# Initialize OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

@generator_drawing_bp.route("/drawing-generator", methods=["GET", "POST"])
def drawing_index():
    drawing_form = TextAreaDrawingIndex()
    user_input = None
    
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated access attempt to conversation_interface")
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        data = request.get_json()
        if not data or 'generate_draw' not in data or 'type' not in data:
            return jsonify({'error': 'Prompt and type are required to generate a drawing.'}), 400

        generate_draw = data['generate_draw']
        generation_type = data['type']

        try:
            drawing_url = generate_drawing_from(generate_draw, generation_type)
            return jsonify({'drawing_url': drawing_url}), 200
        
        except Exception as e:
            print(f"Exception occurred: {e}")
            return jsonify({'error': "An error occurred. Please try reformulating your wishes."}), 500

    return render_template('drawing-generator.html', drawing_form=drawing_form, current_user=current_user,
                           user_input=user_input, drawing_url=None,
                           date=datetime.now().strftime("%a %d %B %Y"))

def generate_drawing_from(generate_draw, generation_type):
    client = openai.OpenAI()

    response = client.images.generate(
        model="dall-e-3",
        prompt=generate_draw,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    return image_url
