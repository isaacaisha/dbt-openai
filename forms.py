from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators, TextAreaField, BooleanField, IntegerField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password", validators=[DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField("Password", validators=[DataRequired(), validators.Length(min=6)])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("SIGN M€ UP ¡!¡")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField('Remember Me: ')
    submit = SubmitField("LET M€ IN ¡!¡")


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


class ConversationIdForm(FlaskForm):
    conversation_id = IntegerField("conversation_id")
    submit = SubmitField('SELECT ¡!¡')


class DeleteForm(FlaskForm):
    conversation_id = IntegerField("conversation_id")
    submit = SubmitField('DELETE ¡!¡')
