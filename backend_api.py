"""
SpeakAlike Backend API - FastAPI server for Electron frontend
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

# PyInstaller compatibility: base path for data files
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

# Set Windows console to UTF-8 to avoid Unicode errors
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # reconfigure may not be available on older Python versions
from typing import Optional, List
from datetime import datetime

# Add espeak-ng to PATH
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Lazy import: TextToSpeech is loaded on first TTS call, not at server startup
# from main import TextToSpeech  # -> imported in init_tts_async()
from audio_processor import prepare_samples_for_cloning, get_audio_info
from catalog import MessageCatalog
from tag_generator import generate_tags

app = FastAPI(title="SpeakAlike API", version="1.0.0")

# CORS for Electron
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
tts = None
catalog: Optional[MessageCatalog] = None
_whisper_model = None  # Lazy-loaded for transcription

# Temporary audio files
TEMP_DIR = Path(tempfile.gettempdir()) / "speakalike"
TEMP_DIR.mkdir(exist_ok=True)

# Status tracking
current_status = {
    "is_speaking": False,
    "message": "Ready",
    "progress": 0,
    "loading": True,  # True while TTS is loading
    "last_audio": None,
    "last_text": None
}

# History of recent messages (independent of catalog)
audio_history = []  # List of {"id": str, "text": str, "audio_path": str, "timestamp": str}


# === Models ===

class TTSRequest(BaseModel):
    text: str
    language: str = "de"


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


class SwitchTTSModelRequest(BaseModel):
    model_id: str


class SentenceCompletionRequest(BaseModel):
    text: str
    model: str = "claude-haiku-4-5-20251001"
    language: str = "de"
    context: str = ""
    recent_messages: list = []


# === Lifecycle ===

async def init_tts_async():
    """Loads TTS engine in the background"""
    global tts
    import asyncio
    import time
    
    current_status["message"] = "TTS-Bibliotheken werden geladen..."
    current_status["loading"] = True
    
    start_time = time.time()
    
    # Run TTS in thread pool to avoid blocking the event loop
    loop = asyncio.get_event_loop()
    
    def create_tts():
        from main import TextToSpeech
        return TextToSpeech()
    
    try:
        tts = await loop.run_in_executor(None, create_tts)
        tts.headless_mode = True
        elapsed = time.time() - start_time
        current_status["message"] = "Bereit"
        print(f"TTS engine loaded and ready! ({elapsed:.1f}s)")
    except Exception as e:
        print(f"Error loading TTS engine: {e}")
        import traceback
        traceback.print_exc()
        current_status["message"] = f"TTS load error: {e}"
    finally:
        current_status["loading"] = False


@app.on_event("startup")
async def startup():
    """Initialises backend on startup"""
    global catalog
    import asyncio
    
    # Load catalog immediately (fast)
    catalog = MessageCatalog()
    current_status["message"] = "Backend gestartet, TTS wird geladen..."
    
    # Load TTS in background
    asyncio.create_task(init_tts_async())


# === Status Endpoints ===

@app.get("/api/status")
async def get_status():
    """Returns current status"""
    return {
        **current_status,
        "gpu_available": tts.gpu_available if tts else False,
        "voice_loaded": tts.current_voice_name if tts else None,
        "tts_model": tts.current_tts_model_id if tts else "xtts_v2",
        "tts_provider": tts.tts_provider if tts else "pyttsx3",
        "elevenlabs_configured": bool(tts.elevenlabs_api_key) if tts else False
    }


# === TTS Model Endpoints ===

@app.get("/api/tts/models")
async def get_tts_models():
    """Returns all available TTS models"""
    if not tts:
        # Fallback: return static list
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
        raise HTTPException(status_code=503, detail="TTS is still loading, please wait...")
    
    if current_status["is_speaking"]:
        raise HTTPException(status_code=409, detail="Generation already in progress")
    
    current_status["message"] = f"Switching to {request.model_id}..."
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
            current_status["message"] = "Error switching model"
            raise HTTPException(status_code=500, detail="Model switch failed")
            
    except Exception as e:
        current_status["loading"] = False
        current_status["message"] = f"Fehler: {str(e)}"
        raise HTTPException(status_code=500, detail=str(e))


# === TTS Endpoints ===

@app.post("/api/tts/speak")
async def speak(request: TTSRequest, background_tasks: BackgroundTasks):
    """Generates speech from text"""
    global current_status
    
    if not tts or current_status.get("loading", False):
        raise HTTPException(status_code=503, detail="TTS is still loading, please wait...")
    
    if current_status["is_speaking"]:
        raise HTTPException(status_code=409, detail="Generation already in progress")
    
    current_status["is_speaking"] = True
    current_status["message"] = "Generating audio..."
    current_status["last_text"] = request.text
    
    try:
        # Generate audio and save
        audio_path = tts.speak_and_save(
            text=request.text,
            language=request.language
        )
        
        if audio_path and os.path.exists(audio_path):
            # Copy to temp directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            dest_path = TEMP_DIR / f"speech_{timestamp}.wav"
            shutil.copy(audio_path, dest_path)
            
            current_status["last_audio"] = str(dest_path)
            current_status["message"] = "Fertig"
            current_status["is_speaking"] = False
            
            # Add to history
            history_entry = {
                "id": timestamp,
                "text": request.text,
                "audio_path": str(dest_path),
                "audio_url": f"/api/audio/{dest_path.name}",
                "timestamp": datetime.now().isoformat()
            }
            audio_history.insert(0, history_entry)
            # Keep only the last 10
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


# Microphone output: second output device (e.g. VB-Cable) for phone calls
mic_output_device = None  # Device index for microphone output
mic_output_enabled = False  # Whether microphone output is active

@app.post("/api/tts/play-audio")
async def play_audio_on_device(data: dict):
    """Plays an audio file on the selected device"""
    try:
        import sounddevice as sd
        import soundfile as sf
        import threading
        
        audio_url = data.get("audio_url", "")
        file_path = None
        
        # Check whether it is a catalog URL
        if "/api/catalog/" in audio_url and "/audio" in audio_url:
            # Extract message_id from URL like /api/catalog/123/audio
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
            # Regular audio URL from TEMP_DIR
            filename = audio_url.split("/")[-1] if "/" in audio_url else audio_url
            file_path = TEMP_DIR / filename
        
        if not file_path or not file_path.exists():
            raise HTTPException(status_code=404, detail="Audio file not found")
        
        # Load and play audio
        audio_data, samplerate = sf.read(str(file_path))
        device = tts.output_device if tts else None
        print(f"[Audio-Play] file={file_path.name}, shape={audio_data.shape}, sr={samplerate}, device={device}")
        
        # Apply volume
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
            """Returns the native sample rate of a device"""
            if dev_index is None:
                return None
            try:
                dev_info = sd.query_devices(dev_index)
                return int(dev_info['default_samplerate'])
            except:
                return None

        def get_device_channels(dev_index):
            """Returns the max output channels of a device (None = use default)"""
            if dev_index is None:
                return None
            try:
                dev_info = sd.query_devices(dev_index)
                return int(dev_info['max_output_channels'])
            except:
                return None

        def match_channels(audio, device_max_ch):
            """Downmix audio only if it has more channels than the device supports.
            Never upmix — PortAudio accepts fewer channels than the device maximum."""
            if device_max_ch is None or device_max_ch <= 0:
                return audio
            current_ch = 1 if audio.ndim == 1 else audio.shape[1]
            if current_ch <= device_max_ch:
                return audio  # already within range, no conversion needed
            # Too many channels for this device → downmix
            if device_max_ch == 1:
                return audio.mean(axis=1).astype(np.float32) if audio.ndim > 1 else audio
            # Keep first device_max_ch channels
            return audio[:, :device_max_ch].astype(np.float32)
        
        # Play simultaneously on speaker AND microphone device
        print(f"[Audio-Play] mic_output_enabled={mic_output_enabled}, mic_output_device={mic_output_device}, samplerate={samplerate}")
        
        if mic_output_enabled and mic_output_device is not None:
            # Convert to mono if stereo (for mic output)
            if len(audio_data.shape) > 1:
                mic_audio = audio_data.mean(axis=1)
            else:
                mic_audio = audio_data.copy()
            
            mic_audio = mic_audio.astype(np.float32)
            
            # Speaker: resample if needed and sd.play (non-blocking)
            try:
                speaker_sr = get_device_samplerate(device)
                speaker_ch = get_device_channels(device)
                speaker_data = audio_data
                play_sr = samplerate
                if speaker_sr and speaker_sr != samplerate:
                    # Resample for mono/stereo
                    if len(audio_data.shape) > 1:
                        speaker_data = np.column_stack([
                            resample_audio(audio_data[:, ch], samplerate, speaker_sr)
                            for ch in range(audio_data.shape[1])
                        ])
                    else:
                        speaker_data = resample_audio(audio_data, samplerate, speaker_sr)
                    play_sr = speaker_sr
                    print(f"[Audio-Play] Speaker resampled: {samplerate} -> {speaker_sr} Hz")
                speaker_data = match_channels(speaker_data, speaker_ch)
                sd.play(speaker_data, play_sr, device=device)
                print(f"[Audio-Play] Speaker playback started (device={device}, sr={play_sr})")
            except Exception as e:
                print(f"[Audio-Play] Speaker sd.play error: {e}")
                # Fallback: resample for default device and play without explicit device
                try:
                    default_sr = get_device_samplerate(None)
                    fb_data = audio_data
                    fb_sr = samplerate
                    if default_sr and default_sr != samplerate:
                        fb_data = resample_audio(
                            audio_data if audio_data.ndim == 1 else audio_data.mean(axis=1),
                            samplerate, default_sr
                        )
                        fb_sr = default_sr
                    sd.play(fb_data, fb_sr)
                    print(f"[Audio-Play] Speaker fallback (default device, sr={fb_sr}) ok")
                except Exception as e2:
                    print(f"[Audio-Play] Speaker fallback also failed: {e2}")
            
            # Microphone output on separate thread
            def play_on_mic():
                nonlocal mic_audio, samplerate
                
                # Resample for mic device if needed
                mic_sr = get_device_samplerate(mic_output_device)
                mic_play_sr = samplerate
                if mic_sr and mic_sr != samplerate:
                    mic_audio = resample_audio(mic_audio, samplerate, mic_sr)
                    mic_play_sr = mic_sr
                    print(f"[Audio-Play] Mic resampled: {samplerate} -> {mic_sr} Hz")
                
                # Attempt 1: sd.play (simplest way, works as fallback)
                try:
                    sd.play(mic_audio, mic_play_sr, device=mic_output_device)
                    sd.wait()
                    print(f"[Audio-Play] Mic output via sd.play successful (device={mic_output_device}, sr={mic_play_sr})")
                    return
                except Exception as e1:
                    print(f"[Audio-Play] sd.play failed (device={mic_output_device}): {e1}")
                
                # Attempt 2: OutputStream
                try:
                    mic_dev_ch = min(1, int(sd.query_devices(mic_output_device)['max_output_channels']))
                    stream_audio = mic_audio if mic_audio.ndim == 1 else mic_audio.mean(axis=1)
                    mic_stream = sd.OutputStream(
                        samplerate=mic_play_sr,
                        channels=mic_dev_ch,
                        device=mic_output_device
                    )
                    mic_stream.start()
                    mic_stream.write(stream_audio.reshape(-1, 1) if mic_dev_ch == 1 else stream_audio)
                    mic_stream.stop()
                    mic_stream.close()
                    print(f"[Audio-Play] Mic output successful (OutputStream, ch={mic_dev_ch})")
                    return
                except Exception as e2:
                    print(f"[Audio-Play] OutputStream failed: {e2}")
                
                # Attempt 3: alternative device with compatible Host-API
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
                                    print(f"[Audio-Play] Trying alternative device {idx} ({dev['name']}, API: {api_name}, sr={alt_sr})")
                                    sd.play(alt_audio, alt_sr, device=idx)
                                    sd.wait()
                                    print(f"[Audio-Play] Microphone output via alternative device {idx} successful")
                                    return
                except Exception as e3:
                    print(f"[Audio-Play] All mic fallbacks failed: {e3}")
            
            threading.Thread(target=play_on_mic, daemon=True).start()
        else:
            # Speaker only (no mic configured or disabled)
            try:
                speaker_sr = get_device_samplerate(device)
                speaker_ch = get_device_channels(device)
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
                    print(f"[Audio-Play] Speaker resampled: {samplerate} -> {speaker_sr} Hz")
                play_data = match_channels(play_data, speaker_ch)
                sd.play(play_data, play_sr, device=device)
            except Exception as e:
                print(f"[Audio-Play] Speaker error: {e}, trying default device...")
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
                    print(f"[Audio-Play] Fallback also failed: {e2}")
            if not mic_output_enabled:
                print(f"[Audio-Play] Microphone output disabled (🎤 button not active)")
            elif mic_output_device is None:
                print(f"[Audio-Play] No microphone device configured")
        
        return {"success": True, "device": device, "mic_device": mic_output_device if mic_output_enabled else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts/stop")
async def stop_speaking():
    """Stops the current playback"""
    import sounddevice as sd
    sd.stop()  # Stop sounddevice playback too
    if tts:
        tts.stop()
    current_status["is_speaking"] = False
    current_status["message"] = "Stopped"
    return {"success": True}


@app.get("/api/typing-sound")
async def get_typing_sound():
    """Serves the typing sound MP3 file"""
    sound_path = BASE_DIR / "electron-app" / "typing-sound.mp3"
    if not sound_path.exists():
        raise HTTPException(status_code=404, detail="typing-sound.mp3 not found")
    return FileResponse(str(sound_path), media_type="audio/mpeg")


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Serves an audio file"""
    file_path = TEMP_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/wav")


