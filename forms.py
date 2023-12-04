from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField, validators, TextAreaField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


# WTForm
class CreateArticleForm(FlaskForm):
    title = StringField("Article Title", validators=[DataRequired()])
    price = StringField("Price (£)", validators=[DataRequired()])
    img_url = StringField("Product Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Product Content", validators=[DataRequired()])
    author = StringField("Product Author")
    author_id = StringField("Author_id")
    submit = SubmitField("SUBMIT PRODUCT ¡!¡")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password", validators=[DataRequired(), validators.Length(min=6)])
    submit = SubmitField("SIGN M€ UP ¡!¡")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), validators.Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LET M€ IN ¡!¡")


# Define a Flask form
class TextAreaForm(FlaskForm):
    writing_text = TextAreaField('Start Writing', [validators.InputRequired(message="Please enter text.")])
    submit = SubmitField()


class EmailForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), validators.Email()])
    phone = IntegerField("Phone Number", validators=[DataRequired()])
    email_message = CKEditorField("Message", validators=[validators.DataRequired()])
    submit = SubmitField("S€ND ¡!¡")


class DeleteForm(FlaskForm):
    conversation_id = StringField("conversation_id")
    submit = SubmitField('SUBMIT COMMENT ¡!¡')
