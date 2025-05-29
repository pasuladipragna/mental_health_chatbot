import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret")
    # Add to Config class
    SECURITY_PASSWORD_HASH = "pbkdf2_sha256"
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "my_precious_salt")



    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI", "sqlite:///chatbot.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_TYPE = "filesystem"  # or "redis" for production
    SESSION_FILE_DIR = os.path.join(os.getcwd(), "flask_session")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True  # Adds extra protection
    SESSION_KEY_PREFIX = "session:"
    SESSION_FILE_THRESHOLD = 200  # Optional: max number of sessions before cleanup

    # CSRF (enabled in prod, disabled in test)
    WTF_CSRF_ENABLED = True

    # Chatbot Model
    MODEL_PATH = os.getenv("MODEL_PATH", "./chatbot_model_small")

    # Hugging Face Token (if using private models)
    HF_TOKEN = os.getenv("HF_TOKEN", "")

    # Flask behavior
    DEBUG = False
    TESTING = False

    LOG_DIR = os.getenv("LOG_DIR", "logs")



class DevelopmentConfig(Config):
    DEBUG = True
    WTF_CSRF_ENABLED = False  # Disable only for dev testing


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SESSION_TYPE = "filesystem"
    SESSION_FILE_DIR = os.path.join(os.getcwd(), "test_sessions")


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True
    SESSION_TYPE = "redis"  # if Redis is used in production
    SESSION_PERMANENT = True
