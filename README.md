# FastSpeak

Eine Text-to-Speech Anwendung mit Voice Cloning für Windows, optimiert für Barrierefreiheit (Eye-Tracking).

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## Features

- **XTTS v2 Voice Cloning** - Klone jede Stimme mit wenigen Sekunden Audio
- **Deutsche Sprachausgabe** - Optimiert für deutsche Texte
- **GPU-Beschleunigung** - Nutzt NVIDIA CUDA für schnelle Generierung
- **Stimmen speichern** - Voice-Modelle persistent speichern und laden
- **MP3-Export** - Generierte Sprache als MP3 speichern
- **Qualitäts-Presets** - Klar, Natürlich, Kreativ
- **Minimalistisches UI** - Clean Design, optimiert für Eye-Tracking

---

## Installation

### Voraussetzungen

- **Python 3.11** (empfohlen)
- **NVIDIA GPU** mit CUDA-Unterstützung (optional, aber empfohlen)
- **Windows 10/11** (andere Betriebssysteme möglich)
- **eSpeak NG** (für Phonem-Konvertierung)

### Schritt 1: Repository klonen

```bash
git clone https://github.com/username/fastspeak.git
cd fastspeak
```

### Schritt 2: Python-Umgebung erstellen

**Mit Conda (empfohlen):**

```bash
conda create -n fastspeak python=3.11
conda activate fastspeak
```

**Oder mit venv:**

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
```

### Schritt 3: PyTorch mit CUDA installieren

Für GPU-Beschleunigung (NVIDIA):

```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

Ohne GPU (nur CPU):

```bash
pip install torch torchvision torchaudio
```

### Schritt 4: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### Schritt 5: eSpeak NG installieren

**Windows:**

1. Download: https://github.com/espeak-ng/espeak-ng/releases
2. Installer ausführen (Standard-Pfad: `C:\Program Files\eSpeak NG`)
3. Der Pfad wird automatisch von FastSpeak erkannt

**Linux:**

```bash
sudo apt-get install espeak-ng
```

**macOS:**

```bash
brew install espeak-ng
```

### Schritt 6: Whisper für Artefakt-Entfernung (optional)

```bash
pip install openai-whisper
```

---

## Verwendung

### GUI starten

```bash
python gui.py
```

### Kommandozeile

```bash
python main.py
```

---

## Bedienung

### Grundfunktionen

1. **Text eingeben** - Im Textfeld den vorzulesenden Text eingeben
2. **Vorlesen** - Grüner Button startet die Sprachausgabe
3. **Stop** - Roter Button stoppt die Wiedergabe
4. **MP3 speichern** - Nach dem Vorlesen kann die Audio-Datei gespeichert werden

### Voice Cloning

1. **Stimme verwalten** → Button "Ändern" klicken
2. **Audio-Samples hochladen** - WAV/MP3-Dateien mit der Zielstimme (min. 6 Sekunden)
3. **Rauschunterdrückung** - Optional aktivieren für bessere Qualität
4. **Stimme speichern** - Modell unter einem Namen speichern
5. **Stimme laden** - Gespeicherte Stimmen können jederzeit geladen werden

### Qualitäts-Presets

| Preset | Beschreibung | Verwendung |
|--------|--------------|------------|
| **Klar** | Wenig Variation, sehr deutlich | Vorlesen von Dokumenten |
| **Natürlich** | Ausgewogene Betonung | Allgemeine Texte |
| **Kreativ** | Mehr Variation, expressiv | Geschichten, Dialoge |

---

## Systemanforderungen

### Minimum

- CPU: Intel Core i5 / AMD Ryzen 5
- RAM: 8 GB
- Speicher: 5 GB (für Modelle)

### Empfohlen

- GPU: NVIDIA RTX 3060 oder besser (8+ GB VRAM)
- RAM: 16 GB
- Speicher: 10 GB SSD

---

## Fehlerbehebung

### "espeak not found"

Stelle sicher, dass eSpeak NG installiert ist und im PATH liegt:

```bash
espeak --version
```

### CUDA nicht erkannt

Prüfe die PyTorch-CUDA-Installation:

```python
import torch
print(torch.cuda.is_available())
print(torch.cuda.get_device_name(0))
```

### Langsame Generierung

1. GPU-Beschleunigung aktivieren (CUDA)
2. Streaming-Modus in den erweiterten Einstellungen aktivieren
3. Kürzere Texte in mehreren Teilen generieren

### Audio-Artefakte am Ende

Die Whisper-basierte Artefakt-Entfernung ist standardmäßig aktiv. Bei Problemen:

```bash
pip install --upgrade openai-whisper
```

---

## Projektstruktur

```
fastspeak/
├── gui.py              # Grafische Benutzeroberfläche
├── main.py             # TTS-Engine (XTTS v2)
├── audio_processor.py  # Audio-Vorverarbeitung
├── requirements.txt    # Python-Abhängigkeiten
├── voice_models/       # Gespeicherte Stimmen
└── README.md           # Diese Datei
```

---

## Lizenz

MIT License - siehe LICENSE-Datei

---

## Danksagung

- [Coqui TTS](https://github.com/coqui-ai/TTS) - XTTS v2 Modell
- [OpenAI Whisper](https://github.com/openai/whisper) - Transkription
- [eSpeak NG](https://github.com/espeak-ng/espeak-ng) - Phonem-Konvertierung
