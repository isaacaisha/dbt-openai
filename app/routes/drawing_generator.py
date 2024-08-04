# DRAWING_GENERATOR.PY

import base64
import io
import os
from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import current_user
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from app.app_forms import TextAreaDrawingIndex
from app.memory import DrawingDatabase, db
from PIL import Image
from openai import OpenAI

generator_drawing_bp = Blueprint('drawing_generator', __name__, template_folder='templates', static_folder='static')

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@generator_drawing_bp.route("/drawing-generator", methods=["GET", "POST"])
def drawing_index():
    drawing_form = TextAreaDrawingIndex()
    user_input = None
    
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        data = request.get_json()
        if not data or 'generate_draw' not in data or 'type' not in data:
            return jsonify({'error': 'Prompt and type are required to generate a drawing.'}), 400

        generate_draw = data['generate_draw']
        generation_type = data['type']
        image_data = data.get('image_data')

        try:
            drawing_url = generate_drawing_from(generate_draw, generation_type, image_data)
            return jsonify({'drawing_url': drawing_url}), 200
        except ValueError as ve:
            print(f"ValueError occurred: {ve}")
            return jsonify({'error': str(ve)}), 400
        except Exception as e:
            print(f"Exception occurred: {e}")
            return jsonify({'error': "An error occurred. Please try reformulating your wishes."}), 500

    return render_template('drawing-generator.html', drawing_form=drawing_form, current_user=current_user,
                           user_input=user_input, drawing_url=None,
                           date=datetime.now().strftime("%a %d %B %Y"))


def generate_drawing_from(generate_draw, generation_type, image_data=None):
    if generation_type == 'generations':
        response = client.images.generate(
            model="dall-e-3",
            prompt=generate_draw,
            style="vivid",
        )
    elif generation_type in ('edits', 'variations'):
        if not image_data:
            raise ValueError("image_data is required for 'edits' and 'variations' generation types.")
        
        # Decode base64 image data
        image_data = image_data.split(",")[1]  # Remove data URI scheme
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))
        
        # Convert image to 'RGBA' format if it's not already
        if image.mode != 'RGBA':
            image = image.convert('RGBA')

        buffered_image = io.BytesIO()
        image.save(buffered_image, format="PNG")
        buffered_image.seek(0)

        if generation_type == 'edits':
            # For edits, no mask required; image transparency will be used instead
            response = client.images.edit(
                image=buffered_image,
                prompt=generate_draw,
            )
        else:  # generation_type == 'variations'
            response = client.images.create_variation(
                image=buffered_image,
            )
    else:
        raise ValueError(f"Unknown generation type: {generation_type}")

    # Check the response content
    print(f"API response: {response}")

    # Properly handle the response
    try:
        image_url = response.data[0].url  # Access the URL from the response data
        print(f"Generated image URL: {image_url}")
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error accessing response data: {e}")
        raise

    return image_url
