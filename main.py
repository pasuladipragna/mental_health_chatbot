import os
import logging
import warnings
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_session import Session
from flask_cors import CORS
from dotenv import load_dotenv
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.routes import register_routes
from app.database import db
from app.models import User, ChatLog
from config import DevelopmentConfig, TestingConfig, ProductionConfig
from flask_login import LoginManager
from app import create_app
from app.scheduler import start_scheduler
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from model_loader import load_models



# LoginManager setup will be done inside create_app()

# Load user from user_id


warnings.filterwarnings("ignore", category=FutureWarning)
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'secret-key'  # REQUIRED for login sessions

    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Config based on FLASK_ENV
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        app.config.from_object(ProductionConfig)
    elif env == "testing":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Create session folder if not exists
    session_dir = Path(app.config['SESSION_FILE_DIR'])
    session_dir.mkdir(parents=True, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)

    Session(app)

    # Setup LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # or your login route
    login_manager.user_loader(load_user)

    # Enable CORS (restrict origins in prod)
    if env == "production":
        CORS(app, origins=["https://Mind-Ease.com"])
    else:
        CORS(app)

    # Setup logging
    if not app.debug and not app.testing:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(log_dir / "app.log", maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

    # Register blueprints
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

    return app


if __name__ == "__main__":
    app = create_app()
    load_models()
    start_scheduler()
    debug_mode = os.getenv("FLASK_ENV", "development") != "production"
    app.run(debug=debug_mode, host="0.0.0.0", port=5000, use_reloader=False)

