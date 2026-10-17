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
            "voice_settings":{"stability":float(os.getenv("ELEVENLABS_STABILITY","0.36")),"similarity_boost":float(os.getenv("ELEVENLABS_SIMILARITY","0.77")),"style":float(os.getenv("ELEVENLABS_STYLE","0.38")),"speed":float(os.getenv("ELEVENLABS_SPEED","1.05")),"use_speaker_boost":True}
        })
        if res.status_code!=200:
            # Do not include response body: API may echo sensitive request information.
            raise RuntimeError(f"Voice API returned status {res.status_code}")
        if len(res.content)>20*1024*1024:
            raise RuntimeError("Voice file exceeds size budget")
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(res.content)
    return target

def make_voice_aligned(text: str, target: Path):
    """Generate MP3 plus character-level timing in one paid TTS call."""
    import base64, json
    if not available(): raise RuntimeError("ElevenLabs credentials missing")
    voice_id = os.environ["ELEVENLABS_VOICE_ID"].strip()
    if not (voice_id.isalnum() and len(voice_id)<=64): raise ValueError("Invalid voice ID")
    if len(text)>4500: raise ValueError("Voice text too long")
    model=os.getenv("ELEVENLABS_MODEL","eleven_multilingual_v2")
    url=f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128"
    settings={"stability":float(os.getenv("ELEVENLABS_STABILITY","0.36")),
              "similarity_boost":float(os.getenv("ELEVENLABS_SIMILARITY","0.77")),
              "style":float(os.getenv("ELEVENLABS_STYLE","0.38")),
              "speed":float(os.getenv("ELEVENLABS_SPEED","1.05")),
              "use_speaker_boost":True}
    with httpx.Client(timeout=125) as client:
        resp=client.post(url,headers={"xi-api-key":os.environ["ELEVENLABS_API_KEY"],"content-type":"application/json"},
                         json={"text":text,"model_id":model,"voice_settings":settings})
        if resp.status_code!=200: raise RuntimeError(f"ElevenLabs aligned speech HTTP {resp.status_code}")
        body=resp.json()
    audio=base64.b64decode(body["audio_base64"],validate=True)
    alignment=body.get("alignment") or body.get("normalized_alignment")
    if not alignment or not alignment.get("characters"): raise RuntimeError("No word alignment received")
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(audio)
    target.with_suffix(".alignment.json").write_text(json.dumps(alignment,ensure_ascii=False),encoding="utf-8")
    return target,alignment
