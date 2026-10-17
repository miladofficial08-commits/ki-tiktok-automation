"""One-time motion-preview test; guarded against restarts and repeated API charges."""
import os,json,time,threading
from pathlib import Path
from . import notifications
ROOT=Path(os.getenv("DATA_DIR","/app/data"))
MARK=ROOT/"motion-review-v1-attempt.json"
def _worker():
    for _ in range(20):
        if notifications.configured():break
        time.sleep(5)
    if not notifications.configured():
        print("Motion test skipped: Telegram not paired",flush=True);return
    if MARK.exists():
        print("Motion test already attempted",flush=True);return
    MARK.write_text(json.dumps({"status":"attempted"}))
    notifications.send_message("Neue Motion-Video-Vorschau wird erstellt: 18 Szenen, ElevenLabs-Stimme, 3 Freigabeoptionen. Kein TikTok-Upload.")
    try:
        from .main import produce_motion
        job=produce_motion()
        MARK.write_text(json.dumps({"status":"finished","job_id":job["job_id"],"telegram":job.get("telegram"),"qa":job.get("qa",{}).get("ok")}))
        print("Motion test finished: "+json.dumps({"job":job["job_id"],"telegram":job.get("telegram")}),flush=True)
    except Exception as err:
        MARK.write_text(json.dumps({"status":"failed","error_type":type(err).__name__}))
        print("Motion test failed: "+type(err).__name__,flush=True)
        notifications.send_message("Motion-Videotest fehlgeschlagen. Kein Upload. Bitte auf eine neue Testversion warten.")
def start():
    if os.getenv("MOTION_DEMO_ONCE","false").lower()=="true":
        threading.Thread(target=_worker,daemon=True,name="motion-once").start()
