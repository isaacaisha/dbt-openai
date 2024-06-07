import secrets
from flask import Blueprint, current_app, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, logout_user
from flask_mail import Mail, Message
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from app.app_forms import LoginForm, PasswordResetForm, PasswordResetRequestForm, RegisterForm
from app.memory import User, db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    register_form = RegisterForm()

    if request.method == "POST":
        # Check if the passwords match
        if register_form.password.data != register_form.confirm_password.data:
            flash("Passwords do not match. Please enter matching passwords ¡!¡😭¡!¡")
            return redirect(url_for('auth.register'))

        # If user's email already exists
        if User.query.filter_by(email=register_form.email.data).first():
            # Send a flash message
            flash("You've already signed up with that email, log in instead! ¡!!🤣¡!¡")
            return redirect(url_for('auth.login'))

        hash_and_salted_password = generate_password_hash(
            register_form.password.data.lower().strip(),
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User()
        new_user.email = request.form['email'].lower().strip()
        new_user.name = request.form['name']
        new_user.password = hash_and_salted_password

        db.session.add(new_user)
        db.session.commit()
        db.session.refresh(new_user)

        # Log in and authenticate the user after adding details to the database.
        login_user(new_user)

        return redirect(url_for('auth.login'))

    return render_template("register.html", register_form=register_form,
                           current_user=current_user, date=datetime.now().strftime("%a %d %B %Y"))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm()

    if request.method == "POST":
        email = request.form.get('email').lower().strip()
        password = request.form.get('password').lower().strip()
        remember_me = login_form.remember_me.data

        # Find user by email entered.
        user = User.query.filter_by(email=email).first()

        # Email doesn't exist
        if not user:
            flash("That email does not exist, try again ¡!¡😭¡!¡")
            return redirect(url_for('auth.login'))

        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again 😭')
            return redirect(url_for('auth.login'))

        # Email exists and password correct
        else:
            # Log in the user
            login_user(user, remember=remember_me)

            # Redirect to the appropriate page after login
            return redirect(url_for('conversation_interface.conversation_interface'))

    return render_template("login.html", login_form=login_form, current_user=current_user,
                           date=datetime.now().strftime("%a %d %B %Y"))


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('conversation_home.home'))


# Generate a secure secret key
secret_key = secrets.token_hex(16)

# Initialize the URLSafeTimedSerializer with the secret key
s = URLSafeTimedSerializer(secret_key)

def send_reset_email(user, token):
    reset_url = url_for('auth.reset_with_token', token=token, _external=True)
    msg = Message('Password Reset Request', recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail = current_app.extensions['mail']
    mail.send(msg)


@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('conversation_interface.conversation_interface'))

    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='password-reset-salt')
            send_reset_email(user, token)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('Email not found!', 'danger')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', form=form, date=datetime.now().strftime("%a %d %B %Y"))

@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('conversation_interface.conversation_interface'))

    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # 1 hour expiration
    except SignatureExpired:
        flash('The password reset link has expired.', 'danger')
        return redirect(url_for('auth.reset_password'))

    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)
            user.password = hashed_password
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('auth.login'))

    return render_template('reset_with_token.html', form=form, token=token)
