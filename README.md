# 🧠 Mind-Ease: Mental Health Chatbot

A web-based mental health chatbot powered by a fine-tuned DialoGPT model and emotion classification. Users can chat with the bot, track moods, and visualize trends.

MindEase is an AI-powered mental health chatbot that supports emotionally intelligent conversations, detects user mood in real time, suggests empathetic replies, tracks emotional trends, and allows users to export their chat history. Built using Flask, Hugging Face Transformers, and a fine-tuned DialoGPT model, it provides a safe space for mental wellness.

---

## 💡 Features

- 🗣️ **AI chatbot** fine-tuned on mental health-related dialogue using DialoGPT
- 🧠 **Emotion detection** using `j-hartmann/emotion-english-distilroberta-base`
- 🧾 **Session-based chat history** with mood labeling
- 📈 **Mood trend visualization** via Chart.js
- 📤 **Chat history export** in JSON, CSV, or PDF
- 🧠 **Suggested replies** based on user emotion
- 🔐 **Authentication** (login/register/forgot password)
- 🛠 **Admin panel** using Flask-Admin

---

## 🚀 Getting Started

### 🔁 Clone the Repo
```bash
git clone https://github.com/yourusername/mental_health_chatbot.git
cd mental_health_chatbot
````

### 🧪 Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate    # Windows
source venv/bin/activate # macOS/Linux
```

### 📦 Install Requirements

```bash
pip install -r requirements.txt
```

### 🔐 Create a `.env` File

```ini
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URI=sqlite:///chatbot.db
CHATBOT_MODEL_PATH=C:\\Users\\Pasul\\OneDrive\\Documents\\Desktop\\mental_health_chatbot\\chatbot_model_small
```

### 🔄 Initialize Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### ▶ Run the App

```bash
python main.py
```

Access at: [http://localhost:5000](http://localhost:5000)

---

## 📈 Mood Trend Chart

Track your emotional history with a dynamic line chart at `/mood_trends`.
Logged moods are stored per session and visualized using Chart.js.

---

## 📤 Export Chat Logs

Easily export conversations for review or sharing:

* `/export_chat/json` → JSON file
* `/export_chat/csv` → CSV spreadsheet
* `/export_chat/pdf` → Printable PDF

---

## 🧠 Suggested Replies

Based on your detected mood, the chatbot offers helpful, emotionally aligned responses like:

* **Sadness**: "Do you want to talk about it?"
* **Joy**: "That's wonderful! What made you happy?"
* **Anger**: "Want to vent? I'm here."
* **Neutral**: "Tell me more. I'm listening."

---

## 🧠 NLP Models Used

* **Chatbot**: Fine-tuned [DialoGPT-medium](https://huggingface.co/microsoft/DialoGPT-medium)
* **Emotion Classifier**: [j-hartmann/emotion-english-distilroberta-base](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base)

---

## 🛠 Tech Stack

| Layer       | Tech                                    |
| ----------- | --------------------------------------- |
| Backend     | Flask, SQLAlchemy, Flask-Login          |
| Frontend    | HTML, JS, Chart.js, Tailwind (optional) |
| Models      | Transformers (Hugging Face), PyTorch    |
| Admin Panel | Flask-Admin                             |
| Export      | CSV, JSON, FPDF for PDF                 |
| Auth        | Flask-Login, hashed passwords           |

---

## ⚠ Known Warnings

> `A decoder-only architecture is being used, but right-padding was detected!`

This is a **non-blocking warning** from the Hugging Face Transformers library.
Although `padding_side='left'` is correctly set, the message may still appear due to internal tokenizer behavior. It does **not affect app functionality**.

---

## 📸 Screenshots :

Create a `screenshots/` folder and add these if you'd like:

* `chat_ui.png`: Main chat interface
* `mood_chart.png`: Mood trends chart
* `export_options.png`: Export buttons or modal

Then embed:

```markdown
![Chat Interface](screenshots/chat_ui.png)
![Mood Trends](screenshots/mood_chart.png)
```

---

## 🤝 Contributing

Pull requests are welcome! For major changes, open an issue first to discuss what you’d like to improve.

---

## 📜 License

MIT License © 2025 \[Pasuladi Pragna]



