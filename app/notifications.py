"""Telegram-only notifications and secure one-time chat pairing.

No incoming public webhook and no TikTok publishing.
"""
from __future__ import annotations
import hmac
import json
import logging
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
LOG = logging.getLogger("studio.telegram")
TOKEN_CHECK = "not_checked"
POLL_CHECK = "not_started"

def telegram_diagnostics() -> dict:
    """Status only. Never returns secret tokens or chat identifiers."""
    return {"bot_token_validation": TOKEN_CHECK, "get_updates": POLL_CHECK,
            "chat_paired": paired_chat_id() is not None}

def _set_check(kind: str, state: str):
    global TOKEN_CHECK, POLL_CHECK
    previous = TOKEN_CHECK if kind == "token" else POLL_CHECK
    if kind == "token":
        TOKEN_CHECK = state
    else:
        POLL_CHECK = state
    if previous != state:
        LOG.info("Telegram %s status: %s", kind, state)


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

def send_video(video_path: str, caption: str, reply_markup: dict | None = None) -> bool:
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
                data={"chat_id": str(chat_id), "caption": caption[:850], "supports_streaming": "true", **({"reply_markup": json.dumps(reply_markup)} if reply_markup else {})},
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
    from . import approvals
    record = approvals.register(job)
    video_ok = send_video(job.get("render", {}).get("video_path", ""),
       "Technische Vorschau. Bei Posten wird NUR eine Freigabe gespeichert, NICHT veröffentlicht.",
       reply_markup=approvals.keyboard(job["job_id"], record["version"]))
    approvals.delivered(job["job_id"], video_ok)
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
    callback = update.get("callback_query")
    if callback:
        chat = (callback.get("message") or {}).get("chat") or {}
        if chat.get("type") != "private" or int(chat.get("id") or 0) != paired_chat_id():
            return
        data = str(callback.get("data", ""))
        from . import approvals
        parts = data.split(":")
        if len(parts) != 4 or parts[0] != "review":
            return
        try:
            version = int(parts[3])
        except ValueError:
            return
        success, message, revision = approvals.decide(parts[2], version, parts[1])
        try:
            with httpx.Client(timeout=12) as client:
                client.post(_api("answerCallbackQuery"), data={"callback_query_id": callback["id"], "text": message[:190], "show_alert": "false"})
        except (httpx.HTTPError, KeyError):
            pass
        if success:
            send_message(message)
            if revision:
                threading.Thread(target=_render_revision, args=(revision,), daemon=True).start()
        return
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
            _set_check("token", "missing")
            time.sleep(30)
            continue
        try:
            with httpx.Client(timeout=38) as client:
                if TOKEN_CHECK != "valid":
                    check = client.get(_api("getMe"), timeout=12)
                    valid = check.status_code == 200 and bool(check.json().get("ok"))
                    _set_check("token", "valid" if valid else f"invalid_http_{check.status_code}")
                    if not valid:
                        time.sleep(30)
                        continue
                r = client.get(_api("getUpdates"), params={
                    "offset": offset, "timeout": 24,
                    "allowed_updates": json.dumps(["message", "callback_query"]),
                    "limit": 20
                })
                if r.status_code != 200:
                    _set_check("poll", f"http_{r.status_code}")
                    time.sleep(15)
                    continue
                response = r.json()
                if not response.get("ok", False):
                    _set_check("poll", "telegram_api_error")
                    time.sleep(15)
                    continue
                _set_check("poll", "ok")
                for item in response.get("result", []):
                    offset = max(offset, int(item["update_id"]) + 1)
                    _save_json(OFFSET, {"offset": offset})
                    _handle(item)
        except (httpx.HTTPError, ValueError, OSError, KeyError, TypeError):
            # Never log request URLs: they contain Telegram bot tokens.
            _set_check("poll", "transport_or_processing_error")
            time.sleep(15)

def start_polling():
    threading.Thread(target=polling_loop, name="telegram-poll", daemon=True).start()


def _render_revision(record: dict):
    """Request a new render with a versioned angle. Publishing is never attempted."""
    from .main import Candidate, ProduceRequest, produce
    old = record["candidate"].copy()
    next_version = record["version"] + 1
    old["id"] = str(old["id"]).split("-v")[0] + f"-v{next_version}"
    old["title"] = str(old["title"])[:110] + f" – andere Perspektive (V{next_version})"
    try:
        result = produce(ProduceRequest(candidate=Candidate(**old)))
        if not (result.get("telegram") or {}).get("video"):
            send_message("Neue Version konnte nicht an Telegram gesendet werden. Kein Upload.")
    except Exception:
        send_message("Überarbeitung fehlgeschlagen. Kein TikTok-Upload.")
