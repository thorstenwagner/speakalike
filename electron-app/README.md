# SpeakAlike Electron App

Moderne Desktop-Anwendung für Text-to-Speech mit Voice Cloning.

## Voraussetzungen

1. **Node.js** (v18+) - Download: https://nodejs.org/
2. **Python 3.11** mit allen TTS-Abhängigkeiten (bereits installiert)

## Installation

### 1. Node.js Abhängigkeiten installieren

```bash
cd electron-app
npm install
```

### 2. Backend starten

Das Backend startet automatisch mit der Electron-App, aber Sie können es auch separat starten:

```bash
cd ..
.\.conda-py311\python.exe backend_api.py
```

Das Backend läuft dann auf http://127.0.0.1:8765

### 3. Electron-App starten

```bash
cd electron-app
npm start
```

## Entwicklung

```bash
npm run dev  # Startet mit DevTools
```

## Build

```bash
npm run build:win  # Windows Installer erstellen
```

## Architektur

```
┌─────────────────────────────────────┐
│         Electron Frontend           │
│    (HTML/CSS/JavaScript)            │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      renderer.js              │  │
│  │  - UI Logik                   │  │
│  │  - API Calls                  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
              │ HTTP
              ▼
┌─────────────────────────────────────┐
│         Python Backend              │
│       (FastAPI + Uvicorn)           │
│                                     │
│  ┌───────────────────────────────┐  │
│  │      backend_api.py           │  │
│  │  - TTS Engine (XTTS v2)       │  │
│  │  - Voice Cloning              │  │
│  │  - Katalog (SQLite)           │  │
│  │  - Tag Generation (Claude)    │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## API Endpoints

| Endpoint | Methode | Beschreibung |
|----------|---------|--------------|
| `/api/status` | GET | Aktueller Status |
| `/api/tts/speak` | POST | Text vorlesen |
| `/api/tts/stop` | POST | Stopp |
| `/api/voice-models` | GET | Liste Voice-Modelle |
| `/api/voice-models/{name}/load` | POST | Modell laden |
| `/api/voice-models/create` | POST | Neues Modell erstellen |
| `/api/catalog` | GET | Katalog durchsuchen |
| `/api/catalog/save` | POST | Zum Katalog hinzufügen |
| `/api/tags/generate` | POST | Auto-Tags generieren |
| `/api/settings` | GET/PUT | Einstellungen |
