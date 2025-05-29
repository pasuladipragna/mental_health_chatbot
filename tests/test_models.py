import unittest
from app import create_app
from app.models import db, User, ChatLog, MoodLog

class ModelTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///:memory:"
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    def test_user_model(self):
        with self.app.app_context():
            user = User(username="testuser", email="test@example.com", password="testpass")
            #user.set_password("testpass")
            db.session.add(user)
            db.session.commit()

            fetched = User.query.filter_by(username="testuser").first()
            self.assertEqual(fetched.email, "test@example.com")
            self.assertIn("testuser", repr(fetched))
            self.assertEqual(fetched.to_dict()["username"], "testuser")
            self.assertTrue(fetched.verify_password("testpass"))
            self.assertFalse(fetched.verify_password("wrongpass"))

    def test_chatlog_model(self):
        with self.app.app_context():
            user = User(username="chatuser", email="chat@example.com", password="chatpass")
            db.session.add(user)
            db.session.commit()

            chat = ChatLog(user_id=user.id, user_input="Hi", bot_response="Hello", mood="joy")
            db.session.add(chat)
            db.session.commit()

            fetched = ChatLog.query.first()
            self.assertEqual(fetched.user_input, "Hi")
            self.assertIn("User", repr(fetched))
            self.assertIn("bot_response", fetched.to_dict())

    def test_moodlog_model(self):
        with self.app.app_context():
            user = User(username="mooduser", email="mood@example.com", password="moodpass")
            db.session.add(user)
            db.session.commit()

            mood = MoodLog(user_id=user.id, mood="sadness")
            db.session.add(mood)
            db.session.commit()

            fetched = MoodLog.query.first()
            self.assertEqual(fetched.mood, "sadness")
            self.assertIn("Mood", repr(fetched))
            self.assertIn("timestamp", fetched.to_dict())

if __name__ == '__main__':
    unittest.main()
