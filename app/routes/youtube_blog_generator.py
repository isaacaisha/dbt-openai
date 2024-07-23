import os
import yt_dlp
import assemblyai as aai
import requests

from dotenv import load_dotenv, find_dotenv
from flask import Blueprint, flash, render_template, request, jsonify, redirect, url_for
from flask import current_app
from datetime import datetime
from openai import OpenAI, OpenAIError
from flask_login import current_user
from app.memory import BlogPost, User, db
from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langdetect import detect

load_dotenv(find_dotenv())

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

generator_yt_blog_bp = Blueprint('yt_blog_generator', __name__, template_folder='templates', static_folder='static')

llm = ChatOpenAI(temperature=0.0, model="gpt-4")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Use `current_app.logger` instead of `generator_yt_blog_bp.logger`
if not YOUTUBE_API_KEY:
    current_app.logger.error("YOUTUBE_API_KEY environment variable is missing.")
if not ASSEMBLYAI_API_KEY:
    current_app.logger.error("ASSEMBLYAI_API_KEY environment variable is missing.")
if not OPENAI_API_KEY:
    current_app.logger.error("OPENAI_API_KEY environment variable is missing.")


@generator_yt_blog_bp.route("/extras-features-home", methods=["GET"])
def extras_features_home():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))
    return render_template('extras-features.html', date=datetime.now().strftime("%a %d %B %Y"))



@generator_yt_blog_bp.route("/blog/generator", methods=["GET", "POST"])
def generate_blog():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                current_app.logger.error("No JSON data received.")
                return jsonify({'error': 'Invalid data sent 😭'}), 400
            
            youtube_link = data.get('link')
            if not youtube_link:
                current_app.logger.error("YouTube link not provided.")
                return jsonify({'error': 'YouTube link is required.'}), 400

            current_app.logger.info(f"Processing YouTube link: {youtube_link}")
            new_blog_article, error_message = process_youtube_video(current_user.id, youtube_link)

            if error_message:
                current_app.logger.error(f"Error generating blog: {error_message}")
                return jsonify({'error': error_message}), 500

            return jsonify({'content': new_blog_article.generated_content}), 200

        except Exception as e:
            current_app.logger.error(f"Unhandled exception in generate_blog: {str(e)}")
            return jsonify({'error': 'An unexpected error occurred'}), 500

    elif request.method == 'GET':
        return render_template('blog-generator.html', date=datetime.now().strftime("%a %d %B %Y"))

    else:
        return jsonify({'error': 'Invalid request method 🤣'}), 405

@generator_yt_blog_bp.route("/blog-posts", methods=["GET"])
def blog_posts():
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    blog_articles = BlogPost.query.filter_by(user_id=current_user.id).all()
    blog_articles.reverse()
    return render_template('blog-posts.html', blog_articles=blog_articles, date=datetime.now().strftime("%a %d %B %Y"))

@generator_yt_blog_bp.route("/blog-details/<int:pk>", methods=["GET"])
def blog_details(pk):
    if not current_user.is_authenticated:
        flash('😂Please login to access this page.🤣')
        return redirect(url_for('auth.login'))

    blog_article_detail = BlogPost.query.get_or_404(pk)
    if current_user.id == blog_article_detail.user_id:
        return render_template('blog-details.html', blog_article_detail=blog_article_detail, date=datetime.now().strftime("%a %d %B %Y"))
    else:
        return redirect(url_for('yt_blog_generator.blog_posts'))

def youtube_title(link):
    try:
        # Extract video ID from different types of YouTube URLs
        video_id = None
        if 'v=' in link:
            video_id = link.split('v=')[-1].split('&')[0]
        elif 'youtu.be/' in link:
            video_id = link.split('youtu.be/')[-1].split('?')[0]
        else:
            current_app.logger.error(f"Unsupported YouTube URL format: {link}")
            return None
        
        if not video_id:
            current_app.logger.error(f"Unable to extract video ID from link: {link}")
            return None
        
        url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}'
        response = requests.get(url)
        response.raise_for_status()  # This will raise an HTTPError for bad responses
        data = response.json()
        
        if 'items' in data and len(data['items']) > 0:
            return data['items'][0]['snippet']['title']
        else:
            current_app.logger.error(f"No items found in YouTube API response for link: {link}")
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling YouTube API: {str(e)}")
    return None

def download_audio(link):
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(AUDIO_FOLDER_PATH, '%(title)s.%(ext)s'),
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(audio_file)
            new_file = base + '.mp3'
            if os.path.exists(audio_file) and not os.path.exists(new_file):
                os.rename(audio_file, new_file)
            current_app.logger.info(f"Audio file downloaded and renamed: {new_file}")
            return new_file, None
    except yt_dlp.utils.RegexNotFoundError:
        current_app.logger.error("Unable to extract metadata from the video")
        return None, "Unable to extract metadata from the video"
    except yt_dlp.utils.DownloadError as e:
        current_app.logger.error(f"Error downloading audio: {str(e)}")
        return None, f"Error downloading audio: {str(e)}"
    except Exception as e:
        current_app.logger.error(f"Error downloading audio: {str(e)}")
        return None, f"Error downloading audio: {str(e)}"

def process_youtube_video(user_id, youtube_link):
    user = db.session.query(User).get(user_id)  

    # Get title
    title = youtube_title(youtube_link)
    if not title:
        return None, "Failed to extract YouTube title."

    # Download audio
    audio_file, download_error = download_audio(youtube_link)
    if download_error:
        return None, download_error

    # Get transcript
    transcription, transcription_error = get_transcription(audio_file)
    if transcription_error:
        cleanup_files([audio_file])
        return None, transcription_error

    # Use OpenAI to generate the blog
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
        cleanup_files([audio_file])
        return None, 'Failed to generate blog article 😭'

    # Save blog article into database
    new_blog_article = BlogPost(
        user_id=user_id, 
        youtube_title=title,
        youtube_link=youtube_link,
        generated_content=blog_content,
    )
    db.session.add(new_blog_article)
    db.session.commit()

    # Clean up: delete audio file after use
    cleanup_files([audio_file])

    return new_blog_article, None

def cleanup_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)

def get_transcription(audio_file):
    aai.settings.api_key = os.getenv('ASSEMBLYAI_API_KEY')
    transcription_text = None
    try:
        transcriber = aai.Transcriber()
        transcript = transcriber.transcribe(audio_file)
        transcription_text = transcript.text
    except Exception as e:
        return None, str(e)
    return transcription_text, None

def generate_blog_from_transcription(transcription):
    prompt = f"Based on the following transcript from a YouTube video, " \
             f"write a comprehensive blog article. Write it based on the transcript, " \
             f"but don't make it look like a YouTube video. " \
             f"Make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt}
            ],
            max_tokens=1000,
            n=1,
            stop=None,
            temperature=0.7
        )
        generated_content = response.choices[0].message.content.strip()
        return generated_content
    except OpenAIError as e:
        current_app.logger.error(f"Error generating blog content: {str(e)}")
        return None
    