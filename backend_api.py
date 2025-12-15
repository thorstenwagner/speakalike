"""
SpeakAlike Backend API - FastAPI Server für Electron Frontend
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Windows Konsole auf UTF-8 setzen, um Unicode-Fehler zu vermeiden
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Falls reconfigure nicht verfügbar ist
from typing import Optional, List
from datetime import datetime

# Füge espeak-ng zum PATH hinzu
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

from main import TextToSpeech
from audio_processor import prepare_samples_for_cloning, get_audio_info
from catalog import MessageCatalog
from tag_generator import generate_tags

app = FastAPI(title="SpeakAlike API", version="1.0.0")

# CORS für Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globale Instanzen
tts: Optional[TextToSpeech] = None
catalog: Optional[MessageCatalog] = None
_whisper_model = None  # Lazy-loaded für Transkription

# Temporäre Audio-Dateien
TEMP_DIR = Path(tempfile.gettempdir()) / "speakalike"
TEMP_DIR.mkdir(exist_ok=True)

# Status-Tracking
current_status = {
    "is_speaking": False,
    "message": "Bereit",
    "progress": 0,
    "loading": True,  # True während TTS lädt
    "last_audio": None,
    "last_text": None
}

# History der letzten Nachrichten (unabhängig vom Katalog)
audio_history = []  # Liste von {"id": str, "text": str, "audio_path": str, "timestamp": str}


# === Models ===

class TTSRequest(BaseModel):
    text: str
    language: str = "de"


class VoiceModelInfo(BaseModel):
    name: str
    path: str
    sample_count: int
    created: Optional[str] = None


class CatalogMessage(BaseModel):
    id: int
    text: str
    audio_path: str
    duration: float
    voice_model: Optional[str]
    language: str
    is_favorite: bool
    created_at: str
    tags: List[str]


class SaveToCatalogRequest(BaseModel):
    tags: List[str] = []


class TagGenerateRequest(BaseModel):
    text: str
    num_tags: int = 5


# === Lifecycle ===

async def init_tts_async():
    """Lädt TTS Engine im Hintergrund"""
    global tts
    import asyncio
    
    current_status["message"] = "XTTS v2 Modell wird geladen..."
    current_status["loading"] = True
    
    # TTS in Thread Pool ausführen um Event Loop nicht zu blockieren
    loop = asyncio.get_event_loop()
    tts = await loop.run_in_executor(None, TextToSpeech)
    tts.headless_mode = True
    
    current_status["message"] = "Bereit"
    current_status["loading"] = False
    print("TTS Engine geladen und bereit!")


@app.on_event("startup")
async def startup():
    """Initialisiert Backend beim Start"""
    global catalog
    import asyncio
    
    # Katalog sofort laden (schnell)
    catalog = MessageCatalog()
    current_status["message"] = "Backend gestartet, TTS wird geladen..."
    
    # TTS im Hintergrund laden
    asyncio.create_task(init_tts_async())


# === Status Endpoints ===

@app.get("/api/status")
async def get_status():
    """Gibt aktuellen Status zurück"""
    return {
        **current_status,
        "gpu_available": tts.gpu_available if tts else False,
        "voice_loaded": tts.current_voice_name if tts else None
    }


# === TTS Endpoints ===

@app.post("/api/tts/speak")
async def speak(request: TTSRequest, background_tasks: BackgroundTasks):
    """Generiert Sprache aus Text"""
    global current_status
    
    if not tts or current_status.get("loading", False):
        raise HTTPException(status_code=503, detail="TTS wird noch geladen, bitte warten...")
    
    if current_status["is_speaking"]:
        raise HTTPException(status_code=409, detail="Generierung läuft bereits")
    
    current_status["is_speaking"] = True
    current_status["message"] = "Generiere Audio..."
    current_status["last_text"] = request.text
    
    try:
        # Generiere Audio und speichere
        audio_path = tts.speak_and_save(
            text=request.text,
            language=request.language
        )
        
        if audio_path and os.path.exists(audio_path):
            # Kopiere in temp Verzeichnis
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = TEMP_DIR / f"speech_{timestamp}.wav"
            shutil.copy(audio_path, dest_path)
            
            current_status["last_audio"] = str(dest_path)
            current_status["message"] = "Fertig"
            current_status["is_speaking"] = False
            
            # Zur History hinzufügen
            history_entry = {
                "id": timestamp,
                "text": request.text,
                "audio_path": str(dest_path),
                "audio_url": f"/api/audio/{dest_path.name}",
                "timestamp": datetime.now().isoformat()
            }
            audio_history.insert(0, history_entry)
            # Nur die letzten 10 behalten
            while len(audio_history) > 10:
                audio_history.pop()
            
            return {
                "success": True,
                "audio_path": str(dest_path),
                "audio_url": f"/api/audio/{dest_path.name}"
            }
        else:
            raise HTTPException(status_code=500, detail="Audio-Generierung fehlgeschlagen")
            
    except Exception as e:
        current_status["is_speaking"] = False
        current_status["message"] = f"Fehler: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/stop")
async def stop_speaking():
    """Stoppt die aktuelle Wiedergabe"""
    if tts:
        tts.stop()
    current_status["is_speaking"] = False
    current_status["message"] = "Gestoppt"
    return {"success": True}


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Liefert eine Audio-Datei"""
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio nicht gefunden")
    return FileResponse(file_path, media_type="audio/wav")


