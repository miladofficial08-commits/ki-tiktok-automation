# KI zum Nachmachen – TikTok Automation (MVP)

Ein kostensensibler, transparenter **Review-only-Prototyp** für einen deutschsprachigen KI-/Vibe-Coding-Kanal.

## Aktueller Funktionsumfang
- n8n steuert die tägliche Ausführung über Railway Private Networking.
- FastAPI-Studio sucht in öffentlich verfügbaren Hacker-News-Signalen nach KI- und Automatisierungsthemen. **Keine TikTok-Viralitätsdaten.**
- Entwürfe entstehen optional über Gemini (ohne API-Key: klar markiertes Demo-Skript).
- Pillow, espeak-ng und FFmpeg rendern eine einfache technische Videovorschau.
- Qualitätsprüfung blockiert alle Demo-Videos konsequent vor Veröffentlichung.
- Optional: Status und Videovorschau per Telegram.
- **Kein automatischer TikTok-Upload und keine ungeprüften Behauptungen über Tests.**

## Installation
1. Im Railway-Projekt einen neuen Service aus diesem Repository mit dem Namen `studio` anlegen.
2. Diesen Service ohne öffentliche Domain betreiben; interner Hostname: `studio.railway.internal:8000`.
3. Railway-Volume an `/app/data` anschließen (nach erfolgreichem Erst-Deploy genügt auch zunächst ein kurzlebiger Test ohne Volume).
4. Studio-Variable `STUDIO_TOKEN` als langes Geheimnis in Railway setzen (niemals committen).
5. In n8n Workflow `n8n/railway-preview.json` importieren, HTTP Header Auth Credential `X-Studio-Token` mit demselben Token konfigurieren und zunächst manuell ausführen.
6. Optionale Variables: `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.

Endpoints: `GET /health`, `GET /api/trends`, `POST /api/produce`, `GET /api/jobs/{job_id}`. Nur `/health` ist ohne Token erreichbar.

## Kosten und Sicherheit
Railway berechnet Rechenzeit, Speicher und Netzwerk. Die Videoerstellung ist CPU-lastig, daher zunächst max. 1 Testlauf pro Tag; keine realen API-Keys in diesem öffentlichen Repository. Diese Entwicklungsstufe ist nicht publikationstauglich.

## Offene Aufgaben vor produktivem TikTok-Kanal
Echte eigene Bildschirm-Demos, hochwertige lizenzierte Animation und Sprache, menschlich überprüfbare Faktenbelege, Rechts-/Qualitätsprüfung, ein offizieller Veröffentlichungsweg, Analytics und verbindliche Kostenlimits.
