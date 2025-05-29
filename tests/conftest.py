import sys
import os
import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.models import User
from app.database import db as _db

@pytest.fixture(scope='session')
def app():
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret'
    }
    app = create_app(test_config=test_config)
    with app.app_context():
        yield app

@pytest.fixture(scope='session')
def db(app):
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.config["LOGIN_DISABLED"] = False  # Make sure login is enforced
    with app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def test_user(db):
    user = User(username="testuser", email="test@example.com", password=generate_password_hash("1234"))
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture(scope='function')
def login_user(client):
    def _login(email, password):
        return client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)
    return _login


def test_print_routes(app):
    for rule in app.url_map.iter_rules():
        print(rule.endpoint, rule.rule)
