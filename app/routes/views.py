from flask import Blueprint, render_template, redirect, url_for, jsonify, send_file, make_response, session, current_app
from flask_login import current_user, login_required
from ..models import MoodLog, ChatLog
from app.database import db
import io
import csv
from fpdf import FPDF
from app.utils import export_logs_as_json
import os
import requests
import json
from pathlib import Path
from sqlalchemy import func
import psutil

views_bp = Blueprint("views", __name__)

# ---------------------------------------------
# Home Route
# ---------------------------------------------
@views_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("views.dashboard"))
    return redirect(url_for("auth.login"))

# ---------------------------------------------
# Dashboard
# ---------------------------------------------
@views_bp.route("/dashboard")
@login_required
def dashboard():
    user_id = session.get("user_id")

    recent_logs = ChatLog.query.filter_by(user_id=user_id).order_by(ChatLog.timestamp.desc()).limit(50).all()

    try:
        weekly_mood = db.session.query(
            func.strftime('%Y-%W', ChatLog.timestamp),
            func.avg(ChatLog.mood_score) 
        ).filter(
            ChatLog.user_id == user_id,
            ChatLog.mood_score != None
        ).group_by(func.strftime('%Y-%W', ChatLog.timestamp)).all()
    except Exception as e:
        print(f"Error in mood trend query: {e}")
        weekly_mood = []

    memory = psutil.virtual_memory()
    print(f"Memory used: {memory.percent}%")

    return render_template("index.html", logs=recent_logs, mood_trend=weekly_mood)
# ---------------------------------------------
# Mood Trends Page (Chart)
# ---------------------------------------------
@views_bp.route("/mood-trends", methods=["GET"])
@login_required
def mood_trends():
    return render_template("mood_trends.html")  # Just render the page


@views_bp.route("/mood-trends/data")
@login_required
def mood_trends_data():
    mood_data = MoodLog.query.filter_by(user_id=current_user.id).all()
    data = [{"date": log.timestamp.strftime('%Y-%m-%d'), "mood": log.mood} for log in mood_data]
    return jsonify(data)

# ---------------------------------------------
# Chat History Viewer
# ---------------------------------------------
@views_bp.route("/chat-history")
@login_required
def chat_history():
    history = ChatLog.query.filter_by(user_id=current_user.id).order_by(ChatLog.timestamp.desc()).all()
    return render_template("chat_history.html", history=history, username=current_user.username)

# ---------------------------------------------
# Export Chat Logs - JSON
# ---------------------------------------------
@views_bp.route("/export/chat/json")
@login_required
def export_chat_json():
    chats = ChatLog.query.filter_by(user_id=current_user.id).order_by(ChatLog.timestamp).all()
    data = [{
        "timestamp": c.timestamp.strftime("%Y-%m-%d %H:%M"),
        "user_message": c.user_message,
        "bot_response": c.bot_response
    } for c in chats]
    return jsonify(data)

# ---------------------------------------------
# Export Chat Logs - CSV
# ---------------------------------------------
@views_bp.route("/export/chat/csv")
@login_required
def export_chat_csv():
    chats = ChatLog.query.filter_by(user_id=current_user.id).order_by(ChatLog.timestamp).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "User Message", "Bot Response"])
    for chat in chats:
        writer.writerow([
            chat.timestamp.strftime("%Y-%m-%d %H:%M"),
            chat.user_message,
            chat.bot_response
        ])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=chat_logs.csv"
    response.headers["Content-type"] = "text/csv"
    return response

# ---------------------------------------------
# Export Chat Logs - PDF
# ---------------------------------------------
@views_bp.route("/export/chat/pdf")
@login_required
def export_chat_pdf():
    chats = ChatLog.query.filter_by(user_id=current_user.id).order_by(ChatLog.timestamp).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Chat Logs", ln=True, align='C')

    for chat in chats:
        pdf.multi_cell(0, 10, f"{chat.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\nUser: {chat.user_message}\nBot: {chat.bot_response}\n")

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=chat_logs.pdf"
    return response

# ---------------------------------------------
# Export Mood Logs - JSON
# ---------------------------------------------
@views_bp.route("/export/mood/json")
@login_required
def export_mood_json():
    moods = MoodLog.query.filter_by(user_id=current_user.id).order_by(MoodLog.timestamp).all()
    data = [{"timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M"), "mood": m.mood} for m in moods]
    return jsonify(data)

# ---------------------------------------------
# Export Mood Logs - CSV
# ---------------------------------------------
@views_bp.route("/export/mood/csv")
@login_required
def export_mood_csv():
    moods = MoodLog.query.filter_by(user_id=current_user.id).order_by(MoodLog.timestamp).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Timestamp", "Mood"])
    for mood in moods:
        writer.writerow([mood.timestamp.strftime("%Y-%m-%d %H:%M"), mood.mood])

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=mood_logs.csv"
    response.headers["Content-type"] = "text/csv"
    return response

# ---------------------------------------------
# Export Mood Logs - PDF
# ---------------------------------------------
@views_bp.route("/export/mood/pdf")
@login_required
def export_mood_pdf():
    moods = MoodLog.query.filter_by(user_id=current_user.id).order_by(MoodLog.timestamp).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Mood Logs", ln=True, align='C')

    for mood in moods:
        pdf.cell(0, 10, txt=f"{mood.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - Mood: {mood.mood}", ln=True)

    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=mood_logs.pdf"
    return response

# ---------------------------------------------
# Export All Logs (General JSON)
# ---------------------------------------------
@views_bp.route("/export/json")
@login_required
def export_json_route():
    return export_logs_as_json()

# ---------------------------------------------
# Contact Therapist Page
# ---------------------------------------------
@views_bp.route("/contact_therapist")
@login_required
def contact_therapist():
    therapists = []
    try:
        path = Path("data/therapists.json")
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                therapists = json.load(f)
    except Exception as e:
        current_app.logger.error(f"Error reading therapists.json: {e}")

    return render_template("contact_therapist.html", therapists=therapists)


def fetch_therapists(location="Hyderabad", radius=5000, keyword="therapist", filename="data/therapists.json"):
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise Exception("Google Places API key not found in environment variables")

    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        "query": f"{keyword} in {location}",
        "radius": radius,
        "key": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code != 200 or "results" not in data:
        raise Exception("Failed to fetch data from Google Places API")

    results = []
    for place in data["results"]:
        results.append({
            "name": place.get("name"),
            "address": place.get("formatted_address"),
            "rating": place.get("rating"),
            "user_ratings_total": place.get("user_ratings_total"),
            "link": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id')}"
        })

    # Save to JSON file
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"[INFO] Fetched and saved {len(results)} therapists to {filename}")

# ---------------------------------------------
# Trigger 500 Error (For Testing)
# ---------------------------------------------
@views_bp.route("/trigger500")
def trigger_500():
    raise Exception("This is a test 500 error")
