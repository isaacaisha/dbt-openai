# YOUTUBE_BLOG_GENERATOR.PY

import os
from io import BytesIO

from dotenv import load_dotenv, find_dotenv
from flask import Blueprint, flash, make_response, render_template, request, jsonify, redirect, send_file, url_for
from flask_login import current_user

from app.memory import BlogPost
from app.routes.utils_youtube_blog import process_youtube_video

from datetime import datetime


load_dotenv(find_dotenv())

generator_yt_blog_bp = Blueprint('yt_blog_generator', __name__, template_folder='templates', static_folder='static')


@generator_yt_blog_bp.route("/extras-features-home", methods=["GET"])
def extras_features_home():
    """Render the extras features page."""
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    return render_template('extras-features.html', date=datetime.now().strftime("%a %d %B %Y"))


@generator_yt_blog_bp.route("/blog/generator", methods=["GET", "POST"])
def generate_blog():
    """Handle the generation of a blog based on a YouTube link."""
    if not current_user.is_authenticated:
        flash('Please login to access this page.')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                print("No JSON data received.")
                return jsonify({'error': 'Invalid data sent 😭'}), 400
            
            youtube_link = data.get('link')
            if not youtube_link:
                print("YouTube link not provided.")
                return jsonify({'error': 'YouTube link is required.'}), 400

            print(f"Processing YouTube link: {youtube_link}")
            new_blog_article, error_message = process_youtube_video(current_user.id, youtube_link)

            if error_message:
                print(f"Error generating blog: {error_message}")
                return jsonify({'error': error_message}), 500  # Return a valid tuple

            # Generate audio file URL
            audio_url = url_for('yt_blog_generator.blog_post_audio', pk=new_blog_article.id, _external=True)

            return jsonify({
                'content': new_blog_article.generated_content,
                'audio_url': audio_url
            }), 200

        except Exception as e:
            print(f"Unhandled exception in generate_blog: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500  # Return a valid tuple

    elif request.method == 'GET':
        return render_template('blog-generator.html', date=datetime.now().strftime("%a %d %B %Y"))

    else:
        return jsonify({'error': 'Invalid request method 🤣'}), 405


@generator_yt_blog_bp.route("/blog-posts", methods=["GET"])
def blog_posts():
    """Render the list of blog posts for the current user."""
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    blog_articles = BlogPost.query.filter_by(user_id=current_user.id).all()
    blog_articles.reverse()
    return render_template('blog-posts.html', blog_articles=blog_articles, date=datetime.now().strftime("%a %d %B %Y"))


@generator_yt_blog_bp.route("/blog-details/<int:pk>", methods=["GET"])
def blog_details(pk):
    """Render the details of a specific blog post."""
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    blog_article_detail = BlogPost.query.get_or_404(pk)
    if current_user.id == blog_article_detail.user_id:
        audio_url = url_for('yt_blog_generator.blog_post_audio', pk=blog_article_detail.id, _external=True)
        return render_template('blog-details.html', blog_article_detail=blog_article_detail, 
                               audio_url=audio_url, date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('yt_blog_generator.blog_posts'))
    

@generator_yt_blog_bp.route("/blog-posts/<int:pk>/audio", methods=["GET"])
def blog_post_audio(pk):
    """Serve the audio version of the blog post from the database."""
    if not current_user.is_authenticated:
        flash('Please login to access this page.')
        return redirect(url_for('auth.login'))

    # Fetch the blog post by its primary key (ID)
    blog_article_detail = BlogPost.query.get_or_404(pk)

    if current_user.id != blog_article_detail.user_id:
        flash("You don't have permission to access this audio.")
        return redirect(url_for('yt_blog_generator.blog_posts'))

    if not blog_article_detail.audio_data:
        flash("No audio available for this blog post.")
        return redirect(url_for('yt_blog_generator.blog_posts'))

    # Serve the audio data as an MP3 file
    audio_filename = f"{blog_article_detail.youtube_title}.mp3"
    response = make_response(blog_article_detail.audio_data)
    response.headers.set('Content-Type', 'audio/mpeg')
    response.headers.set('Content-Disposition', 'inline', filename=audio_filename)
    return response