@app.get("/api/history")
async def get_history():
    """Returns the playback history (all played messages in chronological order)"""
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
    """Adds an entry to the playback history"""
    if catalog:
        catalog.add_to_playback_history(text, audio_url, catalog_id)
    return {"status": "ok"}


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
    """Lists catalog entries"""
    if not catalog:
        return []
    
    # tags parameter is a comma-separated list
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
    
    # Audio duration
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
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    messages = catalog.search()
    message = next((m for m in messages if m["id"] == message_id), None)
    
    if not message:
        raise HTTPException(status_code=404, detail="Nachricht nicht gefunden")
    
    if not os.path.exists(message["audio_path"]):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(message["audio_path"], media_type="audio/wav")


@app.put("/api/catalog/{message_id}/favorite")
async def toggle_favorite(message_id: int):
    """Toggled Favoriten-Status"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    catalog.toggle_favorite(message_id)
    return {"success": True}


@app.put("/api/catalog/{message_id}/tags")
async def update_tags(message_id: int, tags: List[str]):
    """Aktualisiert Tags einer Nachricht"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    catalog.update_tags(message_id, tags)
    return {"success": True}


@app.post("/api/catalog/{message_id}/play")
async def increment_play_count(message_id: int):
    """Increments the play count of a catalog message"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    catalog.update_play_count(message_id)
    return {"success": True}


@app.put("/api/catalog/{message_id}")
async def update_catalog_message(message_id: int, request: dict):
    """Aktualisiert eine Katalog-Nachricht (z.B. is_favorite)"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    if "is_favorite" in request:
        catalog.set_favorite(message_id, request["is_favorite"])
    
    return {"success": True}


