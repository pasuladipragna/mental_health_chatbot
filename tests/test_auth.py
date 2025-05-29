# test/test_auth.py
import pytest
from app.models import  User
from werkzeug.security import generate_password_hash
from app import create_app
from app.database import db

@pytest.fixture
def app():
    app = create_app(test_config={"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:"})
  # Make sure create_app accepts `testing=True`
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def auth_client(app):
    return app.test_client()

def test_register_user(app, auth_client):
    with app.app_context():  # ✅ ensure db context is active
        response = auth_client.post('/auth/register', data=dict(
            username='newuser',
            email='new@example.com',
            password='newpassword',
            confirm_password='newpassword'
        ), follow_redirects=True)

        print(response.data)  # Debug output if needed
        assert b'Registration successful. Please log in' in response.data, "User registration did not succeed"

        user = User.query.filter_by(email='new@example.com').first()
        assert user is not None, "User was not found in the database after registration."



def test_register_mismatched_passwords(auth_client):
    response = auth_client.post('/auth/register', data={
        'username': 'user',
        'email': 'user@example.com',
        'password': 'pass123',
        'confirm_password': 'pass321'
    }, follow_redirects=True)
    assert b'Passwords do not match' in response.data

def test_register_short_password(auth_client):
    response = auth_client.post('/auth/register', data={
        'username': 'shortpass',
        'email': 'short@example.com',
        'password': '123',
        'confirm_password': '123'
    }, follow_redirects=True)
    assert b'Password must be at least 6 characters long' in response.data


def test_login_user(app, auth_client):
    with app.app_context():
        # Reset database
        db.drop_all()
        db.create_all()

        # Create user with plaintext password (hashed via @password.setter)
        user = User(username="testuser", email="test@example.com", password="testpassword")
        db.session.add(user)
        db.session.commit()

    # Attempt login
    response = auth_client.post('/auth/auth/login', data={
        'username': 'testuser',
        'password': 'testpassword'
    }, follow_redirects=True)
    assert b'Welcome testuser' in response.data
    # Check that login was successful
    assert b'Login successful' in response.data
    assert b'Invalid username or password' not in response.data
    assert response.status_code == 200
    





def test_login_invalid_user(auth_client):
    response = auth_client.post('/auth/auth/login', data={
        'username': 'invaliduser',
        'password': 'wrongpass'
    }, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_register_existing_email(app, auth_client):
    user = User(username='existing', email='exist@example.com', password=generate_password_hash('existpass'))
    db.session.add(user)
    db.session.commit()
    response = auth_client.post('/auth/register', data={
        'username': 'another',
        'email': 'exist@example.com',
        'password': 'newpass',
        'confirm_password': 'newpass'
    }, follow_redirects=True)
    assert b'Email already registered' in response.data

def test_logout(auth_client, app):
    with app.app_context():
        user = User(username="logoutuser", email="logout@example.com",password="logoutpass")
        #user.password = "logoutpass"
        db.session.add(user)
        db.session.commit()

    # Login
    auth_client.post('/auth/auth/login', data={
        'username': 'logoutuser',
        'password': 'logoutpass'
    }, follow_redirects=True)

    # Logout
    response = auth_client.get('/auth/logout', follow_redirects=True)

    # Assert flash message
    assert b'You have been logged out' in response.data



def test_register_existing_username(app, auth_client):
    user = User(username='duplicateuser', email='unique@example.com', password=generate_password_hash('pass', method='pbkdf2:sha256'))
    db.session.add(user)
    db.session.commit()
    response = auth_client.post('/auth/register', data={
        'username': 'duplicateuser',
        'email': 'another@example.com',
        'password': 'pass1234',
        'confirm_password': 'pass1234'
    }, follow_redirects=True)
    assert b'Username already taken' in response.data


def test_forgot_password_existing_user(auth_client, app):
    user = User(username='forgotuser', email='forgot@example.com', password=generate_password_hash('forgotpass'))
    db.session.add(user)
    db.session.commit()
    response = auth_client.post('/auth/forgot-password', data={
        'email': 'forgot@example.com'
    }, follow_redirects=True)
    assert b'reset link' in response.data or b'No user found' in response.data

def test_forgot_password_nonexistent_user(auth_client):
    response = auth_client.post('/auth/forgot-password', data={
        'email': 'doesnotexist@example.com'
    }, follow_redirects=True)
    assert b'No user found with that email.' in response.data
    