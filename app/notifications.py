"""Telegram-only notifications and secure one-time chat pairing.

No incoming public webhook and no TikTok publishing.
"""
from __future__ import annotations
import hmac
import json
import os
from pathlib import Path
import threading
import time
import httpx

ROOT = Path(os.getenv("DATA_DIR", "/app/data"))
ROOT.mkdir(parents=True, exist_ok=True)
STATE = ROOT / "telegram-pair.json"
OFFSET = ROOT / "telegram-offset.json"
STATE_LOCK = threading.Lock()

def _bot_token() -> str:
    return os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

def paired_chat_id() -> int | None:
    try:
        chat = int(json.loads(STATE.read_text())["chat_id"])
        return chat if chat > 0 else None
    except (ValueError, OSError, KeyError, TypeError):
        return None

def _api(method: str) -> str:
    return "https://api.telegram.org/bot" + _bot_token() + "/" + method

def configured() -> bool:
    return bool(_bot_token()) and paired_chat_id() is not None

def send_message(message: str) -> bool:
    chat_id = paired_chat_id()
    if not _bot_token() or not chat_id:
        return False
    try:
        with httpx.Client(timeout=25) as client:
            response = client.post(_api("sendMessage"), data={"chat_id": str(chat_id), "text": message[:3800]})
            response.raise_for_status()
            return bool(response.json().get("ok"))
    except (httpx.HTTPError, ValueError):
        return False

def send_video(video_path: str, caption: str) -> bool:
    chat_id = paired_chat_id()
    path = Path(video_path)
    if not _bot_token() or not chat_id or not path.is_file():
        return False
    # Standard Bot API sendVideo has a relatively small upload limit.
    if path.stat().st_size > 45 * 1024 * 1024:
        send_message("Video ist zu gross fuer den Bot. Bitte Renderprofil verkleinern.")
        return False
    try:
        with httpx.Client(timeout=180) as client, path.open("rb") as f:
            response = client.post(
                _api("sendVideo"),
                data={"chat_id": str(chat_id), "caption": caption[:850], "supports_streaming": "true"},
                files={"video": ("vorschau.mp4", f, "video/mp4")},
            )
            response.raise_for_status()
            return bool(response.json().get("ok"))
    except (OSError, httpx.HTTPError, ValueError):
        return False

def notify_production(job: dict) -> dict:
    if not configured():
        return {"message": False, "video": False, "reason": "Telegram noch nicht gekoppelt"}
    qa = job.get("qa", {})
    topic = job.get("candidate", {})
    reasons = ", ".join(qa.get("reasons", []))[:600] or "Noch nicht manuell geprueft"
    status = (
        "KI Video-Studio – neuer Lauf\n"
        f"Thema: {topic.get('title', 'Unbekannt')[:115]}\n"
        f"Quelle: {topic.get('url', '')[:180]}\n"
        f"Qualitaet: {'OK' if qa.get('ok') else 'NICHT FREIGEGEBEN'}\n"
        f"Pruefung: {reasons}\n"
        f"Job: {job.get('job_id', '-')}\n"
        "TikTok-Upload: NICHT aktiviert."
    )
    msg_ok = send_message(status)
    video_ok = send_video(job.get("render", {}).get("video_path", ""), "Technische Videovorschau. Noch nicht publikationstauglich. Kein TikTok-Upload.")
    if not video_ok:
        send_message("Hinweis: Videodatei konnte nicht an Telegram uebermittelt werden.")
    return {"message": msg_ok, "video": video_ok}

def _save_json(path: Path, data: dict):
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data), encoding="utf-8")
    temp.replace(path)

def _offset_value() -> int:
    try:
        return int(json.loads(OFFSET.read_text())["offset"])
    except (ValueError, OSError, KeyError, TypeError):
        return 0

def _handle(update: dict):
    message = update.get("message") or {}
    chat = message.get("chat") or {}
    if chat.get("type") != "private" or not isinstance(message.get("text"), str):
        return
    text = message["text"].strip()
    if text.lower().startswith("/connect "):
        secret = os.getenv("TELEGRAM_PAIR_CODE", "").strip()
        proposed = text.split(maxsplit=1)[1].strip()
        old = paired_chat_id()
        if secret and hmac.compare_digest(secret, proposed) and old is None:
            with STATE_LOCK:
                if paired_chat_id() is None:
                    _save_json(STATE, {"chat_id": int(chat["id"])})
                    send_message("Telegram ist verbunden. Ab jetzt bekommst du Video-Vorschauen und Statusmeldungen. Es werden keine TikTok-Videos automatisch gepostet.")
        elif old == int(chat["id"]):
            send_message("Dieser Chat ist bereits verbunden.")
    elif text.lower() in ("/status", "/start") and paired_chat_id() == int(chat.get("id") or 0):
        send_message("KI Studio online. Telegram verbunden. TikTok-Autopost ist aus.")
    # Other messages are ignored: this is a notification-only bot.

def polling_loop():
    offset = _offset_value()
    while True:
        if not _bot_token():
            time.sleep(30)
            continue
        try:
            with httpx.Client(timeout=38) as client:
                r = client.get(_api("getUpdates"), params={
                    "offset": offset, "timeout": 24,
                    "allowed_updates": json.dumps(["message"]),
                    "limit": 20
                })
                r.raise_for_status()
                for item in r.json().get("result", []):
                    offset = max(offset, int(item["update_id"]) + 1)
                    _save_json(OFFSET, {"offset": offset})
                    _handle(item)
        except Exception:
            # Transient Telegram outages are not a reason to crash the app.
            time.sleep(15)

def start_polling():
    threading.Thread(target=polling_loop, name="telegram-poll", daemon=True).start()
