"""
SpeakAlike - Text-to-Speech Application
"""
import sys
import threading
from pathlib import Path
import tempfile
import os

# Set Windows console to UTF-8 to avoid Unicode errors
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # reconfigure may not be available on older Python versions

# Add espeak-ng to PATH
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

# Coqui TTS imports are lazy-loaded to reduce startup time when ElevenLabs is active
COQUI_AVAILABLE = False
XTTS_DIRECT = False

def _load_coqui_imports():
    """Loads Coqui TTS libraries on demand"""
    global COQUI_AVAILABLE, XTTS_DIRECT, TTS, XttsConfig, Xtts
    if COQUI_AVAILABLE:
        return True
    try:
        from TTS.api import TTS as _TTS
        from TTS.tts.configs.xtts_config import XttsConfig as _XttsConfig
        from TTS.tts.models.xtts import Xtts as _Xtts
        TTS = _TTS
        XttsConfig = _XttsConfig
        Xtts = _Xtts
        COQUI_AVAILABLE = True
        XTTS_DIRECT = True
        return True
    except ImportError:
        try:
            from TTS.api import TTS as _TTS
            TTS = _TTS
            COQUI_AVAILABLE = True
            XTTS_DIRECT = False
            return True
        except ImportError:
            COQUI_AVAILABLE = False
            XTTS_DIRECT = False
            print("Warning: Coqui TTS not available.")
            return False