@app.delete("/api/catalog/{message_id}")
async def delete_message(message_id: int):
    """Deletes a catalog message"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
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
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    # Create temporary file
    suffix = Path(audio.filename).suffix.lower()
    if suffix not in ['.mp3', '.wav', '.ogg', '.m4a']:
        raise HTTPException(status_code=400, detail="Invalid Audio-Format")
    
    temp_path = TEMP_DIR / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    
    try:
        # Save audio
        with open(temp_path, 'wb') as f:
            content = await audio.read()
            f.write(content)
        
        # Get audio info
        try:
            audio_info = get_audio_info(str(temp_path))
            duration = audio_info.get('duration', 0)
        except:
            duration = 0
        
        # Parse tags
        tags_list = [t.strip() for t in tags.split(',') if t.strip()] if tags else []
        
        # Add to catalog
        message_id = catalog.add_message(
            text=text,
            source_audio_path=str(temp_path),
            tags=tags_list,
            voice_model="import",
            duration_seconds=duration
        )
        
        return {"success": True, "message_id": message_id}
        
    finally:
        # Delete temporary file
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """Transkribiert eine Audio-Datei mit Whisper"""
    import torch
    import torchaudio
    import numpy as np
    
    # Create temporary file
    suffix = Path(audio.filename).suffix.lower()
    if suffix not in ['.mp3', '.wav', '.ogg', '.m4a']:
        raise HTTPException(status_code=400, detail="Invalid Audio-Format")
    
    temp_path = TEMP_DIR / f"transcribe_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"
    
    try:
        # Save audio
        with open(temp_path, 'wb') as f:
            content = await audio.read()
            f.write(content)
        
        # Load audio
        waveform, sample_rate = torchaudio.load(str(temp_path))
        
        # Convert to mono
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample to 16 kHz for Whisper
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
            waveform = resampler(waveform)
        
        audio_np = waveform.squeeze().numpy().astype(np.float32)
        
        # Normalise
        max_val = np.max(np.abs(audio_np))
        if max_val > 0:
            audio_np = audio_np / max_val
        
        # Load Whisper (lazy)
        try:
            import whisper
        except ImportError:
            raise HTTPException(status_code=503, detail="Whisper nicht installiert")
        
        # Global Whisper model
        global _whisper_model
        if '_whisper_model' not in globals() or _whisper_model is None:
            print("Loading Whisper model for transcription...")
            _whisper_model = whisper.load_model("base", device="cuda" if torch.cuda.is_available() else "cpu")
            print("Whisper-Modell geladen.")
        
        # Transcribe
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
    """Lists all tags with frequency"""
    if not catalog:
        return []
    
    return [{"name": t[0], "count": t[1]} for t in catalog.get_all_tags()]


# === Sentence Completion with Claude AI ===

@app.post("/api/ai/complete-sentence")
async def complete_sentence_endpoint(
    request: SentenceCompletionRequest,
    x_api_key: Optional[str] = Header(None)
):
    """Completes incomplete sentences using Claude AI"""
    import anthropic
    
    prompt_file = f"prompt_{request.language}.txt"
    prompt_path = BASE_DIR / prompt_file
    if not prompt_path.exists():
        prompt_path = BASE_DIR / "prompt_de.txt"
    system_prompt = prompt_path.read_text(encoding="utf-8")
    
    # Insert dynamic context if available
    if request.context:
        context_line = f"Current conversation context: {request.context}. Take this context into account when completing the text, but the user may also say things that do not directly relate to the context."
        system_prompt = system_prompt.replace("{DYNAMIC_CONTEXT}", context_line)
    else:
        system_prompt = system_prompt.replace("{DYNAMIC_CONTEXT}", "")

    try:
        # API key from header or environment variable
        api_key = x_api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise HTTPException(status_code=401, detail="API Key nicht gesetzt")
        
        print(f"[AI] Anfrage: text='{request.text[:50]}...', model={request.model}, language={request.language}")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Only allow permitted models
        allowed_models = ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"]
        model = request.model if request.model in allowed_models else "claude-haiku-4-5-20251001"
        
        # Try with selected model, fall back on refusal to Haiku
        models_to_try = [model]
        if model != "claude-haiku-4-5-20251001":
            models_to_try.append("claude-haiku-4-5-20251001")
        
        for try_model in models_to_try:
            print(f"[AI] Sending to Claude (model={try_model})...")
            
            # Build messages: previous messages as context + current request
            messages = []
            for msg in request.recent_messages:
                messages.append({"role": "user", "content": msg})
                messages.append({"role": "assistant", "content": msg})
            messages.append({"role": "user", "content": f"Please complete the following abbreviated text: {request.text}"})
            
            message = client.messages.create(
                model=try_model,
                max_tokens=1024,
                system=system_prompt,
                messages=messages
            )
            
            print(f"[AI] Response: stop_reason={message.stop_reason}, content_blocks={len(message.content)}")
            
            # On refusal: try next model
            if message.stop_reason == 'refusal' or not message.content:
                print(f"[AI] {try_model} refused/empty, trying fallback...")
                continue
            
            # Find first text block
            completed_text = None
            for block in message.content:
                if hasattr(block, 'text'):
                    completed_text = block.text.strip()
                    break
            
            if completed_text:
                print(f"[AI] Result ({try_model}): '{completed_text[:80]}'")
                return {"original": request.text, "completed": completed_text}
        
        # All models refused – return original text
        print(f"[AI] All models refused. Returning original text.")
        return {"original": request.text, "completed": request.text, "refusal": True}
        
    except HTTPException:
        raise
    except anthropic.AuthenticationError:
        print("[AI] ERROR: API key invalid")
        raise HTTPException(status_code=401, detail="Invalid API key")
    except anthropic.RateLimitError:
        print("[AI] ERROR: Rate limit reached")
        raise HTTPException(status_code=429, detail="Rate limit reached")
    except Exception as e:
        print(f"[AI] ERROR: {type(e).__name__}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Claude API error: {str(e)}")


# === Tag Generation ===

@app.post("/api/tags/generate")
async def generate_tags_endpoint(request: TagGenerateRequest, x_api_key: Optional[str] = Header(None)):
    """Generates tags using Claude AI"""
    if not catalog:
        raise HTTPException(status_code=503, detail="Catalog not initialised")
    
    api_key = x_api_key or os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=401, detail="No Claude API key configured")
    
    existing_tags = [t[0] for t in catalog.get_all_tags()]
    
    try:
        tags = generate_tags(
            text=request.text,
            existing_tags=existing_tags,
            num_tags=request.num_tags,
            api_key=api_key
        )
        return {"tags": tags}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Audio Devices ===

@app.get("/api/audio-devices")
async def get_audio_devices():
    """Returns list of available output devices"""
    try:
        import sounddevice as sd
        devices = []
        seen_names = {}  # base_name -> (index, hostapi_priority)
        device_list = sd.query_devices()
        host_apis = sd.query_hostapis()
        
        # Host-API priorities: WASAPI > MME > DirectSound > other
        # WDM-KS is avoided (does not support blocking API)
        def hostapi_priority(hostapi_index):
            name = host_apis[hostapi_index]['name'].lower() if hostapi_index < len(host_apis) else ''
            if 'wasapi' in name:
                return 0  # Best choice
            elif 'mme' in name:
                return 1
            elif 'directsound' in name:
                return 2
            elif 'wdm' in name or 'ks' in name:
                return 99  # Avoid – does not support blocking API
            return 3
        
        for i, device in enumerate(device_list):
            # Only output devices (max_output_channels > 0)
            if device['max_output_channels'] > 0:
                # Clean and deduplicate device names
                name = device['name']
                # Use only the main name (before API type like "MME", "Windows DirectSound" etc.)
                base_name = name.split(',')[0].strip() if ',' in name else name
                # Normalise to 31 chars – MME truncates names at 31 chars, this ensures
                # MME and WASAPI/DS variants of the same device map to the same key
                base_name = base_name[:31]
                
                priority = hostapi_priority(device.get('hostapi', 0))
                
                # Skip if we already have this device with better priority
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
    """Sets the output device"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS not initialised")
    
    device_index = device.get("index")
    # None = default device
    tts.output_device = device_index if device_index != -1 else None
    return {"success": True, "device": tts.output_device}


