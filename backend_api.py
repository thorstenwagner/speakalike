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

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Lazy import: TextToSpeech wird erst beim TTS-Start geladen, nicht beim Serverstart
# from main import TextToSpeech  # -> wird in init_tts_async() importiert
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
tts = None
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


class SwitchTTSModelRequest(BaseModel):
    model_id: str
    num_tags: int = 5


class SentenceCompletionRequest(BaseModel):
    text: str
    model: str = "claude-haiku-4-5-20251001"
    language: str = "de"
    context: str = ""
    recent_messages: list = []


# === Lifecycle ===

async def init_tts_async():
    """Lädt TTS Engine im Hintergrund"""
    global tts
    import asyncio
    import time
    
    current_status["message"] = "TTS-Bibliotheken werden geladen..."
    current_status["loading"] = True
    
    start_time = time.time()
    
    # TTS in Thread Pool ausführen um Event Loop nicht zu blockieren
    loop = asyncio.get_event_loop()
    
    def create_tts():
        from main import TextToSpeech
        return TextToSpeech()
    
    tts = await loop.run_in_executor(None, create_tts)
    tts.headless_mode = True
    
    elapsed = time.time() - start_time
    current_status["message"] = "Bereit"
    current_status["loading"] = False
    print(f"TTS Engine geladen und bereit! ({elapsed:.1f}s)")


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
        "voice_loaded": tts.current_voice_name if tts else None,
        "tts_model": tts.current_tts_model_id if tts else "xtts_v2",
        "tts_provider": tts.tts_provider if tts else "coqui",
        "elevenlabs_configured": bool(tts.elevenlabs_api_key) if tts else False
    }


# === TTS Model Endpoints ===

@app.get("/api/tts/models")
async def get_tts_models():
    """Gibt alle verfügbaren TTS-Modelle zurück"""
    if not tts:
        # Fallback: Gib statische Liste zurück
        from main import TextToSpeech
        return {
            "models": TextToSpeech.AVAILABLE_TTS_MODELS,
            "current_model": "xtts_v2"
        }
    
    return {
        "models": tts.get_available_tts_models(),
        "current_model": tts.current_tts_model_id
    }


@app.post("/api/tts/models/switch")
async def switch_tts_model(request: SwitchTTSModelRequest):
    """Wechselt zu einem anderen TTS-Modell"""
    global current_status
    
    if not tts or current_status.get("loading", False):
        raise HTTPException(status_code=503, detail="TTS wird noch geladen, bitte warten...")
    
    if current_status["is_speaking"]:
        raise HTTPException(status_code=409, detail="Generierung läuft bereits")
    
    current_status["message"] = f"Wechsle zu {request.model_id}..."
    current_status["loading"] = True
    
    try:
        success = tts.switch_tts_model(request.model_id)
        
        current_status["loading"] = False
        
        if success:
            current_status["message"] = "Bereit"
            return {
                "success": True,
                "model_id": tts.current_tts_model_id,
                "model_info": tts.AVAILABLE_TTS_MODELS.get(tts.current_tts_model_id, {})
            }
        else:
            current_status["message"] = "Fehler beim Modellwechsel"
            raise HTTPException(status_code=500, detail="Modellwechsel fehlgeschlagen")
            
    except Exception as e:
        current_status["loading"] = False
        current_status["message"] = f"Fehler: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))


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


# Mikrofon-Ausgabe: Zweites Ausgabegerät (z.B. VB-Cable) für Telefonie
mic_output_device = None  # Device-Index für Mikrofon-Ausgabe
mic_output_enabled = False  # Ob Mikrofon-Ausgabe aktiv ist

