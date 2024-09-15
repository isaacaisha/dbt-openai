# WEBSITE_REVIEW.PY

import asyncio
from dotenv import load_dotenv, find_dotenv
from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from flask_login import current_user
from datetime import datetime
from app.app_forms import WebsiteReviewForm
from app.memory import WebsiteReview, db
from sqlalchemy.exc import SQLAlchemyError
from app.routes.utils_website_review import ReviewFilters, get_review, get_reviews, is_valid_url, serialize_review, take_screenshot

load_dotenv(find_dotenv())

# Blueprint declaration
review_website_bp = Blueprint('website_review', __name__, template_folder='templates', static_folder='static')


# Utility Functions (Grouped Together)
async def process_review(domain, user_id):
    website_screenshot = await take_screenshot(domain)
    website_review, tts_url = await get_review(website_screenshot or domain)
    return {
        'domain': domain,
        'user_id': user_id,
        'website_screenshot': website_screenshot,
        'website_review': website_review,
        'tts_url': tts_url
    }


async def save_review(review_data):
    """Save the review to the database."""
    new_review_object = WebsiteReview(
        site_url=review_data['domain'],
        site_image_url=review_data['website_screenshot'],
        feedback=review_data['website_review'],
        tts_url=review_data['tts_url'],
        user_id=review_data['user_id']
    )
    try:
        await asyncio.to_thread(db.session.add, new_review_object)
        await asyncio.to_thread(db.session.commit)
        return new_review_object.id
    except SQLAlchemyError as e:
        await asyncio.to_thread(db.session.rollback)
        print(f"Database error: {str(e)}")
        return None


async def process_review_submission(domain, user_id):
    """Process the review submission including screenshot and review generation."""
    review_data = await process_review(domain, user_id)
    review_data['review_id'] = await save_review(review_data)
    return review_data


def get_latest_review_info(user_id):
    """Retrieve the latest review ID and TTS URL for the user."""
    review = WebsiteReview.query.filter_by(user_id=user_id).order_by(WebsiteReview.id.desc()).first()
    review_id = review.id + 1 if review else 1
    tts_url = review.tts_url if review else None
    return review_id, tts_url


def fetch_reviews_with_count(filters):
    """Fetch reviews and total count based on filters."""
    reviews = get_reviews(filters)
    serialized_reviews = [serialize_review(review) for review in reviews]
    total_reviews = WebsiteReview.query.filter_by(user_id=filters.user_id).count()
    liked_reviews_count = WebsiteReview.query.filter_by(user_id=filters.user_id, liked=filters.liked_value).count()
    return serialized_reviews, total_reviews, liked_reviews_count


def update_review_property(review_id, property_name, update_value_func):
    """Update a specific property of a review."""
    try:
        review = WebsiteReview.query.get(review_id)
        if review:
            setattr(review, property_name, update_value_func(request.get_json()))
            db.session.commit()
            return jsonify({'success': True}), 200
        else:
            return jsonify({'error': 'Review not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


def render_reviews_page(filters, template_name, no_results_message, current_user):
    reviews, total_reviews, liked_reviews_count = fetch_reviews_with_count(filters)

    if not reviews:
        search_message = no_results_message
        return render_template(template_name,
                               current_user=current_user,
                               limit=filters.limit,
                               offset=filters.offset,
                               search=filters.search,
                               search_message=search_message,
                               date=datetime.now().strftime("%a %d %B %Y"))

    return render_template(template_name,
                           current_user=current_user,
                           limit=filters.limit,
                           offset=filters.offset,
                           search=filters.search,
                           reviews=reviews,
                           total_reviews=total_reviews,
                           liked_reviews_count=liked_reviews_count,
                           date=datetime.now().strftime("%a %d %B %Y"))


def render_review_details_page(review_id):
    """Render the review details page."""
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    review_detail = WebsiteReview.query.get_or_404(review_id)

    if current_user.id == review_detail.user_id:
        tts_url = review_detail.tts_url
        return render_template('review-details.html',
                               review_detail=review_detail,
                               tts_url=tts_url,
                               date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('website_review.get_all_reviews'))


def delete_user_review(review_id):
    """Delete a review if the user is the owner."""
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


# Route Handlers (Grouped Together)
@review_website_bp.route('/submit-url', methods=['GET', 'POST'])
async def submit_url():
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'
    domain = request.args.get('domain')

    if domain and is_valid_url(domain):
        response_data = await process_review_submission(domain, user_id)
        if response_data['review_id']:
            return jsonify(response_data)
        else:
            return jsonify({"error": "Database operation failed"}), 500
    else:
        return jsonify({'error': 'Invalid domain URL'})


@review_website_bp.route('/website-review', methods=['GET', 'POST'])
def review_website():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    review_form = WebsiteReviewForm()
    if review_form.validate_on_submit():
        domain = review_form.domain.data
        return redirect(url_for('website_review.submit_url', domain=domain))

    review_id, tts_url = get_latest_review_info(current_user.id)

    return render_template("website-review.html", 
                           current_user=current_user, 
                           review_form=review_form,
                           review_id=review_id,
                           tts_url=tts_url,
                           date=datetime.now().strftime("%a %d %B %Y"))


@review_website_bp.route("/get-all-reviews")
def get_all_reviews():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    filters = ReviewFilters(
        user_id=current_user.id,
        limit=request.args.get('limit', default=None, type=int),
        offset=request.args.get('offset', default=0, type=int),
        search=request.args.get('search', default=None, type=str),
        order_by_desc=True
    )

    return render_reviews_page(
        filters,
        template_name='all-review.html',
        no_results_message=f"No review found for search term: '{filters.search}'",
        current_user=current_user,
    )


@review_website_bp.route("/review-details/<int:pk>", methods=["GET"])
def review_details(pk):
    return render_review_details_page(pk)


@review_website_bp.route("/liked-reviews-details/<int:pk>", methods=["GET"])
def liked_reviews_details(pk):
    return render_review_details_page(pk)


@review_website_bp.route("/liked-reviews")
def liked_reviews():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    filters = ReviewFilters(
        user_id=current_user.id,
        liked_value=1,
        limit=request.args.get('limit', default=None, type=int),
        offset=request.args.get('offset', default=0, type=int),
        search=request.args.get('search', default=None, type=str),
        order_by_desc=True
    )

    return render_reviews_page(
        filters,
        template_name='liked-reviews.html',
        no_results_message=f"No liked review found for search term: '{filters.search}'",
        current_user=current_user,
    )


@review_website_bp.route('/like/<int:review_id>', methods=['POST'])
def update_like(review_id):
    try:
        review = WebsiteReview.query.get(review_id)
        if review:
            review.liked = int(not bool(review.liked))
            db.session.commit()
            return jsonify({'success': True, 'liked': review.liked}), 200
        else:
            return jsonify({'error': 'Review not found'}), 404
    except SQLAlchemyError as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@review_website_bp.route('/rate-feedback', methods=['POST'])
def rate_feedback():
    data = request.get_json()
    review_id = data.get('id')
    user_rating = data.get('user_rating')

    if not review_id:
        return jsonify({'error': 'Invalid review ID'}), 400

    return update_review_property(review_id, 'user_rating', lambda data: user_rating)


@review_website_bp.route('/review/<int:review_id>/tts-url', methods=['GET'])
def get_review_tts_url(review_id):
    review = WebsiteReview.query.get(review_id)
    if review and review.tts_url:
        return jsonify({"tts_url": review.tts_url})
    else:
        return jsonify({"error": "TTS URL not found or Review not found"}), 404


@review_website_bp.route('/delete-review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    return delete_user_review(review_id)
