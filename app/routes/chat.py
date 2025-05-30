from flask import Blueprint, request, jsonify, session, render_template, current_app
from flask_login import current_user, login_required
from pathlib import Path
from ..models import db, MoodLog, ChatLog
import traceback, json

chat_bp = Blueprint('chat_bp', __name__)

# Mood emojis and tips
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
@login_required
def chat():
    try:
        tokenizer = current_app.config["chatbot_tokenizer"]
        model = current_app.config["chatbot_model"]
        emotion_classifier = current_app.config["emotion_classifier"]
        device = current_app.config["device"]

        user_input = request.json.get("message", "").strip()
        if not user_input:
            return jsonify({"error": "Empty message"}), 400
        if len(user_input) > 300:
            return jsonify({"error": "Message too long. Please limit to 300 characters."}), 400

        # Load session history
        if "chat_history" not in session:
            session["chat_history"] = []
        chat_history = session["chat_history"][-10:]

        # Build prompt
        full_convo = ""
        for i, msg in enumerate(chat_history):
            speaker = "User" if i % 2 == 0 else "Bot"
            full_convo += f"{speaker}: {msg} {tokenizer.eos_token} "
        full_convo += f"User: {user_input} {tokenizer.eos_token}"

        # Tokenize and generate
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

        # Detect mood
        try:
            emotion_result = emotion_classifier(user_input)[0]
            mood = emotion_result['label'].lower()
        except Exception:
            mood = 'neutral'

        emoji_icon = mood_emojis.get(mood, '😐')
        tip = tips.get(mood, '')
        if tip and tip not in bot_output:
            bot_output += f" {emoji_icon} {tip}"

        # Update session
        session["chat_history"] = (session.get("chat_history", []) + [user_input, bot_output])[-10:]
        session["last_detected_mood"] = mood
        session.modified = True

        # Save logs
        user_id = current_user.id
        db.session.add(ChatLog(user_id=user_id, user_input=user_input, bot_response=bot_output, mood=mood))
        db.session.add(MoodLog(user_id=user_id, mood=mood))
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


@chat_bp.route("/reset_chat", methods=["POST"])
@login_required
def reset_chat():
    try:
        session.pop("chat_history", None)
        session.pop("mood_log", None)
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
    except Exception:
        therapists = []
    return render_template("contact_therapist.html", therapists=therapists)
