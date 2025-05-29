# app/__init__.py
import os
from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from dotenv import load_dotenv
from config import Config
from .models import  User
from app.routes import register_routes
from flask_login import LoginManager
from app.database import db



login_manager = LoginManager()

# Load environment variables from .env file
load_dotenv()

# ---------------------------------------------
# Application FactorySRF in testing
def create_app(test_config=None):
    app = Flask(__name__, template_folder='../templates', instance_relative_config=False)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Load configuration
    if test_config:
        if isinstance(test_config, dict):
            app.config.update(test_config)
        else:
            app.config.from_object(test_config)  # ✅ handles class-based config
    else:
        app.config.from_object(Config)

    # Fallback defaults
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "super-secret-key"))
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", os.getenv("DATABASE_URI", "sqlite:///chatbot.db"))
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SESSION_TYPE", "filesystem")
    app.config.setdefault("SESSION_FILE_DIR", os.path.join(os.getcwd(), "flask_session"))
    app.config.setdefault("SESSION_PERMANENT", False)

    if app.config.get("TESTING"):
        app.config["WTF_CSRF_ENABLED"] = False

    # --------------- ADD THIS BLOCK ----------------
    if app.config.get("TESTING"):
        # Override the unauthorized handler to return 401 instead of redirecting (302)
        @login_manager.unauthorized_handler
        def unauthorized_callback():
            return {"error": "Unauthorized"}, 401
    # ------------------------------------------------

    db.init_app(app)
    Migrate(app, db)
    Session(app)

    with app.app_context():
        db.create_all()
        register_routes(app)
        register_error_handlers(app)

    if app.config.get("TESTING"):
        @app.route('/trigger500')
        def trigger_500():
            raise Exception("Triggering a 500 error for testing.")

    return app


# ---------------------------------------------
# Error Handlers
# ---------------------------------------------
def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found_error(error):
        return "<h1>404 Not Found</h1><p>The page you requested does not exist.</p>", 404

    @app.errorhandler(500)
    def internal_error(error):
        return "<h1>500 Internal Server Error</h1><p>An unexpected error occurred.</p>", 500
    
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


