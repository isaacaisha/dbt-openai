from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField

delete_form_bp = Blueprint('delete', __name__)


class DeleteForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:")
    submit = SubmitField('DELETE ¡!¡')
