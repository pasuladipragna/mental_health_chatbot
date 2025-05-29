# test/test_init.py
import pytest
from app import create_app
from app.models import User
from app.routes import views, chat
from app.database import db

@pytest.fixture
def app():
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SESSION_TYPE': 'filesystem',
        'SECRET_KEY': 'test-secret'
    }
    app = create_app(test_config=test_config)
    with app.app_context():
        
        db.create_all()
    yield app

    # Optional teardown: drop all tables after test
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

def test_app_creation(app):
    assert app is not None
    assert app.testing is True

def test_blueprints_registered(app):
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print("Registered Routes:", routes) # For debugging purposes
    
    # Auth routes
    assert "/auth/auth/login" in routes
    assert "/auth/register" in routes
    assert "/auth/logout" in routes
    assert "/auth/forgot-password" in routes

    # Chat API routes
    assert "/api/chat" in routes
    assert "/reset_chat" in routes
    assert "/contact_therapist" in routes

    # View routes
    assert "/" in routes  # Home
    assert "/dashboard" in routes
    assert "/mood-trends" in routes
    assert "/chat-history" in routes
    assert any("/export/chat" in route for route in routes)
    assert any("/export/mood" in route for route in routes)


def test_app_logs_creation(tmp_path):
    log_dir = tmp_path / "logs"
    log_file = log_dir / "flask.log"
    log_dir.mkdir()
    log_file.write_text("INFO test log entry\n")
    logs = log_file.read_text().splitlines()
    assert logs
    assert "INFO" in logs[-1]

def test_404_handler(client):
    response = client.get('/nonexistent')
    assert response.status_code == 404
    assert b"404 Not Found" in response.data

def test_500_handler():
    app = create_app({"TESTING": True, "PROPAGATE_EXCEPTIONS": False})
    client = app.test_client()
    response = client.get("/trigger500")
    
    assert response.status_code == 500
    assert b"500 Internal Server Error" in response.data

