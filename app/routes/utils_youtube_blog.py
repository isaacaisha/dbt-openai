# UTILS_YOUTUBE_BLOG_GENERATOR.PY

import os
import yt_dlp
import whisper
import httpx 

from dotenv import load_dotenv, find_dotenv

from openai import OpenAI, OpenAIError
from app.memory import BlogPost, User, db
from io import BytesIO
from langdetect import detect, LangDetectException
from gtts import gTTS


load_dotenv(find_dotenv())

# Define base directory relative to the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_FOLDER_PATH = os.path.join(BASE_DIR, 'static')
AUDIO_FOLDER_PATH = os.path.join(STATIC_FOLDER_PATH, 'media')

# Ensure the directory exists
os.makedirs(AUDIO_FOLDER_PATH, exist_ok=True)

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_COOKIES_PATH = os.getenv('YOUTUBE_COOKIES_PATH')
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def fetch_with_timeout(url, data, timeout=120):
    """Fetch data with a timeout for HTTP requests."""
    client = httpx.Client(http2=False, verify=True, timeout=timeout)

    try:
        response = client.post(url, json=data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except httpx.TimeoutException:
        return {'error': 'The request timed out. Please try again.'}
    except httpx.RequestError as e:
        return {'error': f'An error occurred: {str(e)}'}
    finally:
        client.close()


def youtube_title(link):
    """Extract the title of a YouTube video from its link."""
    client = httpx.Client(http2=False, verify=True)  # Instantiate the client
    try:
        video_id = extract_video_id(link)
        if not video_id:
            print(f"Unable to extract video ID from link: {link}")
            return None

        data = fetch_youtube_data(video_id, client)
        if not data:
            print(f"No items found in YouTube API response for link: {link}")
            return None

        return data.get('items', [{}])[0].get('snippet', {}).get('title')
    except httpx.RequestError as e:
        print(f"Error calling YouTube API: {str(e)}")
    finally:
        client.close()  # Close the client after use


def extract_video_id(link):
    """Extract the video ID from the YouTube link."""
    if 'v=' in link:
        return link.split('v=')[-1].split('&')[0]
    elif 'youtu.be/' in link:
        return link.split('youtu.be/')[-1].split('?')[0]
    elif 'shorts/' in link:
        return link.split('shorts/')[-1].split('?')[0]
    else:
        print(f"Unsupported YouTube URL format: {link}")
        return None


def fetch_youtube_data(video_id, client):
    """Fetch data from YouTube API using the video ID."""
    url = f'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}'
    response = client.get(url)
    response.raise_for_status()
    return response.json()


def download_audio(link):
    """Download audio from a YouTube video."""
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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.youtube.com/',
        'Origin': 'https://www.youtube.com',
        'Sec-Fetch-Mode': 'navigate',

        'rm_cache_dir': True,  # Add this line to remove the cache directory
        'cookiefile': YOUTUBE_COOKIES_PATH,  # Use the cookies file
        'cookies_from_browser': ('chrome', ),  # Use this option to get cookies directly from Chrome
        'verbose': True,  # Add this line
        'dump_single_json': True,  # Add this line to see the exact responses
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=True)
            audio_file = ydl.prepare_filename(info_dict)
            base, ext = os.path.splitext(audio_file)
            new_file = base + '.mp3'
            if os.path.exists(audio_file) and not os.path.exists(new_file):
                os.rename(audio_file, new_file)
            print(f"Audio file downloaded and renamed: {new_file}")
            return new_file, None
    except yt_dlp.utils.RegexNotFoundError:
        print("Unable to extract metadata from the video")
        return None, "Unable to extract metadata from the video"
    except yt_dlp.utils.DownloadError as e:
        print(f"Error downloading audio: {str(e)}")
        return None, f"Error downloading audio: {str(e)}"
    except Exception as e:
        print(f"Error downloading audio: {str(e)}")
        return None, f"Error downloading audio: {str(e)}"


def get_transcription(audio_file_path):
    """Transcribe the audio file using Whisper."""
    try:
        model = whisper.load_model("tiny")  # You can also try "small" or "large" depending on your resources
        result = model.transcribe(audio_file_path)
        transcription_text = result["text"]
        return transcription_text, None
    except Exception as e:
        return None, f"Error transcribing audio with Whisper: {str(e)}"


def generate_blog_from_transcription(transcription):
    """Generate blog content from the transcription using OpenAI."""
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
        print(f"Error generating blog content: {str(e)}")
        return None
    

def process_youtube_video(user_id, youtube_link):
    """Process the YouTube video to generate a blog article."""
    user = db.session.query(User).get(user_id)

    # Get title
    title = youtube_title(youtube_link)
    if not title:
        return None, "Failed to extract YouTube title."

    # Download audio
    audio_file_path, download_error = download_audio(youtube_link)
    if download_error:
        return None, download_error

    # Get transcript
    transcription, transcription_error = get_transcription(audio_file_path)
    if transcription_error:
        cleanup_files([audio_file_path])
        return None, transcription_error

    # Use OpenAI to generate the blog
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
        cleanup_files([audio_file_path])
        return None, 'Failed to generate blog article 😭'

    # Detect the language of the blog content
    try:
        detected_lang = detect(blog_content)
    except LangDetectException:
        detected_lang = 'en'  # Default to English if detection fails

    # Convert the blog content to speech using gTTS
    generated_audio_file_path = os.path.join(AUDIO_FOLDER_PATH, 'blog_audio.mp3')
    tts = gTTS(blog_content, lang=detected_lang)
    tts.save(generated_audio_file_path)

    with open(generated_audio_file_path, 'rb') as generated_audio_file:
        audio_data = generated_audio_file.read()

    # Save blog article into the database with the audio
    new_blog_article = BlogPost(
        user_id=user_id,
        youtube_title=title,
        youtube_link=youtube_link,
        generated_content=blog_content,
        audio_data=audio_data
    )
    db.session.add(new_blog_article)
    db.session.commit()

    # Clean up: delete both the original downloaded audio file and the generated blog audio file
    cleanup_files([audio_file_path, generated_audio_file_path])

    return new_blog_article, None


def cleanup_files(file_paths):
    """Remove specified files from the filesystem."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"Removed file: {file_path}")  # Logging
            except OSError as e:
                print(f"Error removing file {file_path}: {str(e)}")
        else:
            print(f"File not found for removal: {file_path}")  # Logging
