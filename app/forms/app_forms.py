from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, validators
from wtforms.fields.simple import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired

app_form_bp = Blueprint('forms', __name__)


class RegisterForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField("Confirm Password:", validators=[DataRequired(), validators.Length(min=6)])
    name = StringField("Name:", validators=[DataRequired()])
    submit = SubmitField("SIGN ME UP ¡!¡")


class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    remember_me = BooleanField('Remember Me: ', default=True)
    submit = SubmitField("GET ME IN ¡!¡")


class TextAreaFormIndex(FlaskForm):
    text_writing = TextAreaField(
        'Start Writing For Testing:',
        [validators.InputRequired(message="Please, first enter a text.")]
    )
    submit = SubmitField("Click for Response ¡!¡")


class TextAreaForm(FlaskForm):
    writing_text = TextAreaField(
        'Start Writing:',
        [validators.InputRequired(message="Please, first enter a text.")]
    )
    submit = SubmitField("Click for Response ¡!¡")


class ConversationIdForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:")
    submit = SubmitField('SELECT ¡!¡')


class DeleteForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:")
    submit = SubmitField('DELETE ¡!¡')
