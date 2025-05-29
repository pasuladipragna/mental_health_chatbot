import unittest
from flask import Flask
from app import create_app
from app.database import db
from app.models import User
from config import TestingConfig

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app = create_app({"TESTING": True})
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client(use_cookies=True)  # ✅ Preserve cookies/session
        
        db.create_all()

        # Create a test user
        self.test_username = "testuser"
        self.test_email = "testuser@example.com"
        self.test_password = "Test@1234"
        user = User(username=self.test_username, email=self.test_email, password=self.test_password)
        db.session.add(user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    
    @staticmethod
    def create_test_user(username="testuser2", email="test2@example.com", password="testpass"):
        user = User(username=username, email=email, password=password)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    

    def register_and_login(self):
        """ Helper to register and login a user """
        client=  self.client
        # Register user
        client.post('/auth/register', data=dict(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password,
            confirm_password=self.test_password
        ), follow_redirects=True)

        # Login user
        response = client.post('/auth/auth/login', data=dict(
            username=self.test_username,
            password=self.test_password
        ), follow_redirects=True)

        self.assertIn(f"Welcome {self.test_username}".encode('utf-8'), response.data)

        #with client.session_transaction() as sess:
           # user = User.query.filter_by(username=self.test_username).first()
            #sess['user_id'] = str(user.id)
            #sess['username'] = user.username


class AuthTestCase(BaseTestCase):
    def test_register(self):
        response = self.client.post('/auth/register', data=dict(
            username="newuser",
            email="newuser@example.com",
            password="NewUser@123",
            confirm_password="NewUser@123"
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)

    def test_login(self):
        response = self.client.post('/auth/auth/login', data=dict(
            username=self.test_username,
            password=self.test_password
        ), follow_redirects=True)
        self.assertIn(f"Welcome {self.test_username}".encode('utf-8'), response.data)

    def test_forgot_password_page(self):
        response = self.client.get('/auth/forgot-password')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Forgot Password', response.data)


class ChatTestCase(BaseTestCase):
    def test_chat_flow(self):
        with self.client as client:
            email = "chatuser@example.com"
            existing = User.query.filter_by(email=email).first()
            if existing:
                db.session.delete(existing)
                db.session.commit()

            user = User(username="chatuser", email=email, password="testpass")
            db.session.add(user)
            db.session.commit()

            with client.session_transaction() as sess:
                sess['user_id'] = user.id

            # ✅ Log in the user properly
            with self.app.test_request_context():
                from flask_login import login_user
                login_user(user)

            response = client.post('/api/chat', json={"message": "I feel lonely"})
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn("response", data)
            self.assertIn("mood", data)


class ExportTestCase(BaseTestCase):
    def test_export_chat_logs_json(self):
        with self.app.app_context():
            self.register_and_login()
            response = self.client.get('/export/chat/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.mimetype, 'application/json')

    def test_export_chat_logs_csv(self):
        self.register_and_login()
        response = self.client.get('/export/chat/csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')

    def test_export_chat_logs_pdf(self):
        self.register_and_login()
        response = self.client.get('/export/chat/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')

    def test_export_mood_logs_json(self):
        self.register_and_login()
        response = self.client.get('/export/mood/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

    def test_export_mood_logs_csv(self):
        self.register_and_login()
        response = self.client.get('/export/mood/csv')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'text/csv')

    def test_export_mood_logs_pdf(self):
        self.register_and_login()
        response = self.client.get('/export/mood/pdf')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/pdf')


class MoodTrendsTestCase(BaseTestCase):
    def test_mood_trends_page(self):
        self.register_and_login()
        response = self.client.get('/mood-trends')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Mood Trends", response.data)  # Check if page loads with expected content

    def test_mood_trend_chart_data(self):
        self.register_and_login()
        response = self.client.get('/mood-trends/data')  # Adjust this if your route is different
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

        data = response.get_json()
        self.assertIsInstance(data, list)
        if data:  # Only check structure if data is present
            self.assertIn('date', data[0])
            self.assertIn('mood', data[0])


if __name__ == '__main__':
    unittest.main()
