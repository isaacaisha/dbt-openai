from flask import Flask

from .databases.database import database_bp

from .forms.conversation_id_form import conversation_id_form_bp
from .forms.delete_form import delete_form_bp
from .forms.login_form import login_form_bp
from .forms.register_form import register_form_bp
from .forms.text_area_form import text_area_form_bp

from .models.memory import memory_bp, Memory, User, db

from .schemas.schemas import schemas_bp


app = Flask(__name__)

# Register blueprints with unique names
app.register_blueprint(database_bp, name='database')

app.register_blueprint(conversation_id_form_bp, name='conversation_id_form')
app.register_blueprint(delete_form_bp, name='delete_form')
app.register_blueprint(login_form_bp, name='login_form')
app.register_blueprint(register_form_bp, name='register_form')
app.register_blueprint(text_area_form_bp, name='text_area_form')

app.register_blueprint(memory_bp, name='memory')

app.register_blueprint(schemas_bp, name='schemas')
