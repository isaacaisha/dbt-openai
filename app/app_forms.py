# app_forms.py

from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField, IntegerField, validators
from wtforms.fields.simple import StringField, PasswordField, BooleanField, TextAreaField, URLField
from wtforms.validators import DataRequired, InputRequired, NumberRange, EqualTo, ValidationError

app_form_bp = Blueprint('forms', __name__)


class RegisterForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField("Confirm Password:", validators=[DataRequired(), validators.Length(min=6)])
    name = StringField("Name:", validators=[DataRequired()])
    submit = SubmitField("-¡!¡- REGISTER -¡!¡-")


class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    remember_me = BooleanField('Remember Me: ', default=True)
    submit = SubmitField("-¡!¡- LOGIN -¡!¡-")


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email:', validators=[DataRequired(), validators.Email()])
    submit = SubmitField('-¡!¡- Reset Password -¡!¡-')

    def validate_email(form, field):
        field.data = field.data.strip().lower()
        if not field.data:
            raise ValidationError('Invalid email address.')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password:', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('-¡!¡- Reset Password -¡!¡-')


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
    conversation_id = IntegerField("Conversation ID:", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('-¡!¡- SELECT -¡!¡-')


class DeleteForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('-¡!¡- DELETE -¡!¡-')


class ThemeChatForm(FlaskForm):
    theme_name = StringField('Create a Theme or Login into Existing One:', [InputRequired(message="Please, first enter a Theme's Name.")])
    submit = SubmitField("-¡!¡- Start Chatting -¡!¡-")


class ForumChatForm(FlaskForm):
    username = HiddenField("UserName:", validators=[DataRequired()])
    theme_id = HiddenField("Theme's ID:", validators=[DataRequired()])
    message = TextAreaField('Enter a Text & start Chatting:', [InputRequired(message="Please, first enter a text.")])
    submit = SubmitField("-¡!¡- SEND -¡!¡-")


class WebsiteReviewForm(FlaskForm):
    domain = URLField("Enter the domain URL:", validators=[InputRequired(message="Please enter a valid URL.")])
    submit = SubmitField('-¡!¡- SUBMIT -¡!¡-')


class DatabaseForm(FlaskForm):
    database_name = StringField("Database's Name:", validators=[InputRequired()])
    data_id = IntegerField("Data ID:", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('-¡!¡- DELETE -¡!¡-')
