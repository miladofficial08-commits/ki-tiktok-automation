"""Optional paid ElevenLabs voice. No API use unless explicitly enabled.

Requires ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, VOICE_ENGINE=elevenlabs.
Runtime consumes external credits. Never log token or request headers.
"""
from __future__ import annotations
import os
from pathlib import Path
import httpx

def available() -> bool:
    return os.getenv("VOICE_ENGINE","").lower()=="elevenlabs" and bool(os.getenv("ELEVENLABS_API_KEY")) and bool(os.getenv("ELEVENLABS_VOICE_ID"))

def make_voice(text: str, target: Path) -> Path:
    if not available():
        raise RuntimeError("ElevenLabs not explicitly configured")
    voice_id=os.environ["ELEVENLABS_VOICE_ID"].strip()
    if not (voice_id.isalnum() and len(voice_id)<=64):
        raise ValueError("Invalid voice identifier")
    endpoint=f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128"
    # Single 72 sec video normally uses well under 5k characters.
    if len(text)>4500:
        raise ValueError("Speech draft too long")
    with httpx.Client(timeout=90) as client:
        res=client.post(endpoint,headers={"xi-api-key":os.environ["ELEVENLABS_API_KEY"],"content-type":"application/json","accept":"audio/mpeg"},json={
            "text":text,
            "model_id":os.getenv("ELEVENLABS_MODEL","eleven_multilingual_v2"),
            "voice_settings":{"stability":0.55,"similarity_boost":0.75}
        })
        if res.status_code!=200:
            # Do not include response body: API may echo sensitive request information.
            raise RuntimeError(f"Voice API returned status {res.status_code}")
        if len(res.content)>20*1024*1024:
            raise RuntimeError("Voice file exceeds size budget")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(res.content)
    return target
