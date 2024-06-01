import os
import secrets
from datetime import timedelta

import openai
from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager

from app.database import SQLALCHEMY_DATABASE_URL, db, database_bp
from app.app_forms import app_form_bp
from app.memory import memory_bp, User

from app.routes.auth import auth_bp
from app.routes.process_interface_conversation import interface_conversation_bp
from app.routes.home_process import home_conversation_bp
from app.routes.convers_functions import conversation_functionality_bp
from app.routes.llm_conversation import llm_conversation_bp

load_dotenv(find_dotenv())

def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    Bootstrap(app)

    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

    login_manager = LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.init_app(app)

    try:
        openai_api_key = os.environ['OPENAI_API_KEY']
    except KeyError:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    openai.api_key = openai_api_key

    secret_key = secrets.token_hex(19)
    app.secret_key = secret_key

    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_AS_ASCII'] = False

    db.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(database_bp, name='database')
    app.register_blueprint(app_form_bp, name='forms')
    app.register_blueprint(memory_bp, name='memory')
    app.register_blueprint(auth_bp, name='auth')
    app.register_blueprint(home_conversation_bp, name='conversation_home')
    app.register_blueprint(interface_conversation_bp, name='conversation_interface')
    app.register_blueprint(conversation_functionality_bp, name='conversation_function')
    app.register_blueprint(llm_conversation_bp, name='llm_conversation')

    return app

app = create_app()

if __name__ == '__main__':
    home_temp_audio_file = 'home_temp_audio.mp3'
    if os.path.exists(home_temp_audio_file):
        os.remove(home_temp_audio_file)

    interface_temp_audio_file = 'interface_temp_audio.mp3'
    if os.path.exists(interface_temp_audio_file):
        os.remove(interface_temp_audio_file)

    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
