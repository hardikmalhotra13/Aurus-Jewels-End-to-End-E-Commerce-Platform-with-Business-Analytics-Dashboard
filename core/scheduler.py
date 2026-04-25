"""
core/scheduler.py — APScheduler job to auto-fetch gold rates
daily at 9:00 AM IST. Called once at app startup in Home.py.
"""
import threading
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_scheduler_started = False


def start_scheduler():
    """Start the rate-fetch scheduler — runs once per process."""
    global _scheduler_started
    if _scheduler_started:
        return
    _scheduler_started = True

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from core.rate_fetcher import fetch_if_missing

        scheduler = BackgroundScheduler(timezone="Asia/Kolkata")
        scheduler.add_job(
            fetch_if_missing,
            "cron",
            hour    = 9,
            minute  = 0,
            id      = "daily_rate_fetch"
        )
        scheduler.start()

        # Also fetch immediately on startup if missing today
        fetch_if_missing()

    except ImportError:
        # APScheduler not available — fallback to threading
        _threading_fallback()


def _threading_fallback():
    """
    Simple threading fallback if APScheduler unavailable.
    Checks every hour if today's rates are missing.
    """
    import time
    from core.rate_fetcher import fetch_if_missing

    def worker():
        while True:
            try:
                fetch_if_missing()
            except Exception:
                pass
            time.sleep(3600)  # check every hour

    t = threading.Thread(target=worker, daemon=True)
    t.start()