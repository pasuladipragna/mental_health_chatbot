from transformers import AutoModelForCausalLM, AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from flask import session

# === Load Fine-tuned Chatbot Model ===
chatbot_model_path = r"C:\\Users\\Pasul\\OneDrive\\Documents\\Desktop\\mental_health_chatbot\\chatbot_model_small"
chatbot_tokenizer = AutoTokenizer.from_pretrained(chatbot_model_path)
chatbot_tokenizer.pad_token = chatbot_tokenizer.eos_token
chatbot_tokenizer.padding_side = "left"
chatbot_tokenizer.truncation_side = "left"  # optional but good for long inputs
print("Padding side:", chatbot_tokenizer.padding_side)
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

    # Only include the last 3–5 pairs to keep prompt short and coherent
    formatted_chat = ""
    for msg in chat_history[-5:]:
        role = msg.get("sender")
        text = msg.get("message").replace("\n", " ").strip()
        formatted_chat += f"{'User' if role == 'user' else 'Bot'}: {text} {chatbot_tokenizer.eos_token} "

    # Append current user input
    formatted_chat += f"User: {user_input} {chatbot_tokenizer.eos_token}"

    # 🔒 Make sure padding/truncation is still enforced here
    chatbot_tokenizer.padding_side = "left"
    chatbot_tokenizer.truncation_side = "left"

    # ⏱ Proper tokenization with padding & truncation
    inputs = chatbot_tokenizer(
        formatted_chat,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=1000
    ).to(chatbot_model.device)

    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    try:
        output_ids = chatbot_model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_length=min(1024, input_ids.shape[1] + 80),  # keep output short
            pad_token_id=chatbot_tokenizer.eos_token_id,
            do_sample=True,
            top_k=50,
            top_p=0.9,
            temperature=0.7,
            repetition_penalty=1.2,
            no_repeat_ngram_size=3,  # stronger control over repetition
        )

        # Only decode the generated part
        response_ids = output_ids[:, input_ids.shape[1]:]
        bot_response = chatbot_tokenizer.decode(response_ids[0], skip_special_tokens=True).strip()

        #  Post-process to avoid repetition artifacts
        bot_response = ' '.join(dict.fromkeys(bot_response.split()))  # Removes duplicate words

        #  Optionally clip very long responses
        if len(bot_response.split()) > 60:
            bot_response = ' '.join(bot_response.split()[:60]) + '...'

    except Exception as e:
        print(f"[!] Error generating bot response: {e}")
        bot_response = "Sorry, I had trouble understanding. Could you rephrase?"

    #  Mood detection
    detected_mood = detect_mood(user_input)
    return bot_response, detected_mood
