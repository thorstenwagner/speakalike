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
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    print("Warnung: Coqui TTS nicht verfügbar. Fallback auf pyttsx3.")
    import pyttsx3


class TextToSpeech:
    """Text-to-Speech Engine Wrapper"""
    
    def __init__(self):
        self.is_speaking = False
        self.speaker_wav = None
        
        if COQUI_AVAILABLE:
            # Verwende ein Modell das Voice Cloning unterstützt (XTTS)
            try:
                import torch
                # GPU-Unterstützung prüfen
                gpu_available = torch.cuda.is_available()
                self.engine = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", gpu=gpu_available)
                self.use_coqui = True
                if gpu_available:
                    gpu_name = torch.cuda.get_device_name(0)
                    print(f"Coqui TTS initialisiert (XTTS v2 - Voice Cloning) mit GPU: {gpu_name}")
                else:
                    print("Coqui TTS initialisiert (XTTS v2 - Voice Cloning) mit CPU")
            except:
                # Fallback auf einfacheres Modell
                self.engine = TTS(model_name="tts_models/de/thorsten/tacotron2-DDC")
                self.use_coqui = True
                print("Coqui TTS initialisiert (Thorsten)")
        else:
            self.engine = pyttsx3.init()
            self.use_coqui = False
            print("pyttsx3 TTS initialisiert (Fallback)")
    
    def set_speaker_wav(self, wav_files):
        """
        Setzt Audio-Samples für Voice Cloning
        
        Args:
            wav_files (list): Liste von Pfaden zu WAV-Dateien oder None
        """
        self.speaker_wav = wav_files
            
    def speak(self, text, rate=150, language='de'):
        """
        Spricht den übergebenen Text aus
        
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
                # Coqui TTS verwendet - Ausgabe in temporäre Datei
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    output_path = temp_file.name
                
                # Voice Cloning wenn Samples verfügbar
                if self.speaker_wav and len(self.speaker_wav) > 0:
                    self.engine.tts_to_file(
                        text=text,
                        file_path=output_path,
                        speaker_wav=self.speaker_wav[0],  # Verwende erste Sample-Datei
                        language=language
                    )
                else:
                    self.engine.tts_to_file(text=text, file_path=output_path)
                
                # Audio direkt mit sounddevice abspielen
                import sounddevice as sd
                import soundfile as sf
                data, samplerate = sf.read(output_path)
                sd.play(data, samplerate)
                sd.wait()
                
                # Temporäre Datei löschen
                try:
                    os.unlink(output_path)
                except:
                    pass
            else:
                # pyttsx3 Fallback
                self.engine.setProperty('rate', rate)
                voices = self.engine.getProperty('voices')
                
                # Versuche deutsche Stimme zu finden
                for voice in voices:
                    if language in voice.id.lower() or 'german' in voice.name.lower():
                        self.engine.setProperty('voice', voice.id)
                        break
                
                self.engine.say(text)
                self.engine.runAndWait()
        except Exception as e:
            print(f"Fehler beim Vorlesen: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.is_speaking = False
    
    def speak_async(self, text, rate=150, language='de'):
        """Spricht Text asynchron in einem separaten Thread"""
        thread = threading.Thread(target=self.speak, args=(text, rate, language))
        thread.daemon = True
        thread.start()
        return thread
    
    def stop(self):
        """Stoppt die Wiedergabe"""
        if not self.use_coqui and hasattr(self.engine, 'stop'):
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
