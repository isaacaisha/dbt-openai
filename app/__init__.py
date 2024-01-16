import os
import secrets
import openai
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from .databases.database import database_bp
from .forms.app_forms import app_form_bp
from .models.memory import memory_bp, db, User
from .schemas.schemas import schemas_bp
from .routes.auth import auth_bp
from .routes.process_home_conversation import home_conversation_bp
from .routes.process_interface_conversation import interface_conversation_bp
from .routes.conversation_functionality import functionality_conversation_bp
from .routes.llm_conversation import llm_conversation_bp


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')
    Bootstrap(app)

    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Configurations
    try:
        openai_api_key = os.environ['OPENAI_API_KEY']
    except KeyError:
        raise ValueError("OPENAI_API_KEY environment variable is not set.")

    # Set the OpenAI API key
    openai.api_key = openai_api_key

    # Generate a random secret key
    secret_key = secrets.token_hex(19)
    # Set it as the Flask application's secret key
    app.secret_key = secret_key

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.environ['user']}:{os.environ['password']}@"
        f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Initialize database
    with app.app_context():
        db.create_all()

    # Register blueprints
    app.register_blueprint(database_bp, url_prefix='/database', name='database')
    app.register_blueprint(app_form_bp, url_prefix='/app_form', name='forms')
    app.register_blueprint(memory_bp, url_prefix='/memory', name='memory')
    app.register_blueprint(auth_bp, url_prefix='/auth', name='auth')
    app.register_blueprint(home_conversation_bp, url_prefix='/process_home_conversation', name='conversation_home')
    app.register_blueprint(interface_conversation_bp, url_prefix='/process_interface_conversation',
                           name='conversation_interface')
    app.register_blueprint(functionality_conversation_bp, url_prefix='/conversation_functionality',
                           name='conversation_function')
    app.register_blueprint(llm_conversation_bp, url_prefix='/llm_conversation', name='llm_conversation')
    app.register_blueprint(schemas_bp, url_prefix='/schemas', name='schemas')

    return app
