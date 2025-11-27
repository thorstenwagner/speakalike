"""
SpeakAlike - Beispiele für die Verwendung
"""
from main import TextToSpeech


def beispiel_einfach():
    """Einfaches Beispiel: Text vorlesen"""
    print("Beispiel 1: Einfacher Text")
    tts = TextToSpeech()
    tts.speak("Hallo, ich bin SpeakAlike. Ich kann deutschen Text vorlesen!")


def beispiel_geschwindigkeit():
    """Beispiel mit verschiedenen Geschwindigkeiten"""
    print("\nBeispiel 2: Verschiedene Geschwindigkeiten")
    tts = TextToSpeech()
    
    print("  - Langsam (100 WPM)")
    tts.speak("Das ist sehr langsam gesprochen.", rate=100)
    
    print("  - Normal (150 WPM)")
    tts.speak("Das ist normale Geschwindigkeit.", rate=150)
    
    print("  - Schnell (250 WPM)")
    tts.speak("Das ist sehr schnell gesprochen!", rate=250)


def beispiel_asynchron():
    """Beispiel: Asynchrones Vorlesen"""
    print("\nBeispiel 3: Asynchrones Vorlesen")
    tts = TextToSpeech()
    
    print("  - Starte asynchrones Vorlesen...")
    thread = tts.speak_async("Dies wird asynchron vorgelesen, während der Code weiterläuft.")
    
    print("  - Code läuft weiter während gesprochen wird!")
    thread.join()  # Warte auf Fertigstellung
    print("  - Fertig!")


def beispiel_langer_text():
    """Beispiel: Längerer Text"""
    print("\nBeispiel 4: Längerer Text")
    tts = TextToSpeech()
    
    text = """
    SpeakAlike ist eine benutzerfreundliche Anwendung zur Sprachsynthese.
    Sie nutzt die Coqui TTS-Bibliothek, um Text in gesprochene Sprache umzuwandeln.
    Die Anwendung bietet eine grafische Benutzeroberfläche und unterstützt
    verschiedene Sprachen sowie einstellbare Sprechgeschwindigkeiten.
    """
    
    tts.speak(text.strip())


if __name__ == "__main__":
    print("=== SpeakAlike Beispiele ===\n")
    
    # Führe alle Beispiele aus
    beispiel_einfach()
    input("\nDrücken Sie Enter für das nächste Beispiel...")
    
    beispiel_geschwindigkeit()
    input("\nDrücken Sie Enter für das nächste Beispiel...")
    
    beispiel_asynchron()
    input("\nDrücken Sie Enter für das nächste Beispiel...")
    
    beispiel_langer_text()
    
    print("\n=== Alle Beispiele abgeschlossen! ===")
    print("Starten Sie die GUI mit: python gui.py")
