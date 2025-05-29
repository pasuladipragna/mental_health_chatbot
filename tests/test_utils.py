import unittest
from unittest.mock import patch, MagicMock, mock_open
from flask import Response, json
from datetime import datetime
from app.utils import export_logs_as_json, export_logs_as_csv, export_logs_as_pdf, scrape_therapists
from app import create_app
from app.models import db, User, ChatLog
from werkzeug.security import generate_password_hash
import uuid

class DummyLog:
    def __init__(self, timestamp, user_input=None, bot_response=None, mood="neutral"):
        self.timestamp = timestamp
        self.user_input = user_input
        self.bot_response = bot_response
        self.mood = mood

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_input": self.user_input,
            "bot_response": self.bot_response,
            "mood": self.mood
        }

class UtilsTestCase(unittest.TestCase):

    
    def setUp(self):
        self.app = create_app()  # Ensure this loads a test config (e.g., sqlite)
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

            # Create unique test user
            self.username = f"testuser_{uuid.uuid4().hex[:6]}"
            self.password = "testpass"
            self.email = f"{self.username}@example.com"

            user = User(username=self.username, 
                        email=self.email, 
                        password=generate_password_hash(self.password))
            user.set_password(self.password)
            db.session.add(user)
            db.session.commit()

            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_export_logs_as_json(self):
        with self.app.app_context():
            # Create a dummy chat log
            log = ChatLog(
                user_id=self.user_id,
                user_input="Hello",
                bot_response="Hi there!",
                mood="happy"
            )
            db.session.add(log)
            db.session.commit()

        with self.client as client:
            # Simulate login
            login_response = client.post("/auth/auth/login", data={
                "username": self.username,
                "password": self.password
            }, follow_redirects=True)

            self.assertEqual(login_response.status_code, 200)

            with client.session_transaction() as sess:
                print("Session user_id =", sess.get("user_id"))

            # Call the protected route
            response = client.get("/export/json")
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"Hello", response.data)


    
    def test_export_logs_as_csv_empty(self):
        with self.app.test_request_context():
            response = export_logs_as_csv([])
            self.assertEqual(response.status_code, 200)
            self.assertIn("text/csv", response.mimetype)

    def test_export_logs_as_csv_chatlog(self):
        with self.app.test_request_context():
            logs = [DummyLog(datetime.utcnow(), "Hi", "Hello", "joy")]
            response = export_logs_as_csv(logs)
            self.assertEqual(response.status_code, 200)

    def test_export_logs_as_csv_moodlog(self):
        with self.app.test_request_context():
            logs = [DummyLog(datetime.utcnow(), mood="sadness")]
            logs[0].__dict__.pop("user_input", None)
            logs[0].__dict__.pop("bot_response", None)
            response = export_logs_as_csv(logs)
            self.assertEqual(response.status_code, 200)

    def test_export_logs_as_pdf_empty(self):
        with self.app.test_request_context():
            response = export_logs_as_pdf([], title="Test PDF")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "application/pdf")

    def test_export_logs_as_pdf_with_chatlogs(self):
        logs = [DummyLog(datetime.utcnow(), "Hi", "Hello", "joy")]
        with self.app.test_request_context():
            response = export_logs_as_pdf(logs, title="Chat Logs")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "application/pdf")

    def test_export_logs_as_pdf_with_moodlogs(self):
        logs = [DummyLog(datetime.utcnow(), mood="anger")]
        logs[0].__dict__.pop("user_input", None)
        logs[0].__dict__.pop("bot_response", None)
        with self.app.test_request_context():
            response = export_logs_as_pdf(logs, title="Mood Logs")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, "application/pdf")

    @patch("app.utils.requests.get")
    @patch("app.utils.open", new_callable=mock_open)
    @patch("app.utils.BeautifulSoup")
    def test_scrape_therapists(self, mock_bs, mock_open_file, mock_requests_get):
        mock_requests_get.return_value.text = "<html></html>"

        mock_doctor = MagicMock()
        mock_doctor.select_one.side_effect = lambda selector: {
            ".info-section h2": MagicMock(text="Dr. X"),
            ".uv2-spacer--xs": MagicMock(text="5 years"),
            ".clinic-name": MagicMock(text="ABC Clinic"),
            "a": MagicMock(**{"__getitem__.return_value": "/doctor/dr-x"})
        }.get(selector)

        mock_soup = MagicMock()
        mock_soup.select.return_value = [mock_doctor]
        mock_bs.return_value = mock_soup

        scrape_therapists()
        mock_open_file.assert_called_once()
        self.assertTrue(mock_requests_get.called)

    @patch("app.utils.requests.get", side_effect=Exception("Network error"))
    def test_scrape_therapists_network_error(self, mock_get):
        with self.assertRaises(Exception):
            scrape_therapists()

if __name__ == '__main__':
    unittest.main()
