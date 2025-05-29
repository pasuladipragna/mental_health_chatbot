from apscheduler.schedulers.background import BackgroundScheduler
from app.routes.views import fetch_therapists


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_therapists, 'interval', days=15)
    scheduler.start()
