# portfolio_review.py

import json
import os
import cloudinary
import cloudinary.uploader
import requests
# from cloudinary.utils import cloudinary_url
from selenium import webdriver
from flask import Blueprint, current_app, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime

from app.app_forms import PortfolioReviewForm
from app.memory import PortfolioReview, User, db


review_portfolio_bp = Blueprint('portfolio_review', __name__, template_folder='templates', static_folder='static')


# Configuration for Cloudinary     
cloudinary.config( 
    cloud_name = "dobg0vu5e", 
    api_key = os.getenv('CLOUDINARY_API_KEY'), 
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# # Upload an image
# upload_result = cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/getting-started/shoes.jpg",
#                                            public_id="shoes")
# print(upload_result["secure_url"])
# 
# # Optimize delivery by resizing and applying auto-format and auto-quality
# optimize_url, _ = cloudinary_url("shoes", fetch_format="auto", quality="auto")
# print(optimize_url)
# 
# # Transform the image: auto-crop to square aspect_ratio
# auto_crop_url, _ = cloudinary_url("shoes", width=100, height=100, crop="auto", gravity="auto")
# print(auto_crop_url)


# Function to take a screenshot of a URL /Users/lesanebyby/Desktop/chromedriver-mac-arm64
def take_screenshot(url):
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Dev use 👇🏿
        # browser = webdriver.Chrome(options=options)
       	
        # Path to chromedriver executable
        chrome_driver_path = '/usr/bin/chromedriver'
        
        # Create WebDriver instance with the path to chromedriver
        browser = webdriver.Chrome(service=webdriver.chrome.service.Service(chrome_driver_path), options=options)

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

        return review_text, tts_url

    except Exception as e:
        print(f"Error getting review: {str(e)}")
        return None, None


# Endpoint to submit URL for review
@review_portfolio_bp.route('/submit-url', methods=['GET', 'POST'])
def submit_url():
    domain = request.args.get('domain')

    if domain:
        website_screenshot = take_screenshot(domain)

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

            flash('Portfolio review submitted successfully 👌🏿')
            return render_template("index-portfolio.html",
                                   current_user=current_user,
                                   portfolio_form=PortfolioReviewForm(),
                                   website_review=website_review,
                                   website_screenshot=website_screenshot,
                                   tts_url=tts_url,
                                   date=datetime.now().strftime("%a %d %B %Y"))

        else:
            flash('Failed to capture screenshot. Please try again.')
            return redirect(url_for('portfolio_review.index_portfolio'))

    flash('Invalid domain URL.')
    return jsonify({'error': 'Invalid domain URL'})


# Main page route
@review_portfolio_bp.route('/index-portfolio', methods=['GET', 'POST'])
def index_portfolio():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    portfolio_form = PortfolioReviewForm()

    if portfolio_form.validate_on_submit():
        domain = portfolio_form.domain.data
        return redirect(url_for('portfolio_review.submit_url', domain=domain))

    return render_template("index-portfolio.html", current_user=current_user, portfolio_form=portfolio_form,
                            date=datetime.now().strftime("%a %d %B %Y"))


# Error handling example
@review_portfolio_bp.errorhandler(Exception)
def handle_error(error):
    # Log the error
    current_app.logger.error(f"An error occurred: {str(error)}")

    # Flash a generic error message
    flash('An unexpected error occurred. Please try again later.')
    
    # Redirect to the main page or appropriate error page
    return redirect(url_for('portfolio_review.index_portfolio'))

# Endpoint to submit feedback
@review_portfolio_bp.route('/feedback', methods=['POST'])
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


@review_portfolio_bp.route('/update-like/<int:conversation_id>', methods=['POST'])
def update_like(conversation_id):
    # Get the liked status from the request data
    liked = request.json.get('liked')

    # Find the corresponding Memory object in the database using db.session.get()
    conversation = db.session.get(PortfolioReviewForm, conversation_id)

    # Update the liked status of the conversation
    conversation.liked = liked

    # Add the updated conversation object to the session
    db.session.add(conversation)

    # Commit the changes to the database
    db.session.commit()

    # Return a success response
    return 'Liked status updated successfully', 200
