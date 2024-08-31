# DRAWING_GENERATOR.PY

import base64
import io
import os
import requests
import traceback

from flask import Blueprint, flash, redirect, render_template, request, jsonify, url_for, current_app
from flask_login import current_user
from sqlalchemy.exc import SQLAlchemyError
from app.app_forms import TextAreaDrawingIndex
from PIL import Image
from openai import OpenAI
from app.memory import DrawingDatabase, db
from datetime import datetime


generator_drawing_bp = Blueprint('drawing_generator', __name__, template_folder='templates', static_folder='static')

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure directories exist
uploaded_images_path = os.path.join(STATIC_FOLDER_PATH, 'uploaded_images')
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# API Key for DeepAI
api_key = os.getenv("DEEPAI_API_KEY")
    

def fix_base64_padding(base64_str):
    # Add padding if necessary
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    return base64_str


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


def generate_drawing_from(generate_draw, generation_type, image_data):
    try:
        response = None  # Initialize the response variable
        
        headers = {
            'api-key': api_key
        }

        if generation_type == 'generations':
            response = client.images.generate(
                model="dall-e-3",
                prompt=generate_draw,
                style="vivid",
            )
            image_url = response.data[0].url  # Access the URL from the response data
            print(f"Generated image URL: {image_url}")
            return image_url
        
        elif generation_type == 'edits':
            if not image_data:
                raise ValueError("image_data is required for 'edits' generation type.")
            
            image_data = fix_base64_padding(image_data)
            image_bytes = base64.b64decode(image_data)
            print(f"Decoded image bytes length: {len(image_bytes)}")

            # Send request to DeepAI for editing the image
            response = requests.post(
                "https://api.deepai.org/api/image-editor",
                files={'image': image_bytes},
                data={'text': generate_draw},  # Use the prompt for editing
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                image_url = response_data['output_url']  # Access the URL from the response data
                print(f"Generated image URL: {image_url}")
                return image_url
            else:
                raise ValueError(f"DeepAI API error: {response.text}")

        elif generation_type == 'face-to-sticker':
            if not image_data:
                raise ValueError("image_data is required for 'face-to-sticker' generation type.")
            
            image_data = fix_base64_padding(image_data)
            image_bytes = base64.b64decode(image_data)
            print(f"Decoded image bytes length: {len(image_bytes)}")

            # Send request to DeepAI for creating image variations
            response = requests.post(
                "https://api.deepai.org/api/face-to-sticker",
                files={'image': image_bytes},
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                image_url = response_data['output_url']  # Access the URL from the response data
                print(f"Generated image URL: {image_url}")
                return image_url
            else:
                raise ValueError(f"DeepAI API error: {response.text}")

        else:
            raise ValueError(f"Unknown generation type: {generation_type}")

    except Exception as e:
        print(f"Exception occurred during drawing generation: {e}")
        print(f"Generation type: {generation_type}, Prompt: {generate_draw}")
        traceback.print_exc()  # Print the traceback for debugging
        raise


def get_image_base64(image_path):
    """Encode image file to base64."""
    with Image.open(image_path) as image:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")  # Assuming image is in a format that PIL can handle
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    

def analyze_image(image_data):
    """Analyze the image by sending it directly to OpenAI's API."""
    base64_image = get_image_base64(image_data)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What’s in this image?"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()


# Usage in your Flask route
@generator_drawing_bp.route("/drawing-analyze", methods=["POST"])
def analyze_drawing():
    if not current_user.is_authenticated:
        return jsonify({'error': 'Please login to access this page.'}), 401

    file = request.files.get('analyze_image_upload')
    if not file:
        return jsonify({'error': 'No file uploaded.'}), 400

    try:
        # Convert the uploaded file to base64
        description = analyze_image(file)
        return jsonify({'description': description}), 200
    except Exception as e:
        current_app.logger.error(f"Error processing image: {e}")
        return jsonify({'error': 'Failed to process image.'}), 500
    

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
