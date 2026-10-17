"""One-shot 3D AI-agent explainer job, reviewed exclusively on paired Telegram."""
from __future__ import annotations
import json
import os
import threading
import time
from pathlib import Path
from . import notifications

DATA = Path(os.getenv("DATA_DIR", "/app/data"))
MARKER = DATA / "agent-v3-test-attempt.json"

def _run():
    for _ in range(18):
        if notifications.configured():
            break
        time.sleep(5)
    if not notifications.configured():
        print("Agent V3: Telegram not paired - skip", flush=True)
        return
    if MARKER.exists():
        print("Agent V3: test already attempted - skip", flush=True)
        return
    # Record before the paid voice API request so restarts do not charge twice.
    MARKER.write_text(json.dumps({"state": "attempted", "published": False}))
    notifications.send_message(
        "KI-Agent V3: Neues 3D-Schnittmodell-Video wird gerendert. "
        "Das kann einige Minuten dauern. Es wird NICHT auf TikTok gepostet."
    )
    try:
        from .main import produce_agent_v3
        result = produce_agent_v3()
        tg = result.get("telegram") or {}
        MARKER.write_text(json.dumps({
            "state": "finished", "job_id": result["job_id"],
            "telegram_message": bool(tg.get("message")),
            "telegram_video": bool(tg.get("video")),
            "published": False,
        }))
        print("Agent V3 finished: " + json.dumps({
            "job_id": result["job_id"], "telegram": tg,
            "public_posting": False,
        }), flush=True)
    except Exception as exc:
        MARKER.write_text(json.dumps({
            "state": "failed", "error_type": type(exc).__name__, "published": False,
        }))
        print("Agent V3 failed: " + type(exc).__name__, flush=True)
        notifications.send_message(
            "V3-Test fehlgeschlagen. Es wurde nichts veroeffentlicht. "
            "Der Fehler wird im Studio geprueft."
        )

def start():
    if os.getenv("AGENT_V3_ONCE", "false").lower() == "true":
        threading.Thread(target=_run, daemon=True, name="agent-v3-once").start()
