"""Telegram review state machine. No connection to TikTok."""
import json, re, os, threading
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(os.getenv("DATA_DIR","/app/data"))/"approvals"
ROOT.mkdir(parents=True,exist_ok=True)
LOCK=threading.RLock()
def valid(job):
    return bool(re.fullmatch(r"[0-9a-f]{16}",str(job)))
def read(job):
    if not valid(job): return None
    try: return json.loads((ROOT/(job+".json")).read_text())
    except (OSError,ValueError): return None
def write(item):
    if not valid(item["job_id"]): raise ValueError("job")
    p=ROOT/(item["job_id"]+".json")
    q=p.with_suffix(".tmp");q.write_text(json.dumps(item,ensure_ascii=False));q.replace(p)
def register(job):
    with LOCK:
        jid=job["job_id"]
        existing=read(jid)
        if existing: return existing
        candidate = job["candidate"]
        match = re.search(r"-v([2-9])$", str(candidate.get("id","")))
        version = int(match.group(1)) if match else 1
        record={"job_id":jid,"status":"pending","version":version,
                "candidate":job["candidate"],"video_sent":False,"approved":False,
                "created_at":datetime.now(timezone.utc).isoformat(),"posted":False}
        write(record);return record
def delivered(job,ok):
    with LOCK:
        state=read(job)
        if state:
            state["video_sent"]=bool(ok);write(state)
def keyboard(job,version=1):
    return {"inline_keyboard":[
        [{"text":"✅ Posten","callback_data":f"review:approve:{job}:{version}"},
         {"text":"🚫 Nicht posten","callback_data":f"review:reject:{job}:{version}"}],
        [{"text":"🔄 Neu bearbeiten","callback_data":f"review:revise:{job}:{version}"}]
    ]}
def decide(job,version,action):
    with LOCK:
        item=read(job)
        if not item or item["status"]!="pending" or item["version"]!=version:
            return False,"Diese Vorschau ist nicht mehr offen.",None
        if not item.get("video_sent"): return False,"Das Video wurde nicht erfolgreich gesendet.",None
        if action=="approve":
            item["status"]="approved_only_no_upload"
            item["approved"]=True
            message="Freigabe gespeichert. KEIN TikTok-Upload, Qualitätsprüfung weiterhin nötig."
        elif action=="reject":
            item["status"]="rejected"
            message="Video abgelehnt. Kein Upload."
        elif action=="revise":
            if version>=3: return False,"Maximal drei Versionen pro Test. Keine Veröffentlichung.",None
            item["status"]="revision_requested"
            message="Neu-Bearbeitung beauftragt. Neue Vorschau folgt."
        else: return False,"Ungültige Aktion.",None
        write(item)
        return True,message,item if action=="revise" else None
