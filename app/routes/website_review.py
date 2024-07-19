# WEBSITE_REVIEW.PY

import os
import re
import urllib.parse
import asyncio
import cloudinary
import cloudinary.uploader
import requests

from dotenv import load_dotenv, find_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait

from flask import Blueprint, current_app, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime

from app.app_forms import WebsiteReviewForm
from app.memory import WebsiteReview, User, db


load_dotenv(find_dotenv())

review_website_bp = Blueprint('website_review', __name__, template_folder='templates', static_folder='static')

# Fetch paths from environment variables
CHROME_BINARY_PATH = os.getenv('CHROME_BINARY_PATH', '/usr/bin/google-chrome')
CHROME_DRIVER_PATH = os.getenv('CHROMEDRIVER_PATH', '/usr/local/bin/chromedriver')

# Configuration for Cloudinary     
cloudinary.config( 
    cloud_name = "dobg0vu5e", 
    api_key = os.getenv('CLOUDINARY_API_KEY'), 
    api_secret = os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)


# Function to sanitize the URL to a valid public ID
def sanitize_url_for_public_id(url):
    # Encode the URL to handle special characters
    encoded_url = urllib.parse.quote(url, safe='')
    # Replace any remaining unsafe characters
    sanitized_url = encoded_url.replace('%', '_').replace('.', '_').replace('/', '_').replace(':', '_').replace('-', '_')
    # Cloudinary allows only alphanumeric characters, underscores, and hyphens in public IDs
    # So we ensure that all other characters are replaced with underscores
    sanitized_url = ''.join(e if e.isalnum() or e in ['_', '-'] else '_' for e in sanitized_url)
    return sanitized_url[:120]


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

            # Initialize ChromeDriver in the thread
            browser = webdriver.Chrome(service=chrome_service, options=options)

            # Set timeouts
            browser.set_page_load_timeout(30)  # Increase page load timeout
            browser.set_script_timeout(30)     # Increase script timeout

            browser.get(url)

            # Use explicit wait for the page to load
            wait = WebDriverWait(browser, 30)
            wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")

            total_height = browser.execute_script("return document.body.parentNode.scrollHeight")
            browser.set_window_size(1200, total_height)

            screenshot = browser.get_screenshot_as_png()
            browser.quit()

            sanitized_url = sanitize_url_for_public_id(url)

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

        print(f"Sending request to Voiceflow with screenshot URL: {screenshot_url}")
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Ensure we raise an error for bad responses
        data = response.json()
        print(f"Response from Voiceflow: {data}")

        review_text = ""
        tts_url = ""

        for item in data:
            if item['type'] == 'speak' and 'payload' in item:
                if 'message' in item['payload']:
                    review_text = item['payload']['message']
                if 'src' in item['payload']:
                    tts_url = item['payload']['src']
                break
              
        # Clean up review text by removing ## and ** characters
        review_text = re.sub(r'## |##| \*\*|\*\*', '', review_text)
        # Remove <voice name="en-GB-standard-A"> and </voice> tags along with any content between them
        review_text = re.sub(r'<voice\s+name="en-GB-standard-A">.*?</voice>', '', review_text, flags=re.IGNORECASE)
        # Remove any remaining standalone <voice name="en-GB-standard-A"> and </voice> tags
        review_text = re.sub(r'<voice\s+name="en-GB-standard-A">', '', review_text, flags=re.IGNORECASE)
        review_text = re.sub(r'</voice>', '', review_text, flags=re.IGNORECASE)
        return review_text, tts_url

    except Exception as e:
        print(f"Error getting review: {str(e)}")
        return None, None


# Endpoint to submit URL for review
@review_website_bp.route('/submit-url', methods=['GET', 'POST'])
async def submit_url():
    domain = request.args.get('domain')

    if domain:
        website_screenshot = await take_screenshot(domain)

        if website_screenshot:
            website_review, tts_url = get_review(website_screenshot)

            new_review_object = WebsiteReview(
                site_url=domain,
                site_image_url=website_screenshot,
                feedback=website_review,
                tts_url=tts_url,
                user_id=current_user.id
            )

            db.session.add(new_review_object)
            db.session.commit()

            review_id = new_review_object.id
            print(f"New review created with ID: {review_id}") 

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
    

# Main page route
@review_website_bp.route('/website-review', methods=['GET', 'POST'])
def review_website():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    review_form = WebsiteReviewForm()

    website_review = None
    website_screenshot = None
    review_id = None
    tts_url = None

    if review_form.validate_on_submit():
        domain = review_form.domain.data
        return redirect(url_for('website_review.submit_url', domain=domain))
    
    # Fetch the latest review ID
    review = WebsiteReview.query.filter_by(user_id=current_user.id).order_by(WebsiteReview.id.desc()).first()
    review_id = review.id + 1 if review else 1

    return render_template("website-review.html", 
                           current_user=current_user, 
                           review_form=review_form,
                           website_review=website_review,
                           website_screenshot=website_screenshot,
                           review_id=review_id,
                           tts_url=tts_url,
                           date=datetime.now().strftime("%a %d %B %Y"))


