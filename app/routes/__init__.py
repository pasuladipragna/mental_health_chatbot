from flask import Blueprint
from app.routes.auth import auth_bp
from app.routes.chat import chat_bp
from app.routes.views import views_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(chat_bp)
    app.register_blueprint(views_bp, url_prefix='/')