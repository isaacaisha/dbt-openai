from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import SubmitField, IntegerField, validators
from wtforms.fields.simple import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, NumberRange, EqualTo, ValidationError

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


class PasswordResetRequestForm(FlaskForm):
    email = StringField('Email:', validators=[DataRequired(), validators.Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(form, field):
        field.data = field.data.strip().lower()
        if not field.data:
            raise ValidationError('Invalid email address.')


class PasswordResetForm(FlaskForm):
    password = PasswordField('New Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm New Password:', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


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
    submit = SubmitField('SELECT ¡!¡')


class DeleteForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:", validators=[InputRequired(), NumberRange(min=1)])
    submit = SubmitField('SELECT ¡!¡')
    submit = SubmitField('DELETE ¡!¡')
