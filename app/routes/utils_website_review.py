# UTILS_WEBSITE_REVIEW.PY

import os
import re
import urllib.parse
import asyncio
import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv, find_dotenv
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from dataclasses import dataclass
from openai import OpenAI
from app.memory import WebsiteReview
from urllib.parse import urlparse
from gtts import gTTS


load_dotenv(find_dotenv())

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

CHROME_BINARY_PATH = os.getenv('CHROME_BINARY_PATH', '/usr/bin/google-chrome')
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

cloudinary.config( 
    cloud_name="dobg0vu5e", 
    api_key=os.getenv('CLOUDINARY_API_KEY'), 
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)


@dataclass
class ReviewFilters:
    user_id: int = None
    limit: int = None
    offset: int = 0
    search: str = None
    order_by_desc: bool = False
    liked_value: int = None


def is_valid_url(url):
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])


def sanitize_url_for_public_id(url):
    sanitized_url = re.sub(r'[^\w\-]', '_', urllib.parse.quote(url, safe=''))
    return sanitized_url[:120]


def get_reviews(filters: ReviewFilters):
    query = WebsiteReview.query.filter_by(user_id=filters.user_id)
    if filters.liked_value is not None:
        query = query.filter_by(liked=filters.liked_value)
    if filters.search:
        search_term = f"%{filters.search.strip()}%"
        query = query.filter(WebsiteReview.site_url.ilike(search_term))
    if filters.order_by_desc:
        query = query.order_by(WebsiteReview.id.desc())
    if filters.limit:
        query = query.limit(filters.limit)
    if filters.offset:
        query = query.offset(filters.offset)
    return query.all()


def serialize_review(review):
    return {
        "id": review.id,
        "user_id": review.user_id,
        "user_name": review.user.name,
        "site_url": review.site_url,
        "site_image_url": review.site_image_url,
        "feedback": review.feedback,
        "created_at": review.created_at.strftime("%a %d %B %Y %H:%M:%S"),
        "liked": review.liked,
        "tts_url": review.tts_url
    }


def upload_to_cloudinary(audio_file_path):
    try:
        upload_response = cloudinary.uploader.upload(
            audio_file_path,
            folder="tts_audio",
            resource_type='video',
            secure=True
        )
        return upload_response['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        return None
    

async def take_screenshot(url):
    def _screenshot_worker(url):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.binary_location = CHROME_BINARY_PATH
            chrome_service = ChromeService(executable_path=ChromeDriverManager().install())
            browser = webdriver.Chrome(service=chrome_service, options=options)
            browser.set_page_load_timeout(120)
            browser.set_script_timeout(120)
            browser.get(url)
            wait = WebDriverWait(browser, 120)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            total_height = browser.execute_script("return document.body.scrollHeight")
            browser.set_window_size(1200, total_height)
            screenshot = browser.get_screenshot_as_png()
            browser.quit()
            sanitized_url = sanitize_url_for_public_id(url)
            upload_response = cloudinary.uploader.upload(
                screenshot,
                folder="screenshots",
                public_id=f"{sanitized_url}.png",
                resource_type='image',
                secure=True
            )
            return upload_response['secure_url']
        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return None

    return await asyncio.to_thread(_screenshot_worker, url)


def generate_tts_audio(text, lang='en'):
    try:
        tts = gTTS(text=text, lang=lang)
        audio_file_path = os.path.join(AUDIO_FOLDER_PATH, f"{sanitize_url_for_public_id(text)}.mp3")
        tts.save(audio_file_path)
        return audio_file_path
    except Exception as e:
        print(f"Error generating TTS audio: {str(e)}")
        return None
    

async def get_review(screenshot_url):
    payload = _prepare_payload(screenshot_url)
    data = await asyncio.to_thread(_make_voiceflow_request, payload)
    review_text, tts_url = _extract_review_and_tts(data)

    if not tts_url:
        tts_url = _generate_and_upload_tts(review_text)
    
    review_text = _sanitize_review_text(review_text)
    return review_text, tts_url


def _prepare_payload(screenshot_url):
    return {
        "action": {
            "type": "intent",
            "payload": {
                "query": screenshot_url,
                "intent": {"name": "review_intent"},
                "entities": []
            }
        },
        "config": {
            "tts": True,
            "stripSSML": False,
            "stopAll": True,
            "excludeTypes": ["block", "debug", "flow"]
        },
        "state": {"variables": {"x_var": 1}}
    }


def _make_voiceflow_request(payload):
    url = "https://general-runtime.voiceflow.com/state/user/testuser/interact?logs=off"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": os.getenv('VOICEFLOW_AUTHORIZATION')
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def _extract_review_and_tts(data):
    review_text, tts_url = "", ""
    for item in data:
        if item['type'] == 'speak' and 'payload' in item:
            review_text = item['payload'].get('message', "")
            tts_url = item['payload'].get('src', "")
            break
    return review_text, tts_url


def _generate_and_upload_tts(review_text):
    audio_file_path = generate_tts_audio(review_text)
    if audio_file_path:
        return upload_to_cloudinary(audio_file_path)
    return None


def _sanitize_review_text(review_text):
    review_text = re.sub(r'## |##| \*\*|\*\*', '', review_text)
    review_text = re.sub(r'<voice\s+name="en-GB-standard-A">.*?</voice>', '', review_text, flags=re.IGNORECASE)
    review_text = re.sub(r'<voice\s+name="en-GB-standard-A">', '', review_text, flags=re.IGNORECASE)
    review_text = re.sub(r'</voice>', '', review_text, flags=re.IGNORECASE)
    return review_text
