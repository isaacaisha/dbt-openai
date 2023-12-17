from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, validators
from wtforms.validators import DataRequired


register_form_bp = Blueprint('register', __name__)


class RegisterForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password:", validators=[DataRequired(), validators.Length(min=6)])
    confirm_password = PasswordField("Password:", validators=[DataRequired(), validators.Length(min=6)])
    name = StringField("Name:", validators=[DataRequired()])
    submit = SubmitField("SIGN M€ UP ¡!¡")
