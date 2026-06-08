# SpeakAlike

**Sprachsynthese-Tool für Augensteuerung – mit KI-Korrektur, Mini-Modus und Telefonie-Integration**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Electron](https://img.shields.io/badge/Electron-28-47848F.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

SpeakAlike wurde für Menschen entwickelt, die per Augensteuerung kommunizieren. Es verwandelt kurze, fehlerhafte Texteingaben in natürlich klingende Sprache – unterstützt durch Claude AI, die Tippfehler automatisch korrigiert und den Gesprächskontext versteht.

Zwei besonders wichtige Features: Der **Mini-Modus** – ein kompaktes Always-on-Top-Overlay, das jederzeit per `Strg+M` erreichbar ist – und die vollständige **Tastatursteuerung** aller Kernfunktionen per Tastenkürzel, damit Mausbedienung nie notwendig ist.

---

## Highlights

- **KI-Korrektur** – Claude AI korrigiert Augensteuerungs-Tippfehler, ohne Wörter hinzuzufügen
- **ElevenLabs TTS** – natürlich klingende Stimmen in der Cloud (mehrere Modelle und Stimmen wählbar)
- **Mini-Modus** – kompaktes Always-on-Top-Fenster, ideal für den Einsatz neben anderen Apps
- **Mikrofon-Ausgabe** – Sprache über virtuelles Audiokabel direkt in Zoom, Teams oder Telefon einspeisen
- **A–Z Schnellzugriff** – bis zu 26 Sätze per einzelner Taste sofort abrufen
- **Privacy-Modus** – Eingabe wird verborgen, nur das letzte Zeichen bleibt sichtbar

---

## Features

### Sprachsynthese

| Feature | Beschreibung |
|---------|-------------|
| **ElevenLabs (Cloud)** | Natürlich klingende Stimmen; Modelle: Multilingual v2/v3, Flash v2.5, Turbo v2.5 |
| **pyttsx3 (Offline)** | Systemstimmen über Windows SAPI5, kein Internet erforderlich |
| **Dual-Output** | Gleichzeitige Ausgabe über Lautsprecher und virtuelles Mikrofon |
| **Lautstärkeregelung** | Stummschalten und Lautstärke per Schieberegler |

### KI-Korrektur (Claude)

| Feature | Beschreibung |
|---------|-------------|
| **Automatische Korrektur** | Fehlende/falsche Buchstaben werden ergänzt, keine inhaltlichen Änderungen |
| **Gesprächskontext** | Letzte Nachrichten und ein frei beschreibbares Kontextfeld werden mitgesendet |
| **Bestätigungsdialog** | KI-Vorschlag vor dem Sprechen prüfen und manuell bearbeiten |
| **Modellwahl** | Claude Haiku 4.5 (schnell) oder Claude Sonnet 4.6 (präziser) |

### Tastenkürzel

| Kürzel | Funktion |
|--------|----------|
| **Enter** | Text sprechen (bei leerem Feld: letzte Nachricht wiederholen) |
| **A–Z + Enter** | Schnellzugriff-Satz für den jeweiligen Buchstaben abspielen |
| **Strg+Enter** | KI-Vervollständigung auslösen |
| **Strg+Shift+Enter** | KI-Modus dauerhaft ein/aus |
| **Strg+S** | Audio generieren und zum Schnellzugriff hinzufügen |
| **Strg+L** | Sprache wechseln |
| **Strg+D** | Signalton abspielen |
| **Strg+Shift+D** | Vorsignal abspielen |
| **Strg+P** | Privacy-Modus ein/aus |
| **Strg+M** | Mini-Modus ein/aus |
| **Escape** | Dialoge schließen |

### Schnellzugriff (A–Z)

- Bis zu **26 Sätze** (A bis Z) als Schnellzugriff speicherbar
- Abruf durch Eingabe des Buchstabens + Enter im Textfeld
- **Sets** speichern und laden – unterschiedliche Sets für verschiedene Situationen
- Sätze aus dem Katalog oder direkt per `Strg+S` hinzufügen

### Katalog

| Feature | Beschreibung |
|---------|-------------|
| **Nachrichtenkatalog** | Häufig verwendete Sätze mit Audio, Tags und Metadaten speichern |
| **Auto-Tagging** | Claude AI generiert automatisch passende Tags |
| **Tag-Filter** | UND/ODER-Filterung nach beliebig vielen Tags |
| **Favoriten** | Sätze markieren für schnellen Zugriff |
| **Wiedergabezähler** | Zeigt am häufigsten verwendete Sätze |
| **Audio-Import** | MP3/WAV/OGG importieren mit automatischer Transkription (Whisper) |

### Barrierefreiheit & Mini-Modus

| Feature | Beschreibung |
|---------|-------------|
| **Mini-Modus** | Kompaktes Always-on-Top-Overlay (`Strg+M`), Position oben/unten wählbar |
| **Privacy-Modus** | Eingabe unlesbar, nur letztes Zeichen sichtbar (`Strg+P`) |
| **Große Bedienelemente** | Optimiert für Augensteuerung und eingeschränkte Motorik |
| **Visuelle Badges** | „KI" (grün) und „MIC" (rot) zeigen aktive Features auf einen Blick |

### Telefonie-Integration

| Feature | Beschreibung |
|---------|-------------|
| **Virtuelles Mikrofon** | Sprachausgabe über VB-Cable o.ä. in Zoom, Teams, Telefon einspeisen |
| **Tipp-Geräusche** | Simuliert Tastaturklicks auf dem Mikrofon-Kanal während der Eingabe |
| **Echo-Test** | Mikrofon-Gerät direkt in den Einstellungen testen |
| **MIC-Badge** | Pulsierender Badge zeigt aktive Mikrofon-Ausgabe |

---

## Installation

### Entwicklermodus

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Backend starten
python backend_api.py

# 3. Frontend starten (separates Terminal)
cd electron-app
npm install
npm start
```

---

## Konfiguration

### ElevenLabs

ElevenLabs API-Key und Stimme in den **Einstellungen → Sprache** hinterlegen. Der Key wird lokal in `voice_models/.elevenlabs_config` gespeichert (nicht in der Versionskontrolle).

### Claude AI (für KI-Korrektur und Auto-Tagging)

Claude API-Key in den **Einstellungen → Allgemein** hinterlegen oder als Umgebungsvariable setzen:

```bash
CLAUDE_API_KEY=sk-ant-...
```

---

## Architektur

```
┌─────────────────────┐     HTTP/REST     ┌──────────────────────┐
│   Electron-App      │ ◄──────────────►  │   Python Backend     │
│   (Frontend)        │    Port 8765      │   (FastAPI/Uvicorn)  │
│                     │                   │                      │
│  • index.html       │                   │  • pyttsx3 (SAPI5)   │
│  • renderer.js      │                   │  • ElevenLabs API    │
│  • styles.css       │                   │  • Claude AI API     │
│  • preload.js       │                   │  • Whisper (Import)  │
│  • quick-access.html│                   │  • SQLite (Katalog)  │
└─────────────────────┘                   └──────────────────────┘
```

---

## Projektstruktur

```
fastspeak/
├── backend_api.py        # FastAPI-Server (alle REST-Endpunkte)
├── main.py               # TTS-Engine (ElevenLabs / pyttsx3)
├── catalog.py            # SQLite-Katalog
├── tag_generator.py      # Claude-basiertes Auto-Tagging
├── audio_processor.py    # Audio-Vorverarbeitung (Whisper-Import)
├── requirements.txt
└── electron-app/
    ├── main.js           # Electron-Hauptprozess
    ├── renderer.js       # Frontend-Logik
    ├── index.html        # Haupt-UI
    ├── quick-access.html # Schnellzugriff-Popup
    ├── i18n.js           # Übersetzungen (DE/EN)
    └── styles.css
```

---

## Systemanforderungen

- **OS**: Windows 10/11
- **Python**: 3.11+
- **RAM**: 4 GB (8 GB empfohlen)
- **Internet**: für ElevenLabs und Claude AI erforderlich
- **Optional**: VB-Cable für Telefonie-Integration

---

## Lizenz

MIT
