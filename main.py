"""
FastSpeak - Text-to-Speech Anwendung mit Coqui TTS
"""
import sys
import threading
from pathlib import Path
import tempfile
import os

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
    
    def __init__(self):
        self.is_speaking = False
        self.speaker_wav = None
        self.seed = 42  # Fester Seed für konsistente Ausgabe
        
        # Speaker Embedding Cache für bessere Qualität und Performance
        self.gpt_cond_latent = None
        self.speaker_embedding = None
        self.cached_speaker_wav = None
        self.current_voice_name = None  # Name des aktuell geladenen Voice-Modells
        
        # Optimierte Inference-Parameter
        self.gpt_cond_len = 30  # Längere Konditionierung = bessere Stimmerfassung (Standard: 12)
        self.gpt_cond_chunk_len = 6  # Chunk-Größe für stabilere Latents (Standard: 4)
        self.max_ref_len = 60  # Mehr Referenz-Audio verwenden (Standard: 10)
        
        # Erstelle Voice-Modell-Verzeichnis falls nicht vorhanden
        self.VOICE_MODELS_DIR.mkdir(exist_ok=True)
        
        if COQUI_AVAILABLE:
            try:
                import torch
                self.gpu_available = torch.cuda.is_available()
                
                if XTTS_DIRECT and self.gpu_available:
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
    
    def _init_xtts_direct(self):
        """Initialisiert XTTS mit direktem Modell-Zugriff für beste Qualität"""
        import torch
        
        # Lade Modell über TTS API (lädt automatisch herunter)
        self.tts_api = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=True)
        
        # Direkter Zugriff auf das XTTS-Modell für erweiterte Kontrolle
        self.model = self.tts_api.synthesizer.tts_model
        self.use_coqui = True
        self.use_direct = True
        
        gpu_name = torch.cuda.get_device_name(0)
        print(f"XTTS v2 initialisiert (Direkter Zugriff) mit GPU: {gpu_name}")
        print(f"  - gpt_cond_len: {self.gpt_cond_len}s (mehr Kontext)")
        print(f"  - gpt_cond_chunk_len: {self.gpt_cond_chunk_len}s (stabilere Latents)")
        print(f"  - max_ref_len: {self.max_ref_len}s (längere Referenz)")
    
    def _init_tts_api(self):
        """Fallback auf TTS API"""
        import torch
        self.tts_api = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=self.gpu_available)
        self.model = None
        self.use_coqui = True
        self.use_direct = False
        
        if self.gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            print(f"XTTS v2 initialisiert (API-Modus) mit GPU: {gpu_name}")
        else:
            print("XTTS v2 initialisiert (API-Modus) mit CPU")
    
    def _init_fallback(self):
        """Fallback auf einfacheres Modell"""
        self.tts_api = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC")
        self.model = None
        self.use_coqui = True
        self.use_direct = False
        print("Coqui TTS initialisiert (Thorsten Fallback)")
    
    def _init_pyttsx3(self):
        """Fallback auf pyttsx3"""
        import pyttsx3
        self.engine = pyttsx3.init()
        self.model = None
        self.use_coqui = False
        self.use_direct = False
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
            
            # Speichere die Embeddings
            torch.save({
                'gpt_cond_latent': self.gpt_cond_latent,
                'speaker_embedding': self.speaker_embedding,
                'gpt_cond_len': self.gpt_cond_len,
                'gpt_cond_chunk_len': self.gpt_cond_chunk_len,
                'seed': self.seed,
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
            
            # Optionale Parameter wiederherstellen
            if 'gpt_cond_len' in data:
                self.gpt_cond_len = data['gpt_cond_len']
            if 'gpt_cond_chunk_len' in data:
                self.gpt_cond_chunk_len = data['gpt_cond_chunk_len']
            if 'seed' in data:
                self.seed = data['seed']
            
            print(f"Voice-Modell '{self.current_voice_name}' geladen!")
            print(f"  - GPT Latent Shape: {self.gpt_cond_latent.shape}")
            print(f"  - Speaker Embedding Shape: {self.speaker_embedding.shape}")
            
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
            list: Liste von Dictionaries mit 'name' und 'path' für jedes Modell
        """
        models = []
        if self.VOICE_MODELS_DIR.exists():
            for model_file in self.VOICE_MODELS_DIR.glob("*.pt"):
                models.append({
                    'name': model_file.stem,
                    'path': str(model_file)
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
        output_path = os.path.join(temp_dir, "fastspeak_last_audio.wav")
        
        if self.use_direct and self.model and self.gpt_cond_latent is not None:
            self._inference_direct(text, language, output_path)
        elif self.speaker_wav and len(self.speaker_wav) > 0:
            self._inference_api_cloning(text, language, output_path)
        else:
            self._inference_api_default(text, language, output_path)
        
        # Audio abspielen
        data, samplerate = sf.read(output_path)
        sd.play(data, samplerate)
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
            sd.play(data, samplerate)
            sd.wait()
            
        finally:
            try:
                os.unlink(output_path)
            except:
                pass
    
    def _inference_direct(self, text, language, output_path):
        """Direkte XTTS-Inference mit optimierten Parametern"""
        import torch
        import torchaudio
        
        print("Verwende optimierte direkte XTTS-Inference...")
        
        out = self.model.inference(
            text=text,
            language=language,
            gpt_cond_latent=self.gpt_cond_latent,
            speaker_embedding=self.speaker_embedding,
            # Optimierte Parameter für beste Qualität
            temperature=0.3,  # Niedrig für konsistente, klare Ausgabe (Standard: 0.65)
            length_penalty=1.0,  # Ausgeglichene Länge
            repetition_penalty=5.0,  # Hoch gegen Wiederholungen/Stottern
            top_k=30,  # Eingeschränktere Token-Auswahl für Stabilität (Standard: 50)
            top_p=0.75,  # Leicht reduziert für weniger Variation (Standard: 0.8)
            speed=1.0,  # Normale Geschwindigkeit
            enable_text_splitting=True  # Satzweise Verarbeitung
        )
        
        # Speichern mit korrekter Sample-Rate (24kHz für XTTS)
        torchaudio.save(output_path, torch.tensor(out["wav"]).unsqueeze(0), 24000)
    
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
            repetition_penalty=5.0,
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
        print("FastSpeak - Text-to-Speech mit Coqui TTS")
        print("\nVerwendung:")
        print("  python main.py \"Ihr Text hier\"")
        print("\nOder starten Sie die GUI:")
        print("  python gui.py")


if __name__ == "__main__":
    main()
