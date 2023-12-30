from flask import Flask

from .app_creates.app_config import app_config_bp

from .databases.database import database_bp

from .forms.app_forms import app_form_bp

from .models.memory import memory_bp, Memory, User, db

from .routes.auth import auth_bp
from .routes.conversation import conversation_bp

from .schemas.schemas import schemas_bp


app = Flask(__name__)

app.register_blueprint(app_config_bp, name='configure')

app.register_blueprint(database_bp, name='database')

app.register_blueprint(app_form_bp, name='forms')

app.register_blueprint(memory_bp, name='memory')

app.register_blueprint(auth_bp, name='auth')

app.register_blueprint(conversation_bp, name='conversation')

app.register_blueprint(schemas_bp, name='schemas')