# Endpoint to update rating
@review_website_bp.route('/rate-feedback', methods=['POST'])
def rate_feedback():
    data = request.get_json()
    review_id = data.get('id')
    user_rating = data.get('user_rating')

    print(f"Received rate feedback request: review_id={review_id}, rating={user_rating}")

    # Validate review_id
    if not review_id:
        print("Invalid review_id received")
        return jsonify({'error': 'Invalid review ID'}), 400

    # Your logic to update the feedback rating
    review = WebsiteReview.query.get(review_id)
    if review:
        review.user_rating = user_rating
        db.session.commit()
        print(f"Feedback updated successfully for review_id={review_id}")
        return jsonify({'message': 'Feedback rated successfully'}), 200
    else:
        print(f"Review not found for review_id={review_id}")
        return jsonify({'error': 'Review not found'}), 404


# Endpoint to update like
@review_website_bp.route('/like/<int:review_id>', methods=['POST'])
def update_like(review_id):
    data = request.get_json()
    liked = data.get('liked', False)

    try:
        review = WebsiteReview.query.get(review_id)
        if review:
            review.liked = 1 if liked else 0
            db.session.commit()
            return jsonify({'success': True, 'liked': review.liked}), 200
        else:
            return jsonify({'success': False, 'message': 'Review not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def get_reviews(user_id=None, limit=None, offset=None, search=None, order_by_desc=False, liked_value=None):
    query = WebsiteReview.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if search is not None:
        # Ensure that the search is flexible enough for partial URL matches
        search_term = f"%{search.strip()}%"
        query = query.filter(WebsiteReview.site_url.ilike(search_term))
    if liked_value is not None:
        query = query.filter(WebsiteReview.liked == liked_value)
    if order_by_desc:
        query = query.order_by(WebsiteReview.id.desc())
    if limit is not None:
        query = query.limit(limit)
    if offset is not None:
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
    }
    

@review_website_bp.route("/get-all-reviews")
def get_all_reviews():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    user_id = current_user.id

    total_reviews = WebsiteReview.query.filter_by(user_id=user_id).count()
    limit = request.args.get('limit', default=total_reviews, type=int)
    offset = request.args.get('offset', default=None, type=int)
    search = request.args.get('search', default=None, type=str)

    reviews = get_reviews(user_id=user_id, limit=limit, offset=offset, search=search, order_by_desc=True)
    serialized_reviews = [serialize_review(review) for review in reviews]

    # Check if any conversations were found for the search term
    if not serialized_reviews:
        search_message = f"No review found for search term: '{search}'"
        return render_template('all-review.html',
                               current_user=current_user, user_id=user_id,
                               limit=limit, offset=offset, search=search,
                               search_message=search_message,
                               date=datetime.now().strftime("%a %d %B %Y"))

    return render_template('all-review.html',
                           current_user=current_user, owner_id=user_id,
                           limit=limit, offset=offset, search=search,
                           reviews=serialized_reviews,
                           date=datetime.now().strftime("%a %d %B %Y"))


@review_website_bp.route("/review-details/<int:pk>", methods=["GET"])
def review_details(pk):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    tts_url = None
    
    # Fetch the latest review ID
    review = WebsiteReview.query.filter_by(user_id=current_user.id).order_by(WebsiteReview.id.desc()).first()
    review_id = review.id if review else 1

    review_detail = WebsiteReview.query.get_or_404(pk)
    if current_user.id == review_detail.user_id:
        return render_template('review-details.html', review_detail=review_detail, review_id=review_id,
                               tts_url=tts_url, date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('website_review.review_posts'))
    

@review_website_bp.route("/liked-reviews")
def liked_reviews():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    user_id = current_user.id

    total_reviews = WebsiteReview.query.filter_by(user_id=user_id).count()
    limit = request.args.get('limit', default=total_reviews, type=int)
    offset = request.args.get('offset', default=None, type=int)
    search = request.args.get('search', default=None, type=str)

    # Fetch liked reviews
    reviews = get_reviews(user_id=user_id, liked_value=1, search=search, order_by_desc=True)
    serialized_reviews = [serialize_review(review) for review in reviews]

    if not serialized_reviews:
        search_message = f"No liked review found for search term: '{search}'"
        return render_template('liked-reviews.html',
                               current_user=current_user, user_id=user_id,
                               limit=limit, offset=offset, search=search,
                               search_message=search_message,
                               date=datetime.now().strftime("%a %d %B %Y"))

    return render_template('liked-reviews.html',
                           current_user=current_user, owner_id=user_id,
                           limit=limit, offset=offset, search=search,
                           reviews=serialized_reviews,
                           date=datetime.now().strftime("%a %d %B %Y"))


@review_website_bp.route("/liked-reviews-details/<int:pk>", methods=["GET"])
def liked_reviews_details(pk):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    tts_url = None
    
    # Fetch the latest review ID
    review = WebsiteReview.query.filter_by(user_id=current_user.id).order_by(WebsiteReview.id.desc()).first()
    review_id = review.id if review else 1

    liked_review_detail = WebsiteReview.query.get_or_404(pk)
    if current_user.id == liked_review_detail.user_id:
        return render_template('liked-reviews-details.html', liked_review_detail=liked_review_detail, review_id=review_id,
                               tts_url=tts_url, date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('website_review.review_posts'))
