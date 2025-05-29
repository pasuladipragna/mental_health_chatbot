from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.database import db
from sqlalchemy import func


# ---------------------------------------------------
# User Model
# ---------------------------------------------------

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)

    chat_logs = db.relationship('ChatLog', backref='user', lazy=True, cascade="all, delete-orphan")
    mood_logs = db.relationship('MoodLog', backref='user', lazy=True, cascade="all, delete-orphan")
    
    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.set_password(password)  # hash password securely

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_recent_moods(self, limit=10):
        return MoodLog.query.filter_by(user_id=self.id).order_by(MoodLog.timestamp.desc()).limit(limit).all()

    def get_mood_counts(self):
        return (
            db.session.query(MoodLog.mood, func.count(MoodLog.mood))
            .filter_by(user_id=self.id)
            .group_by(MoodLog.mood)
            .all()
        )

    def __repr__(self):
        return f"<User {self.username}>"

    def __str__(self):
        return self.__repr__()
    
    def get_id(self):
        return str(self.id)  # 🔥 Ensure it's always a string

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email
        }

# ---------------------------------------------------
# ChatLog Model
# ---------------------------------------------------
class ChatLog(db.Model):
    __tablename__ = 'chat_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_input = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    mood = db.Column(db.String(50))
    mood_score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)


    def __init__(self, user_id, user_input, bot_response, mood):
        self.user_id = user_id
        self.user_input = user_input
        self.bot_response = bot_response
        self.mood = mood

    def __repr__(self):
        return f"<ChatLog {self.id} | User {self.user_id}>"

    def __str__(self):
        return self.__repr__()

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "user_input": self.user_input,
            "bot_response": self.bot_response,
            "mood": self.mood
        }


# ---------------------------------------------------
# MoodLog Model
# ---------------------------------------------------
class MoodLog(db.Model):
    __tablename__ = 'mood_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mood = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)


    def __init__(self, user_id, mood):
        self.user_id = user_id
        self.mood = mood

    def __repr__(self):
        return f"<MoodLog {self.id} | User {self.user_id} | Mood: {self.mood}>"

    def __str__(self):
        return self.__repr__()

    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "mood": self.mood
        }