@app.get("/api/mic-devices")
async def get_mic_devices():
    """Returns all audio devices suitable for microphone routing (input + output devices, no deduplication)"""
    try:
        import sounddevice as sd
        device_list = sd.query_devices()
        host_apis = sd.query_hostapis()

        def api_priority(hostapi_index):
            name = host_apis[hostapi_index]['name'].lower() if hostapi_index < len(host_apis) else ''
            if 'wasapi' in name:
                return 0
            elif 'mme' in name:
                return 1
            elif 'directsound' in name:
                return 2
            elif 'wdm' in name or 'ks' in name:
                return 99
            return 3

        def api_name(device):
            idx = device.get('hostapi', 0)
            return host_apis[idx]['name'] if idx < len(host_apis) else ''

        # Collect and deduplicate: key = (name_prefix, device_type)
        # MME truncates names at 31 chars, so normalise to first 31 chars to match across APIs
        seen = {}  # (name_prefix, type) -> (priority, entry)
        for i, device in enumerate(device_list):
            has_out = device['max_output_channels'] > 0
            has_in = device['max_input_channels'] > 0
            if not has_out and not has_in:
                continue
            dev_type = 'output' if has_out else 'input'
            name = device['name']
            priority = api_priority(device.get('hostapi', 0))
            if priority == 99:
                continue  # Skip WDM-KS entirely
            key = (name[:31], dev_type)
            if key not in seen or priority < seen[key][0]:
                seen[key] = (priority, {
                    'index': i,
                    'name': name,
                    'type': dev_type,
                    'channels': device['max_output_channels'] if has_out else device['max_input_channels'],
                    'samplerate': device['default_samplerate'],
                    'api': api_name(device),
                })
        devices = [entry for _, entry in seen.values()]
        # Sort: output devices first, then input, both alphabetically
        devices.sort(key=lambda d: (0 if d['type'] == 'output' else 1, d['name']))
        return {"devices": devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Microphone output (for phone calls) ===

@app.get("/api/mic-device")
async def get_mic_device():
    """Returns the current microphone output device and status"""
    return {
        "device": mic_output_device,
        "enabled": mic_output_enabled
    }


@app.put("/api/mic-device")
async def set_mic_device(data: dict):
    """Sets the microphone output device (e.g. VB-Cable)"""
    global mic_output_device, mic_output_enabled
    
    device_index = data.get("index")
    mic_output_device = device_index if device_index is not None and device_index != -1 else None
    
    if "enabled" in data:
        mic_output_enabled = bool(data["enabled"])
    
    return {"success": True, "device": mic_output_device, "enabled": mic_output_enabled}


@app.put("/api/mic-device/toggle")
async def toggle_mic_output(data: dict = {}):
    """Toggles microphone output on/off"""
    global mic_output_enabled
    
    if "enabled" in data:
        mic_output_enabled = bool(data["enabled"])
    else:
        mic_output_enabled = not mic_output_enabled
    
    return {"success": True, "enabled": mic_output_enabled, "device": mic_output_device}


# === Typing sound via microphone ===
_typing_thread = None
_typing_active = False
_typing_audio_data = None  # Loaded keyboard recording
_typing_audio_sr = None

def _load_typing_sound():
    """Loads the keyboard sound file"""
    global _typing_audio_data, _typing_audio_sr
    if _typing_audio_data is not None:
        return True
    
    import soundfile as sf
    from pathlib import Path
    
    sound_path = BASE_DIR / "electron-app" / "typing-sound.mp3"
    if not sound_path.exists():
        print(f"[Typing-Mic] Sound file not found: {sound_path}")
        return False
    
    try:
        # Load MP3 (soundfile can read mp3 via libsndfile)
        data, sr = sf.read(str(sound_path), dtype='float32')
        # Convert to mono
        if len(data.shape) > 1:
            data = data.mean(axis=1)
        _typing_audio_data = data
        _typing_audio_sr = sr
        print(f"[Typing-Mic] Sound loaded: {len(data)/sr:.2f}s, {sr} Hz")
        return True
    except Exception as e:
        print(f"[Typing-Mic] Error loading sound: {e}")
        # Fallback: try with pydub
        try:
            from pydub import AudioSegment
            import numpy as np
            
            audio = AudioSegment.from_mp3(str(sound_path))
            audio = audio.set_channels(1)
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
            samples /= 32768.0
            _typing_audio_data = samples
            _typing_audio_sr = audio.frame_rate
            print(f"[Typing-Mic] Sound loaded via pydub: {len(samples)/audio.frame_rate:.2f}s, {audio.frame_rate} Hz")
            return True
        except Exception as e2:
            print(f"[Typing-Mic] pydub fallback also failed: {e2}")
            return False

def _typing_loop():
    """Plays random clips of the keyboard recording on the mic device"""
    import sounddevice as sd
    import numpy as np
    import time
    import random
    global _typing_active
    
    device = mic_output_device
    if device is None:
        return
    
    if not _load_typing_sound():
        print("[Typing-Mic] No sound available, using synthetic")
        return
    
    audio = _typing_audio_data
    sr = _typing_audio_sr
    
    # Determine sample rate of the mic device
    try:
        dev_info = sd.query_devices(device)
        dev_sr = int(dev_info['default_samplerate'])
    except:
        dev_sr = sr
    
    # Resample if needed
    if dev_sr != sr:
        ratio = dev_sr / sr
        n_samples = int(len(audio) * ratio)
        indices = np.arange(n_samples) / ratio
        indices = np.clip(indices, 0, len(audio) - 1)
        audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)
        sr = dev_sr
    
    print(f"[Typing-Mic] Typing sound started on device {device} ({sr} Hz)")
    
    try:
        while _typing_active:
            # Choose random clip (60-120ms)
            clip_duration = 0.06 + random.random() * 0.06
            clip_samples = int(sr * clip_duration)
            max_start = max(0, len(audio) - clip_samples - int(sr * 0.1))
            start = random.randint(0, max_start) if max_start > 0 else 0
            
            clip = audio[start:start + clip_samples].copy()
            
            # Fade-Out (letzte 20%)
            fade_len = int(len(clip) * 0.2)
            if fade_len > 0:
                clip[-fade_len:] *= np.linspace(1, 0, fade_len)
            
            # Volume variation
            clip *= 0.3 + random.random() * 0.2
            
            # Silent gap between clicks (60-130ms)
            gap = int(sr * (0.06 + random.random() * 0.07))
            chunk = np.concatenate([clip, np.zeros(gap, dtype=np.float32)])
            
            try:
                sd.play(chunk, sr, device=device)
                sd.wait()
            except:
                time.sleep(0.085)
    except Exception as e:
        print(f"[Typing-Mic] Error: {e}")
    
    print(f"[Typing-Mic] Typing sound stopped")

