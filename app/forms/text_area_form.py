from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import SubmitField, validators, TextAreaField


text_area_form_bp = Blueprint('text_area', __name__)


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField(
        'Start Writing:',
        [validators.InputRequired(message="Please, first enter a text.")]
    )
    submit = SubmitField("Click for Response ¡!¡")
