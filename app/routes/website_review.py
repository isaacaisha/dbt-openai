# WEBSITE_REVIEW.PY

import asyncio

from dotenv import load_dotenv, find_dotenv

from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime

from app.app_forms import WebsiteReviewForm
from app.memory import WebsiteReview, db

from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import urlparse

from app.routes.utils_website_review import get_review, get_reviews, is_valid_url, serialize_review, take_screenshot


load_dotenv(find_dotenv())

review_website_bp = Blueprint('website_review', __name__, template_folder='templates', static_folder='static')


# Endpoint to submit URL for review
@review_website_bp.route('/submit-url', methods=['GET', 'POST'])
async def submit_url():
    # Assign a default value to user_id when the user is anonymous
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    domain = request.args.get('domain')

    if domain and is_valid_url(domain):
        # Attempt to take a screenshot
        website_screenshot = await take_screenshot(domain)
        # Always attempt to get the review and TTS URL, even if the screenshot failed or is blank
        website_review, tts_url = await get_review(website_screenshot or domain)

        # Save the new review along with the TTS URL
        new_review_object = WebsiteReview(
            site_url=domain,
            site_image_url=website_screenshot,
            feedback=website_review,
            tts_url=tts_url,
            user_id=user_id
        )

        try:
            await asyncio.to_thread(db.session.add, new_review_object)
            await asyncio.to_thread(db.session.commit)
        except SQLAlchemyError as e:
            await asyncio.to_thread(db.session.rollback)
            print(f"Database error: {str(e)}")
            return jsonify({"error": "Database operation failed"}), 500

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
        print('Invalid domain URL.')
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

    if review_form.validate_on_submit():
        domain = review_form.domain.data
        return redirect(url_for('website_review.submit_url', domain=domain))
    
    # Fetch the latest review ID
    review = WebsiteReview.query.filter_by(user_id=current_user.id).order_by(WebsiteReview.id.desc()).first()
    review_id = review.id + 1 if review else 1

    # Check if the review is None before accessing its attributes
    if review is not None:
        # Use the tts_url from the database
        tts_url = review.tts_url
    else:
        tts_url = None
    
    return render_template("website-review.html", 
                           current_user=current_user, 
                           review_form=review_form,
                           website_review=website_review,
                           website_screenshot=website_screenshot,
                           review_id=review_id,
                           tts_url=tts_url,
                           date=datetime.now().strftime("%a %d %B %Y"))
    

@review_website_bp.route("/get-all-reviews")
def get_all_reviews():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    user_id = current_user.id

    total_reviews = WebsiteReview.query.filter_by(user_id=user_id).count()
    limit = request.args.get('limit', default=None, type=int)
    offset = request.args.get('offset', default=0, type=int)
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
                           total_reviews=total_reviews,
                           date=datetime.now().strftime("%a %d %B %Y"))


@review_website_bp.route("/review-details/<int:pk>", methods=["GET"])
def review_details(pk):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    # Fetch the review details from the database
    review_detail = WebsiteReview.query.get_or_404(pk)

    # Check if the current user is the owner of the review
    if current_user.id == review_detail.user_id:
        # Use the tts_url from the database
        tts_url = review_detail.tts_url

        return render_template('review-details.html',
                               review_detail=review_detail,
                               tts_url=tts_url,
                               date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('website_review.review_posts'))
    

@review_website_bp.route("/liked-reviews")
def liked_reviews():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    user_id = current_user.id

    # Fetch the count of liked reviews
    liked_reviews_count = WebsiteReview.query.filter_by(user_id=user_id, liked=1).count()

    # Get parameters
    limit = request.args.get('limit', default=None, type=int)
    offset = request.args.get('offset', default=0, type=int)  # Set default offset to 0 if not provided
    search = request.args.get('search', default=None, type=str)

    # Fetch liked reviews using the get_reviews function
    reviews = get_reviews(user_id=user_id, liked_value=1, limit=limit, offset=offset, search=search, order_by_desc=True)
    
    serialized_reviews = [serialize_review(review) for review in reviews]
    
    if not serialized_reviews:
        search_message = f"No liked review found for search term: '{search}'"
        return render_template('liked-reviews.html',
                               current_user=current_user, user_id=user_id,
                               limit=limit, offset=offset, search=search,
                               search_message=search_message,
                               liked_reviews_count=liked_reviews_count,
                               date=datetime.now().strftime("%a %d %B %Y"))

    return render_template('liked-reviews.html',
                           current_user=current_user, owner_id=user_id,
                           limit=limit, offset=offset, search=search,
                           reviews=serialized_reviews,
                           liked_reviews_count=liked_reviews_count,
                           date=datetime.now().strftime("%a %d %B %Y"))


@review_website_bp.route("/liked-reviews-details/<int:pk>", methods=["GET"])
def liked_reviews_details(pk):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    # Fetch the liked review details from the database
    liked_review_detail = WebsiteReview.query.get_or_404(pk)

    # Check if the current user is the owner of the liked review details
    if current_user.id == liked_review_detail.user_id:
        # Use the tts_url from the database
        tts_url = liked_review_detail.tts_url

        return render_template('liked-reviews-details.html',
                               liked_review_detail=liked_review_detail,
                               tts_url=tts_url,
                               date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('website_review.review_posts'))


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

    try:
        # Logic to update the feedback rating
        review = WebsiteReview.query.get(review_id)
        if review:
            review.user_rating = user_rating
            db.session.commit()
            print(f"Feedback updated successfully for review_id={review_id}")
            return jsonify({'message': 'Feedback rated successfully'}), 200
        else:
            print(f"Review not found for review_id={review_id}")
            return jsonify({'error': 'Review not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


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
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@review_website_bp.route('/review/<int:review_id>/tts-url', methods=['GET'])
def get_review_tts_url(review_id):
    print(f"Fetching TTS URL for review ID: {review_id}")

    # Fetch the review by ID
    review = WebsiteReview.query.get(review_id)

    if review:
        print(f"Review found: {review}")

        # Check if the TTS URL exists for the review
        if (tts_url := review.tts_url):
            print(f"TTS URL foundS: {tts_url}")

            # Return the TTS URL as JSON
            return jsonify({"tts_url": tts_url})

        else:
            print(f"TTS URL not found for review ID: {review_id}")
            return jsonify({"error": "TTS URL not found"}), 404
    else:
        print(f"Review not found for ID: {review_id}")
        return jsonify({"error": "Review not found"}), 404
    

@review_website_bp.route('/delete-review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    try:
        review = WebsiteReview.query.get(review_id)
        if review and review.user_id == current_user.id:
            db.session.delete(review)
            db.session.commit()
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": "Review not found or unauthorized"}), 404
    except SQLAlchemyError as e:
        print(f"Error deleting review: {str(e)}")
        return jsonify({"error": str(e)}), 500
