from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField("Password:", validators=[DataRequired(), validators.Length(min=6)])
    name = StringField("Name:", validators=[DataRequired()])
    submit = SubmitField("SIGN M€ UP ¡!¡")


class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    remember_me = BooleanField('Remember Me: ', default=True)
    submit = SubmitField("LET M€ IN ¡!¡")


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField(
        'Start Writing for testing:',
        [validators.InputRequired(message="Please enter a text.")]
    )
    submit = SubmitField("Click for Response 🔥¡!¡🔥")


class ConversationIdForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:")
    submit = SubmitField('SELECT ¡!¡')


class DeleteForm(FlaskForm):
    conversation_id = IntegerField("Conversation ID:")
    submit = SubmitField('DELETE ¡!¡')
