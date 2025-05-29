from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from flask import session

# === Load Fine-tuned Chatbot Model ===
chatbot_model_path = r"C:\\Users\\Pasul\\OneDrive\\Documents\\Desktop\\mental_health_chatbot\\chatbot_model_small"
chatbot_tokenizer = AutoTokenizer.from_pretrained(chatbot_model_path)
chatbot_tokenizer.padding_side = "left"
chatbot_tokenizer.pad_token = chatbot_tokenizer.eos_token
chatbot_model = AutoModelForCausalLM.from_pretrained(chatbot_model_path, trust_remote_code=True, local_files_only=True)

device = torch.device("cpu")  # Use "cuda" if available
chatbot_model.to(device)
chatbot_model.eval()

# === Load Emotion Classifier ===
emotion_model_name = "j-hartmann/emotion-english-distilroberta-base"
emotion_tokenizer = AutoTokenizer.from_pretrained(emotion_model_name)
emotion_model = AutoModelForSequenceClassification.from_pretrained(emotion_model_name)

emotion_labels = ['admiration', 'amusement', 'anger', 'annoyance', 'approval', 'caring',
                  'confusion', 'curiosity', 'desire', 'disappointment', 'disapproval', 'disgust',
                  'embarrassment', 'excitement', 'fear', 'gratitude', 'grief', 'joy', 'love',
                  'nervousness', 'optimism', 'pride', 'realization', 'relief', 'remorse',
                  'sadness', 'surprise', 'neutral']

mood_support = {
    "joy": "😊 Stay positive and share your happiness with others!",
    "sadness": "😢 It's okay to feel sad. Talking to a friend or journaling might help.",
    "anger": "😠 Try deep breathing or a short walk to cool down.",
    "fear": "😨 You’re not alone. Consider grounding techniques or talking to someone you trust.",
    "surprise": "😮 Unexpected things happen. Stay calm and adapt.",
    "disgust": "🤢 Try to shift your focus to something more positive.",
    "neutral": "🙂 Keep going! Maintaining a balanced mindset is healthy."
}

def detect_mood(user_input):
    inputs = emotion_tokenizer(user_input, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = emotion_model(**inputs).logits
    probs = F.softmax(logits, dim=1)
    top_idx = torch.argmax(probs, dim=1).item()
    return emotion_labels[top_idx]

def get_bot_response(user_input, user_id=None):
    chat_history = session.get("chat_history", [])
    formatted_chat = ""

    for msg in chat_history[-5:]:
        role = msg.get("sender")
        text = msg.get("message")
        formatted_chat += f"{'User' if role == 'user' else 'Bot'}: {text}{chatbot_tokenizer.eos_token}"

    formatted_chat += f"User: {user_input}{chatbot_tokenizer.eos_token}"

    inputs = chatbot_tokenizer(
        formatted_chat,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=1024
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    try:
        output_ids = chatbot_model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,  # ✅ FIXED
            max_length=min(1024, input_ids.shape[1] + 100),
            pad_token_id=chatbot_tokenizer.eos_token_id,
            do_sample=True,
            top_k=50,
            top_p=0.92,
            temperature=0.7,
            repetition_penalty=1.3,
            no_repeat_ngram_size=2,  # ✅ Prevents repeated short phrases
        )
        response_ids = output_ids[:, input_ids.shape[1]:]
        bot_response = chatbot_tokenizer.decode(response_ids[0], skip_special_tokens=True).strip()
        if len(bot_response.split()) > 50:
            bot_response = ' '.join(bot_response.split()[:50]) + '...'

        
    except Exception as e:
        print(f"[!] Error generating bot response: {e}")
        bot_response = "Sorry, I had trouble understanding. Could you rephrase?"

    detected_mood = detect_mood(user_input)
    return bot_response, detected_mood