@app.post("/api/mic-device/typing/start")
async def start_typing_on_mic():
    """Starts typing sound on the microphone output device"""
    global _typing_thread, _typing_active
    import threading
    
    if not mic_output_enabled or mic_output_device is None:
        return {"success": False, "reason": "Microphone output not active"}
    
    if _typing_active:
        return {"success": True, "already_running": True}
    
    _typing_active = True
    _typing_thread = threading.Thread(target=_typing_loop, daemon=True)
    _typing_thread.start()
    return {"success": True}

@app.post("/api/mic-device/typing/stop")
async def stop_typing_on_mic():
    """Stops typing sound on the microphone output device"""
    global _typing_active, _typing_thread
    _typing_active = False
    if _typing_thread:
        _typing_thread.join(timeout=1)
        _typing_thread = None
    return {"success": True}


@app.post("/api/mic-device/echo-test")
async def mic_echo_test():
    """Plays a test tone on the microphone output device and simultaneously records it,
    then plays back the recorded audio on the speaker."""
    import sounddevice as sd
    import numpy as np

    if mic_output_device is None:
        raise HTTPException(status_code=400, detail="No microphone device configured")

    def make_tone(sample_rate):
        duration = 1.5
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        tone = np.zeros_like(t)
        freqs = [523.25, 659.25, 783.99]  # C5, E5, G5
        note_len = int(sample_rate * 0.4)
        gap_len = int(sample_rate * 0.05)
        for i, freq in enumerate(freqs):
            start = i * (note_len + gap_len)
            end = min(start + note_len, len(t))
            segment = t[start:end] - t[start]
            env = np.ones(end - start)
            attack = min(int(sample_rate * 0.02), len(env))
            release = min(int(sample_rate * 0.05), len(env))
            env[:attack] = np.linspace(0, 1, attack)
            env[-release:] = np.linspace(1, 0, release)
            tone[start:end] = np.sin(2 * np.pi * freq * segment) * 0.5 * env
        return tone.astype(np.float32)

    # Use native sample rate of each device
    mic_sr = int(sd.query_devices(mic_output_device)['default_samplerate'])
    mic_tone = make_tone(mic_sr)

    # Play test tone on microphone device
    try:
        sd.play(mic_tone, mic_sr, device=mic_output_device)
        sd.wait()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error playing on mic device: {e}")

    # Play same test tone on speaker (so user can hear what was sent)
    try:
        output_device = tts.output_device if tts else None
        spk_sr = int(sd.query_devices(output_device)['default_samplerate']) if output_device is not None else mic_sr
        spk_tone = make_tone(spk_sr)
        sd.play(spk_tone, spk_sr, device=output_device)
        sd.wait()
    except Exception as e:
        print(f"Speaker playback error: {e}")

    return {"success": True, "message": "Test tone played on mic device and speaker"}


