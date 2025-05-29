from flask import Blueprint, request, jsonify, session, render_template, current_app
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer as EmotionTokenizer
import json, traceback, os
from pathlib import Path
from ..models import db, MoodLog, ChatLog
from .views import login_required
from app.database import db
from flask import current_app
from flask_login import current_user
from model_loader import load_models, chatbot_model, chatbot_tokenizer, emotion_classifier

chat_bp = Blueprint('chat_bp', __name__)


# Load chatbot model
model_path = os.getenv("CHATBOT_MODEL_PATH", r"C:\Users\Pasul\OneDrive\Documents\Desktop\mental_health_chatbot\chatbot_model_small")
model = AutoModelForCausalLM.from_pretrained(model_path)
tokenizer = AutoTokenizer.from_pretrained(model_path)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)

# Load emotion classifier
emotion_model_id = "j-hartmann/emotion-english-distilroberta-base"
emotion_tokenizer = EmotionTokenizer.from_pretrained(emotion_model_id)
emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_id)
emotion_classifier = pipeline("text-classification", model=emotion_model, tokenizer=emotion_tokenizer, top_k=1)

# Emojis and tips
mood_emojis = {
    'joy': '😊', 'sadness': '😢', 'anger': '😠', 'fear': '😨',
    'love': '❤️', 'surprise': '😲', 'neutral': '😐'
}
tips = {
    'joy': "Keep smiling and enjoy the moment!",
    'sadness': "It's okay to feel sad. Take deep breaths.",
    'anger': "Try calming down with a short walk or breathing exercise.",
    'fear': "You're safe now. Focus on the present.",
    'love': "Spread the love to those around you!",
    'surprise': "Take a moment to process things calmly.",
    'neutral': "How are you feeling really?"
}

@chat_bp.route("/api/chat", methods=["POST"])
#@login_required
def chat():
    load_models()  # Ensure models are loaded
    try:
        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "Empty message"}), 400
        if len(user_input) > 300:
            return jsonify({"error": "Message too long. Please limit to 300 characters."}), 400

        if "chat_history" not in session:
            session["chat_history"] = []

        chat_history = session["chat_history"][-10:]
        full_convo = ""
        for i, msg in enumerate(chat_history):
            speaker = "User" if i % 2 == 0 else "Bot"
            full_convo += f"{speaker}: {msg} {tokenizer.eos_token} "
        full_convo += f"User: {user_input} {tokenizer.eos_token}"

        inputs = tokenizer(full_convo, return_tensors='pt', padding=True, truncation=True)
        input_ids = inputs['input_ids'].to(device)
        attention_mask = inputs['attention_mask'].to(device)

        output_ids = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=1000,
            pad_token_id=tokenizer.eos_token_id
        )

        raw_output = tokenizer.decode(output_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
        cleaned_output = raw_output[len(user_input):].strip() if raw_output.lower().startswith(user_input.lower()) else raw_output.strip()
        if not cleaned_output or len(cleaned_output.split()) < 3:
            cleaned_output = "Thanks for sharing that. I'm here to listen—want to talk more about it?"

        bot_output = cleaned_output

        try:
            emotion_result = emotion_classifier(user_input)[0]
            mood = emotion_result['label'].lower()
        except Exception:
            mood = 'neutral'

        emoji_icon = mood_emojis.get(mood, '😐')
        tip = tips.get(mood, '')
        if tip and tip not in bot_output:
            bot_output += f" {emoji_icon} {tip}"

        session["chat_history"] = (session.get("chat_history", []) + [user_input, bot_output])[-10:]
        session['last_detected_mood'] = mood
        session.modified = True

        # ✅ Save logs to DB using current_user.id
        user_id = current_user.id
        chat_log = ChatLog(user_id=user_id, user_input=user_input, bot_response=bot_output, mood=mood)
        db.session.add(chat_log)
        mood_log = MoodLog(user_id=user_id, mood=mood)
        db.session.add(mood_log)
        db.session.commit()

        return jsonify({
            "response": bot_output,
            "mood": mood,
            "emoji": emoji_icon,
            "tip": tip
        })

    except Exception:
        current_app.logger.error("[CHAT ERROR] %s", traceback.format_exc())
        return jsonify({"error": "Internal server error."}), 500

@chat_bp.route('/reset_chat', methods=['POST'])
@login_required
def reset_chat():
    try:
        session.pop('chat_history', None)
        session.pop('mood_log', None)
        session.modified = True
        return jsonify({"status": "reset", "message": "Chat session cleared."}), 200
    except Exception:
        return jsonify({"error": "Failed to reset chat"}), 500

@chat_bp.route("/contact_therapist")
@login_required
def contact_therapist():
    therapists = []
    try:
        path = Path("data/therapists.json")
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                therapists = json.load(f)
    except Exception as e:
        therapists = []

    return render_template("contact_therapist.html", therapists=therapists)

def start_therapist_scheduler():
    # Placeholder for background job initialization
    pass

start_therapist_scheduler()

print("[INFO] Chatbot and emotion classifier loaded successfully on", device)
