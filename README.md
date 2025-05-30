# 🧠 Mind-Ease: Mental Health Chatbot

A web-based mental health chatbot powered by a fine-tuned DialoGPT model and emotion classification. Users can chat with the bot, track moods, and visualize trends.

## Features
- Fine-tuned chatbot (DialoGPT)
- Emotion classification (DistilRoBERTa)
- Mood tracking and visualization (Chart.js)
- Session-based chat history
- Export chats as CSV, JSON, PDF
- User authentication

## How to Run
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env

# Run app
python app.py
