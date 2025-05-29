import unittest
from unittest.mock import patch, MagicMock
from app import create_app, chatbot
from app.models import db, User

class ChatbotTests(unittest.TestCase):

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            user = User(username="testuser", email="test@example.com", password="hashed")
            db.session.add(user)
            db.session.commit()
            self.user_id = user.id

    def tearDown(self):
        with self.app.app_context():
            db.drop_all()

    @patch("app.chatbot.chatbot_model.generate")
    @patch("app.chatbot.chatbot_tokenizer")
    def test_get_bot_response_success(self, mock_tokenizer, mock_generate):
        # Mock tokenizer
        mock_tokenizer.eos_token = ""
        mock_tokenizer.return_value = {"input_ids": MagicMock(shape=(1, 10)), "attention_mask": MagicMock()}
        mock_tokenizer.decode.return_value = "Sure, I'm here for you."
        
        # Mock model generate
        mock_tensor = MagicMock()
        mock_tensor.__getitem__.return_value = [101, 102, 103]
        mock_generate.return_value = mock_tensor


        with patch("app.chatbot.session", {"chat_history": [
            {"sender": "user", "message": "Hi"},
            {"sender": "bot", "message": "Hello"},
        ]}):
            response, mood = chatbot.get_bot_response("I feel down", user_id=1)
            self.assertIsInstance(response, str)
            self.assertIn(response, "Sure, I'm here for you.")
            self.assertIsInstance(mood, str)

    @patch("app.chatbot.chatbot_model.generate", side_effect=Exception("Error"))
    @patch("app.chatbot.chatbot_tokenizer")
    def test_get_bot_response_failure(self, mock_tokenizer, mock_generate):
        mock_tokenizer.eos_token = ""
        mock_tokenizer.return_value = {"input_ids": MagicMock(shape=(1, 10)), "attention_mask": MagicMock()}
        mock_tokenizer.decode.return_value = ""

        with patch("app.chatbot.session", {"chat_history": []}):
            response, mood = chatbot.get_bot_response("Tell me something", user_id=1)
            self.assertIn("trouble", response)
            self.assertIsInstance(mood, str)

    @patch("app.chatbot.emotion_model")
    @patch("app.chatbot.emotion_tokenizer")
    def test_detect_mood(self, mock_tokenizer, mock_model):
        mock_tokenizer.return_value = {"input_ids": MagicMock()}
        mock_logits = MagicMock()
        mock_logits.logits = MagicMock()
        mock_logits.logits.__getitem__.return_value = [0.1] * len(chatbot.emotion_labels)
        mock_model.return_value = mock_logits
        mock_argmax = MagicMock()
        mock_argmax.item.return_value = 5
        with patch("torch.argmax", return_value=mock_argmax):
            mood = chatbot.detect_mood("I'm feeling down")
            self.assertIn(mood, chatbot.emotion_labels)

