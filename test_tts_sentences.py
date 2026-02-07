"""
Test-Skript für TTS-Generierung mit verschiedenen Sätzen.
Testet die Stop-Marker-Erkennung im Live-Betrieb.
"""

import requests
import time
import json

BASE_URL = "http://127.0.0.1:8765"

# Testsätze - verschiedene Längen und Schwierigkeiten
TEST_SENTENCES = [
    # Kurze Sätze
    "Hallo, wie geht es dir?",
    "Das ist ein Test.",
    "What the fuck?",
    
    # Mittellange Sätze
    "Ich habe das nur im Video gesehen, weiß aber nicht wie es geht.",
    "Die Sonne scheint heute besonders schön durch das Fenster.",
    
    # Längere Sätze
    "Künstliche Intelligenz verändert die Art und Weise, wie wir arbeiten und kommunizieren.",
    "Der schnelle braune Fuchs springt über den faulen Hund, das ist ein bekannter Pangramm-Satz.",
    
    # Sätze mit Zahlen und Sonderzeichen
    "Es ist jetzt 15 Uhr und die Temperatur beträgt 22 Grad Celsius.",
    
    # Fragen
    "Können Sie mir bitte erklären, wie das funktioniert?",
]


def check_backend():
    """Prüfe ob das Backend läuft."""
    try:
        response = requests.get(f"{BASE_URL}/api/status", timeout=5)
        return response.status_code == 200
    except:
        return False


def load_voice_model(model_name="meine_stimme"):
    """Lade ein Voice-Modell."""
    try:
        response = requests.post(f"{BASE_URL}/api/voice-models/{model_name}/load", timeout=30)
        return response.status_code == 200
    except Exception as e:
        print(f"  Fehler beim Laden des Modells: {e}")
        return False


def generate_speech(text, language="de"):
    """Generiere Sprache für einen Text."""
    try:
        response = requests.post(
            f"{BASE_URL}/api/tts/speak",
            json={
                "text": text,
                "language": language,
                "speed": 1.0
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "audio_url": data.get("audio_url"),
                "duration": data.get("duration"),
                "generation_time": data.get("generation_time")
            }
        else:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    print("=" * 70)
    print("TTS Satz-Test")
    print("=" * 70)
    
    # Prüfe Backend
    print("\n[1] Prüfe Backend-Verbindung...")
    if not check_backend():
        print("  ❌ Backend nicht erreichbar! Bitte starten mit: .\\start_backend.bat")
        return
    print("  ✅ Backend läuft")
    
    # Lade Voice-Modell
    print("\n[2] Lade Voice-Modell...")
    if not load_voice_model():
        print("  ⚠️ Konnte Modell nicht laden, verwende Standard")
    else:
        print("  ✅ Modell geladen")
    
    # Teste Sätze
    print("\n[3] Generiere Test-Sätze...")
    print("-" * 70)
    
    results = []
    for i, sentence in enumerate(TEST_SENTENCES, 1):
        print(f"\n  [{i}/{len(TEST_SENTENCES)}] \"{sentence[:50]}{'...' if len(sentence) > 50 else ''}\"")
        
        start_time = time.time()
        result = generate_speech(sentence)
        elapsed = time.time() - start_time
        
        if result["success"]:
            print(f"      ✅ Erfolgreich in {elapsed:.2f}s")
            print(f"         Audio-Dauer: {result.get('duration', 'N/A')}s")
            results.append({"sentence": sentence, "success": True, "time": elapsed})
        else:
            print(f"      ❌ Fehler: {result['error']}")
            results.append({"sentence": sentence, "success": False, "error": result['error']})
        
        # Kleine Pause zwischen Generierungen
        time.sleep(0.5)
    
    # Zusammenfassung
    print("\n" + "=" * 70)
    print("Zusammenfassung")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    print(f"  Erfolgreich: {successful}/{len(results)}")
    print(f"  Fehlgeschlagen: {failed}/{len(results)}")
    
    if successful > 0:
        avg_time = sum(r["time"] for r in results if r["success"]) / successful
        print(f"  Durchschnittliche Generierungszeit: {avg_time:.2f}s")
    
    if failed > 0:
        print("\n  Fehlgeschlagene Sätze:")
        for r in results:
            if not r["success"]:
                print(f"    - \"{r['sentence'][:40]}...\": {r['error']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
