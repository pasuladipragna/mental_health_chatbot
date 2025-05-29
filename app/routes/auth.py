# app/routes/auth.py
from flask import Blueprint, request, redirect, url_for, flash, session, render_template
from app.models import  User
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db
from flask import session

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):  # ✅ CORRECT

            login_user(user)
            print("Session contents:", session)
            flash("Login successful", "success")
            user_id = user.id
            if isinstance(user_id, bytes):
                user_id = user_id.decode('utf-8')  # Decode if needed 
            session["user_id"] = str(user.id)

            #session["username"] = user.username
            return redirect(url_for("views.dashboard"))
        else:
            flash("Invalid username or password", "error")
            return render_template('login.html', username=username)

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match')
            return redirect(url_for('auth.register'))

        if len(password) < 6:
            flash('Password must be at least 6 characters long')
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        existing_user_email = User.query.filter_by(email=email).first()
        existing_user_username = User.query.filter_by(username=username).first()

        if existing_user_username:
            flash('Username already taken', 'danger')
            return redirect(url_for('auth.register'))

        if existing_user_email:
            flash('Email already registered', 'danger')
            return redirect(url_for('auth.register'))

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. Please log in.')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            flash('If this email exists in our system, a reset link will be sent.')
        else:
            flash('No user found with that email.')
        return redirect(url_for('auth.login'))
    return render_template('forgot_password.html')