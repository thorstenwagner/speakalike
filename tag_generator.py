"""
SpeakAlike Tag Generator - Automatische Schlagwort-Generierung mit Claude
"""
import os
from typing import List, Optional

# API Key aus .env oder Umgebungsvariable laden
def get_api_key() -> Optional[str]:
    """Lädt den Claude API Key aus verschiedenen Quellen."""
    # Erst Umgebungsvariable prüfen
    key = os.environ.get("CLAUDE_API_KEY")
    if key:
        return key
    
    # Dann .env Datei im gleichen Verzeichnis
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("CLAUDE_API_KEY=") and not line.startswith("#"):
                    key = line.split("=", 1)[1].strip().strip('"\'')
                    if key and not key.startswith("#"):
                        return key
    
    # Dann .env im fasttypet Verzeichnis (falls vorhanden)
    fasttypet_env = os.path.join(os.path.dirname(__file__), "..", "fasttypet", ".env")
    if os.path.exists(fasttypet_env):
        with open(fasttypet_env, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("CLAUDE_API_KEY=") and not line.startswith("#"):
                    key = line.split("=", 1)[1].strip().strip('"\'')
                    if key and not key.startswith("#"):
                        return key
    
    return None


def generate_tags(text: str, existing_tags: List[str] = None, 
                  num_tags: int = 5, api_key: str = None) -> List[str]:
    """
    Generiert Schlagwörter für einen Text mit Claude.
    
    Args:
        text: Der Text, für den Tags generiert werden sollen
        existing_tags: Liste bereits vorhandener Tags (werden bevorzugt)
        num_tags: Anzahl der zu generierenden Tags
        api_key: Claude API Key (optional, wird sonst aus .env geladen)
        
    Returns:
        Liste von Schlagwörtern
    """
    if not api_key:
        api_key = get_api_key()
    
    if not api_key:
        print("Kein Claude API Key gefunden!")
        return []
    
    try:
        import anthropic
    except ImportError:
        print("anthropic Paket nicht installiert. Bitte 'pip install anthropic' ausführen.")
        return []
    
    # Existing tags formatieren
    existing_tags_str = ""
    if existing_tags:
        existing_tags_str = f"""
Bereits vorhandene Schlagwörter in der Datenbank (bevorzuge diese wenn passend):
{', '.join(existing_tags)}
"""
    
    prompt = f"""Generiere genau {num_tags} passende Schlagwörter für folgenden gesprochenen Text.

Text:
"{text}"
{existing_tags_str}
Regeln:
1. Schlagwörter sollen den Inhalt/Thema beschreiben
2. Einwortige, kurze Tags (keine Sätze)
3. Kleingeschrieben
4. Auf Deutsch
5. Wenn ein vorhandenes Schlagwort passt, verwende es
6. Kategorien wie: thema, emotion, anlass, empfänger, etc.

Antworte NUR mit den {num_tags} Schlagwörtern, getrennt durch Kommas, ohne weitere Erklärung."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # Schnell und günstig
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Response parsen
        response_text = message.content[0].text.strip()
        
        # Tags extrahieren (Komma-getrennt)
        tags = [tag.strip().lower() for tag in response_text.split(',')]
        
        # Auf num_tags begrenzen
        tags = tags[:num_tags]
        
        return tags
        
    except Exception as e:
        print(f"Fehler bei Tag-Generierung: {e}")
        return []


# Test
if __name__ == "__main__":
    test_text = "Hallo, ich wollte nur kurz fragen, ob wir uns morgen zum Mittagessen treffen können?"
    existing = ["frage", "termin", "begrüßung", "arbeit", "privat", "familie"]
    
    print(f"Text: {test_text}")
    print(f"Vorhandene Tags: {existing}")
    
    tags = generate_tags(test_text, existing)
    print(f"Generierte Tags: {tags}")
