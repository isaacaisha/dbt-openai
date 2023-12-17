from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField


conversation_id_form_bp = Blueprint('conversation', __name__)


class ConversationIdForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:")
    submit = SubmitField('SELECT ¡!¡')
