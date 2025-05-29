import pytest
import json
import torch
from unittest.mock import patch, MagicMock
from app import create_app, db
from app.models import User

# ---------- Fixtures ----------

@pytest.fixture
def app():
    app = create_app(test_config={
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret'
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def user(app):
    test_user = User(username="testuser", email="test@example.com", password="testpass123")
    db.session.add(test_user)
    db.session.commit()
    return test_user

@pytest.fixture
def authenticated_client(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)  # Flask-Login default
        sess["_fresh"] = True  # Mark session as fresh
    yield client

# ---------- CHAT API ----------
def test_login_and_access(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True

    response = client.get("/some_protected_route")
    assert response.status_code != 401


@patch("app.routes.chat.emotion_classifier")
@patch("app.routes.chat.tokenizer")
@patch("app.routes.chat.model")
def test_chat_valid_input(mock_model, mock_tokenizer, mock_emotion, authenticated_client):
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_tokenizer.decode.return_value = "I'm here for you."
    mock_emotion.return_value = [{"label": "joy", "score": 0.98}]

    response = authenticated_client.post("/api/chat", json={"message": "I'm feeling good today!"})
    data = response.get_json()

    assert response.status_code == 200
    assert "I'm here for you." in data["response"]
    assert data["mood"] == "joy"
    assert "😊" in data["emoji"]
    assert "Keep smiling" in data["tip"]

@patch("app.routes.chat.model")
def test_chat_empty_input(mock_model, authenticated_client):
    response = authenticated_client.post("/api/chat", json={"message": ""})
    assert response.status_code == 400
    assert response.get_json()["error"] == "Empty message"

@patch("app.routes.chat.model")
def test_chat_long_input(mock_model, authenticated_client):
    long_message = "a" * 301
    response = authenticated_client.post("/api/chat", json={"message": long_message})
    assert response.status_code == 400
    assert "too long" in response.get_json()["error"]

def test_chat_no_user_id(client):
    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 401

@patch("app.routes.chat.model")
@patch("app.routes.chat.tokenizer")
@patch("app.routes.chat.emotion_classifier", side_effect=Exception("classifier error"))
def test_chat_emotion_fallback(mock_emotion, mock_tokenizer, mock_model, authenticated_client):
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_tokenizer.decode.return_value = "Thanks for sharing."

    response = authenticated_client.post("/api/chat", json={"message": "Not sure how I feel."})
    data = response.get_json()

    assert response.status_code == 200
    assert data["mood"] == "neutral"
    assert "😐" in data["emoji"]

# ---------- RESET CHAT ----------

def test_reset_chat(authenticated_client):
    with authenticated_client.session_transaction() as sess:
        sess["chat_history"] = ["Hi", "Hello!"]
    response = authenticated_client.post("/reset_chat")
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "reset"
    with authenticated_client.session_transaction() as sess:
        assert "chat_history" not in sess

# ---------- EXPORT ----------

def test_export_chat_csv(authenticated_client):
    response = authenticated_client.get("/export/chat/csv")
    assert response.status_code == 200
    assert "text/csv" in response.content_type

@patch("app.routes.chat.model")
@patch("app.routes.chat.tokenizer")
@patch("app.routes.chat.emotion_classifier")
def test_mood_trend(mock_emotion, mock_tokenizer, mock_model, authenticated_client):
    mock_model.generate.return_value = torch.tensor([[1, 2, 3]])
    mock_tokenizer.decode.return_value = "I'm listening."
    mock_emotion.side_effect = [
        [{"label": "joy", "score": 0.95}],
        [{"label": "anger", "score": 0.85}],
        [{"label": "neutral", "score": 0.80}],
    ]

    for msg in ["I'm happy", "I'm stressed", "I'm okay"]:
        authenticated_client.post("/api/chat", json={"message": msg})

    response = authenticated_client.get("/mood_trends")
    assert response.status_code == 200
    assert "mood_trends" in response.get_json()

# ---------- CONTACT THERAPIST ----------

def test_contact_therapist_exists(tmp_path, app, authenticated_client):
    test_json = tmp_path / "therapists.json"
    test_json.write_text(json.dumps([{"name": "Dr. Test", "email": "test@clinic.com"}]))

    with patch("app.routes.chat.Path") as mock_path:
        mock_path.return_value.exists.return_value = True
        mock_path.return_value.open.return_value.__enter__.return_value = open(test_json)
        response = authenticated_client.get("/contact_therapist")
        assert response.status_code == 200
        assert b"Dr. Test" in response.data

def test_contact_therapist_missing(authenticated_client):
    response = authenticated_client.get("/contact_therapist")
    assert response.status_code == 200
    assert b"No therapists available" in response.data or b"[]" in response.data
