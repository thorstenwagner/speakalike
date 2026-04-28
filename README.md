# SpeakAlike

**Sprachsynthese-Tool mit KI-gestützter Textkorrektur, Voice Cloning und Augensteuerung**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Electron](https://img.shields.io/badge/Electron-28-47848F.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

SpeakAlike wurde speziell für Menschen entwickelt, die per Augensteuerung kommunizieren. Es verwandelt kurze, fehlerhafte Texteingaben in natürlich klingende Sprache – unterstützt durch künstliche Intelligenz, die Tippfehler automatisch korrigiert und den Gesprächskontext versteht.

---

## Highlights

- **KI-Korrektur in Echtzeit** – Claude AI korrigiert Tippfehler aus der Augensteuerung, ohne Wörter hinzuzufügen
- **Voice Cloning** – Eigene Stimme klonen und in Gesprächen verwenden
- **Mikrofon-Ausgabe für Telefonie** – Sprache direkt über virtuelle Audiokabel (z.B. VB-Cable) in Zoom, Teams oder Telefon einspeisen
- **Schnellzugriffe** – Häufig verwendete Sätze per Tastendruck abspielen
- **Privacy-Modus** – Eingabetext wird verborgen, ideal wenn andere den Bildschirm sehen

---

## Features

### Sprachsynthese

| Feature | Beschreibung |
|---------|-------------|
| **Coqui XTTS v2** | Lokale, GPU-beschleunigte Sprachsynthese mit Voice Cloning (17 Sprachen) |
| **ElevenLabs** | Cloud-basierte Synthese (Multilingual v2/v3, Flash v2.5, Turbo v2.5) |
| **Voice Cloning** | Eigene Stimme aus 5–30 Sekunden Audio klonen und als Modell speichern |
| **Sprachparameter** | Geschwindigkeit (0.5x–2.0x), Temperatur, Wiederholungsstrafe feinjustierbar |
| **Dual-Output** | Gleichzeitige Ausgabe über Lautsprecher und virtuelles Mikrofon |

### KI-Korrektur (Claude)

| Feature | Beschreibung |
|---------|-------------|
| **Automatische Korrektur** | Fehlende/falsche Buchstaben werden erkannt und korrigiert |
| **Gesprächskontext** | Letzte 5 Minuten Nachrichten werden als Kontext mitgesendet |
| **Kontextfeld** | Gesprächssituation beschreiben (z.B. „Arztbesuch", „Einkaufen") für bessere Ergebnisse |
| **KI an/aus** | Per Strg+Enter im leeren Feld umschaltbar, grüner „KI"-Badge zeigt Status |
| **Bestätigungsdialog** | KI-Vorschlag vor dem Sprechen prüfen und bearbeiten |
| **Modellwahl** | Claude Haiku 4.5 (schnell) oder Claude Sonnet 4.6 (präziser) |

### Tastenkürzel

| Kürzel | Funktion |
|--------|----------|
| **Enter** | Text sprechen (bei leerem Feld: letzte Nachricht wiederholen) |
| **Strg+Enter** | KI-Korrektur auslösen / KI-Modus umschalten |
| **Strg+L** | Sprache wechseln (Deutsch ↔ Englisch) |
| **Strg+D** | Signalton abspielen |
| **Strg+P** | Privacy-Modus ein/aus |
| **Strg+M** | Mikrofon-Ausgabe ein/aus |
| **Q, E, T, U, I, Y, C, N** | Schnellzugriff-Sätze 1–8 abspielen |
| **Escape** | Dialoge schließen / Mini-Modus beenden |
| **Tab** | Durch Vorschläge navigieren |

### Katalog & Schnellzugriffe

| Feature | Beschreibung |
|---------|-------------|
| **Katalog** | Häufig verwendete Sätze mit Audio speichern und organisieren |
| **Auto-Tagging** | KI generiert automatisch passende Tags für gespeicherte Sätze |
| **Tag-Filter** | Sätze nach Tags filtern (UND/ODER-Modus) |
| **Schnellzugriffe** | Bis zu 20 Sätze per Drag & Drop als Schnellzugriff anlegen |
| **Schnellzugriff-Sets** | Verschiedene Sets nach Situation speichern und laden |
| **Wiedergabezähler** | Zeigt an, welche Sätze am häufigsten verwendet werden |

### Smarte Vorschläge

| Feature | Beschreibung |
|---------|-------------|
| **Semantische Suche** | Ähnliche Sätze aus dem Verlauf werden beim Tippen vorgeschlagen |
| **Multilingual-Embeddings** | Vorschläge basieren auf Bedeutung, nicht nur Wortgleichheit |
| **Kontextbewusstsein** | Berücksichtigt den aktuellen Gesprächsverlauf |

### Barrierefreiheit

| Feature | Beschreibung |
|---------|-------------|
| **Große Bedienelemente** | Optimiert für Augensteuerung und eingeschränkte Motorik |
| **Privacy-Modus** | Eingabetext wird unlesbar, nur letztes Zeichen sichtbar (Strg+P) |
| **Mini-Modus** | Kompaktes Overlay-Fenster, bleibt im Vordergrund |
| **Visuelle Badges** | „KI" (grün) und „MIC" (rot) zeigen aktive Features auf einen Blick |
| **Tastatursteuerung** | Alle wichtigen Funktionen ohne Maus erreichbar |

### Telefonie-Integration

| Feature | Beschreibung |
|---------|-------------|
| **Virtuelles Mikrofon** | Sprachausgabe über VB-Cable o.ä. in Zoom, Teams, Telefon einspeisen |
| **Tipp-Geräusche** | Simuliert Tastaturklicks auf dem Mikrofon-Kanal während der Eingabe |
| **Echo-Test** | Mikrofon-Gerät direkt in den Einstellungen testen |
| **MIC-Badge** | Roter pulsierender Badge zeigt aktive Mikrofon-Ausgabe |

### Weitere Features

| Feature | Beschreibung |
|---------|-------------|
| **Dark Mode** | Standard-Theme, heller Modus umschaltbar |
| **Verlauf** | Letzte 50 Nachrichten mit Zeitstempel |
| **Audio-Import** | MP3/WAV/OGG importieren mit automatischer Transkription (Whisper) |
| **Audio-Download** | Generierte Sprache als WAV speichern |
| **Deutsch & Englisch** | Volle Unterstützung beider Sprachen |

---

## Installation

### Installer (empfohlen)

`SpeakAlike Setup 1.0.0.exe` ausführen – enthält Electron-App, Python-Backend und Voice Models.

### Entwicklermodus

```bash
# Backend starten
conda activate .conda-py311
python backend_api.py

# Frontend starten (separates Terminal)
cd electron-app
npm install
npm start
```

---

## Architektur

```
┌─────────────────────┐     HTTP/REST     ┌──────────────────────┐
│   Electron-App      │ ◄──────────────►  │   Python Backend     │
│   (Frontend)        │    Port 8765      │   (FastAPI/Uvicorn)  │
│                     │                   │                      │
│  • index.html       │                   │  • Coqui XTTS (GPU)  │
│  • renderer.js      │                   │  • ElevenLabs API    │
│  • styles.css       │                   │  • Claude AI API     │
│  • preload.js       │                   │  • Whisper (Import)  │
│  • quick-access.html│                   │  • Embeddings        │
└─────────────────────┘                   └──────────────────────┘
```

---

## Systemanforderungen

### Minimum

- CPU: Intel Core i5 / AMD Ryzen 5
- RAM: 8 GB
- Speicher: 5 GB

### Empfohlen

- GPU: NVIDIA RTX 3060 oder besser (8+ GB VRAM)
- RAM: 16 GB
- Speicher: 10 GB SSD

---

## Lizenz

MIT
