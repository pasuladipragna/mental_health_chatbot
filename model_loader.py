from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Global cache (in RAM)
chatbot_tokenizer = None
chatbot_model = None
emotion_classifier = None

def load_models():
    global chatbot_tokenizer, chatbot_model, emotion_classifier

    # Load fine-tuned DialoGPT model (chatbot)
    if chatbot_model is None or chatbot_tokenizer is None:
        print("[INFO] Loading fine-tuned DialoGPT model into RAM...")
        model_path = r"C:\Users\Pasul\OneDrive\Documents\Desktop\mental_health_chatbot\chatbot_model_small"
        chatbot_tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, force_download=True)
        chatbot_tokenizer.padding_side = "left"  # ✅ Prevents right-padding warning
        chatbot_model = AutoModelForCausalLM.from_pretrained(model_path)
        chatbot_model.eval()
        print("[INFO] Fine-tuned DialoGPT model loaded.")

    # Load emotion classifier (DistilRoBERTa)
    if emotion_classifier is None:
        print("[INFO] Loading emotion classifier into RAM...")
        emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=False,
            top_k=1,
            truncation=True
        )
        print("[INFO] Emotion classifier loaded.")

    return chatbot_tokenizer, chatbot_model, emotion_classifier
