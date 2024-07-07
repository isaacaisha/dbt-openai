import os
import assemblyai as aai

from flask import Blueprint, flash, render_template, request, jsonify, redirect, url_for
from datetime import datetime
from openai import OpenAI, OpenAIError
from pytube import YouTube
from flask_login import current_user
from app.memory import BlogPost, User, db

from langchain.chains import ConversationChain
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langdetect import detect


features_extras_bp = Blueprint('extras_features', __name__)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

llm = ChatOpenAI(temperature=0.0, model="gpt-4o")
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory, verbose=False)
# memory_summary = ConversationSummaryBufferMemory(llm=llm, max_token_limit=3)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


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


# def generate_blog_from_transcription(transcription):
#     if not transcription:
#         return None, None
#     
#     detected_lang = detect(transcription)
#     print(f"Detected language: {detected_lang}")  # Debugging
#     
#     prompts = {
#         'fr': f"Sur la base de la transcription suivante d'une vidéo YouTube, rédigez un article de blog complet. Écrivez-le en français :\n\n{transcription}\n\nArticle:",
#         'es': f"Basado en la siguiente transcripción de un video de YouTube, escribe un artículo de blog completo. Escríbelo en español:\n\n{transcription}\n\nArtículo:",
#         'default': f"Based on the following transcript from a YouTube video, write a comprehensive blog article. Write it in English:\n\n{transcription}\n\nArticle:"
#     }
# 
#     user_message = prompts.get(detected_lang, prompts['default'])
#     print(f"Using prompt: {user_message}")  # Debugging
# 
#     try:
#         response = conversation.predict(input=user_message)
# 
#         if isinstance(response, str):
#             generated_content = response
#         else:
#             generated_content = response.choices[0].message['content']
# 
#         generated_content = generated_content.replace('#', '').replace('*', '')
# 
#         print(f'LLM Response:\n{generated_content}\n')
# 
#         return generated_content, detected_lang
#     
#     except OpenAIError as e:
#         print(f"OpenAI API Error: {e}")
#         return None, None
#     except Exception as e:
#         print(f"Error generating blog content: {str(e)}")
#         return None, None


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
    new_blog_article = BlogPost(
        user_id=current_user.id, 
        youtube_title=title,
        youtube_link=youtube_link,
        generated_content=blog_content,
    )
    db.session.add(new_blog_article)
    db.session.commit()

    return new_blog_article, None
