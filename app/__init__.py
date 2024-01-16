import os

from flask import Flask

from .databases.database import database_bp
from .forms.app_forms import app_form_bp
from .models.memory import memory_bp, db, User
from .schemas.schemas import schemas_bp

from .routes.auth import auth_bp
from .routes.process_interface_conversation import interface_conversation_bp
from .routes.home_process import home_conversation_bp
from .routes.convers_functions import conversation_functionality_bp
from .routes.llm_conversation import llm_conversation_bp


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"postgresql://{os.environ['user']}:{os.environ['password']}@"
        f"{os.environ['host']}:{os.environ['port']}/{os.environ['database']}")
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
    app.register_blueprint(schemas_bp, name='schemas')

    return app


app = create_app()
