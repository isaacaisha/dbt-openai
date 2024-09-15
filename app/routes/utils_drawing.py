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

from dataclasses import dataclass


load_dotenv(find_dotenv())

@dataclass
class APIContext:
    api_key: str
    client: OpenAI

# Initialize the context
api_context = APIContext(
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")),
    # API Key for DeepAI
    api_key = os.getenv("DEEPAI_API_KEY")
)


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



def process_image_with_api(image_data, api_url, api_key, additional_data=None):
    if not image_data:
        raise ValueError("image_data is required.")

    image_data = fix_base64_padding(image_data)
    image_bytes = base64.b64decode(image_data)
    print(f"Decoded image bytes length: {len(image_bytes)}")

    headers = {
        'api-key': api_key
    }

    files = {'image': ('image.jpg', image_bytes)}
    data = additional_data if additional_data else {}

    response = requests.post(
        api_url,
        files=files,
        data=data,
        headers=headers
    )

    if response.status_code == 200:
        response_data = response.json()
        image_url = response_data['output_url']
        print(f"Generated image URL: {image_url}")
        return image_url
    else:
        raise ValueError(f"DeepAI API error: {response.text}")
    

def handle_generations(generate_draw, image_data, context: APIContext):
    response = context.client.images.generate(
        model="dall-e-3",
        prompt=generate_draw,
        style="vivid",
    )
    image_url = response.data[0].url
    print(f"Generated image URL: {image_url}")
    return image_url

def handle_edits(generate_draw, image_data, context: APIContext):
    api_url = "https://api.deepai.org/api/image-editor"
    additional_data = {'text': generate_draw}
    return process_image_with_api(image_data, api_url, context.api_key, additional_data)

def handle_face_to_sticker(generate_draw, image_data, context: APIContext):
    api_url = "https://api.deepai.org/api/face-to-sticker"
    return process_image_with_api(image_data, api_url, context.api_key)

def generate_drawing_from(generate_draw, generation_type, image_data, context: APIContext):
    try:
        handlers = {
            'generations': handle_generations,
            'edits': handle_edits,
            'face-to-sticker': handle_face_to_sticker,
        }

        if generation_type not in handlers:
            raise ValueError(f"Unknown generation type: {generation_type}")

        return handlers[generation_type](generate_draw, image_data, context)

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


@dataclass
class DrawingData:
    user_name: str
    user_prompt: str
    analysis_text: str
    audio_url: str
    image_url: str

def save_drawing_datas(drawing_data: DrawingData):
    try:
        new_entry = DrawingDatabase(
            user_name=drawing_data.user_name,
            user_prompt=drawing_data.user_prompt,
            analysis_text=drawing_data.analysis_text,
            audio_url=drawing_data.audio_url,
            image_url=drawing_data.image_url,
        )
        db.session.add(new_entry)
        db.session.commit()
        return new_entry.id
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"Error saving drawing data: {e}")
        return None
