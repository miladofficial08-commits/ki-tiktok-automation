"""Single paid voice check; never schedules TikTok publishing."""
from __future__ import annotations
import hashlib
import json
import os
import threading
from pathlib import Path
from datetime import datetime, timezone
from . import notifications, voice

SAMPLE = ("Stell dir vor: Du beschreibst einer KI deine Idee. "
          "Und daraus entsteht eine App, die du wirklich benutzen kannst. "
          "Wie gut funktioniert das? Genau das probieren wir aus.")
DATA = Path(os.getenv("DATA_DIR", "/app/data")) / "voice-tests"

def _run():
    if not voice.available() or not notifications.configured():
        print("Voice test skipped: voice or Telegram missing", flush=True)
        return
    DATA.mkdir(parents=True, exist_ok=True)
    label = hashlib.sha256(os.getenv("ELEVENLABS_VOICE_ID", "").encode()).hexdigest()[:12]
    marker = DATA / (label + "-v1.json")
    if marker.exists():
        print("Voice test already attempted; skipping", flush=True)
        return
    marker.write_text(json.dumps({"status": "started", "at": datetime.now(timezone.utc).isoformat()}))
    try:
        audio = voice.make_voice(SAMPLE, DATA / (label + "-sample.mp3"))
        delivered = notifications.send_audio(
            str(audio), "Stimmprobe: junge, lebendige Tech-Erzaehlerstimme. "
                        "Bitte beurteilen: passt sie zur Marke?")
        marker.write_text(json.dumps({"status": "completed", "telegram_delivered": delivered}))
        print("Voice test: generated; telegram_delivered=" + str(delivered), flush=True)
        if not delivered:
            notifications.send_message("ElevenLabs-Stimme erzeugt, aber Audio konnte nicht gesendet werden.")
    except Exception as exc:
        marker.write_text(json.dumps({"status": "failed", "error_type": type(exc).__name__}))
        print("Voice test: failed with " + type(exc).__name__, flush=True)
        notifications.send_message("Der kurze ElevenLabs-Stimmtest ist fehlgeschlagen. Kein erneuter automatischer Versuch.")

def start():
    if os.getenv("VOICE_TEST_ENABLED", "false").lower() == "true":
        threading.Thread(target=_run, daemon=True, name="voice-test-once").start()
