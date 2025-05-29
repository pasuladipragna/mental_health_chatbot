import pytest
from datetime import datetime
from flask import url_for
from app.models import User, ChatLog, MoodLog
from werkzeug.security import generate_password_hash
import uuid
# ---------------------------------------------------
# Helper Fixture: Create & Login Test User
# ---------------------------------------------------
@pytest.fixture
def test_user_logged_in(client, db, app):
    with app.app_context():
        unique_id = str(uuid.uuid4())[:8]
        username = f"testuser_{unique_id}"
        email = f"{username}@example.com"
        password = "testpass"

        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()

        # Set session manually
        with client.session_transaction() as sess:
            sess["user_id"] = user.id  # Adjust according to your login logic

        # Return basic fields only
        return user


# ---------------------------------------------------
# Route Protection: Login Required
# ---------------------------------------------------
@pytest.mark.parametrize("route", [
    "/dashboard", "/chat-history", "/mood-trends", "/mood-trends/data",
    "/export/chat/json", "/export/chat/csv", "/export/chat/pdf",
    "/export/mood/json", "/export/mood/csv", "/export/mood/pdf",
    "/export/json", "/contact_therapist"
])
def test_login_required_redirects(client, route):
    res = client.get(route)
    assert res.status_code in [302, 401]
    if res.status_code == 302:
        assert "/login" in res.headers["Location"]

# ---------------------------------------------------
# Dashboard View
# ---------------------------------------------------
def test_dashboard_authenticated(client):
    client.post("/auth/auth/login", data={
        "username": "testuser",
        "password": "testpass"
    }, follow_redirects=True)

    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200

# ---------------------------------------------------
# Chat History View
# ---------------------------------------------------
def test_chat_history_view(client, db, test_user_logged_in):
    # Add a chat entry for the test user
    db.session.add(ChatLog(
        user_id=test_user_logged_in.id,
        user_input="Hey",
        bot_response="Hi",
        mood="neutral"
    ))
    db.session.commit()

    # 🔒 Manually set session user_id inside the test client
    with client.session_transaction() as session:
        session["user_id"] = test_user_logged_in.id


    # Make the request with an authenticated session (already set in fixture)
    response = client.get("/chat-history")
    
    assert response.status_code == 200
    assert b"Hey" in response.data or b"Hi" in response.data


# ---------------------------------------------------
# Mood Trends View + Data
# ---------------------------------------------------
def test_mood_trends_view(client, test_user_logged_in):
    res = client.get("/mood-trends")
    assert res.status_code == 200

def test_mood_trends_data(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(MoodLog(user_id=test_user_logged_in.id, mood="happy"))
        db.session.commit()
    res = client.get("/mood-trends/data")
    json_data = res.get_json()
    assert isinstance(json_data, list)
    assert any("happy" in entry["mood"] for entry in json_data)

# ---------------------------------------------------
# Export Routes - Chat Logs
# ---------------------------------------------------
def test_export_chat_json(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(ChatLog(user_id=test_user_logged_in.id, user_input="Hi", bot_response="Hello!", mood="calm"))
        db.session.commit()
    res = client.get("/export/chat/json")
    assert res.status_code == 200
    assert res.is_json
    assert b"Hi" in res.data

def test_export_chat_csv(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(ChatLog(user_id=test_user_logged_in.id, user_input="Hi", bot_response="Hello!", mood="calm"))
        db.session.commit()
    res = client.get("/export/chat/csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type

def test_export_chat_pdf(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(ChatLog(user_id=test_user_logged_in.id, user_input="Hi", bot_response="Hello!", mood="calm"))
        db.session.commit()
    res = client.get("/export/chat/pdf")
    assert res.status_code == 200
    assert "application/pdf" in res.content_type

# ---------------------------------------------------
# Export Routes - Mood Logs
# ---------------------------------------------------
def test_export_mood_json(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(MoodLog(user_id=test_user_logged_in.id, mood="calm"))
        db.session.commit()
    res = client.get("/export/mood/json")
    assert res.status_code == 200
    assert res.is_json
    assert b"calm" in res.data

def test_export_mood_csv(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(MoodLog(user_id=test_user_logged_in.id, mood="sad"))
        db.session.commit()
    res = client.get("/export/mood/csv")
    assert res.status_code == 200
    assert "text/csv" in res.content_type

def test_export_mood_pdf(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(MoodLog(user_id=test_user_logged_in.id, mood="angry"))
        db.session.commit()
    res = client.get("/export/mood/pdf")
    assert res.status_code == 200
    assert "application/pdf" in res.content_type

# ---------------------------------------------------
# Combined JSON Export
# ---------------------------------------------------
def test_export_combined_json(client, db, app, test_user_logged_in):
    with app.app_context():
        db.session.add(ChatLog(user_id=test_user_logged_in.id, user_input="Hi", bot_response="Hello!", mood="happy"))
        db.session.add(MoodLog(user_id=test_user_logged_in.id, mood="happy"))
        db.session.commit()
    res = client.get("/export/json")
    data = res.get_json()
    assert "chat_logs" in data
    assert "mood_logs" in data

# ---------------------------------------------------
# Contact Therapist View
# ---------------------------------------------------
def test_contact_therapist_view(client, test_user_logged_in):
    res = client.get("/contact_therapist")
    assert res.status_code == 200

# ---------------------------------------------------
# Trigger Internal Server Error (Optional Route)
# ---------------------------------------------------
def test_trigger_500(client):
    with pytest.raises(Exception):
        client.get("/trigger500")
