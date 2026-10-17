"""Small built-in clock as a temporary fallback until n8n is imported.

Only runs when Telegram is paired, with a single daily preview and no upload.
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import os
import threading
import time
from . import notifications

DATA = Path(os.getenv("DATA_DIR", "/app/data"))
STAMP = DATA / "last-scheduled-run.json"
TIMEZONE = ZoneInfo("Europe/Berlin")

def _last_day() -> str:
    try:
        return json.loads(STAMP.read_text()).get("day", "")
    except (OSError, ValueError):
        return ""

def _write_day(day: str):
    temp = STAMP.with_suffix(".tmp")
    temp.write_text(json.dumps({"day": day}))
    temp.replace(STAMP)

def run_daily():
    from .main import trends, produce, ProduceRequest, Candidate
    raw = trends()
    choices = raw.get("candidates") or []
    if not choices:
        notifications.send_message("KI Trendradar: Heute kein passendes Thema aus der aktuellen Quelle gefunden. Keine Produktion.")
        return
    result = produce(ProduceRequest(candidate=Candidate(**choices[0])))
    if result.get("status") == "blocked_quality_review":
        return  # preview notification is already sent by produce()
    notifications.send_message("KI Video-Studio: Tageslauf abgeschlossen: " + str(result.get("status")))

def scheduler_loop():
    while True:
        try:
            current = datetime.now(TIMEZONE)
            enabled = os.getenv("AUTO_DAILY", "false").lower() == "true"
            # Only the 08:00 hour, no overnight surprise jobs on deploy.
            if enabled and current.hour == 8 and notifications.configured():
                day = current.date().isoformat()
                if _last_day() != day:
                    _write_day(day)  # at-most-once; failed jobs require a new day or manual retry
                    try:
                        run_daily()
                    except Exception:
                        notifications.send_message("KI Video-Studio: Der Tageslauf ist fehlgeschlagen. Keine TikTok-Veroeffentlichung.")
        except Exception:
            pass
        time.sleep(35)

def start_scheduler():
    threading.Thread(target=scheduler_loop, name="studio-scheduler", daemon=True).start()
