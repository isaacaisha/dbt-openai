# DRAWING_GENERATOR.PY

import base64
import io
import os
import traceback
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

            # Save the generated drawing data to the database
            user_name = current_user.name
            save_generated_drawing(user_name, generate_draw, drawing_url)

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


def fix_base64_padding(base64_str):
    # Add padding if necessary
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    return base64_str


def generate_drawing_from(generate_draw, generation_type, image_data):
    try:
        if generation_type == 'generations':
            response = client.images.generate(
                model="dall-e-3",
                prompt=generate_draw,
                style="vivid",
            )
        elif generation_type in ('edits', 'variations'):
            if not image_data:
                raise ValueError("image_data is required for 'edits' and 'variations' generation types.")
            
            # Fix padding for base64 image data
            image_data = fix_base64_padding(image_data)

            # Decode base64 image data
            image_bytes = base64.b64decode(image_data)
            print(f"Decoded image bytes length: {len(image_bytes)}")

            image = Image.open(io.BytesIO(image_bytes))
            print(f"Image opened: Size={image.size}, Mode={image.mode}")

            # Convert image to 'RGBA' format if it's not already
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            buffered_image = io.BytesIO()
            image.save(buffered_image, format="PNG")
            buffered_image.seek(0)

            if generation_type == 'edits':
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
        if not response.data or len(response.data) == 0:
            raise ValueError("No image data returned from the API.")

        image_url = response.data[0].url  # Access the URL from the response data
        print(f"Generated image URL: {image_url}")
        return image_url

    except Exception as e:
        print(f"Exception occurred during drawing generation: {e}")
        print(f"Generation type: {generation_type}, Prompt: {generate_draw}")
        traceback.print_exc()  # Print the traceback for debugging
        raise


def save_generated_drawing(user_name, user_prompt, image_url):
    try:
        new_entry = DrawingDatabase(
            user_name=user_name,
            user_prompt=user_prompt,
            image_url=image_url,
        )
        db.session.add(new_entry)
        db.session.commit()
        return new_entry.id
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error saving drawing data: {e}")
        return None
