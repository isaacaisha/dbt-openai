# PORTFOLIO_REVIEW.PY

import json
import os
import asyncio
import cloudinary
import cloudinary.uploader
import requests
from dotenv import load_dotenv, find_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

from flask import Blueprint, current_app, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime

from app.app_forms import PortfolioReviewForm
from app.memory import PortfolioReview, User, db


load_dotenv(find_dotenv())

# Fetch paths from environment variables
CHROME_BINARY_PATH = os.getenv('CHROME_BINARY_PATH', '/usr/src/app/chrome/chromium/chrome')
CHROME_DRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')

review_website_bp = Blueprint('website_review', __name__, template_folder='templates', static_folder='static')

# Configuration for Cloudinary     
cloudinary.config( 
    cloud_name = "dobg0vu5e", 
    api_key = os.getenv('CLOUDINARY_API_KEY'), 
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)


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
            chrome_service = ChromeService(executable_path=CHROME_DRIVER_PATH)
            # Logging for debugging
            print(f"Binary location set to: {options.binary_location}")

            # Initialize ChromeDriver in the thread
            browser = webdriver.Chrome(service=chrome_service, options=options)

            browser.get(url)

            total_height = browser.execute_script("return document.body.parentNode.scrollHeight")
            browser.set_window_size(1200, total_height)

            screenshot = browser.get_screenshot_as_png()
            browser.quit()

            sanitized_url = url.replace('http://', '').replace('https://', '').replace('/', '_').replace(':', '_')

            # Upload screenshot to Cloudinary
            upload_response = cloudinary.uploader.upload(
                screenshot,
                folder="screenshots",
                public_id=f"{sanitized_url}.png",
                resource_type='image'
            )

            return upload_response['url']

        except Exception as e:
            print(f"Error taking screenshot: {str(e)}")
            return None

    return await asyncio.to_thread(_screenshot_worker, url)


# Function to get review text using Voiceflow API
def get_review(screenshot_url):
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

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        data = response.json()

        review_text = ""
        tts_url = ""

        for item in data:
            if item['type'] == 'speak' and 'payload' in item:
                if 'message' in item['payload']:
                    review_text = item['payload']['message']
                if 'src' in item['payload']:
                    tts_url = item['payload']['src']
                break

        # print(f'review_text:\n{data}')
        return review_text, tts_url

    except Exception as e:
        print(f"Error getting review: {str(e)}")
        return None, None


# Main page route
@review_website_bp.route('/website-review', methods=['GET', 'POST'])
def review_website():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    portfolio_form = PortfolioReviewForm()

    website_review = None
    website_screenshot = None
    review_id = None
    tts_url = None

    if portfolio_form.validate_on_submit():
        domain = portfolio_form.domain.data
        return redirect(url_for('website_review.submit_url', domain=domain))

    return render_template("website-review.html", 
                           current_user=current_user, 
                           portfolio_form=portfolio_form,
                           website_review=website_review,
                           website_screenshot=website_screenshot,
                           review_id=review_id,
                           tts_url=tts_url,
                           date=datetime.now().strftime("%a %d %B %Y"))


# Endpoint to submit URL for review
@review_website_bp.route('/submit-url', methods=['GET', 'POST'])
async def submit_url():
    domain = request.args.get('domain')

    if domain:
        website_screenshot = await take_screenshot(domain)

        if website_screenshot:
            website_review, tts_url = get_review(website_screenshot)

            new_review_object = PortfolioReview(
                site_url=domain,
                site_image_url=website_screenshot,
                feedback=website_review,
                user_id=current_user.id
            )

            db.session.add(new_review_object)
            db.session.commit()

            review_id = new_review_object.id

            response_data = {
                'website_screenshot': website_screenshot,
                'website_review': website_review,
                'tts_url': tts_url,
                'review_id': review_id,
            }

            return jsonify(response_data)

        else:
            flash('Failed to capture screenshot. Please try again.')
            return redirect(url_for('website_review.review_website'))

    flash('Invalid domain URL.')
    return jsonify({'error': 'Invalid domain URL'})


# Endpoint to submit feedback
@review_website_bp.route('/feedback', methods=['POST'])
def feedback():
    data = request.get_json()
    review_id = data.get('id')
    rating_type = data.get('user_rating')

    try:
        review = PortfolioReview.query.get(review_id)
        if review:
            review.user_rating = rating_type
            db.session.commit()
            return jsonify({'status': 'success', 'message': 'Feedback submitted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Review not found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


# Endpoint to submit like
@review_website_bp.route('/like/<int:review_id>', methods=['POST'])
def update_like(review_id):
    data = request.get_json()
    liked = data.get('liked', False)

    try:
        review = PortfolioReview.query.get(review_id)
        if review:
            review.liked = 1 if liked else 0
            db.session.commit()
            return jsonify({'success': True, 'message': 'Like status updated successfully'})
        else:
            return jsonify({'success': False, 'message': 'Review not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})