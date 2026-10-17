"""Runs Brand V2 once and delivers review-ready preview to Telegram."""
from __future__ import annotations
import json,os,threading,time
from pathlib import Path
from . import notifications
ROOT=Path(os.getenv("DATA_DIR","/app/data"))
MARKER=ROOT/"brand-v2-once-attempt.json"

def run():
    for _ in range(24):
        if notifications.configured():break
        time.sleep(5)
    if not notifications.configured():
        print("Brand V2 skipped: Telegram not ready",flush=True)
        return
    if MARKER.exists():
        print("Brand V2 already attempted",flush=True)
        return
    MARKER.write_text(json.dumps({"state":"started","tiktok_uploaded":False}))
    notifications.send_message("Brand Prototype V2 wird produziert: Mintgrüne Zwei-Wort-Karaoke-Untertitel, neue Schrift, ElevenLabs-Timing. Kein TikTok-Upload.")
    try:
        from .main import produce_karaoke_v2
        job=produce_karaoke_v2()
        MARKER.write_text(json.dumps({"state":"completed","job_id":job["job_id"],"telegram":job.get("telegram"),"tiktok_uploaded":False}))
        print("Brand V2 render completed: "+json.dumps({"job":job["job_id"],"telegram":job.get("telegram")}),flush=True)
    except Exception as exc:
        MARKER.write_text(json.dumps({"state":"failed","error_type":type(exc).__name__,"tiktok_uploaded":False}))
        print("Brand V2 render failed: "+type(exc).__name__,flush=True)
        notifications.send_message("Brand V2 Videotest konnte nicht abgeschlossen werden. Kein Upload.")
def start():
    if os.getenv("BRAND_V2_ONCE","false").lower()=="true":
        threading.Thread(target=run,daemon=True,name="brand-v2-once").start()