@app.post("/api/tts/play-audio")
async def play_audio_on_device(data: dict):
    """Spielt eine Audio-Datei auf dem ausgewählten Gerät ab"""
    try:
        import sounddevice as sd
        import soundfile as sf
        import threading
        
        audio_url = data.get("audio_url", "")
        file_path = None
        
        # Prüfe ob es eine Katalog-URL ist
        if "/api/catalog/" in audio_url and "/audio" in audio_url:
            # Extrahiere message_id aus URL wie /api/catalog/123/audio
            parts = audio_url.split("/")
            try:
                message_id = int(parts[-2])
                messages = catalog.search() if catalog else []
                message = next((m for m in messages if m["id"] == message_id), None)
                if message and os.path.exists(message["audio_path"]):
                    file_path = Path(message["audio_path"])
            except (ValueError, IndexError):
                pass
        else:
            # Normale Audio-URL aus TEMP_DIR
            filename = audio_url.split("/")[-1] if "/" in audio_url else audio_url
            file_path = TEMP_DIR / filename
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio nicht gefunden")
        
        # Audio laden und abspielen
        audio_data, samplerate = sf.read(str(file_path))
        device = tts.output_device if tts else None
        
        # Lautstärke anwenden
        volume = data.get("volume", 1.0)
        if isinstance(volume, (int, float)) and 0 <= volume <= 1:
            audio_data = audio_data * volume
        
        import numpy as np
        
        def resample_audio(audio, orig_sr, target_sr):
            """Einfaches Resampling per Interpolation"""
            if orig_sr == target_sr:
                return audio
            ratio = target_sr / orig_sr
            n_samples = int(len(audio) * ratio)
            indices = np.arange(n_samples) / ratio
            indices = np.clip(indices, 0, len(audio) - 1)
            return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
        
        def get_device_samplerate(dev_index):
            """Gibt die native Samplerate eines Geräts zurück"""
            if dev_index is None:
                return None
            try:
                dev_info = sd.query_devices(dev_index)
                return int(dev_info['default_samplerate'])
            except:
                return None
        
        # Gleichzeitig auf Lautsprecher UND Mikrofon-Gerät abspielen
        print(f"[Audio-Play] mic_output_enabled={mic_output_enabled}, mic_output_device={mic_output_device}, samplerate={samplerate}")
        
        if mic_output_enabled and mic_output_device is not None:
            # Mono konvertieren falls Stereo (für Mic-Ausgabe)
            if len(audio_data.shape) > 1:
                mic_audio = audio_data.mean(axis=1)
            else:
                mic_audio = audio_data.copy()
            
            mic_audio = mic_audio.astype(np.float32)
            
            # Lautsprecher: Resample falls nötig und sd.play (non-blocking)
            try:
                speaker_sr = get_device_samplerate(device)
                speaker_data = audio_data
                play_sr = samplerate
                if speaker_sr and speaker_sr != samplerate:
                    # Resample für Mono/Stereo
                    if len(audio_data.shape) > 1:
                        speaker_data = np.column_stack([
                            resample_audio(audio_data[:, ch], samplerate, speaker_sr)
                            for ch in range(audio_data.shape[1])
                        ])
                    else:
                        speaker_data = resample_audio(audio_data, samplerate, speaker_sr)
                    play_sr = speaker_sr
                    print(f"[Audio-Play] Lautsprecher resampled: {samplerate} -> {speaker_sr} Hz")
                sd.play(speaker_data, play_sr, device=device)
                print(f"[Audio-Play] Lautsprecher-Wiedergabe gestartet (device={device}, sr={play_sr})")
            except Exception as e:
                print(f"[Audio-Play] Lautsprecher sd.play Fehler: {e}")
                # Fallback: ohne explizites Device
                try:
                    sd.play(audio_data, samplerate)
                    print(f"[Audio-Play] Lautsprecher Fallback (Standard-Device) ok")
                except Exception as e2:
                    print(f"[Audio-Play] Auch Lautsprecher Fallback fehlgeschlagen: {e2}")
            
            # Mikrofon-Ausgabe auf separatem Thread
            def play_on_mic():
                nonlocal mic_audio, samplerate
                
                # Resample für Mic-Device falls nötig
                mic_sr = get_device_samplerate(mic_output_device)
                mic_play_sr = samplerate
                if mic_sr and mic_sr != samplerate:
                    mic_audio = resample_audio(mic_audio, samplerate, mic_sr)
                    mic_play_sr = mic_sr
                    print(f"[Audio-Play] Mic resampled: {samplerate} -> {mic_sr} Hz")
                
                # Versuch 1: sd.play (einfachster Weg, funktionierte als Fallback)
                try:
                    sd.play(mic_audio, mic_play_sr, device=mic_output_device)
                    sd.wait()
                    print(f"[Audio-Play] Mikrofon-Ausgabe via sd.play erfolgreich (device={mic_output_device}, sr={mic_play_sr})")
                    return
                except Exception as e1:
                    print(f"[Audio-Play] sd.play fehlgeschlagen (device={mic_output_device}): {e1}")
                
                # Versuch 2: OutputStream
                try:
                    mic_stream = sd.OutputStream(
                        samplerate=mic_play_sr,
                        channels=1,
                        device=mic_output_device
                    )
                    mic_stream.start()
                    mic_stream.write(mic_audio.reshape(-1, 1))
                    mic_stream.stop()
                    mic_stream.close()
                    print(f"[Audio-Play] Mikrofon-Ausgabe erfolgreich (OutputStream)")
                    return
                except Exception as e2:
                    print(f"[Audio-Play] OutputStream fehlgeschlagen: {e2}")
                
                # Versuch 3: Alternatives Device mit kompatibler Host-API
                try:
                    target_name = None
                    all_devices = sd.query_devices()
                    if mic_output_device < len(all_devices):
                        target_name = all_devices[mic_output_device]['name'].split(',')[0].strip()
                    
                    if target_name:
                        host_apis = sd.query_hostapis()
                        for idx, dev in enumerate(all_devices):
                            if idx == mic_output_device:
                                continue
                            if dev['max_output_channels'] <= 0:
                                continue
                            dev_base = dev['name'].split(',')[0].strip()
                            if dev_base == target_name:
                                api_name = host_apis[dev.get('hostapi', 0)]['name'].lower()
                                if 'wdm' not in api_name and 'ks' not in api_name:
                                    alt_sr = int(dev['default_samplerate'])
                                    alt_audio = resample_audio(mic_audio, mic_play_sr, alt_sr) if alt_sr != mic_play_sr else mic_audio
                                    print(f"[Audio-Play] Versuche alternatives Device {idx} ({dev['name']}, API: {api_name}, sr={alt_sr})")
                                    sd.play(alt_audio, alt_sr, device=idx)
                                    sd.wait()
                                    print(f"[Audio-Play] Mikrofon-Ausgabe über alternatives Device {idx} erfolgreich")
                                    return
                except Exception as e3:
                    print(f"[Audio-Play] Alle Mic-Fallbacks fehlgeschlagen: {e3}")
            
            threading.Thread(target=play_on_mic, daemon=True).start()
        else:
            # Nur Lautsprecher (kein Mic konfiguriert oder deaktiviert)
            try:
                speaker_sr = get_device_samplerate(device)
                play_data = audio_data
                play_sr = samplerate
                if speaker_sr and speaker_sr != samplerate:
                    if len(audio_data.shape) > 1:
                        play_data = np.column_stack([
                            resample_audio(audio_data[:, ch], samplerate, speaker_sr)
                            for ch in range(audio_data.shape[1])
                        ])
                    else:
                        play_data = resample_audio(audio_data, samplerate, speaker_sr)
                    play_sr = speaker_sr
                    print(f"[Audio-Play] Lautsprecher resampled: {samplerate} -> {speaker_sr} Hz")
                sd.play(play_data, play_sr, device=device)
            except Exception as e:
                print(f"[Audio-Play] Lautsprecher Fehler: {e}, versuche Standard-Device...")
                try:
                    default_sr = get_device_samplerate(None)
                    if default_sr and default_sr != samplerate:
                        if len(audio_data.shape) > 1:
                            play_data = np.column_stack([
                                resample_audio(audio_data[:, ch], samplerate, default_sr)
                                for ch in range(audio_data.shape[1])
                            ])
                        else:
                            play_data = resample_audio(audio_data, samplerate, default_sr)
                        sd.play(play_data, default_sr)
                    else:
                        sd.play(audio_data, samplerate)
                except Exception as e2:
                    print(f"[Audio-Play] Auch Fallback fehlgeschlagen: {e2}")
            if not mic_output_enabled:
                print(f"[Audio-Play] Mikrofon-Ausgabe deaktiviert (🎤 Button nicht aktiv)")
            elif mic_output_device is None:
                print(f"[Audio-Play] Kein Mikrofon-Gerät konfiguriert")
        
        return {"success": True, "device": device, "mic_device": mic_output_device if mic_output_enabled else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/stop")
async def stop_speaking():
    """Stoppt die aktuelle Wiedergabe"""
    import sounddevice as sd
    sd.stop()  # Stoppe auch sounddevice Wiedergabe
    if tts:
        tts.stop()
    current_status["is_speaking"] = False
    current_status["message"] = "Gestoppt"
    return {"success": True}


@app.get("/api/typing-sound")
async def get_typing_sound():
    """Liefert die Typing-Sound MP3-Datei"""
    sound_path = Path(os.path.dirname(os.path.abspath(__file__))) / "electron-app" / "typing-sound.mp3"
    if not sound_path.exists():
        raise HTTPException(status_code=404, detail="typing-sound.mp3 nicht gefunden")
    return FileResponse(str(sound_path), media_type="audio/mpeg")


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
        history = catalog.get_playback_history(limit=50)
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
            "sample_count": model.get('sample_count', 1),
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
    
    # Voice-Modelle sind .pt Dateien
    model_path = tts.VOICE_MODELS_DIR / f"{name}.pt"
    if not model_path.exists():
        raise HTTPException(status_code=404, detail=f"Modell '{name}' nicht gefunden")
    
    # Datei löschen (nicht Verzeichnis)
    model_path.unlink()
    
    if tts.current_voice_name == name:
        tts.current_voice_name = None
        tts.speaker_wav = None
        tts.gpt_cond_latent = None
        tts.speaker_embedding = None
    
    return {"success": True, "message": f"Modell '{name}' gelöscht"}


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
            "audio_url": f"/api/catalog/{m['id']}/audio" if m.get("audio_path") else None,
            "duration": m.get("duration_seconds", 0),
            "voice_model": m.get("voice_model", ""),
            "language": "de",
            "is_favorite": bool(m.get("is_favorite", 0)),
            "play_count": m.get("play_count", 0),
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


@app.post("/api/catalog/{message_id}/play")
async def increment_play_count(message_id: int):
    """Erhöht den Play-Count einer Katalog-Nachricht"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    catalog.update_play_count(message_id)
    return {"success": True}


@app.put("/api/catalog/{message_id}")
async def update_catalog_message(message_id: int, request: dict):
    """Aktualisiert eine Katalog-Nachricht (z.B. is_favorite)"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Katalog nicht initialisiert")
    
    if "is_favorite" in request:
        catalog.set_favorite(message_id, request["is_favorite"])
    
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


