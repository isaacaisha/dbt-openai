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

from openai import OpenAI
from app.memory import WebsiteReview
from urllib.parse import urlparse
from gtts import gTTS


load_dotenv(find_dotenv())

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

# Fetch paths from environment variables
CHROME_BINARY_PATH = os.getenv('CHROME_BINARY_PATH', '/usr/bin/google-chrome')

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Configuration for Cloudinary     
cloudinary.config( 
    cloud_name = "dobg0vu5e", 
    api_key = os.getenv('CLOUDINARY_API_KEY'), 
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)


# Helper Functions
def is_valid_url(url):
    parsed_url = urlparse(url)
    return all([parsed_url.scheme, parsed_url.netloc])


# Function to sanitize the URL to a valid public ID
def sanitize_url_for_public_id(url):
    # Encode the URL to handle special characters and replace any non-alphanumeric characters with underscores
    sanitized_url = re.sub(r'[^\w\-]', '_', urllib.parse.quote(url, safe=''))
    return sanitized_url[:120]


# Database and Serialization Functions
def get_reviews(user_id=None, limit=None, offset=None, search=None, order_by_desc=False, liked_value=None):
    filters = {}
    if user_id is not None:
        filters['user_id'] = user_id
    if liked_value is not None:
        filters['liked'] = liked_value
    
    query = WebsiteReview.query.filter_by(**filters)
    
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(WebsiteReview.site_url.ilike(search_term))
    
    if order_by_desc:
        query = query.order_by(WebsiteReview.id.desc())
    
    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)
    
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


# Cloudinary and Screenshot Functions
def upload_to_cloudinary(audio_file_path):
    try:
        # Upload the audio file to Cloudinary
        upload_response = cloudinary.uploader.upload(
            audio_file_path,
            folder="tts_audio",  # Organizing uploads in a specific folder
            resource_type='video',  # Cloudinary treats audio as video
            secure=True  # Ensure the URL is HTTPS
        )
        
        # Return the secure URL of the uploaded audio file
        return upload_response['secure_url']
    except Exception as e:
        print(f"Error uploading to Cloudinary: {str(e)}")
        return None
    

# Function to take a screenshot
async def take_screenshot(url):
    def _screenshot_worker(url):
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

            # Set the binary location for Chrome
            options.binary_location = CHROME_BINARY_PATH

            # Create a ChromeDriverService instance
            chrome_service = ChromeService(executable_path=ChromeDriverManager().install())

            # Initialize ChromeDriver in the thread
            browser = webdriver.Chrome(service=chrome_service, options=options)

            # Set timeouts
            browser.set_page_load_timeout(120)  # Increase page load timeout
            browser.set_script_timeout(120)     # Increase script timeout

            browser.get(url)

            # Use explicit wait for the page to load
            wait = WebDriverWait(browser, 120)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            #total_height = browser.execute_script("return document.body.parentNode.scrollHeight")
            total_height = browser.execute_script("return document.body.scrollHeight")
            browser.set_window_size(1200, total_height)
            
            # Take the screenshot after scrolling
            screenshot = browser.get_screenshot_as_png()
            browser.quit()

            sanitized_url = sanitize_url_for_public_id(url)

            # Upload screenshot to Cloudinary
            upload_response = cloudinary.uploader.upload(
                screenshot,
                folder="screenshots",
                public_id=f"{sanitized_url}.png",
                resource_type='image',
                secure=True  # Ensure the URL is HTTPS
            )

            screenshot_url = upload_response['secure_url']  # Use secure_url to enforce HTTPS
            return screenshot_url

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


# Function to get review text using Voiceflow API
async def get_review(screenshot_url):
    def _get_review_worker(screenshot_url):
        try:
            url = "https://general-runtime.voiceflow.com/state/user/testuser/interact?logs=off"

            payload = {
                "action": {
                    "type": "intent",
                    "payload": {
                        "query": screenshot_url,
                        "intent": {"name": "review_intent"},
                        "entities": []
                    }
                },
                "config": {
                    "tts": True,  # Enable TTS
                    "stripSSML": False,
                    "stopAll": True,
                    "excludeTypes": ["block", "debug", "flow"]
                },
                "state": {"variables": {"x_var": 1}}
            }
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": os.getenv('VOICEFLOW_AUTHORIZATION')
            }

            print(f"Sending request to Voiceflow with screenshot URL: {screenshot_url}")

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # print(f"Response from Voiceflow: {data}")

            review_text = ""
            tts_url = ""
            for item in data:
                if item['type'] == 'speak' and 'payload' in item:
                    if 'message' in item['payload']:
                        review_text = item['payload']['message']
                    if 'src' in item['payload']:
                        tts_url = item['payload']['src']
                    break

            # Use gtts if tts_url is empty
            if not tts_url:
                audio_file_path = generate_tts_audio(review_text)
                if audio_file_path:
                    # Optionally, you can upload the audio to Cloudinary and set tts_url accordingly
                    # Example: upload audio to cloudinary and get the URL
                    tts_url = upload_to_cloudinary(audio_file_path)


            # Clean up review text by removing ## and ** characters
            review_text = re.sub(r'## |##| \*\*|\*\*', '', review_text)
            # Remove <voice name="en-GB-standard-A"> and </voice> tags along with any content between them
            review_text = re.sub(r'<voice\s+name="en-GB-standard-A">.*?</voice>', '', review_text, flags=re.IGNORECASE)
            # Remove any remaining standalone <voice name="en-GB-standard-A"> and </voice> tags
            review_text = re.sub(r'<voice\s+name="en-GB-standard-A">', '', review_text, flags=re.IGNORECASE)
            review_text = re.sub(r'</voice>', '', review_text, flags=re.IGNORECASE)

            # print(f"Extracted review text: {review_text}")
            # print(f"Extracted TTS URL: {tts_url}")

            return review_text, tts_url

        except Exception as e:
            print(f"Error getting review: {str(e)}")
            return None, None

    return await asyncio.to_thread(_get_review_worker, screenshot_url)
