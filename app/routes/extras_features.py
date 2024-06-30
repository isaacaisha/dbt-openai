from flask import Blueprint, flash, render_template, request, jsonify, redirect, url_for
from datetime import datetime
import json
import os
import assemblyai as aai
import openai
from pytube import YouTube
from flask_login import current_user, login_required
from app.memory import BlogPost, User, db


features_extras_bp = Blueprint('extras_features', __name__)


@features_extras_bp.route("/extras-features-home", methods=["GET"])
def extras_features_home():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    return render_template('extras-features.html', date=datetime.now().strftime("%a %d %B %Y"))


@features_extras_bp.route("/blog/generator", methods=["GET", "POST"])
def generate_blog():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    
    elif request.method == 'POST':
        try:           
            data = request.get_json()
            youtube_link = data.get('link')
        except (KeyError, TypeError) as e:
            return jsonify({'error': 'Invalid data sent 😭'}), 400

        new_blog_article, error_message = process_youtube_video(current_user.id, youtube_link)

        if error_message:
            return jsonify({'error': error_message}), 500
        
        return jsonify({'content': new_blog_article.generated_content}), 200

    elif request.method == 'GET':
        return render_template('blog-generator.html', date=datetime.now().strftime("%a %d %B %Y"))

    else:
        return jsonify({'error': 'Invalid request method 🤣'}), 405
# def blog_generator():
#     if request.method == "POST":
#         if request.content_type != 'application/json':
#             return jsonify({'error': 'Unsupported Media Type'}), 415
# 
#         data = request.get_json()
#         youtube_link = data.get('link')
# 
#         if not youtube_link:
#             return jsonify({'error': 'Invalid data sent 😭'}), 400
# 
#         title = youtube_title(youtube_link)
#         transcription = get_transcription(youtube_link)
# 
#         if not transcription:
#             return jsonify({'error': 'Failed to get transcript 😭'}), 500
# 
#         blog_content = generate_blog_from_transcription(transcription)
# 
#         if not blog_content:
#             return jsonify({'error': 'Failed to generate blog article 😭'}), 500
# 
#         new_blog_article = BlogPost(
#             user_id=current_user.id,
#             youtube_title=title,
#             youtube_link=youtube_link,
#             generated_content=blog_content,
#             created_at=datetime.utcnow()
#         )
# 
#         db.session.add(new_blog_article)
#         db.session.commit()
# 
#         return jsonify({'content': blog_content})
#     elif request.method == "GET":
#         return render_template('blog-generator.html', date=datetime.now().strftime("%a %d %B %Y"))
#     else:
#         return jsonify({'error': 'Invalid request method 🤣'}), 405


@features_extras_bp.route("/blog-posts", methods=["GET"])
def blog_posts():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    blog_articles = BlogPost.query.filter_by(user_id=current_user.id).all()
    blog_articles.reverse()
    return render_template('blog-posts.html', blog_articles=blog_articles, date=datetime.now().strftime("%a %d %B %Y"))


@features_extras_bp.route("/blog-details/<int:pk>", methods=["GET"])
def blog_details(pk):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    blog_article_detail = BlogPost.query.get_or_404(pk)
    if current_user.id == blog_article_detail.user_id:
        return render_template('blog-details.html', blog_article_detail=blog_article_detail, date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('extras_features.blog_posts'))

def youtube_title(link):
    youtube = YouTube(link)
    title = youtube.title
    return title

def download_audio(link):
    youtube = YouTube(link)
    video_audio = youtube.streams.filter(only_audio=True).first()
    out_file = video_audio.download(output_path="static/media")  # Adjust as necessary
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = os.getenv('AAI_API_KEY')

    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)
        print(transcript) 
        transcription_text = transcript.text
    except Exception as e:
        print(f"AssemblyAI Client Error: {str(e)}")
        transcription_text = None
    finally:
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"Deleted audio file: {audio_file}")

    return transcription_text

def generate_blog_from_transcription(transcription):
    openai.api_key = os.getenv('OPENAI_API_KEY')

    prompt = f"Based on the following transcript from a YouTube video, " \
             f"write a comprehensive blog article. Write it based on the transcript, " \
             f"but don't make it look like a YouTube video. " \
             f"Make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Replace with an appropriate model from OpenAI's current options
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": ""},
            ],
            max_tokens=1000,
            timeout=30  # Example: set timeout to 30 seconds
        )
        generated_content = response['choices'][0]['message']['content'].strip()
        return generated_content
    except openai.OpenAIError as e:
        print(f"OpenAI API Error: {e}")
        return None
    except Exception as e:
        print(f"Error generating blog content: {str(e)}")
        return None


def process_youtube_video(user_id, youtube_link):
    user = db.session.query(User).get(user_id)  

    # Get title
    title = youtube_title(youtube_link)

    # Get transcript
    transcription = get_transcription(youtube_link)
    if not transcription:
        return None, 'Failed to get transcript 😭'

    # Use OpenAI to generate the blog
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
        return None, 'Failed to generate blog article 😭'

    # Save blog article into database
    new_blog_article = BlogPost.objects.create(
        user_id=current_user.id, 
        youtube_title=title,
        youtube_link=youtube_link,
        generated_content=blog_content,
    )
    db.session.add(new_blog_article)
    db.session.commit()

    return new_blog_article, None

    