# === Sentence Completion with Claude AI ===

@app.post("/api/ai/complete-sentence")
async def complete_sentence_endpoint(
    request: SentenceCompletionRequest,
    x_api_key: Optional[str] = Header(None)
):
    """Vervollständigt unvollständige Sätze mit Claude AI"""
    import anthropic
    
    prompt_file = f"prompt_{request.language}.txt"
    prompt_path = Path(__file__).parent / prompt_file
    if not prompt_path.exists():
        prompt_path = Path(__file__).parent / "prompt_de.txt"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    # Dynamischen Kontext einfügen, falls vorhanden
    if request.context:
        context_line = f"Aktueller Gesprächskontext: {request.context}. Berücksichtige diesen Kontext bei der Vervollständigung, aber der Nutzer kann auch Dinge sagen, die nicht direkt zum Kontext passen."
        system_prompt = system_prompt.replace("{DYNAMIC_CONTEXT}", context_line)
    else:
        system_prompt = system_prompt.replace("{DYNAMIC_CONTEXT}", "")

    try:
        # API Key aus Header oder Umgebungsvariable
        api_key = x_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="API Key nicht gesetzt")
        
        print(f"[AI] Anfrage: text='{request.text[:50]}...', model={request.model}, language={request.language}")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Nur erlaubte Modelle zulassen
        allowed_models = ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"]
        model = request.model if request.model in allowed_models else "claude-haiku-4-5-20251001"
        
        # Versuche mit gewähltem Modell, bei Refusal Fallback auf Haiku
        models_to_try = [model]
        if model != "claude-haiku-4-5-20251001":
            models_to_try.append("claude-haiku-4-5-20251001")
        
        for try_model in models_to_try:
            print(f"[AI] Sende an Claude (model={try_model})...")
            
            # Nachrichten aufbauen: vorherige Nachrichten als Kontext + aktuelle Anfrage
            messages = []
            for msg in request.recent_messages:
                messages.append({"role": "user", "content": msg})
                messages.append({"role": "assistant", "content": msg})
            messages.append({"role": "user", "content": f"Bitte vervollständige folgenden abgekürzten Text: {request.text}"})
            
            message = client.messages.create(
                model=try_model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            
            print(f"[AI] Antwort: stop_reason={message.stop_reason}, content_blocks={len(message.content)}")
            
            # Bei Verweigerung: nächstes Modell versuchen
            if message.stop_reason == 'refusal' or not message.content:
                print(f"[AI] {try_model} hat verweigert/leer, versuche Fallback...")
                continue
            
            # Ersten Text-Block finden
            completed_text = None
            for block in message.content:
                if hasattr(block, 'text'):
                    completed_text = block.text.strip()
                    break
            
            if completed_text:
                print(f"[AI] Ergebnis ({try_model}): '{completed_text[:80]}'")
                return {"original": request.text, "completed": completed_text}
        
        # Alle Modelle haben verweigert – Originaltext zurückgeben
        print(f"[AI] Alle Modelle haben verweigert. Gebe Originaltext zurück.")
        return {"original": request.text, "completed": request.text, "refusal": True}
        
    except HTTPException:
        raise
    except anthropic.AuthenticationError:
        print("[AI] FEHLER: API Key ungültig")
        raise HTTPException(status_code=401, detail="API Key ungültig")
    except anthropic.RateLimitError:
        print("[AI] FEHLER: Rate Limit erreicht")
        raise HTTPException(status_code=429, detail="Rate Limit erreicht")
    except Exception as e:
        print(f"[AI] FEHLER: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Claude API Fehler: {str(e)}")


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


# === Audio Devices ===

@app.get("/api/audio-devices")
async def get_audio_devices():
    """Gibt Liste der verfügbaren Ausgabegeräte zurück"""
    try:
        import sounddevice as sd
        devices = []
        seen_names = {}  # base_name -> (index, hostapi_priority)
        device_list = sd.query_devices()
        host_apis = sd.query_hostapis()
        
        # Host-API Prioritäten: WASAPI > MME > DirectSound > Rest
        # WDM-KS wird vermieden (unterstützt kein blocking API)
        def hostapi_priority(hostapi_index):
            name = host_apis[hostapi_index]['name'].lower() if hostapi_index < len(host_apis) else ''
            if 'wasapi' in name:
                return 0  # Beste Wahl
            elif 'mme' in name:
                return 1
            elif 'directsound' in name:
                return 2
            elif 'wdm' in name or 'ks' in name:
                return 99  # Vermeiden - unterstützt kein blocking API
            return 3
        
        for i, device in enumerate(device_list):
            # Nur Ausgabegeräte (max_output_channels > 0)
            if device['max_output_channels'] > 0:
                # Gerätenamen bereinigen und deduplizieren
                name = device['name']
                # Nur den Hauptnamen verwenden (vor API-Typ wie "MME", "Windows DirectSound" etc.)
                base_name = name.split(',')[0].strip() if ',' in name else name
                
                priority = hostapi_priority(device.get('hostapi', 0))
                
                # Überspringe wenn wir dieses Gerät schon haben mit besserer Priorität
                if base_name in seen_names:
                    existing_priority = seen_names[base_name]['priority']
                    if priority >= existing_priority:
                        continue
                
                seen_names[base_name] = {
                    'priority': priority,
                    'device': {
                        'index': i,
                        'name': name,
                        'channels': device['max_output_channels'],
                        'samplerate': device['default_samplerate']
                    }
                }
        
        devices = [v['device'] for v in seen_names.values()]
        return {"devices": devices, "current": tts.output_device if tts else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/audio-device")
async def set_audio_device(device: dict):
    """Setzt das Ausgabegerät"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS nicht initialisiert")
    
    device_index = device.get("index")
    # None = Standard-Gerät
    tts.output_device = device_index if device_index != -1 else None
    return {"success": True, "device": tts.output_device}


# === Mikrofon-Ausgabe (für Telefonie) ===

@app.get("/api/mic-device")
async def get_mic_device():
    """Gibt das aktuelle Mikrofon-Ausgabegerät und Status zurück"""
    return {
        "device": mic_output_device,
        "enabled": mic_output_enabled
    }


@app.put("/api/mic-device")
async def set_mic_device(data: dict):
    """Setzt das Mikrofon-Ausgabegerät (z.B. VB-Cable)"""
    global mic_output_device, mic_output_enabled
    
    device_index = data.get("index")
    mic_output_device = device_index if device_index is not None and device_index != -1 else None
    
    if "enabled" in data:
        mic_output_enabled = bool(data["enabled"])
    
    return {"success": True, "device": mic_output_device, "enabled": mic_output_enabled}


@app.put("/api/mic-device/toggle")
async def toggle_mic_output(data: dict = {}):
    """Schaltet Mikrofon-Ausgabe ein/aus"""
    global mic_output_enabled
    
    if "enabled" in data:
        mic_output_enabled = bool(data["enabled"])
    else:
        mic_output_enabled = not mic_output_enabled
    
    return {"success": True, "enabled": mic_output_enabled, "device": mic_output_device}


# === Tipp-Geräusch über Mikrofon ===
_typing_thread = None
_typing_active = False
_typing_audio_data = None  # Geladene Tastatur-Aufnahme
_typing_audio_sr = None

def _load_typing_sound():
    """Lädt die Tastatur-Sound-Datei"""
    global _typing_audio_data, _typing_audio_sr
    if _typing_audio_data is not None:
        return True
    
    import soundfile as sf
    from pathlib import Path
    
    sound_path = Path(__file__).parent / "electron-app" / "typing-sound.mp3"
    if not sound_path.exists():
        print(f"[Typing-Mic] Sound-Datei nicht gefunden: {sound_path}")
        return False
    
    try:
        # MP3 laden (soundfile kann mp3 über libsndfile lesen)
        data, sr = sf.read(str(sound_path), dtype='float32')
        # Mono konvertieren
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        _typing_audio_data = data
        _typing_audio_sr = sr
        print(f"[Typing-Mic] Sound geladen: {len(data)/sr:.2f}s, {sr} Hz")
        return True
    except Exception as e:
        print(f"[Typing-Mic] Fehler beim Laden: {e}")
        # Fallback: mit pydub probieren
        try:
            from pydub import AudioSegment
            import numpy as np
            
            audio = AudioSegment.from_mp3(str(sound_path))
            audio = audio.set_channels(1)
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples /= 32768.0
            _typing_audio_data = samples
            _typing_audio_sr = audio.frame_rate
            print(f"[Typing-Mic] Sound via pydub geladen: {len(samples)/audio.frame_rate:.2f}s, {audio.frame_rate} Hz")
            return True
        except Exception as e2:
            print(f"[Typing-Mic] Auch pydub Fallback fehlgeschlagen: {e2}")
            return False

def _typing_loop():
    """Spielt zufällige Ausschnitte der Tastatur-Aufnahme auf dem Mic-Device ab"""
    import sounddevice as sd
    import numpy as np
    import time
    import random
    global _typing_active
    
    device = mic_output_device
    if device is None:
        return
    
    if not _load_typing_sound():
        print("[Typing-Mic] Kein Sound verfügbar, verwende synthetisch")
        return
    
    audio = _typing_audio_data
    sr = _typing_audio_sr
    
    # Samplerate des Mic-Geräts ermitteln
    try:
        dev_info = sd.query_devices(device)
        dev_sr = int(dev_info['default_samplerate'])
    except:
        dev_sr = sr
    
    # Resample wenn nötig
    if dev_sr != sr:
        ratio = dev_sr / sr
        n_samples = int(len(audio) * ratio)
        indices = np.arange(n_samples) / ratio
        indices = np.clip(indices, 0, len(audio) - 1)
        audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
        sr = dev_sr
    
    print(f"[Typing-Mic] Tipp-Sound gestartet auf Device {device} ({sr} Hz)")
    
    try:
        while _typing_active:
            # Zufälligen Ausschnitt wählen (60-120ms Clip)
            clip_duration = 0.06 + random.random() * 0.06
            clip_samples = int(sr * clip_duration)
            max_start = max(0, len(audio) - clip_samples - int(sr * 0.1))
            start = random.randint(0, max_start) if max_start > 0 else 0
            
            clip = audio[start:start + clip_samples].copy()
            
            # Fade-Out (letzte 20%)
            fade_len = int(len(clip) * 0.2)
            if fade_len > 0:
                clip[-fade_len:] *= np.linspace(1, 0, fade_len)
            
            # Lautstärke-Variation
            clip *= 0.3 + random.random() * 0.2
            
            # Stille-Pause zwischen Klicks (60-130ms)
            gap = int(sr * (0.06 + random.random() * 0.07))
            chunk = np.concatenate([clip, np.zeros(gap, dtype=np.float32)])
            
            try:
                sd.play(chunk, sr, device=device)
                sd.wait()
            except:
                time.sleep(0.085)
    except Exception as e:
        print(f"[Typing-Mic] Fehler: {e}")
    
    print(f"[Typing-Mic] Tipp-Sound gestoppt")

@app.post("/api/mic-device/typing/start")
async def start_typing_on_mic():
    """Startet Tipp-Geräusch auf dem Mikrofon-Ausgabegerät"""
    global _typing_thread, _typing_active
    import threading
    
    if not mic_output_enabled or mic_output_device is None:
        return {"success": False, "reason": "Mikrofon-Ausgabe nicht aktiv"}
    
    if _typing_active:
        return {"success": True, "already_running": True}
    
    _typing_active = True
    _typing_thread = threading.Thread(target=_typing_loop, daemon=True)
    _typing_thread.start()
    return {"success": True}

@app.post("/api/mic-device/typing/stop")
async def stop_typing_on_mic():
    """Stoppt Tipp-Geräusch auf dem Mikrofon-Ausgabegerät"""
    global _typing_active, _typing_thread
    _typing_active = False
    if _typing_thread:
        _typing_thread.join(timeout=1)
        _typing_thread = None
    return {"success": True}


@app.post("/api/mic-device/echo-test")
async def mic_echo_test():
    """Spielt einen Testton auf dem Mikrofon-Ausgabegerät ab und nimmt ihn gleichzeitig auf,
    dann gibt er das aufgenommene Audio auf dem Lautsprecher wieder."""
    import sounddevice as sd
    import numpy as np
    import threading
    
    if mic_output_device is None:
        raise HTTPException(status_code=400, detail="Kein Mikrofon-Gerät konfiguriert")
    
    sample_rate = 24000
    duration = 1.5  # Sekunden
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    
    # Erkennbarer Testton: drei aufsteigende Töne (Ding-Ding-Ding)
    tone = np.zeros_like(t)
    freqs = [523.25, 659.25, 783.99]  # C5, E5, G5
    note_len = int(sample_rate * 0.4)
    gap_len = int(sample_rate * 0.05)
    for i, freq in enumerate(freqs):
        start = i * (note_len + gap_len)
        end = start + note_len
        if end > len(t):
            end = len(t)
        segment = t[start:end] - t[start]
        # Hüllkurve (Attack/Release)
        env = np.ones(end - start)
        attack = min(int(sample_rate * 0.02), len(env))
        release = min(int(sample_rate * 0.05), len(env))
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)
        tone[start:end] = np.sin(2 * np.pi * freq * segment) * 0.5 * env
    
    tone = tone.astype(np.float32)
    
    # Testton auf Mikrofon-Gerät abspielen
    try:
        sd.play(tone, sample_rate, device=mic_output_device)
        sd.wait()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abspielen auf Mic-Gerät: {e}")
    
    # Gleichen Testton auf Lautsprecher abspielen (damit User hört was gesendet wurde)
    try:
        output_device = tts.output_device if tts else None
        sd.play(tone, sample_rate, device=output_device)
        sd.wait()
    except Exception as e:
        print(f"Lautsprecher-Wiedergabe Fehler: {e}")
    
    return {"success": True, "message": "Testton wurde auf Mic-Gerät und Lautsprecher abgespielt"}


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
        "repetition_penalty": tts.repetition_penalty,
        "tts_provider": tts.tts_provider,
        "elevenlabs_configured": bool(tts.elevenlabs_api_key),
        "elevenlabs_voice_id": tts.elevenlabs_voice_id,
        "elevenlabs_model_id": tts.elevenlabs_model_id,
        "elevenlabs_stability": tts.elevenlabs_stability,
        "elevenlabs_similarity_boost": tts.elevenlabs_similarity_boost,
        "elevenlabs_style": tts.elevenlabs_style,
        "elevenlabs_use_speaker_boost": tts.elevenlabs_use_speaker_boost
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


# === ElevenLabs Provider ===

class ElevenLabsConfigRequest(BaseModel):
    api_key: Optional[str] = None
    voice_id: Optional[str] = None
    model_id: Optional[str] = None
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None
    style: Optional[float] = None
    use_speaker_boost: Optional[bool] = None


class ProviderSwitchRequest(BaseModel):
    provider: str  # "elevenlabs" oder "coqui"


@app.get("/api/tts/provider")
async def get_provider():
    """Gibt den aktuellen TTS-Provider zurück"""
    if not tts:
        return {"provider": "coqui", "elevenlabs_configured": False}
    
    return {
        "provider": tts.tts_provider,
        "elevenlabs_configured": bool(tts.elevenlabs_api_key),
        "elevenlabs_voice_id": tts.elevenlabs_voice_id,
        "elevenlabs_model_id": tts.elevenlabs_model_id
    }


@app.post("/api/tts/provider/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """Wechselt den TTS-Provider"""
    if request.provider not in ("elevenlabs", "coqui"):
        raise HTTPException(status_code=400, detail="Ungültiger Provider. Erlaubt: 'elevenlabs', 'coqui'")
    
    if tts:
        if request.provider == "elevenlabs" and not tts.elevenlabs_api_key:
            raise HTTPException(status_code=400, detail="ElevenLabs API-Key nicht konfiguriert")
        success = tts.set_tts_provider(request.provider)
        return {"success": success, "provider": tts.tts_provider}
    
    # TTS noch nicht geladen — Provider in Config speichern
    try:
        import json
        from main import TextToSpeech
        config_file = TextToSpeech.ELEVENLABS_CONFIG_FILE
        config = {}
        if config_file.exists():
            config = json.loads(config_file.read_text(encoding='utf-8'))
        config['provider'] = request.provider
        config_file.write_text(json.dumps(config), encoding='utf-8')
        return {"success": True, "provider": request.provider}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/elevenlabs/config")
async def set_elevenlabs_config(request: ElevenLabsConfigRequest):
    """Konfiguriert ElevenLabs API-Key, Voice-ID und Modell"""
    if tts:
        success = tts.set_elevenlabs_config(
            api_key=request.api_key,
            voice_id=request.voice_id,
            model_id=request.model_id,
            stability=request.stability,
            similarity_boost=request.similarity_boost,
            style=request.style,
            use_speaker_boost=request.use_speaker_boost
        )
        return {"success": success}
    
    # TTS noch nicht geladen — Config direkt auf Disk speichern
    try:
        import json
        from main import TextToSpeech
        config_file = TextToSpeech.ELEVENLABS_CONFIG_FILE
        config = {}
        if config_file.exists():
            config = json.loads(config_file.read_text(encoding='utf-8'))
        if request.api_key is not None:
            config['api_key'] = request.api_key
        if request.voice_id is not None:
            config['voice_id'] = request.voice_id
        if request.model_id is not None:
            config['model_id'] = request.model_id
        if request.stability is not None:
            config['stability'] = request.stability
        if request.similarity_boost is not None:
            config['similarity_boost'] = request.similarity_boost
        if request.style is not None:
            config['style'] = request.style
        if request.use_speaker_boost is not None:
            config['use_speaker_boost'] = request.use_speaker_boost
        config_file.write_text(json.dumps(config), encoding='utf-8')
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/elevenlabs/voices")
async def get_elevenlabs_voices():
    """Listet alle ElevenLabs-Stimmen auf"""
    if tts:
        voices = tts.list_elevenlabs_voices()
        return {"voices": voices, "current_voice_id": tts.elevenlabs_voice_id}
    
    # TTS noch nicht geladen — direkt ElevenLabs SDK nutzen
    try:
        import json
        from main import TextToSpeech
        config_file = TextToSpeech.ELEVENLABS_CONFIG_FILE
        if not config_file.exists():
            return {"voices": [], "current_voice_id": None}
        config = json.loads(config_file.read_text(encoding='utf-8'))
        api_key = config.get('api_key')
        if not api_key:
            return {"voices": [], "current_voice_id": None}
        
        from elevenlabs.client import ElevenLabs
        client = ElevenLabs(api_key=api_key)
        response = client.voices.search()
        voices = [{'voice_id': v.voice_id, 'name': v.name, 'category': getattr(v, 'category', 'unknown')} for v in response.voices]
        return {"voices": voices, "current_voice_id": config.get('voice_id')}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Main ===

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765)
