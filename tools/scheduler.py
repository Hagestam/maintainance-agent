from apscheduler.schedulers.background import BackgroundScheduler
from tools.planning_tools import build_nightly_plan

scheduler = BackgroundScheduler()

def start_scheduler():
    # Runs every day at 18:00 (6pm)
    scheduler.add_job(
        build_nightly_plan,
        trigger="cron",
        hour=18,
        minute=0,
        id="nightly_plan",
        replace_existing=True
    )
    scheduler.start()
    print("[SCHEDULER] Nightly planner scheduled for 18:00 daily")

def stop_scheduler():
    scheduler.shutdown()