@app.get("/api/history")
async def get_history():
    """Gibt den Wiedergabe-Verlauf zurück (alle abgespielten Nachrichten in zeitlicher Reihenfolge)"""
    if catalog:
        history = catalog.get_playback_history(limit=10)
        result = []
        for item in history:
            result.append({
                "id": f"history_{item['id']}",
                "text": item["text"],
                "audio_url": item["audio_url"],
                "timestamp": item["played_at"],
                "in_catalog": item["catalog_id"] is not None,
                "catalog_id": item["catalog_id"]
            })
        return result
    return []


@app.post("/api/history/add")
async def add_to_history(text: str, audio_url: str, catalog_id: int = None):
    """Fügt einen Eintrag zum Wiedergabe-Verlauf hinzu"""
    if catalog:
        catalog.add_to_playback_history(text, audio_url, catalog_id)
    return {"status": "ok"}


# === Voice Model Endpoints ===

@app.get("/api/voice-models")
async def list_voice_models():
    """Listet alle verfügbaren Voice-Modelle (.pt Dateien)"""
    if not tts:
        return []
    
    # Nutze die eingebaute Methode aus main.py
    saved_models = tts.list_saved_voice_models()
    
    models = []
    for model in saved_models:
        models.append({
            "name": model['name'],
            "path": model['path'],
            "sample_count": 1,  # .pt Datei enthält bereits die Embeddings
            "is_active": tts.current_voice_name == model['name']
        })
    
    return models


