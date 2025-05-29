# model_loader.py

from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch

# Global cache (in RAM)
chatbot_tokenizer = None
chatbot_model = None
emotion_classifier = None

def load_models():
    global chatbot_tokenizer, chatbot_model, emotion_classifier

    # Load fine-tuned DialoGPT model
    if chatbot_model is None or chatbot_tokenizer is None:
        print("[INFO] Loading fine-tuned DialoGPT model into RAM...")
        model_path = r"C:\Users\Pasul\OneDrive\Documents\Desktop\mental_health_chatbot\chatbot_model_small"
        chatbot_tokenizer = AutoTokenizer.from_pretrained(model_path)
        chatbot_model = AutoModelForCausalLM.from_pretrained(model_path)
        chatbot_model.eval()
        print("[INFO] Fine-tuned DialoGPT model loaded.")

    # Load emotion classifier
    if emotion_classifier is None:
        print("[INFO] Loading emotion classifier into RAM...")
        emotion_classifier = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")
        print("[INFO] Emotion classifier loaded.")
