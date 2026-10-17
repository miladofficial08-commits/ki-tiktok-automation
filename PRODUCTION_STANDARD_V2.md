# KI zum Nachmachen: Produktionsstandard v2 (Stand 2026-10-17)

## Erkenntnis aus Testvideo und englischer Referenz
Bisherige 72s-Demo: 9 nahezu identische Texttafeln zu je 8s, keine gezeigte App, kein animierter Handlungsablauf, TTS mit espeak-ng, fehlender narrativer Beleg. NICHT publizieren.
Englische Referenz: charakterbasierte Umgebung + echte visuelle UI-Aktionen (Terminal, GitHub, Suchergebnisse, Ordner), kurze Karten, viele Anschlussbewegungen, stimmige Typografie, keine ausufernden Fülltafeln.
Nicht replizieren/stehlen, sondern eigene Welt und eigenes Maskottchen mit konsistenter Markenidentität entwickeln.

## Drei deutsche Serien
A. Ich habe es mit KI gebaut (~45%): Produkt/Demo zeigen; 1 nützlicher konkreter Mini-Workflow, Ergebnis und Grenzen.
B. Diesen Job übernimmt jetzt KI (~35%): Ausgangssituation, Automation in Aktion, messbar belegtes Vorher/Nachher.
C. Das kommt gerade aus den USA (~20%): Originalquelle und Datum, Erklärung, was praktisch nachgebaut werden kann; keine erfundene Viralität.

## Freigabekriterium für 60–90s TikTok
- Hook in 0–1.5s als echte Aktion oder klares Vorher/Nachher, nicht Überschriftenkarte.
- 3–6s pro Beat; 12–22 bedeutungsvolle Shots pro Minute. Jede Einstellung hat Bewegung/eine Erklärung/einen echten Übergang. Kein aggressives Dauerblinken.
- 9:16, mindestens 720x1280 für technische Vorschau, Ziel 1080x1920. Captions gut lesbar innerhalb Safe Area.
- 60–90s hat 1 klare Behauptung und 1 **sichtbar gezeigte** Demo. Kein leeres KI-Hype-Versprechen.
- Echte Softwareaufnahmen dürfen nur aktuelle Funktion und testbare Abläufe zeigen. Wenn ein Mockup simuliert wird, wird es als DEMO markiert.
- UI-Layer: Content maximal 2–3 Zeilen pro Moment; Kontinuität über Farbsystem/Maskottchen; kein kindischer Stil; kurze Klangakzente sparsam.
- Ton: deutsche natürliche Sprecherstimme, realistische Betonung, Pegel und Lautheit; Hintergrundmusik nur lizenzgeprüft, nicht in Konkurrenz zur Stimme.
- Dramaturgie: Hook → Problem → Vorher → KI-Handlung 1 → KI-Handlung 2 → Resultat → Limitation → Anwendungsfall → offene Community-Frage.
- QA: richtige Aussprache, Quellen und Produktversion, Urheberrechte, Ton, Audio/Visual-Synchronität, Textränder, eindeutige Demonstration, keine falschen Performancezahlen.
- Kein automatischer TikTok-Upload ohne Telegram-Genehmigung, Inhalts-QA UND spätere offizielle Schnittstelle.
- Telegram-Optionen: „Posten“ = nur **Freigabe für eine spätere Publishing-Phase**, „Nicht posten“ = blockiert, „Neu bearbeiten“ = neues Storyboard/Render mit begrenzten Iterationen. Vor TikTok-Anbindung erfolgt garantiert kein Upload.

## Bevorzugter kostenbewusster Technikstack
- Railway + n8n als Prozesssteuerung; Python/FastAPI als kontrollierende Produktions-API.
- Für wiederverwendbare, saubere 2D/2.5D-Motion-Szenen: FFmpeg + SVG/Lottie/React/Remotion (Lizenz je nach Projekt prüfen). Kein teurer Video-Gen-Aufruf für jeden Shot.
- Für überzeugende reale Screens: automatisierbare Test-Webapp + Playwright-Aufzeichnung/Animation und eigene UI-Mockups mit Kennzeichnung. Keine geschützten Fremdvideos übernehmen.
- Stimme: ElevenLabs über API nur mit gültiger kommerzieller Lizenz; gezielter A/B-Vergleich gegen deutsches lokales Piper-TTS mit Lizenzprüfung. Niemals espeak-ng im finalen Clip.
- Enges Kostenbudget 30 EUR/Monat: Railway + Sprecherstimme + kleine KI-Textkosten; High-End 3D-Generierung pro Clip passt voraussichtlich nicht dauerhaft hinein.

## Nächster implementierbarer Meilenstein
Ein wirklich gutes und explizit als DEMO gekennzeichnetes Proof-of-Concept zu „Baue einen Habit Tracker aus einer Idee“, **nicht** als behauptete eigene Live-Produktion, sofern die App nicht echt erstellt/getestet wurde.
Dazu eine neu entwickelte 2.5D Figur, animierte UI, Terminal-Eingabe, Dateibaum, Preview, Klick, sichtbares Resultat, mindestens 15 unterschiedliche sinnvolle Kamera-/UI-Shots; ruhige, hochwertige Farben und konsistente deutsche typografische Anweisungen.
Erst danach 3 Buttons auf Telegram vollständig verifizieren und den gesamten Ablauf stress-testen.
