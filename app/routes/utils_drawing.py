# UTILS_DRAWING.PY

import base64
import io
import os
import requests
import traceback

from dotenv import load_dotenv, find_dotenv

from openai import OpenAI

from PIL import Image
from gtts import gTTS

from sqlalchemy.exc import SQLAlchemyError
from app.memory import DrawingDatabase, db


load_dotenv(find_dotenv())

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# API Key for DeepAI
api_key = os.getenv("DEEPAI_API_KEY")


def fix_base64_padding(base64_str):
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    return base64_str


def get_image_base64(image_path):
    """Encode image file to base64."""
    with Image.open(image_path) as image:
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    

def text_to_speech(text, filename, audio_folder_path):
    tts = gTTS(text)
    audio_file_path = os.path.join(audio_folder_path, filename)
    tts.save(audio_file_path)

    if os.path.exists(audio_file_path):
        print(f"File successfully saved: {audio_file_path}")
    else:
        print(f"Failed to save file: {audio_file_path}")
        raise FileNotFoundError(f"Audio file was not saved to {audio_file_path}")
    
    return audio_file_path


def generate_drawing_from(generate_draw, generation_type, image_data, api_key, client):
    try:
        response = None
        
        headers = {
            'api-key': api_key
        }

        if generation_type == 'generations':
            response = client.images.generate(
                model="dall-e-3",
                prompt=generate_draw,
                style="vivid",
            )
            image_url = response.data[0].url
            print(f"Generated image URL: {image_url}")
            return image_url
        
        elif generation_type == 'edits':
            if not image_data:
                raise ValueError("image_data is required for 'edits' generation type.")
            
            image_data = fix_base64_padding(image_data)
            image_bytes = base64.b64decode(image_data)
            print(f"Decoded image bytes length: {len(image_bytes)}")

            response = requests.post(
                "https://api.deepai.org/api/image-editor",
                files={'image': image_bytes},
                data={'text': generate_draw},
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                image_url = response_data['output_url']
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

            response = requests.post(
                "https://api.deepai.org/api/face-to-sticker",
                files={'image': image_bytes},
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                image_url = response_data['output_url']
                print(f"Generated image URL: {image_url}")
                return image_url
            else:
                raise ValueError(f"DeepAI API error: {response.text}")

        else:
            raise ValueError(f"Unknown generation type: {generation_type}")

    except Exception as e:
        print(f"Exception occurred during drawing generation: {e}")
        traceback.print_exc()
        raise


def analyze_image(image_data):
    """Analyze the image by sending it directly to OpenAI's API."""
    base64_image = get_image_base64(image_data)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    
    payload = {
        "model": "gpt-4o",
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
    

def save_drawing_datas(user_name, user_prompt, image_url):
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
