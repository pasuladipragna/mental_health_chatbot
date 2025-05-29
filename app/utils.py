import io
import csv
from fpdf import FPDF
from flask import send_file, Response
from datetime import datetime
# therapist_scraper.py
import requests
from bs4 import BeautifulSoup
import json
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from flask import jsonify, session
from app.models import ChatLog

def scrape_therapists():
    url = "https://www.practo.com/hyderabad/psychologist"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    therapists = []
    for doc in soup.select(".doctor-card")[:3]:
        name = doc.select_one(".info-section h2").text.strip()
        experience = doc.select_one(".uv2-spacer--xs").text.strip()
        clinic = doc.select_one(".clinic-name").text.strip() if doc.select_one(".clinic-name") else "N/A"
        link = "https://www.practo.com" + doc.select_one("a")["href"]

        therapists.append({
            "name": name,
            "experience": experience,
            "clinic": clinic,
            "link": link
        })

    with open("static/data/therapists.json", "w") as f:
        json.dump(therapists, f, indent=4)
    print(f"[{datetime.now()}] Therapist data updated.")

def start_therapist_scheduler():
    scheduler = BackgroundScheduler()
    
    # Update every 30 days (you can change days=15 if needed)
    scheduler.add_job(scrape_therapists, 'interval', days=30, next_run_time=datetime.now())
    
    scheduler.start()
    print("Therapist update scheduler started.")

# Schedule to run every 15 days
if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_therapists, 'interval', days=15)
    scheduler.start()
    scrape_therapists()


# ---------------------------------------------
# Export Logs as JSON
# ---------------------------------------------
# app/utils.py

def export_logs_as_json():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify([]), 401

    logs = ChatLog.query.filter_by(user_id=user_id).all()
    return jsonify([log.to_dict() for log in logs])





# ---------------------------------------------
# Export Logs as CSV
# ---------------------------------------------
def export_logs_as_csv(logs):
    output = io.StringIO()
    writer = csv.writer(output)

    if not logs:
        writer.writerow(["No data available"])
    elif hasattr(logs[0], "bot_response"):  # ChatLog
        writer.writerow(["Timestamp", "User Input", "Bot Response", "Mood"])
        for log in logs:
            writer.writerow([
                log.timestamp.strftime("%Y-%m-%d %H:%M"),
                log.user_input,
                log.bot_response,
                log.mood
            ])
    else:  # MoodLog
        writer.writerow(["Timestamp", "Mood"])
        for log in logs:
            writer.writerow([
                log.timestamp.strftime("%Y-%m-%d %H:%M"),
                log.mood
            ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )


# ---------------------------------------------
# Export Logs as PDF
# ---------------------------------------------
def export_logs_as_pdf(logs, title="Logs"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt=title, ln=True, align="C")
    pdf.ln(5)

    # Data
    pdf.set_font("Arial", size=11)
    if not logs:
        pdf.cell(0, 10, txt="No data available.", ln=True)
    elif hasattr(logs[0], "bot_response"):  # ChatLog
        for log in logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M")
            pdf.multi_cell(0, 10, 
                f"[{timestamp}]\n"
                f"You: {log.user_input}\n"
                f"Bot: {log.bot_response}\n"
                f"Mood: {log.mood}\n"
                "--------------------------------------------"
            )
            pdf.ln(2)
    else:  # MoodLog
        for log in logs:
            timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M")
            pdf.multi_cell(0, 10, 
                f"[{timestamp}] Mood: {log.mood}\n"
                "--------------------------------------------"
            )
            pdf.ln(2)

    # Output PDF
    pdf_output = io.BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)

    return send_file(
        pdf_output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

# app/utils.py
def suggest_tips_for_mood(mood):
    tips = {
        'joy': "Keep smiling and enjoy the moment!",
        'sadness': "It's okay to feel sad. Take deep breaths.",
        'anger': "Try calming down with a short walk or breathing exercise.",
        'fear': "You're safe now. Focus on the present.",
        'love': "Spread the love to those around you!",
        'surprise': "Take a moment to process things calmly.",
        'neutral': "How are you feeling really?"
    }
    return tips.get(mood.lower(), "Take a deep breath and talk to someone if needed.")