# === Settings ===

@app.get("/api/settings")
async def get_settings():
    """Returns TTS settings"""
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
        "elevenlabs_use_speaker_boost": tts.elevenlabs_use_speaker_boost,
        "pyttsx3_voice_id": tts.pyttsx3_voice_id,
        "pyttsx3_gender": tts.pyttsx3_gender
    }


@app.put("/api/settings")
async def update_settings(settings: dict):
    """Updates TTS settings"""
    if not tts:
        raise HTTPException(status_code=503, detail="TTS not initialised")
    
    if "temperature" in settings:
        tts.temperature = settings["temperature"]
    if "speed" in settings:
        tts.speed = settings["speed"]
    if "top_k" in settings:
        tts.top_k = settings["top_k"]
    if "top_p" in settings:
        tts.top_p = settings["top_p"]
    if "repetition_penalty" in settings:
        # XTTS requires penalty > 1.0 and < 2.0
        penalty = min(max(float(settings["repetition_penalty"]), 1.01), 1.99)
        tts.repetition_penalty = penalty
    if "pyttsx3_voice_id" in settings:
        tts.pyttsx3_voice_id = settings["pyttsx3_voice_id"] or None
        tts._save_elevenlabs_config()
    if "pyttsx3_gender" in settings:
        tts.pyttsx3_gender = settings["pyttsx3_gender"] or None
        tts._save_elevenlabs_config()
    
    return {"success": True}