class TextToSpeech:
    """Text-to-Speech engine wrapper with optimised voice cloning"""
    
    # Directory for saved voice models
    _voice_models_env = os.environ.get('SPEAKALIKE_VOICE_MODELS')
    if _voice_models_env:
        VOICE_MODELS_DIR = Path(_voice_models_env)
    else:
        VOICE_MODELS_DIR = Path(__file__).parent / "voice_models"
    LAST_MODEL_FILE = VOICE_MODELS_DIR / ".last_model"
    LAST_TTS_MODEL_FILE = VOICE_MODELS_DIR / ".last_tts_model"
    
    # ElevenLabs configuration files
    ELEVENLABS_CONFIG_FILE = VOICE_MODELS_DIR / ".elevenlabs_config"
    
    # Available TTS models for voice cloning
    AVAILABLE_TTS_MODELS = {
        "xtts_v2": {
            "name": "XTTS v2 (Standard)",
            "model_name": "tts_models/multilingual/multi-dataset/xtts_v2",
            "supports_cloning": True,
            "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu", "hi"],
            "description": "Best quality, 17 languages, voice cloning"
        },
        "xtts_v1.1": {
            "name": "XTTS v1.1",
            "model_name": "tts_models/multilingual/multi-dataset/xtts_v1.1",
            "supports_cloning": True,
            "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh-cn", "ja", "ko", "hu", "hi"],
            "description": "Older version, slightly faster"
        },
        "bark": {
            "name": "Bark (Kreativ)",
            "model_name": "tts_models/multilingual/multi-dataset/bark",
            "supports_cloning": True,
            "languages": ["de", "en", "es", "fr", "it", "pt", "pl", "zh", "ja", "ko", "ru", "tr", "hi", "ar"],
            "description": "Creative voice, supports emotions"
        },
        "tortoise_v2": {
            "name": "Tortoise v2 (Langsam, HQ)",
            "model_name": "tts_models/en/multi-dataset/tortoise-v2",
            "supports_cloning": True,
            "languages": ["en"],
            "description": "Very high quality, English only, slow"
        },
        "vits_de": {
            "name": "VITS Deutsch (Schnell)",
            "model_name": "tts_models/de/thorsten/vits",
            "supports_cloning": False,
            "languages": ["de"],
            "description": "Fast, no voice cloning, German voice"
        }
    }
    
    def __init__(self, model_id="xtts_v2"):
        self.is_speaking = False
        self.speaker_wav = None
        self.seed = 42  # Fixed seed for consistent output
        
        # Output device (None = default device)
        self.output_device = None
        
        # Current TTS model
        self.current_tts_model_id = model_id
        
        # TTS provider: "elevenlabs" or "pyttsx3"
        self.tts_provider = "pyttsx3"  # Default (may be overridden by ElevenLabs config)
        
        # pyttsx3 state
        self.pyttsx3_voice_id = None  # specific SAPI5 voice ID (None = auto by language)
        self.pyttsx3_gender = None    # 'male', 'female' or None (auto)

        # ElevenLabs state
        self.elevenlabs_client = None
        self.elevenlabs_api_key = None
        self.elevenlabs_voice_id = None
        self.elevenlabs_model_id = "eleven_multilingual_v2"
        self.elevenlabs_stability = 0.5
        self.elevenlabs_similarity_boost = 0.75
        self.elevenlabs_style = 0.0
        self.elevenlabs_use_speaker_boost = False
        self._load_elevenlabs_config()
        
        # Speaker embedding cache for better quality and performance
        self.gpt_cond_latent = None
        self.speaker_embedding = None
        self.cached_speaker_wav = None
        self.current_voice_name = None  # Name of the currently loaded voice model
        
        # Performance settings
        self.use_streaming = False  # Streaming for faster first output
        
        # Optimised inference parameters (balance between quality and speed)
        self.gpt_cond_len = 6  # Reduced for faster generation (default: 12)
        self.gpt_cond_chunk_len = 3  # Smaller chunks = faster (default: 4)
        self.max_ref_len = 30  # Reduced for performance (default: 10)
        
        # Advanced quality settings
        self.temperature = 0.65  # Default value for better generation
        self.top_k = 50  # Default value
        self.top_p = 0.8  # Default value
        self.repetition_penalty = 1.5  # Reduced from 2.0 — too high clips words
        self.speed = 1.0  # Speech speed
        self.length_penalty = 1.0  # Default value
        
        # Create voice model directory if it doesn't exist
        self.VOICE_MODELS_DIR.mkdir(exist_ok=True)

        # Always initialise pyttsx3 as fallback
        self._init_pyttsx3()
        self.gpu_available = False
        self.model = None
        self.use_coqui = False
        self.use_direct = False
        if self.tts_provider == 'elevenlabs':
            print("ElevenLabs provider active, pyttsx3 ready as fallback")
    
    def _get_model_name(self):
        """Returns the model_name for the current TTS model"""
        if self.current_tts_model_id in self.AVAILABLE_TTS_MODELS:
            return self.AVAILABLE_TTS_MODELS[self.current_tts_model_id]["model_name"]
        return "tts_models/multilingual/multi-dataset/xtts_v2"
    
    def _init_xtts_direct(self):
        """Initialises XTTS with direct model access for best quality"""
        import torch
        
        # Enable GPU optimisations
        torch.backends.cudnn.benchmark = True
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        
        model_name = self._get_model_name()
        
        # Load model via TTS API (downloads automatically)
        self.tts_api = TTS(model_name=model_name, gpu=True)
        
        # Direct access to the XTTS model for extended control
        self.model = self.tts_api.synthesizer.tts_model
        
        self.use_coqui = True
        self.use_direct = True
        
        gpu_name = torch.cuda.get_device_name(0)
        model_info = self.AVAILABLE_TTS_MODELS.get(self.current_tts_model_id, {})
        print(f"{model_info.get('name', 'TTS')} initialised (direct access) with GPU: {gpu_name}")
        print(f"  - cudnn.benchmark: enabled")
        print(f"  - gpt_cond_len: {self.gpt_cond_len}s (more context)")
        print(f"  - gpt_cond_chunk_len: {self.gpt_cond_chunk_len}s (more stable latents)")
        print(f"  - max_ref_len: {self.max_ref_len}s (longer reference)")
    
    def _init_tts_api(self):
        """Fallback to TTS API"""
        import torch
        model_name = self._get_model_name()
        self.tts_api = TTS(model_name=model_name, gpu=self.gpu_available)
        self.model = None
        self.use_coqui = True
        self.use_direct = False
        
        model_info = self.AVAILABLE_TTS_MODELS.get(self.current_tts_model_id, {})
        if self.gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"{model_info.get('name', 'TTS')} initialised (API mode) with GPU: {gpu_name}")
        else:
            print(f"{model_info.get('name', 'TTS')} initialised (API mode) with CPU")
    
    def _init_fallback(self):
        """Fallback to a simpler model"""
        self.tts_api = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC")
        self.model = None
        self.use_coqui = True
        self.use_direct = False
        self.current_tts_model_id = "fallback"
        print("Coqui TTS initialised (Thorsten fallback)")
    
    def _init_pyttsx3(self):
        """Initialise pyttsx3 as fallback"""
        import pyttsx3
        self.engine = pyttsx3.init()
        self.current_tts_model_id = "pyttsx3"
        print("pyttsx3 TTS initialised (fallback)")

    def _check_internet(self):
        """Checks whether an internet connection is available"""
        import socket
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except Exception:
            return False

    def _speak_pyttsx3_and_save(self, text, language='de', rate=150):
        """Speech output via pyttsx3, returns audio path (subprocess, COM-safe)"""
        import subprocess, sys
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "speakalike_last_audio.wav")
        voice_arg = self.pyttsx3_voice_id or ''
        gender_arg = self.pyttsx3_gender or ''
        script = (
            "import pyttsx3, sys\n"
            "text, out, lang, rate, voice_id, gender = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5], sys.argv[6]\n"
            "e = pyttsx3.init()\n"
            "if voice_id:\n"
            "    e.setProperty('voice', voice_id)\n"
            "else:\n"
            "    voices = e.getProperty('voices')\n"
            "    def lang_ok(v): return ('_' + lang + '-') in v.id.lower()\n"
            "    def gen_ok(v): g = getattr(v, 'gender', None); return not gender or (g and g.lower() == gender.lower())\n"
            "    match = next((v for v in voices if lang_ok(v) and gen_ok(v)), None)\n"
            "    match = match or next((v for v in voices if lang_ok(v)), None)\n"
            "    if match: e.setProperty('voice', match.id)\n"
            "e.setProperty('rate', rate)\n"
            "e.save_to_file(text, out)\n"
            "e.runAndWait()\n"
            "e.stop()\n"
        )
        try:
            subprocess.run(
                [sys.executable, '-c', script, text, output_path, language, str(rate), voice_arg, gender_arg],
                timeout=30,
                check=True
            )
        except subprocess.TimeoutExpired:
            print("pyttsx3 subprocess timeout")
            return None
        except subprocess.CalledProcessError as e:
            print(f"pyttsx3 subprocess error: {e}")
            return None
        if os.path.exists(output_path):
            return output_path
        return None

    def get_pyttsx3_voices(self):
        """Returns a list of available pyttsx3 voices"""
        import pyttsx3
        try:
            e = pyttsx3.init()
            voices = [{'id': v.id, 'name': v.name, 'gender': getattr(v, 'gender', None)} for v in e.getProperty('voices')]
            e.stop()
            return voices
        except Exception as ex:
            print(f"Error loading pyttsx3 voices: {ex}")
            return []

    def set_speaker_wav(self, wav_files):
        """
        Sets audio samples for voice cloning and computes speaker embeddings
        
        Args:
            wav_files (list): List of paths to WAV files, or None
        """
        self.speaker_wav = wav_files
        
        # Invalidate cache when samples change
        if wav_files != self.cached_speaker_wav:
            self.gpt_cond_latent = None
            self.speaker_embedding = None
            self.cached_speaker_wav = wav_files
            
            # Pre-compute embeddings for better quality
            if wav_files and len(wav_files) > 0 and self.use_direct and self.model:
                self._compute_speaker_latents(wav_files)
    
    def _compute_speaker_latents(self, wav_files):
        """
        Computes speaker latents with optimised parameters for better voice capture
        """
        try:
            import torch
            print("Computing optimised speaker embeddings...")
            
            # Set seed for reproducibility
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(self.seed)
            
            # Extended conditioning for better voice capture
            # Only use parameters supported by the API
            self.gpt_cond_latent, self.speaker_embedding = self.model.get_conditioning_latents(
                audio_path=wav_files,
                gpt_cond_len=self.gpt_cond_len,  # More audio for GPT conditioning
                gpt_cond_chunk_len=self.gpt_cond_chunk_len,  # More stable chunk processing
            )
            
            print(f"Speaker embeddings computed from {len(wav_files)} sample(s)")
            print(f"  - GPT Latent Shape: {self.gpt_cond_latent.shape}")
            print(f"  - Speaker Embedding Shape: {self.speaker_embedding.shape}")
            
        except Exception as e:
            print(f"Error computing speaker embeddings: {e}")
            self.gpt_cond_latent = None
            self.speaker_embedding = None
    
    def save_voice_model(self, name):
        """
        Saves the current voice model (speaker embeddings) to disk
        
        Args:
            name (str): Name for the voice model (e.g. "my_voice")
            
        Returns:
            str: Path to the saved file, or None on error
        """
        if self.gpt_cond_latent is None or self.speaker_embedding is None:
            print("No speaker embeddings to save!")
            return None
        
        try:
            import torch
            
            # Clean the name for use as filename
            safe_name = "".join(c for c in name if c.isalnum() or c in "._- ").strip()
            if not safe_name:
                safe_name = "voice_model"
            
            model_path = self.VOICE_MODELS_DIR / f"{safe_name}.pt"
            
            # Save embeddings and all parameters
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
            print(f"Voice model '{name}' saved to: {model_path}")
            
            # Save as last used model
            self._save_last_model_name(name)
            
            return str(model_path)
            
        except Exception as e:
            print(f"Error saving voice model: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def load_voice_model(self, name_or_path):
        """
        Loads a saved voice model from disk
        
        Args:
            name_or_path (str): Model name or full file path
            
        Returns:
            bool: True on success, False on error
        """
        try:
            import torch
            
            # Check whether it's a path or a name
            if os.path.isfile(name_or_path):
                model_path = Path(name_or_path)
            else:
                # Look in the voice model directory
                model_path = self.VOICE_MODELS_DIR / f"{name_or_path}.pt"
            
            if not model_path.exists():
                print(f"Voice model not found: {model_path}")
                return False
            
            # Load the embeddings
            data = torch.load(model_path, map_location='cuda' if torch.cuda.is_available() else 'cpu')
            
            self.gpt_cond_latent = data['gpt_cond_latent']
            self.speaker_embedding = data['speaker_embedding']
            self.current_voice_name = data.get('name', model_path.stem)
            
            # NOTE: gpt_cond_len and temperature are NOT restored from file,
            # because the optimised defaults (gpt_cond_len=5, temperature=0.70)
            # produce better pitch reproduction (tested with samples 29+41)
            
            # Restore only these parameters:
            if 'top_k' in data:
                self.top_k = data['top_k']
            if 'top_p' in data:
                self.top_p = data['top_p']
            if 'repetition_penalty' in data:
                # Clamp to valid range (1.0 – 2.0)
                self.repetition_penalty = min(data['repetition_penalty'], 2.0)
            if 'speed' in data:
                self.speed = data['speed']
            if 'seed' in data:
                self.seed = data['seed']
            
            print(f"Voice model '{self.current_voice_name}' loaded!")
            print(f"  - GPT Latent Shape: {self.gpt_cond_latent.shape}")
            print(f"  - Speaker Embedding Shape: {self.speaker_embedding.shape}")
            print(f"  - Current parameters: gpt_cond_len={self.gpt_cond_len}, temperature={self.temperature}")
            
            # Save as last used model
            self._save_last_model_name(self.current_voice_name)
            
            return True
            
        except Exception as e:
            print(f"Error loading voice model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def list_saved_voice_models(self):
        """
        Lists all saved voice models
        
        Returns:
            list: List of dicts with 'name', 'path' and 'sample_count' for each model
        """
        import torch
        models = []
        if self.VOICE_MODELS_DIR.exists():
            for model_file in self.VOICE_MODELS_DIR.glob("*.pt"):
                # Try to read sample_count from the file
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
        Deletes a saved voice model
        
        Args:
            name (str): Name of the model to delete
            
        Returns:
            bool: True on success, False on error
        """
        try:
            model_path = self.VOICE_MODELS_DIR / f"{name}.pt"
            if model_path.exists():
                model_path.unlink()
                print(f"Voice model '{name}' deleted")
                return True
            else:
                print(f"Voice model '{name}' not found")
                return False
        except Exception as e:
            print(f"Error deleting voice model: {e}")
            return False
    
    def _save_last_model_name(self, name):
        """Saves the name of the last used voice model"""
        try:
            self.LAST_MODEL_FILE.write_text(name, encoding='utf-8')
        except Exception as e:
            print(f"Error saving last model name: {e}")
    
    def _get_last_model_name(self):
        """Returns the name of the last used voice model"""
        try:
            if self.LAST_MODEL_FILE.exists():
                return self.LAST_MODEL_FILE.read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"Error reading last model name: {e}")
        return None
    
    def _save_last_tts_model(self, model_id):
        """Saves the ID of the last used TTS model"""
        try:
            self.LAST_TTS_MODEL_FILE.write_text(model_id, encoding='utf-8')
        except Exception as e:
            print(f"Error saving TTS model: {e}")
    
    def _get_last_tts_model(self):
        """Returns the ID of the last used TTS model"""
        try:
            if self.LAST_TTS_MODEL_FILE.exists():
                return self.LAST_TTS_MODEL_FILE.read_text(encoding='utf-8').strip()
        except Exception as e:
            print(f"Error reading TTS model: {e}")
        return None
    
    def get_available_tts_models(self):
        """
        Returns all available TTS models
        
        Returns:
            dict: Dictionary with model IDs as keys and model info as values
        """
        return self.AVAILABLE_TTS_MODELS
    
    def get_current_tts_model(self):
        """
        Returns the currently loaded TTS model
        
        Returns:
            dict: Dictionary with model_id and model_info
        """
        model_info = self.AVAILABLE_TTS_MODELS.get(self.current_tts_model_id, {})
        return {
            "model_id": self.current_tts_model_id,
            "model_info": model_info,
            "supports_cloning": model_info.get("supports_cloning", False)
        }
    
    def switch_tts_model(self, model_id):
        """
        Switches to a different TTS model
        
        Args:
            model_id (str): ID of the new model (e.g. "xtts_v2", "bark", "vits_de")
            
        Returns:
            bool: True on success, False on error
        """
        if model_id not in self.AVAILABLE_TTS_MODELS:
            print(f"Unknown TTS model: {model_id}")
            return False
        
        if model_id == self.current_tts_model_id:
            print(f"TTS model {model_id} is already active")
            return True
        
        try:
            import torch
            
            print(f"Switching TTS model to: {self.AVAILABLE_TTS_MODELS[model_id]['name']}")
            
            # Release old resources
            if hasattr(self, 'tts_api') and self.tts_api:
                del self.tts_api
            if hasattr(self, 'model') and self.model:
                del self.model
            
            # Free GPU memory
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            
            # Set new model
            self.current_tts_model_id = model_id
            
            # Invalidate cache
            self.gpt_cond_latent = None
            self.speaker_embedding = None
            
            # Load new model
            if XTTS_DIRECT and self.gpu_available and model_id.startswith("xtts"):
                self._init_xtts_direct()
            else:
                self._init_tts_api()
            
            # Save preference
            self._save_last_tts_model(model_id)
            
            print(f"TTS model switched to: {self.AVAILABLE_TTS_MODELS[model_id]['name']}")
            return True
            
        except Exception as e:
            print(f"Error switching TTS model: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # === ElevenLabs Integration ===
    
    def _load_elevenlabs_config(self):
        """Loads ElevenLabs configuration from disk"""
        try:
            if self.ELEVENLABS_CONFIG_FILE.exists():
                import json
                config = json.loads(self.ELEVENLABS_CONFIG_FILE.read_text(encoding='utf-8'))
                self.elevenlabs_api_key = config.get('api_key')
                self.elevenlabs_voice_id = config.get('voice_id')
                self.pyttsx3_voice_id = config.get('pyttsx3_voice_id')
                self.pyttsx3_gender = config.get('pyttsx3_gender')
                self.elevenlabs_model_id = config.get('model_id', 'eleven_multilingual_v2')
                self.elevenlabs_stability = config.get('stability', 0.5)
                self.elevenlabs_similarity_boost = config.get('similarity_boost', 0.75)
                self.elevenlabs_style = config.get('style', 0.0)
                self.elevenlabs_use_speaker_boost = config.get('use_speaker_boost', False)
                if self.elevenlabs_api_key:
                    self.tts_provider = config.get('provider', 'elevenlabs')
                    self._init_elevenlabs()
        except Exception as e:
            print(f"Error loading ElevenLabs configuration: {e}")
    
    def _save_elevenlabs_config(self):
        """Saves ElevenLabs configuration to disk"""
        try:
            import json
            config = {
                'api_key': self.elevenlabs_api_key,
                'voice_id': self.elevenlabs_voice_id,
                'pyttsx3_voice_id': self.pyttsx3_voice_id,
                'pyttsx3_gender': self.pyttsx3_gender,
                'model_id': self.elevenlabs_model_id,
                'provider': self.tts_provider,
                'stability': self.elevenlabs_stability,
                'similarity_boost': self.elevenlabs_similarity_boost,
                'style': self.elevenlabs_style,
                'use_speaker_boost': self.elevenlabs_use_speaker_boost
            }
            self.ELEVENLABS_CONFIG_FILE.write_text(
                json.dumps(config), encoding='utf-8'
            )
        except Exception as e:
            print(f"Error saving ElevenLabs configuration: {e}")
    
    def _init_elevenlabs(self):
        """Initialises the ElevenLabs client"""
        if not self.elevenlabs_api_key:
            print("ElevenLabs: No API key configured")
            return False
        try:
            from elevenlabs.client import ElevenLabs
            self.elevenlabs_client = ElevenLabs(api_key=self.elevenlabs_api_key)
            print("ElevenLabs client initialised")
            return True
        except Exception as e:
            print(f"Error initialising ElevenLabs: {e}")
            self.elevenlabs_client = None
            return False
    
    def set_elevenlabs_config(self, api_key=None, voice_id=None, model_id=None,
                               stability=None, similarity_boost=None, style=None,
                               use_speaker_boost=None):
        """
        Configures ElevenLabs API key, voice ID and model.
        
        Returns:
            bool: True on success
        """
        if api_key is not None:
            self.elevenlabs_api_key = api_key
        if voice_id is not None:
            self.elevenlabs_voice_id = voice_id
        if model_id is not None:
            self.elevenlabs_model_id = model_id
        if stability is not None:
            self.elevenlabs_stability = stability
        if similarity_boost is not None:
            self.elevenlabs_similarity_boost = similarity_boost
        if style is not None:
            self.elevenlabs_style = style
        if use_speaker_boost is not None:
            self.elevenlabs_use_speaker_boost = use_speaker_boost
        
        self._save_elevenlabs_config()
        
        if self.elevenlabs_api_key:
            return self._init_elevenlabs()
        return True
    
    def set_tts_provider(self, provider):
        """
        Switches the TTS provider.

        Args:
            provider: "elevenlabs" or "pyttsx3"
        """
        if provider not in ("elevenlabs", "pyttsx3"):
            return False
        self.tts_provider = provider
        self._save_elevenlabs_config()
        print(f"TTS provider switched to: {provider}")
        return True
    
    def list_elevenlabs_voices(self):
        """
        Lists all ElevenLabs voices.
        
        Returns:
            list: List of dicts with 'voice_id' and 'name'
        """
        if not self.elevenlabs_client:
            if not self._init_elevenlabs():
                return []
        try:
            response = self.elevenlabs_client.voices.search()
            voices = []
            for v in response.voices:
                voices.append({
                    'voice_id': v.voice_id,
                    'name': v.name,
                    'category': getattr(v, 'category', 'unknown')
                })
            return voices
        except Exception as e:
            print(f"Error fetching ElevenLabs voices: {e}")
            return []
    
    def _speak_elevenlabs_and_save(self, text, language):
        """
        Generates audio via the ElevenLabs API and saves it as WAV.
        Falls back to pyttsx3 automatically on error.
        """
        import time
        start_time = time.time()

        if not self._check_internet():
            print("No internet connection, falling back to pyttsx3...")
            return self._speak_pyttsx3_and_save(text, language)

        if not self.elevenlabs_client:
            if not self._init_elevenlabs():
                print("ElevenLabs not available, falling back to pyttsx3...")
                return self._speak_pyttsx3_and_save(text, language)

        if not self.elevenlabs_voice_id:
            print("ElevenLabs: No voice ID configured, falling back to pyttsx3...")
            return self._speak_pyttsx3_and_save(text, language)
        
        try:
            print(f"ElevenLabs: Generating audio...")
            print(f"  Voice ID: {self.elevenlabs_voice_id}")
            print(f"  Model: {self.elevenlabs_model_id}")
            
            # Language code mapping: v3 uses ISO 639-3 (3-letter), v2 uses ISO 639-1 (2-letter)
            is_v3 = 'v3' in (self.elevenlabs_model_id or '')
            if is_v3:
                lang_map = {"de": "deu", "en": "eng", "es": "spa", "fr": "fra", "it": "ita",
                            "pt": "por", "nl": "nld", "pl": "pol", "ru": "rus", "ja": "jpn",
                            "zh": "cmn", "ko": "kor", "sv": "swe", "da": "dan", "fi": "fin",
                            "tr": "tur", "ar": "ara", "hi": "hin", "cs": "ces", "el": "ell",
                            "hu": "hun", "ro": "ron", "uk": "ukr", "no": "nor", "vi": "vie"}
            else:
                lang_map = {"de": "de", "en": "en", "es": "es", "fr": "fr", "it": "it"}
            language_code = lang_map.get(language, language)
            
            # Prepare text for TTS
            tts_text = text.strip()
            word_count = len(tts_text.split())
            
            if is_v3 and word_count <= 3 and language_code != "eng":
                # v3: audio tag for language control on short texts
                accent_map = {"deu": "German", "spa": "Spanish", "fra": "French",
                              "ita": "Italian", "por": "Portuguese", "nld": "Dutch",
                              "pol": "Polish", "rus": "Russian", "jpn": "Japanese"}
                accent = accent_map.get(language_code)
                if accent:
                    tts_text = f"[strong {accent} accent] {tts_text}"
            elif not is_v3 and word_count <= 3 and language_code != "en":
                # v2: force period at end for short texts
                if tts_text and tts_text[-1] not in '.!?…':
                    tts_text = tts_text + '.'
            
            from elevenlabs import VoiceSettings
            voice_settings = VoiceSettings(
                stability=self.elevenlabs_stability,
                similarity_boost=self.elevenlabs_similarity_boost,
                style=self.elevenlabs_style,
                use_speaker_boost=self.elevenlabs_use_speaker_boost
            )
            
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                text=tts_text,
                voice_id=self.elevenlabs_voice_id,
                model_id=self.elevenlabs_model_id,
                output_format="pcm_24000",
                language_code=language_code,
                voice_settings=voice_settings
            )
            
            # Collect audio bytes
            audio_bytes = b""
            for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    audio_bytes += chunk
            
            if not audio_bytes:
                print("ElevenLabs: No audio data received, falling back to pyttsx3...")
                return self._speak_pyttsx3_and_save(text, language)
            
            # PCM 24 kHz 16-bit mono → save as WAV
            import numpy as np
            import scipy.io.wavfile as wavfile
            
            wav_data = np.frombuffer(audio_bytes, dtype=np.int16)
            
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, "speakalike_last_audio.wav")
            wavfile.write(output_path, 24000, wav_data)
            
            elapsed = time.time() - start_time
            audio_duration = len(wav_data) / 24000
            print(f"  ElevenLabs Audio generiert in {elapsed:.2f}s ({audio_duration:.1f}s Audio)")
            
            # Play audio (only when not in headless/API mode)
            if not getattr(self, 'headless_mode', False):
                import sounddevice as sd
                import soundfile as sf
                data, samplerate = sf.read(output_path)
                sd.play(data, samplerate, device=self.output_device)
                sd.wait()
            
            return output_path
            
        except Exception as e:
            print(f"ElevenLabs error: {e}, falling back to pyttsx3...")
            import traceback
            traceback.print_exc()
            return self._speak_pyttsx3_and_save(text, language)
    
    def load_last_model(self):
        """
        Automatically loads the last used voice model
        
        Returns:
            bool: True if a model was loaded, False otherwise
        """
        last_name = self._get_last_model_name()
        if last_name:
            model_path = self.VOICE_MODELS_DIR / f"{last_name}.pt"
            if model_path.exists():
                print(f"Loading last used voice model: {last_name}")
                return self.load_voice_model(last_name)
            else:
                print(f"Last used model '{last_name}' no longer available")
        return False
            
    def speak(self, text, rate=150, language='de'):
        """
        Speaks the given text
        
        Args:
            text (str): The text to speak
            rate (int): Speech rate (words per minute)
            language (str): Language code (e.g. 'de', 'en')
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
        Speaks the text and returns the path to the audio file
        
        Args:
            text (str): The text to speak
            rate (int): Speech rate (words per minute)
            language (str): Language code (e.g. 'de', 'en')
            
        Returns:
            str: Path to the saved WAV file, or None on error
        """
        if not text.strip():
            return None
            
        self.is_speaking = True
        
        try:
            # ElevenLabs as primary provider
            if self.tts_provider == "elevenlabs":
                return self._speak_elevenlabs_and_save(text, language)

            # pyttsx3 as fallback
            return self._speak_pyttsx3_and_save(text, language)
        except Exception as e:
            print(f"Fehler beim Vorlesen: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            self.is_speaking = False
    
    def _speak_coqui_and_save(self, text, language):
        """Speech output via Coqui TTS, returns audio path"""
        import torch
        import numpy as np
        import random
        import sounddevice as sd
        import soundfile as sf
        
        # Set seed for consistent output
        torch.manual_seed(self.seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(self.seed)
            torch.cuda.manual_seed_all(self.seed)
        
        # Create persistent file in temp directory
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, "speakalike_last_audio.wav")
        
        if self.use_direct and self.model and self.gpt_cond_latent is not None:
            self._inference_direct(text, language, output_path)
        elif self.speaker_wav and len(self.speaker_wav) > 0:
            self._inference_api_cloning(text, language, output_path)
        else:
            self._inference_api_default(text, language, output_path)
        
        # Play audio (only when not in headless/API mode)
        if not getattr(self, 'headless_mode', False):
            data, samplerate = sf.read(output_path)
            sd.play(data, samplerate, device=self.output_device)
            sd.wait()
        
        return output_path
    
    def _speak_coqui(self, text, language):
        """Speech output via Coqui TTS (optimised)"""
        import torch
        import numpy as np
        import random
        import sounddevice as sd
        import soundfile as sf
        
        # Set seed for consistent output
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
                # Direct XTTS access with cached embeddings (best quality)
                self._inference_direct(text, language, output_path)
            elif self.speaker_wav and len(self.speaker_wav) > 0:
                # TTS API with voice cloning
                self._inference_api_cloning(text, language, output_path)
            else:
                # TTS API without voice cloning
                self._inference_api_default(text, language, output_path)
            
            # Play audio
            data, samplerate = sf.read(output_path)
            sd.play(data, samplerate, device=self.output_device)
            sd.wait()
            
        finally:
            try:
                os.unlink(output_path)
            except:
                pass
    
    def _inference_direct(self, text, language, output_path):
        """Direct XTTS inference with optimised parameters"""
        import torch
        import numpy as np
        import scipy.io.wavfile as wavfile
        import time
        
        start_time = time.time()
        print(f"Generiere Audio...")
        print(f"  Parameter: gpt_cond_len={self.gpt_cond_len}, temperature={self.temperature}")
        
        # Save original text (without stop marker) for trimming
        original_text = text
        
        # Append stop marker to text
        text_with_marker = self._add_stop_marker(text, language)
        print(f"  Text with stop marker: '{text_with_marker}'")
        
        # Streaming mode for faster first audio output
        if self.use_streaming:
            self._inference_direct_streaming(original_text, language, output_path)
            print(f"  Generation complete in {time.time() - start_time:.2f}s (streaming)")
            return
        
        # --- TIMING: XTTS Inference ---
        t_inference = time.time()
        # Generate the entire text in one pass (with stop marker)
        with torch.inference_mode():
            out = self.model.inference(
                text=text_with_marker,
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
        t_inference = time.time() - t_inference
        
        wav = np.array(out["wav"])
        audio_duration = len(wav) / 24000
        
        # DEBUG: Save audio BEFORE trimming to Desktop
        import os
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        debug_path = os.path.join(desktop, "DEBUG_vor_trim.wav")
        wav_debug = np.clip(wav, -1.0, 1.0)
        wav_debug_int16 = (wav_debug * 32767).astype(np.int16)
        wavfile.write(debug_path, 24000, wav_debug_int16)
        
        # --- TIMING: Whisper Trimming ---
        t_whisper = time.time()
        # Remove artifacts at the end (searches for stop marker)
        wav = self._remove_artifacts_with_transcription(wav, original_text, sample_rate=24000, language=language)
        t_whisper = time.time() - t_whisper
        
        # --- TIMING: WAV saving ---
        t_save = time.time()
        # Save as standard PCM WAV (16-bit) for maximum compatibility
        wav = np.clip(wav, -1.0, 1.0)
        wav_int16 = (wav * 32767).astype(np.int16)
        wavfile.write(output_path, 24000, wav_int16)
        t_save = time.time() - t_save
        
        total = time.time() - start_time
        print(f"\n  ⏱ TIMING overview:")
        print(f"    XTTS Inference:    {t_inference:.2f}s  ({t_inference/total*100:.0f}%)")
        print(f"    Audio duration:    {audio_duration:.2f}s  (realtime factor: {t_inference/audio_duration:.1f}x)")
        print(f"    Whisper Trimming:  {t_whisper:.2f}s  ({t_whisper/total*100:.0f}%)")
        print(f"    WAV save:          {t_save:.2f}s  ({t_save/total*100:.0f}%)")
        print(f"    TOTAL:             {total:.2f}s")
    
    def _inference_direct_streaming(self, text, language, output_path):
        """Streaming inference for faster first audio output"""
        import torch
        import torchaudio
        import numpy as np
        
        # Save original text (without stop marker) for trimming
        original_text = text
        
        # Append stop marker to text
        text_with_marker = self._add_stop_marker(text, language)
        print(f"  Text with stop marker (streaming): '{text_with_marker}'")
        
        chunks = []
        
        # Use streaming generator (with stop marker)
        for chunk in self.model.inference_stream(
            text=text_with_marker,
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
            stream_chunk_size=20  # Smaller chunks = faster start
        ):
            chunks.append(chunk)
        
        # Concatenate all chunks
        if chunks:
            wav = np.concatenate([c.cpu().numpy() for c in chunks])
            
            # Remove artifacts at the end (searches for stop marker)
            wav = self._remove_artifacts_with_transcription(wav, original_text, sample_rate=24000, language=language)
            torchaudio.save(output_path, torch.tensor(wav).unsqueeze(0), 24000)

    # Universal stop marker for all languages.
    # "Tango Tango Tango" is phonetically unique, sounds the same in every language,
    # and does NOT interfere with XTTS (unlike "Ende der Nachricht" which swallowed words)
    STOP_MARKER = "Tango Tango Tango."
    
    # Recognition patterns: Whisper may transcribe "Tango" with slight variations
    STOP_MARKER_WORDS = ["tango", "tangoo", "tanco", "ango", "tanga", "ango", "tangutan"]

    def _add_stop_marker(self, text, language):
        """
        Appends the universal stop marker to the end of the text.
        """
        marker = self.STOP_MARKER
        
        # Check whether the text ALREADY contains the stop marker
        if "tango" in text.lower():
            print(f"  WARNING: Text already contains 'tango'!")
            return text
        
        result = f"{text.rstrip()}... {marker}"
        print(f"  Stop marker: '{marker}' appended (with '...' pause)")
        return result

    def _find_stop_marker_position(self, recognized_words, language):
        """
        Finds the position of the stop marker "Tango Tango Tango" in the recognised words.
        Searches for at least 2 consecutive "tango" words.
        
        Returns:
            Tuple (start time, index) or (None, None)
        """
        import re
        
        def normalize(w):
            return re.sub(r'[^\w]', '', w.lower())
        
        words_text = [normalize(w["word"]) for w in recognized_words]
        
        print(f"  Searching for stop marker 'tango' in: {words_text[-10:] if len(words_text) > 10 else words_text}")
        
        def is_tango(word):
            return any(t in word for t in self.STOP_MARKER_WORDS)
        
        # Search for at least 2 consecutive "tango" words
        for i in range(len(words_text) - 1):
            if is_tango(words_text[i]) and is_tango(words_text[i + 1]):
                print(f"  -> Stop marker '{words_text[i]}' + '{words_text[i+1]}' at {recognized_words[i]['start']:.2f}s (index {i})")
                return recognized_words[i]["start"], i
        
        # Fallback: single "tango" in the last 30% of words
        search_start = max(1, int(len(words_text) * 0.7))
        for i in range(len(words_text) - 1, search_start - 1, -1):
            if is_tango(words_text[i]):
                print(f"  -> Single stop marker word '{words_text[i]}' at {recognized_words[i]['start']:.2f}s (index {i}) [fallback]")
                return recognized_words[i]["start"], i
        
        print(f"  -> Stop marker NOT found!")
        return None, None

    def _remove_artifacts_with_transcription(self, audio, expected_text, sample_rate=24000, language="de"):
        """
        Removes artifacts at the end of audio using Whisper transcription.
        
        Uses a stop-marker sentence appended to the text.
        The audio is cut at the start of the stop marker.
        
        Args:
            audio: Audio array (numpy)
            expected_text: The expected text that was spoken (without stop marker)
            sample_rate: Audio sample rate
            language: Language code for stop marker detection
            
        Returns:
            Trimmed audio array
        """
        import numpy as np
        
        if len(audio) == 0:
            return audio
        
        try:
            # Lazy-load faster-whisper on first call
            if not hasattr(self, '_whisper_model') or self._whisper_model is None:
                print("  Loading faster-whisper model for artifact detection...")
                import os
                # Work around CTranslate2 ROCm path bug on NVIDIA
                os.environ["CT2_SUPPRESS_ROCM_INIT"] = "1"
                from faster_whisper import WhisperModel
                # medium model with CTranslate2 – detects stop marker more reliably than base
                try:
                    self._whisper_model = WhisperModel("medium", device="cuda", compute_type="float16")
                    print("  faster-whisper model (medium, CUDA float16) loaded.")
                except Exception:
                    # Fallback to CPU if CUDA has issues
                    self._whisper_model = WhisperModel("medium", device="cpu", compute_type="int8")
                    print("  faster-whisper model (medium, CPU int8) loaded.")
            
            import torch
            import torchaudio
            
            # Convert numpy to torch tensor
            audio_tensor = torch.tensor(audio).float()
            if audio_tensor.dim() == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            
            # Resample to 16 kHz using torchaudio (better quality than scipy)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=16000)
                audio_16k = resampler(audio_tensor).squeeze().numpy()
            else:
                audio_16k = audio_tensor.squeeze().numpy()
            
            # Normalise audio for Whisper (important!)
            audio_16k = audio_16k.astype(np.float32)
            max_val = np.max(np.abs(audio_16k))
            if max_val > 0:
                audio_16k = audio_16k / max_val
            
            # Debug: show audio info
            print(f"  Whisper input: {len(audio_16k)} samples, max={np.max(np.abs(audio_16k)):.3f}, dtype={audio_16k.dtype}")
            
            # Determine Whisper language (mapping for some languages)
            whisper_lang = language
            if language == "zh-cn":
                whisper_lang = "zh"
            
            # Transcribe with faster-whisper (word_timestamps)
            segments, info = self._whisper_model.transcribe(
                audio_16k,
                language=whisper_lang,
                word_timestamps=True,
                vad_filter=False
            )
            
            # Collect all recognised words with timestamps
            recognized_words = []
            full_text = ""
            for segment in segments:
                full_text += segment.text
                if segment.words:
                    for word_info in segment.words:
                        word = word_info.word.strip()
                        if word:
                            recognized_words.append({
                                "word": word,
                                "start": word_info.start,
                                "end": word_info.end
                            })
            
            # Debug: show what was recognised
            if full_text:
                print(f"  Whisper recognised: '{full_text[:100]}...' " if len(full_text) > 100 else f"  Whisper recognised: '{full_text}'")
            else:
                print("  Whisper: No text recognised")
            
            if not recognized_words:
                print("  No words recognised, using fallback trimming")
                return self._remove_trailing_artifacts(audio, sample_rate)
            
            # Debug: show recognised words
            print(f"  Recognised words ({len(recognized_words)}): {[w['word'] for w in recognized_words]}")
            
            # NEW STRATEGY: search for the stop marker
            stop_marker_start, stop_marker_index = self._find_stop_marker_position(recognized_words, language)
            
            if stop_marker_start is not None:
                print(f"  Stop marker found at {stop_marker_start:.2f}s (index {stop_marker_index})")
                
                # Find the end of the last word BEFORE the stop marker.
                # IMPORTANT: skip words that may also belong to the stop marker
                import re
                def normalize(w):
                    return re.sub(r'[^\w]', '', w.lower())
                
                # Stop marker words to skip
                stop_words = set(self.STOP_MARKER_WORDS)
                
                # Search backwards for the first word that does NOT belong to the stop marker
                last_content_index = stop_marker_index - 1
                while last_content_index >= 0:
                    word = normalize(recognized_words[last_content_index]["word"])
                    if word not in stop_words:
                        break
                    last_content_index -= 1
                
                if last_content_index >= 0:
                    last_content_word = recognized_words[last_content_index]
                    last_word_end = last_content_word["end"]
                    print(f"  Last content word: '{last_content_word['word']}' ends at {last_word_end:.2f}s (index {last_content_index})")
                    # Cut after last content word (+ 200 ms buffer for natural fade)
                    cut_time = last_word_end + 0.2
                else:
                    # Fallback: cut 300 ms before stop marker
                    print(f"  No content word found, using fallback")
                    cut_time = max(0, stop_marker_start - 0.3)
                
                end_sample = int(cut_time * sample_rate)
                
                # Soft fade-out (100 ms)
                fade_duration = 0.1
                fade_samples = int(fade_duration * sample_rate)
                if end_sample > fade_samples:
                    fade_start = end_sample - fade_samples
                    fade_curve = np.power(np.linspace(1.0, 0.0, fade_samples), 2)
                    audio = audio.copy()
                    audio[fade_start:end_sample] *= fade_curve[:end_sample - fade_start]
                
                trimmed = audio[:end_sample]
                
                original_duration = len(audio) / sample_rate
                trimmed_duration = len(trimmed) / sample_rate
                
                print(f"  -> Stop marker trimming: {original_duration:.2f}s -> {trimmed_duration:.2f}s "
                      f"({original_duration - trimmed_duration:.2f}s removed)")
                
                return trimmed
            
            # FALLBACK: stop marker not found, use word-count method
            print(f"  Stop marker not recognised, using word count as fallback")
            
            expected_words = self._normalize_text(expected_text).split()
            print(f"  Expected words ({len(expected_words)}): {expected_words}")
            
            # Strategy: simply count words.
            # The expected text has N words → take the end of the Nth recognised word
            num_expected = len(expected_words)
            
            if len(recognized_words) >= num_expected:
                # All words recognised — cut after the last expected word
                last_valid_word_info = recognized_words[num_expected - 1]
                last_valid_end = last_valid_word_info["end"]
                last_valid_word = last_valid_word_info["word"]
                
                print(f"  Expecting {num_expected} words, cutting after word {num_expected}: '{last_valid_word}' at {last_valid_end:.2f}s")
            else:
                # Fewer recognised words than expected — take everything
                last_valid_word_info = recognized_words[-1]
                last_valid_end = last_valid_word_info["end"]
                last_valid_word = last_valid_word_info["word"]
                
                print(f"  Only {len(recognized_words)} of {num_expected} words recognised, using all up to '{last_valid_word}' at {last_valid_end:.2f}s")
            
            if last_valid_end > 0:
                # Convert time back to sample position (at original sample rate)
                end_sample = int(last_valid_end * sample_rate)
                # Add 350 ms buffer for natural fade
                end_sample = min(end_sample + int(0.35 * sample_rate), len(audio))
                
                # Soft fade-out (150 ms) for natural transition
                fade_duration = 0.15  # 150 ms
                fade_samples = int(fade_duration * sample_rate)
                if end_sample > fade_samples:
                    fade_start = end_sample - fade_samples
                    # Exponential fade-out for more natural sound
                    fade_curve = np.power(np.linspace(1.0, 0.0, fade_samples), 2)
                    audio = audio.copy()
                    audio[fade_start:end_sample] *= fade_curve[:end_sample - fade_start]
                
                trimmed = audio[:end_sample]
                
                original_duration = len(audio) / sample_rate
                trimmed_duration = len(trimmed) / sample_rate
                
                if original_duration - trimmed_duration > 0.05:
                    print(f"  -> Whisper trimming: {original_duration:.2f}s -> {trimmed_duration:.2f}s "
                          f"({original_duration - trimmed_duration:.2f}s artifacts removed)")
                    print(f"    Last word: '{last_valid_word}'")
                
                return trimmed
            else:
                print("  No text recognised, using fallback trimming")
                return self._remove_trailing_artifacts(audio, sample_rate)
                
        except ImportError:
            print("  Whisper not installed, using fallback trimming")
            return self._remove_trailing_artifacts(audio, sample_rate)
        except Exception as e:
            print(f"  Whisper error: {e}, using fallback trimming")
            return self._remove_trailing_artifacts(audio, sample_rate)
    
    def _normalize_text(self, text):
        """Normalises text for comparison (lowercase, alphanumeric only)"""
        import re
        text = text.lower().strip()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        return text
    
    def _is_likely_artifact(self, word):
        """
        Checks whether a word is likely an artifact/hallucination.
        
        Artifacts often have:
        - Non-Latin characters
        - Very short unusual character sequences
        - Special characters
        """
        import re
        
        if not word:
            return True
        
        # Check for non-Latin characters (except German umlauts)
        # Allowed: a-z, äöüß, digits
        latin_pattern = re.compile(r'^[a-zäöüß0-9]+$', re.IGNORECASE)
        if not latin_pattern.match(word):
            return True
        
        # Very short words that are not valid German words
        common_short = {'ich', 'du', 'er', 'es', 'ja', 'so', 'da', 'an', 'in', 'um', 'zu', 'ob', 'wo', 'oh', 'ah', 'na', 'ey', 'hi', 'ok'}
        if len(word) <= 2 and word.lower() not in common_short:
            return True
        
        return False
    
    def _words_match(self, word1, word2, threshold=0.5):
        """Checks whether two words are similar enough (fuzzy match)"""
        w1 = word1.lower()
        w2 = word2.lower()
        
        # Exact match
        if w1 == w2:
            return True
        
        # Normalise phonetically similar spellings (German/English)
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
        
        # Match after normalisation
        if w1_norm == w2_norm:
            return True
        
        # One word contains the other — only if the shorter word is long enough
        # and the longer word is not much longer (prevents "der" in "ender")
        min_len = min(len(w1), len(w2))
        max_len = max(len(w1), len(w2))
        if min_len >= 4 and max_len <= min_len + 2:  # Stricter: at least 4 chars, max 2 char difference
            if w1 in w2 or w2 in w1:
                return True
            if w1_norm in w2_norm or w2_norm in w1_norm:
                return True
        
        # Same start (at least 3 chars) — only if lengths are similar
        if len(w1) >= 3 and len(w2) >= 3 and abs(len(w1) - len(w2)) <= 2:
            if w1[:3] == w2[:3]:
                return True
            # Or same first 2 chars for shorter words
            if w1[:2] == w2[:2] and (len(w1) <= 5 or len(w2) <= 5):
                return True
        
        # Levenshtein-like check for small differences
        if abs(len(w1) - len(w2)) <= 3:
            matches = sum(c1 == c2 for c1, c2 in zip(w1, w2))
            max_len = max(len(w1), len(w2))
            if max_len > 0 and matches / max_len >= threshold:
                return True
        
        # Also for normalised versions
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
        Removes artifacts/hallucinations at the end of audio.
        
        Searches for the last significant speech activity and cuts after it
        to remove unintelligible sounds at the end.
        
        Args:
            audio: Audio array
            sample_rate: Sample rate
            silence_threshold_db: Silence threshold in dB
            min_silence_duration: Minimum silence duration to detect end
        """
        import numpy as np
        
        if len(audio) == 0:
            return audio
        
        # Compute RMS energy in small windows
        window_size = int(0.02 * sample_rate)  # 20 ms window
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
        
        # Convert to dB
        rms_db = 20 * np.log10(rms_values + 1e-10)
        max_db = np.max(rms_db)
        rms_db_normalized = rms_db - max_db
        
        # Find the last position with speech
        is_speech = rms_db_normalized > silence_threshold_db
        
        # Search backwards for the last speech segment
        min_silence_windows = int(min_silence_duration * sample_rate / hop_size)
        
        last_speech_window = len(is_speech) - 1
        silence_count = 0
        
        for i in range(len(is_speech) - 1, -1, -1):
            if is_speech[i]:
                if silence_count >= min_silence_windows:
                    # We found a silence segment after speech —
                    # this could be the start of artifacts
                    last_speech_window = i + min_silence_windows // 2
                    break
                silence_count = 0
            else:
                silence_count += 1
        
        # Berechne die Sample-Position
        end_sample = min((last_speech_window + 1) * hop_size + window_size, len(audio))
        
        # Add a short fade-out (50 ms)
        fade_samples = int(0.05 * sample_rate)
        if end_sample > fade_samples:
            fade_start = end_sample - fade_samples
            fade_curve = np.linspace(1.0, 0.0, fade_samples)
            audio[fade_start:end_sample] *= fade_curve[:end_sample - fade_start]
        
        # Cut
        trimmed = audio[:end_sample]
        
        original_duration = len(audio) / sample_rate
        trimmed_duration = len(trimmed) / sample_rate
        
        if original_duration - trimmed_duration > 0.1:
            print(f"  -> Audio trimmed: {original_duration:.2f}s -> {trimmed_duration:.2f}s "
                  f"({original_duration - trimmed_duration:.2f}s artifacts removed)")
        
        return trimmed
    
    def _remove_trailing_silence(self, audio, sample_rate=24000, silence_threshold_db=-40):
        """
        Removes only genuine silence at the end of audio (less aggressive).
        
        Keeps more audio than _remove_trailing_artifacts — useful when
        Whisper has not recognised everything but the audio is complete.
        """
        import numpy as np
        
        if len(audio) == 0:
            return audio
        
        # Compute RMS energy in small windows
        window_size = int(0.05 * sample_rate)  # 50 ms window
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
                # There is still audio here — cut 300 ms later
                end_sample = min(end + int(0.3 * sample_rate), len(audio))
                
                # Fade-out (100 ms)
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
                    print(f"  -> Silence trimming: {original_duration:.2f}s -> {trimmed_duration:.2f}s")
                
                return trimmed
        
        return audio
    
    def _inference_api_cloning(self, text, language, output_path):
        """TTS API inference with voice cloning"""
        self.tts_api.tts_to_file(
            text=text,
            file_path=output_path,
            speaker_wav=self.speaker_wav,
            language=language,
            split_sentences=True,
            temperature=0.4,  # Lower temperature for consistency
            length_penalty=1.0,
            repetition_penalty=2.0,
            top_k=30,
            top_p=0.75
        )
    
    def _inference_api_default(self, text, language, output_path):
        """TTS API inference without voice cloning — uses built-in voice"""
        # XTTS v2 has built-in speakers — use one of them
        # Available speakers can be queried with tts_api.speakers
        try:
            # Try to use a built-in speaker
            available_speakers = getattr(self.tts_api, 'speakers', None)
            if available_speakers and len(available_speakers) > 0:
                # Use the first available speaker
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
                # Fallback: use a standard reference WAV or simple output.
                # XTTS without speaker_wav only works with speaker_idx
                self.tts_api.tts_to_file(
                    text=text,
                    file_path=output_path,
                    speaker="Claribel Dervla",  # Default XTTS speaker
                    language=language,
                    split_sentences=True
                )
        except Exception as e:
            print(f"Error in default TTS, trying fallback: {e}")
            # Last resort — simplest form
            self.tts_api.tts_to_file(
                text=text,
                file_path=output_path,
                language=language
            )
    
    def _speak_pyttsx3(self, text, rate, language):
        """Fallback speech output with pyttsx3"""
        self.engine.setProperty('rate', rate)
        voices = self.engine.getProperty('voices')
        
        for voice in voices:
            if language in voice.id.lower() or 'german' in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break
        
        self.engine.say(text)
        self.engine.runAndWait()
    
    def speak_async(self, text, rate=150, language='de'):
        """Speaks text asynchronously in a separate thread"""
        thread = threading.Thread(target=self.speak, args=(text, rate, language))
        thread.daemon = True
        thread.start()
        return thread
    
    def stop(self):
        """Stops playback"""
        if not self.use_coqui and hasattr(self, 'engine') and hasattr(self.engine, 'stop'):
            self.engine.stop()
        self.is_speaking = False


def main():
    """Command-line version for quick tests"""
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        tts = TextToSpeech()
        print(f"Spreche: {text}")
        tts.speak(text)
    else:
        print("SpeakAlike - Text-to-Speech")
        print("\nUsage:")
        print("  python main.py \"Your text here\"")
        print("\nOr start the GUI:")
        print("  python gui.py")


if __name__ == "__main__":
    main()
