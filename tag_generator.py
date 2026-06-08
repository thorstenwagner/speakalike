"""
SpeakAlike Tag Generator - Automatische Schlagwort-Generierung mit Claude
"""
import os
from typing import List, Optional

# API Key aus .env oder Umgebungsvariable laden
def get_api_key() -> Optional[str]:
    """Loads the Claude API key from various sources."""
    # Check environment variable first
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
    Generates keywords for a text using Claude.
    
    Args:
        text: the text for which tags should be generated
        existing_tags: Liste bereits vorhandener Tags (werden bevorzugt)
        num_tags: Anzahl der zu generierenden Tags
        api_key: Claude API Key (optional, wird sonst aus .env geladen)
        
    Returns:
        List of keywords
    """
    if not api_key:
        api_key = get_api_key()
    
    if not api_key:
        print("Kein Claude API Key gefunden!")
        return []
    
    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed. Please run 'pip install anthropic'.")
        return []
    
    # Existing tags formatieren
    existing_tags_str = ""
    if existing_tags:
        existing_tags_str = f"""
Existing keywords in the database (prefer these if applicable):
{', '.join(existing_tags)}
"""
    
    prompt = f"""Generate exactly {num_tags} suitable keywords for the following spoken text.

Text:
"{text}"
{existing_tags_str}
Regeln:
1. Keywords should describe the content/topic
2. Single-word, short tags (no sentences)
3. Kleingeschrieben
4. Auf Deutsch
5. Wenn ein vorhandenes Schlagwort passt, verwende es
6. Categories such as: topic, emotion, occasion, recipient, etc.

Reply ONLY with the {num_tags} keywords, separated by commas, without further explanation."""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",  # Fast and cost-effective
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
        print(f"Tag generation error: {e}")
        raise


# Test
if __name__ == "__main__":
    test_text = "Hello, I just wanted to ask if we could meet for lunch tomorrow?"
    existing = ["question", "appointment", "greeting", "work", "personal", "family"]
    
    print(f"Text: {test_text}")
    print(f"Vorhandene Tags: {existing}")
    
    tags = generate_tags(test_text, existing)
    print(f"Generierte Tags: {tags}")
