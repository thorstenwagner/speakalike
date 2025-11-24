"""
FastSpeak - Einfache Text-to-Speech Anwendung mit pyttsx3
"""
import sys
import threading
import pyttsx3


class TextToSpeech:
    """Text-to-Speech Engine Wrapper"""
    
    def __init__(self):
        self.is_speaking = False
        self.engine = pyttsx3.init()
        print("pyttsx3 TTS initialisiert")
        
        # Setze deutsche Stimme falls verfügbar
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if 'german' in voice.name.lower() or 'de' in voice.id.lower():
                self.engine.setProperty('voice', voice.id)
                print(f"Deutsche Stimme gewählt: {voice.name}")
                break
            
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
            # Setze Sprechgeschwindigkeit
            self.engine.setProperty('rate', rate)
            
            # Versuche passende Sprachstimme zu finden
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if language in voice.id.lower() or (language == 'de' and 'german' in voice.name.lower()):
                    self.engine.setProperty('voice', voice.id)
                    break
            
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Fehler beim Vorlesen: {e}")
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
        try:
            self.engine.stop()
        except:
            pass
        self.is_speaking = False


def main():
    """Kommandozeilen-Version für schnelle Tests"""
    if len(sys.argv) > 1:
        text = ' '.join(sys.argv[1:])
        tts = TextToSpeech()
        print(f"Spreche: {text}")
        tts.speak(text)
    else:
        print("FastSpeak - Text-to-Speech")
        print("\nVerwendung:")
        print("  python main_simple.py \"Ihr Text hier\"")
        print("\nOder starten Sie die GUI:")
        print("  python gui.py")


if __name__ == "__main__":
    main()
