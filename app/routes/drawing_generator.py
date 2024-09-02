# DRAWING_GENERATOR.PY

import os
import traceback

from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for
from flask_login import current_user
from app.routes.utils_drawing import api_key, client, text_to_speech, analyze_image, generate_drawing_from, save_drawing_datas
from app.app_forms import TextAreaDrawingIndex
from datetime import datetime


generator_drawing_bp = Blueprint('drawing_generator', __name__, template_folder='templates', static_folder='static')

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Correct the path to point to the static/media directory in the app folder
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, '..', 'static')  # Go up one level to the app directory
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the media directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)


@generator_drawing_bp.route("/drawing-generator", methods=["GET", "POST"])
def drawing_index():
    # Allow access to both authenticated and unauthenticated users
    user_name = current_user.name if current_user.is_authenticated else "anonymous"

    drawing_form = TextAreaDrawingIndex()
    user_input = None

    if request.method == "POST":
        data = request.get_json()
        if not data or 'generate_draw' not in data or 'type' not in data:
            return jsonify({'error': 'Prompt and type are required to generate a drawing.'}), 400
        
        generate_draw = data['generate_draw']
        generation_type = data['type']
        image_data = data.get('image_data')

        try:
            drawing_url = generate_drawing_from(generate_draw, generation_type, image_data, api_key, client)

            # Save the generated drawing data to the database
            save_drawing_datas(user_name, generate_draw, drawing_url)

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


@generator_drawing_bp.route("/drawing-analyze", methods=["POST"])
def analyze_drawing():
    # Allow access to both authenticated and unauthenticated users
    user_name = current_user.name if current_user.is_authenticated else "anonymous"

    file = request.files.get('analyze_image_upload')
    if not file:
        return jsonify({'error': 'No file uploaded.'}), 400

    try:
        # Convert the uploaded file to base64
        description = analyze_image(file)

        # Extract the analysis text
        analysis_text = description['choices'][0]['message']['content']

        # Generate the audio file from the analysis text
        audio_filename = f"image_analysis_audio.mp3"
        text_to_speech(analysis_text, audio_filename, AUDIO_FOLDER_PATH)

        # Create the audio file URL
        audio_url = url_for('static', filename=f'media/{audio_filename}')
        print(f"Generated audio URL: {audio_url}")

        # Save the analysis result and audio URL to the database using save_drawing_datas
        save_drawing_datas(user_name, analysis_text, audio_url)

        # Return the analysis text and audio file URL
        print(f"'description': {description}, 'audio_url': {audio_url}")
        return jsonify({'description': description, 'audio_url': audio_url}), 200
    except FileNotFoundError as e:
        flash(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Error processing image: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to process image.'}), 500