@app.post("/api/voice-models/{name}/load")
async def load_voice_model(name: str):
    """Lädt ein Voice-Modell (.pt Datei)"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS nicht initialisiert")
    
    current_status["message"] = f"Lade Voice-Modell: {name}..."
    
    try:
        # Nutze die eingebaute load_voice_model Methode
        success = tts.load_voice_model(name)
        
        if not success:
            raise HTTPException(status_code=404, detail="Modell nicht gefunden oder konnte nicht geladen werden")
        
        current_status["message"] = f"Voice-Modell geladen: {name}"
        return {"success": True, "name": name}
        
    except Exception as e:
        current_status["message"] = f"Fehler: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice-models/create")
async def create_voice_model(
    name: str = Form(...),
    files: List[UploadFile] = File(...)
):
    """Erstellt ein neues Voice-Modell aus Audio-Samples"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS nicht initialisiert")
    
    model_dir = tts.VOICE_MODELS_DIR / name
    if model_dir.exists():
        raise HTTPException(status_code=409, detail="Modell existiert bereits")
    
    model_dir.mkdir(parents=True)
    
    try:
        saved_files = []
        for i, file in enumerate(files):
            file_path = model_dir / f"sample_{i+1}.wav"
            content = await file.read()
            file_path.write_bytes(content)
            saved_files.append(str(file_path))
        
        # Optimiere Samples
        current_status["message"] = "Optimiere Audio-Samples..."
        optimized = prepare_samples_for_cloning(saved_files, min_total_duration=10)
        
        # Berechne Speaker-Embeddings
        current_status["message"] = "Berechne Speaker-Embeddings..."
        tts.set_speaker_wav(optimized)
        
        # Speichere als .pt Voice-Modell
        current_status["message"] = "Speichere Voice-Modell..."
        model_path = tts.save_voice_model(name)
        
        if not model_path:
            raise Exception("Konnte Voice-Modell nicht speichern")
        
        # Aufräumen: Lösche den temporären Ordner mit den Samples
        if model_dir.exists():
            shutil.rmtree(model_dir)
        
        current_status["message"] = f"Voice-Modell '{name}' erstellt"
        
        return {
            "success": True,
            "name": name,
            "samples": len(optimized),
            "path": model_path
        }
        
    except Exception as e:
        # Cleanup bei Fehler
        if model_dir.exists():
            shutil.rmtree(model_dir)
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/voice-models/{name}")
async def delete_voice_model(name: str):
    """Löscht ein Voice-Modell"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS nicht initialisiert")
    
    model_path = tts.VOICE_MODELS_DIR / name
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Modell nicht gefunden")
    
    shutil.rmtree(model_path)
    
    if tts.current_voice_name == name:
        tts.current_voice_name = None
        tts.speaker_wav = None
    
    return {"success": True}


# === Catalog Endpoints ===

@app.get("/api/catalog")
async def list_catalog(
    search: Optional[str] = None,
    tags: Optional[str] = None,
    tag_mode: str = "and",
    favorites_only: bool = False,
    order_by: str = "created_at",
    limit: int = 50
):
    """Listet Katalog-Einträge"""
    if not catalog:
        return []
    
    # tags Parameter ist eine komma-separierte Liste
    tags_list = [t.strip() for t in tags.split(',')] if tags else None
    
    messages = catalog.search(
        query=search,
        tags=tags_list,
        tag_mode=tag_mode,
        favorites_only=favorites_only,
        order_by=order_by,
        limit=limit
    )
    
    return [
        {
            "id": m["id"],
            "text": m["text"],
            "audio_path": m["audio_path"],
            "duration": m.get("duration_seconds", 0),
            "voice_model": m.get("voice_model", ""),
            "language": "de",
            "is_favorite": bool(m.get("is_favorite", 0)),
            "created_at": m.get("created_at", ""),
            "tags": m.get("tags", [])
        }
        for m in messages
    ]


@app.post("/api/catalog/save")
async def save_to_catalog(request: SaveToCatalogRequest):
    """Speichert letzte Generierung im Katalog"""
    if not catalog or not tts:
        raise HTTPException(status_code=503, detail="Nicht initialisiert")
    
    if not current_status["last_audio"] or not current_status["last_text"]:
        raise HTTPException(status_code=400, detail="Keine Audio zum Speichern")
    
    audio_path = current_status["last_audio"]
    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio-Datei nicht gefunden")
    
    # Audio-Länge
    try:
        import soundfile as sf
        data, sr = sf.read(audio_path)
        duration = len(data) / sr
    except:
        duration = 0.0
    
    message_id = catalog.add_message(
        text=current_status["last_text"],
        source_audio_path=audio_path,
        duration_seconds=duration,
        voice_model=tts.current_voice_name,
        tags=request.tags
    )
    
    return {"success": True, "id": message_id}


@app.get("/api/catalog/{message_id}/audio")
async def get_catalog_audio(message_id: int):
    """Liefert Audio einer Katalog-Nachricht"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    messages = catalog.search()
    message = next((m for m in messages if m["id"] == message_id), None)
    
    if not message:
        raise HTTPException(status_code=404, detail="Nachricht nicht gefunden")
    
    if not os.path.exists(message["audio_path"]):
        raise HTTPException(status_code=404, detail="Audio nicht gefunden")
    
    return FileResponse(message["audio_path"], media_type="audio/wav")


@app.put("/api/catalog/{message_id}/favorite")
async def toggle_favorite(message_id: int):
    """Toggled Favoriten-Status"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    catalog.toggle_favorite(message_id)
    return {"success": True}


@app.put("/api/catalog/{message_id}/tags")
async def update_tags(message_id: int, tags: List[str]):
    """Aktualisiert Tags einer Nachricht"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    catalog.update_tags(message_id, tags)
    return {"success": True}


