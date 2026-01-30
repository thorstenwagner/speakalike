"""
SpeakAlike - Text-to-Speech Anwendung mit Coqui TTS
"""
import sys
import threading
from pathlib import Path
import tempfile
import os

# Windows Konsole auf UTF-8 setzen, um Unicode-Fehler zu vermeiden
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # Falls reconfigure nicht verfügbar ist

# Füge espeak-ng zum PATH hinzu
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

try:
    from TTS.api import TTS
    from TTS.tts.configs.xtts_config import XttsConfig
    from TTS.tts.models.xtts import Xtts
    COQUI_AVAILABLE = True
    XTTS_DIRECT = True
except ImportError:
    try:
        from TTS.api import TTS
        COQUI_AVAILABLE = True
        XTTS_DIRECT = False
    except ImportError:
        COQUI_AVAILABLE = False
        XTTS_DIRECT = False
        print("Warnung: Coqui TTS nicht verfügbar. Fallback auf pyttsx3.")
        import pyttsx3


class TextToSpeech:
    """Text-to-Speech Engine Wrapper mit optimiertem Voice Cloning"""
    
    # Verzeichnis für gespeicherte Voice-Modelle
    VOICE_MODELS_DIR = Path(__file__).parent / "voice_models"
    LAST_MODEL_FILE = Path(__file__).parent / "voice_models" / ".last_model"
    LAST_TTS_MODEL_FILE = Path(__file__).parent / "voice_models" / ".last_tts_model"
    
    # Verfügbare TTS-Modelle für Voice Cloning
    AVAILABLE_TTS_MODELS = {
        "xtts_v2": {
            "name": "XTTS v2 (Standard)",
            "model_name": "tts_models/multilingual/multi-dataset/xtts_v2",
            "supports_cloning": True,
            "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu", "hi"],
            "description": "Beste Qualität, 17 Sprachen, Voice Cloning"
        },
        "xtts_v1.1": {
            "name": "XTTS v1.1",
            "model_name": "tts_models/multilingual/multi-dataset/xtts_v1.1",
            "supports_cloning": True,
            "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu", "hi"],
            "description": "Ältere Version, etwas schneller"
        },
        "bark": {
            "name": "Bark (Kreativ)",
            "model_name": "tts_models/multilingual/multi-dataset/bark",
            "supports_cloning": True,
            "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "zh", "ja", "ko", "ru", "tr", "hi", "ar"],
            "description": "Kreative Stimme, unterstützt Emotionen"
        },
        "tortoise_v2": {
            "name": "Tortoise v2 (Langsam, HQ)",
            "model_name": "tts_models/en/multi-dataset/tortoise-v2",
            "supports_cloning": True,
            "languages": ["en"],
            "description": "Sehr hohe Qualität, nur Englisch, langsam"
        },
        "vits_de": {
            "name": "VITS Deutsch (Schnell)",
            "model_name": "tts_models/de/thorsten/vits",
            "supports_cloning": False,
            "languages": ["de"],
            "description": "Schnell, kein Voice Cloning, deutsche Stimme"
        }
    }
    
    def __init__(self, model_id="xtts_v2"):
        self.is_speaking = False
        self.speaker_wav = None
        self.seed = 42  # Fester Seed für konsistente Ausgabe
        
        # Ausgabegerät (None = Standard-Gerät)
        self.output_device = None
        
        # Aktuelles TTS-Modell
        self.current_tts_model_id = model_id
        
        # Speaker Embedding Cache für bessere Qualität und Performance
        self.gpt_cond_latent = None
        self.speaker_embedding = None
        self.cached_speaker_wav = None
        self.current_voice_name = None  # Name des aktuell geladenen Voice-Modells
        
        # Performance-Einstellungen
        self.use_streaming = False  # Streaming für schnellere erste Ausgabe
        
        # Optimierte Inference-Parameter (Balance zwischen Qualität und Geschwindigkeit)
        self.gpt_cond_len = 6  # Reduziert für schnellere Generierung (Standard: 12)
        self.gpt_cond_chunk_len = 3  # Kleinere Chunks = schneller (Standard: 4)
        self.max_ref_len = 30  # Reduziert für Performance (Standard: 10)
        
        # Erweiterte Qualitätseinstellungen
        self.temperature = 0.65  # Standard-Wert für bessere Generierung
        self.top_k = 50  # Standard-Wert
        self.top_p = 0.8  # Standard-Wert
        self.repetition_penalty = 2.0  # Gegen Stottern/Wiederholungen
        self.speed = 1.0  # Sprechgeschwindigkeit
        self.length_penalty = 1.0  # Standard-Wert
        
        # Erstelle Voice-Modell-Verzeichnis falls nicht vorhanden
        self.VOICE_MODELS_DIR.mkdir(exist_ok=True)
        
        if COQUI_AVAILABLE:
            try:
                import torch
                self.gpu_available = torch.cuda.is_available()
                
                # Lade zuletzt genutztes TTS-Modell
                saved_model_id = self._get_last_tts_model()
                if saved_model_id and saved_model_id in self.AVAILABLE_TTS_MODELS:
                    self.current_tts_model_id = saved_model_id
                
                if XTTS_DIRECT and self.gpu_available and self.current_tts_model_id.startswith("xtts"):
                    # Direkter XTTS-Zugriff für beste Kontrolle
                    self._init_xtts_direct()
                else:
                    # Fallback auf TTS API
                    self._init_tts_api()
                    
            except Exception as e:
                print(f"Fehler bei XTTS-Init: {e}")
                self._init_fallback()
        else:
            self._init_pyttsx3()
    
    def _get_model_name(self):
        """Gibt den model_name für das aktuelle TTS-Modell zurück"""
        if self.current_tts_model_id in self.AVAILABLE_TTS_MODELS:
            return self.AVAILABLE_TTS_MODELS[self.current_tts_model_id]["model_name"]
        return "tts_models/multilingual/multi-dataset/xtts_v2"
    
    def _init_xtts_direct(self):
        """Initialisiert XTTS mit direktem Modell-Zugriff für beste Qualität"""
        import torch
        
        model_name = self._get_model_name()
        
        # Lade Modell über TTS API (lädt automatisch herunter)
        self.tts_api = TTS(model_name=model_name, gpu=True)
        
        # Direkter Zugriff auf das XTTS-Modell für erweiterte Kontrolle
        self.model = self.tts_api.synthesizer.tts_model
        self.use_coqui = True
        self.use_direct = True
        
        gpu_name = torch.cuda.get_device_name(0)
        model_info = self.AVAILABLE_TTS_MODELS.get(self.current_tts_model_id, {})
        print(f"{model_info.get('name', 'TTS')} initialisiert (Direkter Zugriff) mit GPU: {gpu_name}")
        print(f"  - gpt_cond_len: {self.gpt_cond_len}s (mehr Kontext)")
        print(f"  - gpt_cond_chunk_len: {self.gpt_cond_chunk_len}s (stabilere Latents)")
        print(f"  - max_ref_len: {self.max_ref_len}s (längere Referenz)")
    
    def _init_tts_api(self):
        """Fallback auf TTS API"""
        import torch
        model_name = self._get_model_name()
        self.tts_api = TTS(model_name=model_name, gpu=self.gpu_available)
        self.model = None
        self.use_coqui = True
        self.use_direct = False
        
        model_info = self.AVAILABLE_TTS_MODELS.get(self.current_tts_model_id, {})
        if self.gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"{model_info.get('name', 'TTS')} initialisiert (API-Modus) mit GPU: {gpu_name}")
        else:
            print(f"{model_info.get('name', 'TTS')} initialisiert (API-Modus) mit CPU")
    
    def _init_fallback(self):
        """Fallback auf einfacheres Modell"""
        self.tts_api = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC")
        self.model = None
        self.use_coqui = True
        self.use_direct = False
        self.current_tts_model_id = "fallback"
        print("Coqui TTS initialisiert (Thorsten Fallback)")
    
    def _init_pyttsx3(self):
        """Fallback auf pyttsx3"""
        import pyttsx3
        self.engine = pyttsx3.init()
        self.model = None
        self.use_coqui = False
        self.use_direct = False
        self.current_tts_model_id = "pyttsx3"
        print("pyttsx3 TTS initialisiert (Fallback)")
    
    def set_speaker_wav(self, wav_files):
        """
        Setzt Audio-Samples für Voice Cloning und berechnet Speaker Embeddings
        
        Args:
            wav_files (list): Liste von Pfaden zu WAV-Dateien oder None
        """
        self.speaker_wav = wav_files
        
        # Invalidiere Cache wenn sich die Samples ändern
        if wav_files != self.cached_speaker_wav:
            self.gpt_cond_latent = None
            self.speaker_embedding = None
            self.cached_speaker_wav = wav_files
            
            # Berechne Embeddings vorab für bessere Qualität
            if wav_files and len(wav_files) > 0 and self.use_direct and self.model:
                self._compute_speaker_latents(wav_files)
    
    def _compute_speaker_latents(self, wav_files):
        """
        Berechnet Speaker Latents mit optimierten Parametern für bessere Stimmerfassung
        """
        try:
            import torch
            print("Berechne optimierte Speaker-Embeddings...")
            
            # Seed setzen für Reproduzierbarkeit
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(self.seed)
            
            # Erweiterte Konditionierung für bessere Stimmerfassung
            # Nur Parameter verwenden, die von der API unterstützt werden
            self.gpt_cond_latent, self.speaker_embedding = self.model.get_conditioning_latents(
                audio_path=wav_files,
                gpt_cond_len=self.gpt_cond_len,  # Mehr Audio für GPT-Konditionierung
                gpt_cond_chunk_len=self.gpt_cond_chunk_len,  # Stabilere Chunk-Verarbeitung
            )
            
            print(f"Speaker-Embeddings berechnet aus {len(wav_files)} Sample(s)")
            print(f"  - GPT Latent Shape: {self.gpt_cond_latent.shape}")
            print(f"  - Speaker Embedding Shape: {self.speaker_embedding.shape}")
            
        except Exception as e:
            print(f"Fehler bei Speaker-Embedding-Berechnung: {e}")
            self.gpt_cond_latent = None
            self.speaker_embedding = None
    
    def save_voice_model(self, name):
        """
        Speichert das aktuelle Voice-Modell (Speaker-Embeddings) auf der Festplatte
        
        Args:
            name (str): Name für das Voice-Modell (z.B. "meine_stimme")
            
        Returns:
            str: Pfad zur gespeicherten Datei oder None bei Fehler
        """
        if self.gpt_cond_latent is None or self.speaker_embedding is None:
            print("Keine Speaker-Embeddings zum Speichern vorhanden!")
            return None
        
        try:
            import torch
            
            # Bereinige den Namen für Dateinamen
            safe_name = "".join(c for c in name if c.isalnum() or c in "._- ").strip()
            if not safe_name:
                safe_name = "voice_model"
            
            model_path = self.VOICE_MODELS_DIR / f"{safe_name}.pt"
            
            # Speichere die Embeddings und alle Parameter
            sample_count = len(self.speaker_wav) if self.speaker_wav else 1
            torch.save({
                'gpt_cond_latent': self.gpt_cond_latent,
                'speaker_embedding': self.speaker_embedding,
                'gpt_cond_len': self.gpt_cond_len,
                'gpt_cond_chunk_len': self.gpt_cond_chunk_len,
                'temperature': self.temperature,
                'top_k': self.top_k,
                'top_p': self.top_p,
                'repetition_penalty': self.repetition_penalty,
                'speed': self.speed,
                'seed': self.seed,
                'sample_count': sample_count,
                'name': name
            }, model_path)
            
            self.current_voice_name = name
            print(f"Voice-Modell '{name}' gespeichert unter: {model_path}")
            
            # Speichere als zuletzt genutztes Modell
            self._save_last_model_name(name)
            
            return str(model_path)
            
        except Exception as e:
            print(f"Fehler beim Speichern des Voice-Modells: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_voice_model(self, name_or_path):
        """
        Lädt ein gespeichertes Voice-Modell von der Festplatte
        
        Args:
            name_or_path (str): Name des Modells oder vollständiger Pfad
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            import torch
            
            # Prüfe ob es ein Pfad oder ein Name ist
            if os.path.isfile(name_or_path):
                model_path = Path(name_or_path)
            else:
                # Suche im Voice-Modell-Verzeichnis
                model_path = self.VOICE_MODELS_DIR / f"{name_or_path}.pt"
            
            if not model_path.exists():
                print(f"Voice-Modell nicht gefunden: {model_path}")
                return False
            
            # Lade die Embeddings
            data = torch.load(model_path, map_location='cuda' if torch.cuda.is_available() else 'cpu')
            
            self.gpt_cond_latent = data['gpt_cond_latent']
            self.speaker_embedding = data['speaker_embedding']
            self.current_voice_name = data.get('name', model_path.stem)
            
            # HINWEIS: gpt_cond_len und temperature werden NICHT aus der Datei geladen,
            # da die optimierten Standardwerte (gpt_cond_len=5, temperature=0.70) 
            # bessere Pitch-Reproduktion liefern (getestet mit Samples 29+41)
            
            # Nur diese Parameter wiederherstellen:
            if 'top_k' in data:
                self.top_k = data['top_k']
            if 'top_p' in data:
                self.top_p = data['top_p']
            if 'repetition_penalty' in data:
                # Begrenze auf gültigen Bereich (1.0 - 2.0)
                self.repetition_penalty = min(data['repetition_penalty'], 2.0)
            if 'speed' in data:
                self.speed = data['speed']
            if 'seed' in data:
                self.seed = data['seed']
            
            print(f"Voice-Modell '{self.current_voice_name}' geladen!")
            print(f"  - GPT Latent Shape: {self.gpt_cond_latent.shape}")
            print(f"  - Speaker Embedding Shape: {self.speaker_embedding.shape}")
            print(f"  - Aktuelle Parameter: gpt_cond_len={self.gpt_cond_len}, temperature={self.temperature}")
            
            # Speichere als zuletzt genutztes Modell
            self._save_last_model_name(self.current_voice_name)
            
            return True
            
        except Exception as e:
            print(f"Fehler beim Laden des Voice-Modells: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_saved_voice_models(self):
        """
        Listet alle gespeicherten Voice-Modelle auf
        
        Returns:
            list: Liste von Dictionaries mit 'name', 'path' und 'sample_count' für jedes Modell
        """
        import torch
        models = []
        if self.VOICE_MODELS_DIR.exists():
            for model_file in self.VOICE_MODELS_DIR.glob("*.pt"):
                # Versuche sample_count aus der Datei zu lesen
                sample_count = 1  # Default
                try:
                    data = torch.load(model_file, map_location='cpu', weights_only=False)
                    sample_count = data.get('sample_count', 1)
                except:
                    pass
                
                models.append({
                    'name': model_file.stem,
                    'path': str(model_file),
                    'sample_count': sample_count
                })
        return models
    
    def delete_voice_model(self, name):
        """
        Löscht ein gespeichertes Voice-Modell
        
        Args:
            name (str): Name des zu löschenden Modells
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        try:
            model_path = self.VOICE_MODELS_DIR / f"{name}.pt"
            if model_path.exists():
                model_path.unlink()
                print(f"Voice-Modell '{name}' gelöscht")
                return True
            else:
                print(f"Voice-Modell '{name}' nicht gefunden")
                return False
        except Exception as e:
            print(f"Fehler beim Löschen: {e}")
            return False
    
    def _save_last_model_name(self, name):
        """Speichert den Namen des zuletzt genutzten Modells"""
        try:
            self.LAST_MODEL_FILE.write_text(name, encoding='utf-8')
        except Exception as e:
            print(f"Fehler beim Speichern des letzten Modellnamens: {e}")
    
    def _get_last_model_name(self):
        """Gibt den Namen des zuletzt genutzten Modells zurück"""
        try:
            if self.LAST_MODEL_FILE.exists():
                return self.LAST_MODEL_FILE.read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"Fehler beim Lesen des letzten Modellnamens: {e}")
        return None
    
    def _save_last_tts_model(self, model_id):
        """Speichert die ID des zuletzt genutzten TTS-Modells"""
        try:
            self.LAST_TTS_MODEL_FILE.write_text(model_id, encoding='utf-8')
        except Exception as e:
            print(f"Fehler beim Speichern des TTS-Modells: {e}")
    
    def _get_last_tts_model(self):
        """Gibt die ID des zuletzt genutzten TTS-Modells zurück"""
        try:
            if self.LAST_TTS_MODEL_FILE.exists():
                return self.LAST_TTS_MODEL_FILE.read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"Fehler beim Lesen des TTS-Modells: {e}")
        return None
    
    def get_available_tts_models(self):
        """
        Gibt alle verfügbaren TTS-Modelle zurück
        
        Returns:
            dict: Dictionary mit Modell-IDs als Keys und Modell-Infos als Values
        """
        return self.AVAILABLE_TTS_MODELS
    
    def get_current_tts_model(self):
        """
        Gibt das aktuell geladene TTS-Modell zurück
        
        Returns:
            dict: Dictionary mit model_id und model_info
        """
        model_info = self.AVAILABLE_TTS_MODELS.get(self.current_tts_model_id, {})
        return {
            "model_id": self.current_tts_model_id,
            "model_info": model_info,
            "supports_cloning": model_info.get("supports_cloning", False)
        }
    
    def switch_tts_model(self, model_id):
        """
        Wechselt zu einem anderen TTS-Modell
        
        Args:
            model_id (str): ID des neuen Modells (z.B. "xtts_v2", "bark", "vits_de")
            
        Returns:
            bool: True bei Erfolg, False bei Fehler
        """
        if model_id not in self.AVAILABLE_TTS_MODELS:
            print(f"Unbekanntes TTS-Modell: {model_id}")
            return False
        
        if model_id == self.current_tts_model_id:
            print(f"TTS-Modell {model_id} ist bereits aktiv")
            return True
        
        try:
            import torch
            
            print(f"Wechsle TTS-Modell zu: {self.AVAILABLE_TTS_MODELS[model_id]['name']}")
            
            # Alte Ressourcen freigeben
            if hasattr(self, 'tts_api') and self.tts_api:
                del self.tts_api
            if hasattr(self, 'model') and self.model:
                del self.model
            
            # GPU-Speicher freigeben
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Neues Modell setzen
            self.current_tts_model_id = model_id
            
            # Cache invalidieren
            self.gpt_cond_latent = None
            self.speaker_embedding = None
            
            # Neues Modell laden
            if XTTS_DIRECT and self.gpu_available and model_id.startswith("xtts"):
                self._init_xtts_direct()
            else:
                self._init_tts_api()
            
            # Präferenz speichern
            self._save_last_tts_model(model_id)
            
            print(f"TTS-Modell gewechselt zu: {self.AVAILABLE_TTS_MODELS[model_id]['name']}")
            return True
            
        except Exception as e:
            print(f"Fehler beim Wechseln des TTS-Modells: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_last_model(self):
        """
        Lädt automatisch das zuletzt genutzte Voice-Modell
        
        Returns:
            bool: True wenn ein Modell geladen wurde, False sonst
        """
        last_name = self._get_last_model_name()
        if last_name:
            model_path = self.VOICE_MODELS_DIR / f"{last_name}.pt"
            if model_path.exists():
                print(f"Lade zuletzt genutztes Voice-Modell: {last_name}")
                return self.load_voice_model(last_name)
            else:
                print(f"Zuletzt genutztes Modell '{last_name}' nicht mehr vorhanden")
        return False
            
    def speak(self, text, rate=150, language='de'):
        """
        Spricht den übergebenen Text mit optimiertem Voice Cloning aus
        
        Args:
            text (str): Der zu sprechende Text
            rate (int): Sprechgeschwindigkeit (Wörter pro Minute)
            language (str): Sprachcode (z.B. 'de', 'en')
        """
        if not text.strip():
            return
            
        self.is_speaking = True
        
        try:
            if self.use_coqui:
                self._speak_coqui(text, language)
            else:
                self._speak_pyttsx3(text, rate, language)
        except Exception as e:
            print(f"Fehler beim Vorlesen: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_speaking = False
    
    def speak_and_save(self, text, rate=150, language='de'):
        """
        Spricht den Text aus und gibt den Pfad zur Audio-Datei zurück
        
        Args:
            text (str): Der zu sprechende Text
            rate (int): Sprechgeschwindigkeit (Wörter pro Minute)
            language (str): Sprachcode (z.B. 'de', 'en')
            
        Returns:
            str: Pfad zur gespeicherten WAV-Datei oder None bei Fehler
        """
        if not text.strip():
            return None
            
        self.is_speaking = True
        
        try:
            if self.use_coqui:
                return self._speak_coqui_and_save(text, language)
            else:
                self._speak_pyttsx3(text, rate, language)
                return None
        except Exception as e:
            print(f"Fehler beim Vorlesen: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.is_speaking = False
    
    def _speak_coqui_and_save(self, text, language):
        """Sprachausgabe mit Coqui TTS und Rückgabe des Audio-Pfads"""
        import torch
        import numpy as np
        import random
        import sounddevice as sd
        import soundfile as sf
        
        # Seed setzen für konsistente Ausgabe
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)
        
        # Persistente Datei im temp-Verzeichnis erstellen
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "speakalike_last_audio.wav")
        
        if self.use_direct and self.model and self.gpt_cond_latent is not None:
            self._inference_direct(text, language, output_path)
        elif self.speaker_wav and len(self.speaker_wav) > 0:
            self._inference_api_cloning(text, language, output_path)
        else:
            self._inference_api_default(text, language, output_path)
        
        # Audio abspielen (nur wenn nicht headless/API-Modus)
        if not getattr(self, 'headless_mode', False):
            data, samplerate = sf.read(output_path)
            sd.play(data, samplerate, device=self.output_device)
            sd.wait()
        
        return output_path
    
    def _speak_coqui(self, text, language):
        """Sprachausgabe mit Coqui TTS (optimiert)"""
        import torch
        import numpy as np
        import random
        import sounddevice as sd
        import soundfile as sf
        
        # Seed setzen für konsistente Ausgabe
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            if self.use_direct and self.model and self.gpt_cond_latent is not None:
                # Direkter XTTS-Zugriff mit gecachten Embeddings (beste Qualität)
                self._inference_direct(text, language, output_path)
            elif self.speaker_wav and len(self.speaker_wav) > 0:
                # TTS API mit Voice Cloning
                self._inference_api_cloning(text, language, output_path)
            else:
                # TTS API ohne Voice Cloning
                self._inference_api_default(text, language, output_path)
            
            # Audio abspielen
            data, samplerate = sf.read(output_path)
            sd.play(data, samplerate, device=self.output_device)
            sd.wait()
            
        finally:
            try:
                os.unlink(output_path)
            except:
                pass
    
    def _inference_direct(self, text, language, output_path):
        """Direkte XTTS-Inference mit optimierten Parametern"""
        import torch
        import numpy as np
        import scipy.io.wavfile as wavfile
        import time
        
        start_time = time.time()
        print(f"Generiere Audio...")
        print(f"  Parameter: gpt_cond_len={self.gpt_cond_len}, temperature={self.temperature}")
        
        # Streaming-Modus für schnelleres erstes Audio
        if self.use_streaming:
            self._inference_direct_streaming(text, language, output_path)
            print(f"  Generierung abgeschlossen in {time.time() - start_time:.2f}s (Streaming)")
            return
        
        # Generiere den gesamten Text in einem Stück
        out = self.model.inference(
            text=text,
            language=language,
            gpt_cond_latent=self.gpt_cond_latent,
            speaker_embedding=self.speaker_embedding,
            temperature=self.temperature,
            length_penalty=self.length_penalty,
            repetition_penalty=self.repetition_penalty,
            top_k=self.top_k,
            top_p=self.top_p,
            speed=self.speed,
            enable_text_splitting=True
        )
        
        wav = np.array(out["wav"])
        
        # DEBUG: Speichere Audio VOR dem Trimming auf Desktop
        import os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        debug_path = os.path.join(desktop, "DEBUG_vor_trim.wav")
        wav_debug = np.clip(wav, -1.0, 1.0)
        wav_debug_int16 = (wav_debug * 32767).astype(np.int16)
        wavfile.write(debug_path, 24000, wav_debug_int16)
        print(f"  DEBUG: Audio vor Trimming gespeichert: {debug_path}")
        
        # Artefakte am Ende entfernen
        wav = self._remove_artifacts_with_transcription(wav, text, sample_rate=24000)
        
        # Speichern als Standard-PCM WAV (16-bit) für maximale Kompatibilität
        wav = np.clip(wav, -1.0, 1.0)
        wav_int16 = (wav * 32767).astype(np.int16)
        wavfile.write(output_path, 24000, wav_int16)
        print(f"  Generierung abgeschlossen in {time.time() - start_time:.2f}s")
    
    def _inference_direct_streaming(self, text, language, output_path):
        """Streaming-Inference für schnellere erste Audioausgabe"""
        import torch
        import torchaudio
        import numpy as np
        
        chunks = []
        
        # Streaming-Generator verwenden
        for chunk in self.model.inference_stream(
            text=text,
            language=language,
            gpt_cond_latent=self.gpt_cond_latent,
            speaker_embedding=self.speaker_embedding,
            temperature=self.temperature,
            length_penalty=self.length_penalty,
            repetition_penalty=self.repetition_penalty,
            top_k=self.top_k,
            top_p=self.top_p,
            speed=self.speed,
            enable_text_splitting=True,
            stream_chunk_size=20  # Kleinere Chunks = schnellerer Start
        ):
            chunks.append(chunk)
        
        # Alle Chunks zusammenfügen
        if chunks:
            wav = np.concatenate([c.cpu().numpy() for c in chunks])
            
            wav = self._remove_artifacts_with_transcription(wav, text, sample_rate=24000)
            torchaudio.save(output_path, torch.tensor(wav).unsqueeze(0), 24000)

    def _remove_artifacts_with_transcription(self, audio, expected_text, sample_rate=24000):
        """
        Entfernt Artefakte am Ende des Audios durch Whisper-Transkription.
        
        Vergleicht den transkribierten Text mit dem erwarteten Text und
        schneidet das Audio am Ende des erkannten Textes ab.
        
        Args:
            audio: Audio-Array (numpy)
            expected_text: Der erwartete Text der gesprochen wurde
            sample_rate: Sample-Rate des Audios
            
        Returns:
            Getrimmtes Audio-Array
        """
        import numpy as np
        
        if len(audio) == 0:
            return audio
        
        try:
            # Lazy-Load Whisper beim ersten Aufruf
            if not hasattr(self, '_whisper_model') or self._whisper_model is None:
                print("  Lade Whisper-Modell für Artefakt-Erkennung...")
                import whisper
                # Verwende das base Modell - gut für Deutsch
                self._whisper_model = whisper.load_model("base", device="cuda")
                print("  Whisper-Modell geladen.")
            
            # Whisper erwartet Audio bei 16kHz als float32 im Bereich [-1, 1]
            import torch
            import torchaudio
            
            # Konvertiere numpy zu torch tensor
            audio_tensor = torch.tensor(audio).float()
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Resample zu 16kHz mit torchaudio (bessere Qualität als scipy)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                audio_16k = resampler(audio_tensor).squeeze().numpy()
            else:
                audio_16k = audio_tensor.squeeze().numpy()
            
            # Normalisiere Audio für Whisper (wichtig!)
            audio_16k = audio_16k.astype(np.float32)
            max_val = np.max(np.abs(audio_16k))
            if max_val > 0:
                audio_16k = audio_16k / max_val
            
            # Debug: Zeige Audio-Info
            print(f"  Whisper-Input: {len(audio_16k)} samples, max={np.max(np.abs(audio_16k)):.3f}, dtype={audio_16k.dtype}")
            
            # Transkribiere mit Wort-Zeitstempeln
            result = self._whisper_model.transcribe(
                audio_16k,
                language="de",
                word_timestamps=True,
                fp16=torch.cuda.is_available(),
                verbose=False
            )
            
            # Debug: Zeige was erkannt wurde
            if result.get("text"):
                print(f"  Whisper erkannt: '{result['text'][:100]}...' " if len(result.get("text", "")) > 100 else f"  Whisper erkannt: '{result.get('text', '')}'")
            else:
                print("  Whisper: Kein Text erkannt")
            
            # Finde das letzte Wort das zum erwarteten Text gehört
            expected_words = self._normalize_text(expected_text).split()
            
            if not result.get("segments"):
                print("  Keine Segmente erkannt, verwende Fallback-Trimming")
                return self._remove_trailing_artifacts(audio, sample_rate)
            
            # Sammle alle erkannten Wörter mit Zeitstempeln
            recognized_words = []
            for segment in result["segments"]:
                if "words" in segment:
                    for word_info in segment["words"]:
                        word = self._normalize_text(word_info["word"])
                        if word:
                            recognized_words.append({
                                "word": word,
                                "start": word_info["start"],
                                "end": word_info["end"]
                            })
            
            if not recognized_words:
                print("  Keine Wörter erkannt, verwende Fallback-Trimming")
                return self._remove_trailing_artifacts(audio, sample_rate)
            
            # Debug: Zeige erkannte Wörter
            print(f"  Erkannte Wörter ({len(recognized_words)}): {[w['word'] for w in recognized_words]}")
            print(f"  Erwartete Wörter ({len(expected_words)}): {expected_words}")
            
            # Strategie: Einfach zählen!
            # Der erwartete Text hat N Wörter → nimm das Ende des N-ten erkannten Wortes
            num_expected = len(expected_words)
            
            if len(recognized_words) >= num_expected:
                # Alle Wörter erkannt - schneide nach dem letzten erwarteten Wort
                last_valid_word_info = recognized_words[num_expected - 1]
                last_valid_end = last_valid_word_info["end"]
                last_valid_word = last_valid_word_info["word"]
                
                print(f"  Erwarte {num_expected} Wörter, schneide nach Wort {num_expected}: '{last_valid_word}' bei {last_valid_end:.2f}s")
            else:
                # Weniger erkannte Wörter als erwartet - nimm alles
                last_valid_word_info = recognized_words[-1]
                last_valid_end = last_valid_word_info["end"]
                last_valid_word = last_valid_word_info["word"]
                
                print(f"  Nur {len(recognized_words)} von {num_expected} Wörtern erkannt, verwende alle bis '{last_valid_word}' bei {last_valid_end:.2f}s")
            
            if last_valid_end > 0:
                # Konvertiere Zeit zurück zu Sample-Position (bei Original-Samplerate)
                end_sample = int(last_valid_end * sample_rate)
                # Füge 350ms Puffer hinzu für natürliches Ausklingen
                end_sample = min(end_sample + int(0.35 * sample_rate), len(audio))
                
                # Sanftes Fade-Out (150ms) für natürlichen Übergang
                fade_duration = 0.15  # 150ms
                fade_samples = int(fade_duration * sample_rate)
                if end_sample > fade_samples:
                    fade_start = end_sample - fade_samples
                    # Exponentielles Fade-Out für natürlicheren Klang
                    fade_curve = np.power(np.linspace(1.0, 0.0, fade_samples), 2)
                    audio = audio.copy()
                    audio[fade_start:end_sample] *= fade_curve[:end_sample - fade_start]
                
                trimmed = audio[:end_sample]
                
                original_duration = len(audio) / sample_rate
                trimmed_duration = len(trimmed) / sample_rate
                
                if original_duration - trimmed_duration > 0.05:
                    print(f"  -> Whisper-Trimming: {original_duration:.2f}s -> {trimmed_duration:.2f}s "
                          f"({original_duration - trimmed_duration:.2f}s Artefakte entfernt)")
                    print(f"    Letztes Wort: '{last_valid_word}'")
                
                return trimmed
            else:
                print("  Kein Text erkannt, verwende Fallback-Trimming")
                return self._remove_trailing_artifacts(audio, sample_rate)
                
        except ImportError:
            print("  Whisper nicht installiert, verwende Fallback-Trimming")
            return self._remove_trailing_artifacts(audio, sample_rate)
        except Exception as e:
            print(f"  Whisper-Fehler: {e}, verwende Fallback-Trimming")
            return self._remove_trailing_artifacts(audio, sample_rate)
    
    def _normalize_text(self, text):
        """Normalisiert Text für Vergleich (Kleinbuchstaben, nur alphanumerisch)"""
        import re
        text = text.lower().strip()
        # Entferne Satzzeichen
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def _is_likely_artifact(self, word):
        """
        Prüft ob ein Wort wahrscheinlich ein Artefakt/Halluzination ist.
        
        Artefakte haben oft:
        - Nicht-lateinische Zeichen
        - Sehr kurze ungewöhnliche Zeichenfolgen
        - Sonderzeichen
        """
        import re
        
        if not word:
            return True
        
        # Prüfe auf nicht-lateinische Zeichen (außer deutschen Umlauten)
        # Erlaubt: a-z, äöüß, Zahlen
        latin_pattern = re.compile(r'^[a-zäöüß0-9]+$', re.IGNORECASE)
        if not latin_pattern.match(word):
            return True
        
        # Sehr kurze Wörter die keine deutschen Wörter sind
        common_short = {'ich', 'du', 'er', 'es', 'ja', 'so', 'da', 'an', 'in', 'um', 'zu', 'ob', 'wo', 'oh', 'ah', 'na', 'ey', 'hi', 'ok'}
        if len(word) <= 2 and word.lower() not in common_short:
            return True
        
        return False
    
    def _words_match(self, word1, word2, threshold=0.5):
        """Prüft ob zwei Wörter ähnlich genug sind (fuzzy match)"""
        w1 = word1.lower()
        w2 = word2.lower()
        
        # Exakter Match
        if w1 == w2:
            return True
        
        # Normalisiere phonetisch ähnliche Schreibweisen (deutsch/englisch)
        def normalize(w):
            replacements = [
                ('tz', 'z'), ('ts', 'z'), ('ceps', 'zeps'),  # biceps -> bizeps
                ('ph', 'f'), ('ck', 'k'), ('dt', 't'), ('th', 't'),
                ('ae', 'ä'), ('oe', 'ö'), ('ue', 'ü'), ('ss', 'ß'),
                ('ai', 'ei'), ('ey', 'ei'), ('ay', 'ei'),
                ('c', 'k'), ('qu', 'kw'), ('x', 'ks'), ('y', 'i'),
            ]
            for old, new in replacements:
                w = w.replace(old, new)
            return w
        
        w1_norm = normalize(w1)
        w2_norm = normalize(w2)
        
        # Match nach Normalisierung
        if w1_norm == w2_norm:
            return True
        
        # Ein Wort enthält das andere - aber nur wenn das kürzere Wort lang genug ist
        # und das längere Wort nicht viel länger ist (verhindert "der" in "ender")
        min_len = min(len(w1), len(w2))
        max_len = max(len(w1), len(w2))
        if min_len >= 4 and max_len <= min_len + 2:  # Strenger: mind. 4 Zeichen, max 2 Zeichen Differenz
            if w1 in w2 or w2 in w1:
                return True
            if w1_norm in w2_norm or w2_norm in w1_norm:
                return True
        
        # Gleicher Anfang (mind. 3 Zeichen) - nur wenn Längen ähnlich sind
        if len(w1) >= 3 and len(w2) >= 3 and abs(len(w1) - len(w2)) <= 2:
            if w1[:3] == w2[:3]:
                return True
            # Oder gleicher Anfang mit 2 Zeichen bei kürzeren Wörtern
            if w1[:2] == w2[:2] and (len(w1) <= 5 or len(w2) <= 5):
                return True
        
        # Levenshtein-ähnliche Prüfung für kleine Unterschiede
        if abs(len(w1) - len(w2)) <= 3:
            matches = sum(c1 == c2 for c1, c2 in zip(w1, w2))
            max_len = max(len(w1), len(w2))
            if max_len > 0 and matches / max_len >= threshold:
                return True
        
        # Auch für normalisierte Versionen
        if abs(len(w1_norm) - len(w2_norm)) <= 3:
            matches = sum(c1 == c2 for c1, c2 in zip(w1_norm, w2_norm))
            max_len = max(len(w1_norm), len(w2_norm))
            if max_len > 0 and matches / max_len >= threshold:
                return True
        
        return False
    
    def _remove_trailing_artifacts(self, audio, sample_rate=24000, 
                                    silence_threshold_db=-35, 
                                    min_silence_duration=0.15):
        """
        Entfernt Artefakte/Halluzinationen am Ende des Audios.
        
        Sucht nach der letzten signifikanten Sprachaktivität und schneidet
        danach ab, um unverständliche Laute am Ende zu entfernen.
        
        Args:
            audio: Audio-Array
            sample_rate: Sample-Rate
            silence_threshold_db: Schwellwert für Stille in dB
            min_silence_duration: Minimale Stille-Dauer um Ende zu erkennen
        """
        import numpy as np
        
        if len(audio) == 0:
            return audio
        
        # Berechne RMS-Energie in kleinen Fenstern
        window_size = int(0.02 * sample_rate)  # 20ms Fenster
        hop_size = window_size // 2
        
        # Sliding window RMS
        num_windows = (len(audio) - window_size) // hop_size + 1
        if num_windows <= 0:
            return audio
            
        rms_values = []
        for i in range(num_windows):
            start = i * hop_size
            end = start + window_size
            window = audio[start:end]
            rms = np.sqrt(np.mean(window ** 2))
            rms_values.append(rms)
        
        rms_values = np.array(rms_values)
        
        # Konvertiere zu dB
        rms_db = 20 * np.log10(rms_values + 1e-10)
        max_db = np.max(rms_db)
        rms_db_normalized = rms_db - max_db
        
        # Finde die letzte Position mit Sprache
        is_speech = rms_db_normalized > silence_threshold_db
        
        # Suche von hinten nach vorne nach dem letzten Sprachsegment
        min_silence_windows = int(min_silence_duration * sample_rate / hop_size)
        
        last_speech_window = len(is_speech) - 1
        silence_count = 0
        
        for i in range(len(is_speech) - 1, -1, -1):
            if is_speech[i]:
                if silence_count >= min_silence_windows:
                    # Wir haben ein Stille-Segment nach Sprache gefunden
                    # Das könnte der Beginn von Artefakten sein
                    last_speech_window = i + min_silence_windows // 2
                    break
                silence_count = 0
            else:
                silence_count += 1
        
        # Berechne die Sample-Position
        end_sample = min((last_speech_window + 1) * hop_size + window_size, len(audio))
        
        # Füge ein kurzes Fade-Out hinzu (50ms)
        fade_samples = int(0.05 * sample_rate)
        if end_sample > fade_samples:
            fade_start = end_sample - fade_samples
            fade_curve = np.linspace(1.0, 0.0, fade_samples)
            audio[fade_start:end_sample] *= fade_curve[:end_sample - fade_start]
        
        # Schneide ab
        trimmed = audio[:end_sample]
        
        original_duration = len(audio) / sample_rate
        trimmed_duration = len(trimmed) / sample_rate
        
        if original_duration - trimmed_duration > 0.1:
            print(f"  -> Audio getrimmt: {original_duration:.2f}s -> {trimmed_duration:.2f}s "
                  f"({original_duration - trimmed_duration:.2f}s Artefakte entfernt)")
        
        return trimmed
    
    def _remove_trailing_silence(self, audio, sample_rate=24000, silence_threshold_db=-40):
        """
        Entfernt nur echte Stille am Ende des Audios (weniger aggressiv).
        
        Behält mehr Audio als _remove_trailing_artifacts, gut wenn
        Whisper nicht alles erkannt hat aber das Audio komplett ist.
        """
        import numpy as np
        
        if len(audio) == 0:
            return audio
        
        # Berechne RMS-Energie in kleinen Fenstern
        window_size = int(0.05 * sample_rate)  # 50ms Fenster
        hop_size = window_size // 2
        
        num_windows = (len(audio) - window_size) // hop_size + 1
        if num_windows <= 0:
            return audio
        
        # Finde von hinten nach vorne die erste Stelle mit echtem Audio
        for i in range(num_windows - 1, -1, -1):
            start = i * hop_size
            end = start + window_size
            window = audio[start:end]
            rms = np.sqrt(np.mean(window ** 2))
            rms_db = 20 * np.log10(rms + 1e-10)
            
            if rms_db > silence_threshold_db:
                # Hier ist noch Audio - schneide 300ms danach ab
                end_sample = min(end + int(0.3 * sample_rate), len(audio))
                
                # Fade-Out (100ms)
                fade_samples = int(0.1 * sample_rate)
                if end_sample > fade_samples:
                    fade_start = end_sample - fade_samples
                    fade_curve = np.linspace(1.0, 0.0, fade_samples)
                    audio = audio.copy()
                    audio[fade_start:end_sample] *= fade_curve[:end_sample - fade_start]
                
                trimmed = audio[:end_sample]
                
                original_duration = len(audio) / sample_rate
                trimmed_duration = len(trimmed) / sample_rate
                
                if original_duration - trimmed_duration > 0.1:
                    print(f"  -> Silence-Trimming: {original_duration:.2f}s -> {trimmed_duration:.2f}s")
                
                return trimmed
        
        return audio
    
    def _inference_api_cloning(self, text, language, output_path):
        """TTS API Inference mit Voice Cloning"""
        self.tts_api.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=self.speaker_wav,
            language=language,
            split_sentences=True,
            temperature=0.4,  # Niedrigere Temperatur für Konsistenz
            length_penalty=1.0,
            repetition_penalty=2.0,
            top_k=30,
            top_p=0.75
        )
    
    def _inference_api_default(self, text, language, output_path):
        """TTS API Inference ohne Voice Cloning - verwendet eingebaute Stimme"""
        # XTTS v2 hat eingebaute Speaker - verwende einen davon
        # Verfügbare Speaker können mit tts_api.speakers abgefragt werden
        try:
            # Versuche einen eingebauten Speaker zu verwenden
            available_speakers = getattr(self.tts_api, 'speakers', None)
            if available_speakers and len(available_speakers) > 0:
                # Verwende den ersten verfügbaren Speaker
                speaker = available_speakers[0]
                self.tts_api.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker=speaker,
                    language=language,
                    split_sentences=True,
                    temperature=0.5,
                    length_penalty=1.0,
                    repetition_penalty=2.0
                )
            else:
                # Fallback: Verwende eine Standard-Referenz-WAV oder einfache Ausgabe
                # Bei XTTS ohne Speaker-Wav funktioniert nur mit speaker_idx
                self.tts_api.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker="Claribel Dervla",  # Standard XTTS Speaker
                    language=language,
                    split_sentences=True
                )
        except Exception as e:
            print(f"Fehler bei Standard-TTS, versuche Fallback: {e}")
            # Letzter Fallback - einfachste Form
            self.tts_api.tts_to_file(
                text=text,
                file_path=output_path,
                language=language
            )
    
    def _speak_pyttsx3(self, text, rate, language):
        """Fallback Sprachausgabe mit pyttsx3"""
        self.engine.setProperty('rate', rate)
        voices = self.engine.getProperty('voices')
        
        for voice in voices:
            if language in voice.id.lower() or 'german' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.engine.say(text)
        self.engine.runAndWait()
    
    def speak_async(self, text, rate=150, language='de'):
        """Spricht Text asynchron in einem separaten Thread"""
        thread = threading.Thread(target=self.speak, args=(text, rate, language))
        thread.daemon = True
        thread.start()
        return thread
    
    def stop(self):
        """Stoppt die Wiedergabe"""
        if not self.use_coqui and hasattr(self, 'engine') and hasattr(self.engine, 'stop'):
            self.engine.stop()
        self.is_speaking = False


def main():
    """Kommandozeilen-Version für schnelle Tests"""
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        tts = TextToSpeech()
        print(f"Spreche: {text}")
        tts.speak(text)
    else:
        print("SpeakAlike - Text-to-Speech mit Coqui TTS")
        print("\nVerwendung:")
        print("  python main.py \"Ihr Text hier\"")
        print("\nOder starten Sie die GUI:")
        print("  python gui.py")


if __name__ == "__main__":
    main()
