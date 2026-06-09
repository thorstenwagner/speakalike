# SpeakAlike

**Speech synthesis tool for eye-tracking control – with AI correction, mini mode, and telephony integration**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Electron](https://img.shields.io/badge/Electron-28-47848F.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Written by an ALS patient for other people with ALS (pwALS). SpeakAlike was built for people who communicate via eye-tracking.  I was frustrated by other commercial systems that were clearly developed for a different target group like older patients and rather not for power users. These programs use the entire screen and are hard to use while you are doing something else like gaming.

Speakalike uses ElevenLabs to convert text to natural-sounding speech including voice cloning and addresses many annoying things that come with communication by eyes:

- Typing by eye tracking is more error prone. Speakalike uses Claude to fix typos, add punctuation and addresses certain flaws of ElevenLabs like pronouncing numbers by converting numbers to text. The AI correction is robust enough to correct every sentence without double checking it - simply by using a toggle.

- You can define sets of messages you use often. I personally have one for everyday use like help requests, one for my kids and several for board and video games. You can quickly access them via the mini mode

- **Mini Mode** – a compact always-on-top, transparent overlay accessible at any time from within any program – and full **keyboard control** of all core functions via shortcuts and quick-access to your sets of predefined sets so mouse operation is never required.

- Other people are standing behind you and are reading what you are typing. This is so annoying. Therefore Speakalike comes with a **privacy mode** that blurs everything you type simply by one hotkey.


---

## Highlights

- **AI Correction** – Claude AI corrects eye-tracking typos without adding extra words
- **ElevenLabs TTS** – natural-sounding cloud voices (multiple models and voices selectable)
- **Mini Mode** – compact always-on-top window, ideal for use alongside other apps
- **Microphone Output** – feed speech into Zoom, Teams or phone calls via virtual audio cable
- **A–Z Quick Access** – recall up to 26 phrases instantly with a single key
- **Privacy Mode** – input is hidden, only the last character remains visible

---

## Features

### Speech Synthesis

| Feature | Description |
|---------|-------------|
| **ElevenLabs (Cloud)** | Natural-sounding voices; models: Multilingual v2/v3, Flash v2.5, Turbo v2.5 |
| **pyttsx3 (Offline)** | System voices via Windows SAPI5, no internet required |
| **Dual Output** | Simultaneous output to speakers and virtual microphone |
| **Volume Control** | Mute and adjust volume via slider |

### AI Correction (Claude)

| Feature | Description |
|---------|-------------|
| **Auto Correction** | Missing/wrong characters are completed, no content changes |
| **Conversation Context** | Recent messages and a freely editable context field are included |
| **Confirmation Dialog** | Review and edit the AI suggestion before speaking |
| **Model Selection** | Claude Haiku 4.5 (fast) or Claude Sonnet 4.6 (more precise) |

### Keyboard Shortcuts

| Shortcut | Function |
|----------|----------|
| **Enter** | Speak text (empty field: repeat last message) |
| **A–Z + Enter** | Play quick-access phrase for that letter |
| **Ctrl+Enter** | Trigger AI completion |
| **Ctrl+Shift+Enter** | Toggle AI mode permanently on/off |
| **Ctrl+S** | Generate audio and add to quick access |
| **Ctrl+L** | Switch language |
| **Ctrl+D** | Play signal tone |
| **Ctrl+Shift+D** | Toggle pre-signal mode |
| **Ctrl+P** | Toggle privacy mode |
| **Ctrl+M** | Toggle mini mode |
| **Escape** | Close dialogs |

### Quick Access (A–Z)

- Up to **26 phrases** (A to Z) storable as quick access
- Triggered by typing the letter + Enter in the text field
- **Sets** – save and load different sets for different situations
- Add phrases from the catalog or directly via `Ctrl+S`

### Catalog

| Feature | Description |
|---------|-------------|
| **Message Catalog** | Store frequently used phrases with audio, tags and metadata |
| **Auto-Tagging** | Claude AI automatically generates suitable tags |
| **Tag Filter** | AND/OR filtering by any number of tags |
| **Favorites** | Mark phrases for quick access |
| **Play Counter** | Shows most frequently used phrases |
| **Audio Import** | Import MP3/WAV/OGG with automatic transcription (Whisper) |

### Accessibility & Mini Mode

| Feature | Description |
|---------|-------------|
| **Mini Mode** | Compact always-on-top overlay (`Ctrl+M`), position top/bottom selectable |
| **Privacy Mode** | Input hidden, only last character visible (`Ctrl+P`) |
| **Large Controls** | Optimised for eye-tracking and limited motor control |
| **Visual Badges** | "AI" (green) and "MIC" (red) show active features at a glance |

### Telephony Integration

| Feature | Description |
|---------|-------------|
| **Virtual Microphone** | Feed speech into Zoom, Teams or phone via VB-Cable or similar |
| **Typing Sounds** | Simulates keyboard clicks on the microphone channel during input |
| **Echo Test** | Test the microphone device directly in settings |
| **MIC Badge** | Pulsing badge indicates active microphone output |

---

## Installation

### Developer Mode

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start backend
python backend_api.py

# 3. Start frontend (separate terminal)
cd electron-app
npm install
npm start
```

---

## Configuration

### ElevenLabs

Add your ElevenLabs API key and voice in **Settings → Voice**. The key is stored locally in `voice_models/.elevenlabs_config` (not tracked by version control).

### Claude AI (for AI correction and auto-tagging)

Add your Claude API key in **Settings → General** or set it as an environment variable:

```bash
CLAUDE_API_KEY=sk-ant-...
```

---

## Architecture

```
┌─────────────────────┐     HTTP/REST     ┌──────────────────────┐
│   Electron App      │ ◄──────────────►  │   Python Backend     │
│   (Frontend)        │    Port 8765      │   (FastAPI/Uvicorn)  │
│                     │                   │                      │
│  • index.html       │                   │  • pyttsx3 (SAPI5)   │
│  • renderer.js      │                   │  • ElevenLabs API    │
│  • styles.css       │                   │  • Claude AI API     │
│  • preload.js       │                   │  • Whisper (Import)  │
│  • quick-access.html│                   │  • SQLite (Catalog)  │
└─────────────────────┘                   └──────────────────────┘
```

---

## Project Structure

```
fastspeak/
├── backend_api.py        # FastAPI server (all REST endpoints)
├── main.py               # TTS engine (ElevenLabs / pyttsx3)
├── catalog.py            # SQLite catalog
├── tag_generator.py      # Claude-based auto-tagging
├── audio_processor.py    # Audio preprocessing (Whisper import)
├── requirements.txt
└── electron-app/
    ├── main.js           # Electron main process
    ├── renderer.js       # Frontend logic
    ├── index.html        # Main UI
    ├── quick-access.html # Quick access popup
    ├── i18n.js           # Translations (DE/EN)
    └── styles.css
```

---

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.11+
- **RAM**: 4 GB (8 GB recommended)
- **Internet**: required for ElevenLabs and Claude AI
- **Optional**: VB-Cable for telephony integration

---

## License

MIT