@app.delete("/api/catalog/{message_id}")
async def delete_message(message_id: int):
    """Löscht eine Katalog-Nachricht"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    catalog.delete_message(message_id)
    return {"success": True}


@app.post("/api/catalog/import")
async def import_audio(
    audio: UploadFile = File(...),
    text: str = Form(...),
    tags: str = Form("")
):
    """Importiert eine Audio-Datei in den Katalog"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    # Temporäre Datei erstellen
    suffix = Path(audio.filename).suffix.lower()
    if suffix not in ['.mp3', '.wav', '.ogg', '.m4a']:
        raise HTTPException(status_code=400, detail="Ungültiges Audio-Format")
    
    temp_path = TEMP_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    
    try:
        # Audio speichern
        with open(temp_path, 'wb') as f:
            content = await audio.read()
            f.write(content)
        
        # Audio-Info holen
        try:
            audio_info = get_audio_info(str(temp_path))
            duration = audio_info.get('duration', 0)
        except:
            duration = 0
        
        # Tags parsen
        tags_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
        
        # Zum Katalog hinzufügen
        message_id = catalog.add_message(
            text=text,
            source_audio_path=str(temp_path),
            tags=tags_list,
            voice_model="import",
            duration_seconds=duration
        )
        
        return {"success": True, "message_id": message_id}
        
    finally:
        # Temporäre Datei löschen
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transkribiert eine Audio-Datei mit Whisper"""
    import torch
    import torchaudio
    import numpy as np
    
    # Temporäre Datei erstellen
    suffix = Path(audio.filename).suffix.lower()
    if suffix not in ['.mp3', '.wav', '.ogg', '.m4a']:
        raise HTTPException(status_code=400, detail="Ungültiges Audio-Format")
    
    temp_path = TEMP_DIR / f"transcribe_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    
    try:
        # Audio speichern
        with open(temp_path, 'wb') as f:
            content = await audio.read()
            f.write(content)
        
        # Audio laden
        waveform, sample_rate = torchaudio.load(str(temp_path))
        
        # Mono konvertieren
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample zu 16kHz für Whisper
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
        
        audio_np = waveform.squeeze().numpy().astype(np.float32)
        
        # Normalisieren
        max_val = np.max(np.abs(audio_np))
        if max_val > 0:
            audio_np = audio_np / max_val
        
        # Whisper laden (lazy)
        try:
            import whisper
        except ImportError:
            raise HTTPException(status_code=503, detail="Whisper nicht installiert")
        
        # Globales Whisper-Modell
        global _whisper_model
        if '_whisper_model' not in globals() or _whisper_model is None:
            print("Lade Whisper-Modell für Transkription...")
            _whisper_model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")
            print("Whisper-Modell geladen.")
        
        # Transkribieren
        result = _whisper_model.transcribe(
            audio_np,
            language="de",
            fp16=torch.cuda.is_available(),
            verbose=False
        )
        
        return {"text": result.get("text", "").strip()}
        
    finally:
        if temp_path.exists():
            temp_path.unlink()


@app.get("/api/catalog/tags")
async def get_all_tags():
    """Listet alle Tags mit Häufigkeit"""
    if not catalog:
        return []
    
    return [{"name": t[0], "count": t[1]} for t in catalog.get_all_tags()]


# === Tag Generation ===

@app.post("/api/tags/generate")
async def generate_tags_endpoint(request: TagGenerateRequest):
    """Generiert Tags mit Claude AI"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    existing_tags = [t[0] for t in catalog.get_all_tags()]
    
    try:
        tags = generate_tags(
            text=request.text,
            existing_tags=existing_tags,
            num_tags=request.num_tags
        )
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Settings ===

@app.get("/api/settings")
async def get_settings():
    """Gibt TTS-Einstellungen zurück"""
    if not tts:
        return {}
    
    return {
        "temperature": tts.temperature,
        "speed": tts.speed,
        "top_k": tts.top_k,
        "top_p": tts.top_p,
        "repetition_penalty": tts.repetition_penalty
    }


@app.put("/api/settings")
async def update_settings(settings: dict):
    """Aktualisiert TTS-Einstellungen"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS nicht initialisiert")
    
    if "temperature" in settings:
        tts.temperature = settings["temperature"]
    if "speed" in settings:
        tts.speed = settings["speed"]
    if "top_k" in settings:
        tts.top_k = settings["top_k"]
    if "top_p" in settings:
        tts.top_p = settings["top_p"]
    if "repetition_penalty" in settings:
        # XTTS erfordert penalty > 1.0 und < 2.0
        penalty = min(max(float(settings["repetition_penalty"]), 1.01), 1.99)
        tts.repetition_penalty = penalty
    
    return {"success": True}


# === Main ===

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