# === ElevenLabs Provider ===


@app.get("/api/pyttsx3/voices")
async def get_pyttsx3_voices():
    """Returns available pyttsx3 system voices"""
    if not tts:
        return []
    return tts.get_pyttsx3_voices()


class ElevenLabsConfigRequest(BaseModel):
    api_key: Optional[str] = None
    voice_id: Optional[str] = None
    model_id: Optional[str] = None
    stability: Optional[float] = None
    similarity_boost: Optional[float] = None
    style: Optional[float] = None
    use_speaker_boost: Optional[bool] = None


class ProviderSwitchRequest(BaseModel):
    provider: str  # "elevenlabs" or "pyttsx3"


@app.get("/api/tts/provider")
async def get_provider():
    """Returns the current TTS provider"""
    if not tts:
        return {"provider": "pyttsx3", "elevenlabs_configured": False}
    
    return {
        "provider": tts.tts_provider,
        "elevenlabs_configured": bool(tts.elevenlabs_api_key),
        "elevenlabs_voice_id": tts.elevenlabs_voice_id,
        "elevenlabs_model_id": tts.elevenlabs_model_id
    }


@app.post("/api/tts/provider/switch")
async def switch_provider(request: ProviderSwitchRequest):
    """Switches the TTS provider"""
    if request.provider not in ("elevenlabs", "pyttsx3"):
        raise HTTPException(status_code=400, detail="Invalid provider. Allowed: 'elevenlabs', 'pyttsx3'")
    
    if tts:
        if request.provider == "elevenlabs" and not tts.elevenlabs_api_key:
            raise HTTPException(status_code=400, detail="ElevenLabs API key not configured")
        success = tts.set_tts_provider(request.provider)
        return {"success": success, "provider": tts.tts_provider}
    
    # TTS not yet loaded — save provider to config
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



