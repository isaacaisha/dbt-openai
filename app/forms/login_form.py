from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators, BooleanField
from wtforms.validators import DataRequired


login_form_bp = Blueprint('login', __name__)


class LoginForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired()])
    remember_me = BooleanField('Remember Me: ', default=True)
    submit = SubmitField("LET M€ IN ¡!¡")
