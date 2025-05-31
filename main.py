import os
import logging
import warnings
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_cors import CORS
from flask_login import LoginManager
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv
import torch
from app.routes import register_routes
from app.database import db
from app.models import User, ChatLog
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from app.scheduler import start_scheduler
from model_loader import load_models

# Ignore FutureWarnings from dependencies
warnings.filterwarnings("ignore", category=FutureWarning)

# Load .env environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

    # Determine environment and load corresponding config
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        app.config.from_object(ProductionConfig)
    elif env == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Create session directory if needed
    Path(app.config['SESSION_FILE_DIR']).mkdir(parents=True, exist_ok=True)

    # Initialize Flask extensions
    db.init_app(app)
    Migrate(app, db)
    Session(app)

    # Login manager setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Enable CORS (restrict in production)
    if env == "production":
        CORS(app, origins=["https://Mind-Ease.com"])
    else:
        CORS(app)

    # Setup file logging for production
    if not app.debug and not app.testing:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(log_dir / "app.log", maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    # Register routes (Blueprints)
    register_routes(app)

    # Register error handlers
    @app.errorhandler(404)
    def not_found(e):
        app.logger.warning(f"404 Not Found: {request.url}")
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error(f"500 Internal Server Error: {str(e)}", exc_info=True)
        return jsonify({"error": "Internal Server Error"}), 500

    # Setup Flask-Admin
    admin = Admin(app, name='Admin', template_mode='bootstrap3')
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(ChatLog, db.session))

    # Load models into memory and attach to app config
    chatbot_tokenizer, chatbot_model, emotion_classifier = load_models()
    app.config['chatbot_tokenizer'] = chatbot_tokenizer
    app.config['chatbot_model'] = chatbot_model
    app.config['emotion_classifier'] = emotion_classifier

    app.config['device'] = "cuda" if torch.cuda.is_available() else "cpu"

    return app


if __name__ == "__main__":
    app = create_app()
    start_scheduler()
    app.run(
        debug=os.getenv("FLASK_ENV", "development") != "production",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        use_reloader=False
    )
