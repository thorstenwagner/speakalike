"""
Unit Tests für die Stop-Marker-Erkennung.

Testet verschiedene Whisper-Transkriptionen, einschließlich typischer Fehlerkennungen.
"""

import unittest
import sys
import os

# Füge das Projektverzeichnis zum Pfad hinzu
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import TextToSpeech


class TestStopMarkerDetection(unittest.TestCase):
    """Tests für die Stop-Marker-Erkennung."""
    
    @classmethod
    def setUpClass(cls):
        """Erstelle eine Mock-Instanz des TextToSpeech ohne TTS zu laden."""
        # Wir erstellen eine minimale Instanz nur für die Marker-Erkennung
        cls.wrapper = TextToSpeech.__new__(TextToSpeech)
        # Kopiere die Klassen-Attribute
        cls.wrapper.STOP_MARKERS = TextToSpeech.STOP_MARKERS
        cls.wrapper.STOP_MARKER_PATTERNS = TextToSpeech.STOP_MARKER_PATTERNS
    
    def _create_word_list(self, words, start_time=0.0, word_duration=0.3):
        """Hilfsfunktion: Erstellt eine Wort-Liste mit Zeitstempeln."""
        result = []
        current_time = start_time
        for word in words:
            result.append({
                "word": word,
                "start": current_time,
                "end": current_time + word_duration
            })
            current_time += word_duration + 0.1  # Kleine Pause zwischen Wörtern
        return result
    
    # ==================== Deutsche Tests ====================
    
    def test_de_standard_marker(self):
        """Test: Korrekt erkannter Stop-Marker 'Ende der Nachricht'."""
        words = self._create_word_list([
            "Ich", "habe", "das", "nur", "im", "Video", "gesehen",
            "Ende", "der", "Nachricht"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNotNone(start_time, "Stop-Marker sollte gefunden werden")
        self.assertEqual(index, 7, "Index sollte bei 'Ende' sein")
        self.assertEqual(words[index]["word"], "Ende")
    
    def test_de_whisper_fehler_danach_ich(self):
        """Test: Whisper erkennt 'Ende danach ich' statt 'Ende der Nachricht'."""
        words = self._create_word_list([
            "Ich", "habe", "das", "nun", "Video", "gesehen.",
            "Weiß,", "aber", "nicht", "wie", "es", "geht.",
            "Ende", "danach", "ich."
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNotNone(start_time, "Stop-Marker sollte trotz Fehlerkennung gefunden werden")
        self.assertEqual(index, 12, "Index sollte bei 'Ende' sein")
        self.assertEqual(words[index]["word"], "Ende")
    
    def test_de_whisper_fehler_nur_danach(self):
        """Test: Whisper erkennt nur 'danach' ohne 'Ende'."""
        words = self._create_word_list([
            "Das", "ist", "ein", "Test",
            "danach"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNotNone(start_time, "Stop-Marker sollte bei 'danach' gefunden werden")
        self.assertEqual(words[index]["word"], "danach")
    
    def test_de_marker_mit_punkt(self):
        """Test: Stop-Marker mit Satzzeichen 'Ende.' und 'Nachricht.'"""
        words = self._create_word_list([
            "Hallo", "Welt",
            "Ende.", "der", "Nachricht."
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNotNone(start_time, "Stop-Marker sollte trotz Punkt gefunden werden")
        self.assertEqual(index, 2, "Index sollte bei 'Ende.' sein")
    
    def test_de_nur_ende_der(self):
        """Test: Whisper erkennt 'Ende der' aber nicht 'Nachricht'."""
        words = self._create_word_list([
            "Das", "ist", "der", "Text",
            "Ende", "der"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNotNone(start_time, "Stop-Marker sollte bei 'Ende der' gefunden werden")
        self.assertEqual(words[index]["word"], "Ende")
    
    def test_de_kein_marker_im_text(self):
        """Test: Kein Stop-Marker vorhanden."""
        words = self._create_word_list([
            "Das", "ist", "ein", "normaler", "Text", "ohne", "Marker"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNone(start_time, "Kein Stop-Marker sollte gefunden werden")
        self.assertIsNone(index)
    
    def test_de_ende_mitten_im_text_ignoriert(self):
        """Test: 'Ende' mitten im Text sollte ignoriert werden (nur letzte 6 Wörter)."""
        words = self._create_word_list([
            "Am", "Ende", "des", "Tages",  # Dieses "Ende" sollte ignoriert werden
            "ist", "alles", "gut", "gelaufen",
            "und", "das", "war", "schön"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNone(start_time, "Stop-Marker am Anfang sollte ignoriert werden")
    
    # ==================== Englische Tests ====================
    
    def test_en_standard_marker(self):
        """Test: Englischer Stop-Marker 'End of message'."""
        words = self._create_word_list([
            "This", "is", "a", "test",
            "End", "of", "message"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "en")
        
        self.assertIsNotNone(start_time, "Englischer Stop-Marker sollte gefunden werden")
        self.assertEqual(words[index]["word"], "End")
    
    def test_en_nur_message(self):
        """Test: Nur 'message' am Ende."""
        words = self._create_word_list([
            "Hello", "world", "message"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "en")
        
        self.assertIsNotNone(start_time, "Stop-Marker sollte bei 'message' gefunden werden")
    
    # ==================== Add Stop Marker Tests ====================
    
    def test_add_stop_marker_de(self):
        """Test: Stop-Marker wird korrekt hinzugefügt."""
        text = "Das ist ein Test"
        result = self.wrapper._add_stop_marker(text, "de")
        
        self.assertEqual(result, "Das ist ein Test. Ende der Nachricht.")
    
    def test_add_stop_marker_bereits_vorhanden(self):
        """Test: Stop-Marker wird nicht doppelt hinzugefügt."""
        text = "Das ist ein Test. Ende der Nachricht."
        result = self.wrapper._add_stop_marker(text, "de")
        
        self.assertEqual(result, text, "Text sollte unverändert bleiben")
    
    def test_add_stop_marker_en(self):
        """Test: Englischer Stop-Marker."""
        text = "This is a test"
        result = self.wrapper._add_stop_marker(text, "en")
        
        self.assertEqual(result, "This is a test. End of message.")
    
    # ==================== Edge Cases ====================
    
    def test_leere_wortliste(self):
        """Test: Leere Wortliste."""
        words = []
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "de")
        
        self.assertIsNone(start_time)
        self.assertIsNone(index)
    
    def test_unbekannte_sprache_fallback(self):
        """Test: Unbekannte Sprache fällt auf Englisch zurück."""
        words = self._create_word_list([
            "Test", "End", "of", "message"
        ])
        
        start_time, index = self.wrapper._find_stop_marker_position(words, "xyz")
        
        self.assertIsNotNone(start_time, "Sollte auf Englisch zurückfallen")


class TestStopMarkerPatterns(unittest.TestCase):
    """Tests für die Stop-Marker-Muster-Konfiguration."""
    
    def test_alle_sprachen_haben_patterns(self):
        """Test: Alle Sprachen in STOP_MARKERS haben auch STOP_MARKER_PATTERNS."""
        for lang in TextToSpeech.STOP_MARKERS.keys():
            self.assertIn(lang, TextToSpeech.STOP_MARKER_PATTERNS,
                         f"Sprache '{lang}' fehlt in STOP_MARKER_PATTERNS")
    
    def test_pattern_format(self):
        """Test: Alle Patterns haben das korrekte Format."""
        for lang, patterns in TextToSpeech.STOP_MARKER_PATTERNS.items():
            self.assertIn("first_words", patterns,
                         f"'{lang}' fehlt 'first_words'")
            self.assertIn("second_words", patterns,
                         f"'{lang}' fehlt 'second_words'")
            self.assertIsInstance(patterns["first_words"], list,
                                 f"'{lang}' first_words sollte Liste sein")
            self.assertIsInstance(patterns["second_words"], list,
                                 f"'{lang}' second_words sollte Liste sein")
            self.assertGreater(len(patterns["first_words"]), 0,
                              f"'{lang}' first_words sollte nicht leer sein")
            self.assertGreater(len(patterns["second_words"]), 0,
                              f"'{lang}' second_words sollte nicht leer sein")


if __name__ == "__main__":
    # Unterdrücke die Debug-Ausgaben während der Tests
    import io
    from contextlib import redirect_stdout
    
    print("=" * 60)
    print("Stop-Marker Unit Tests")
    print("=" * 60)
    
    # Führe Tests mit unterdrückter Ausgabe aus
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestStopMarkerDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestStopMarkerPatterns))
    
    # Runner mit Verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Zusammenfassung
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print(f"✅ Alle {result.testsRun} Tests erfolgreich!")
    else:
        print(f"❌ {len(result.failures)} Fehler, {len(result.errors)} Errors")
    print("=" * 60)
