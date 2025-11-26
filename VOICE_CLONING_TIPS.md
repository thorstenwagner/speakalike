# Voice Cloning Optimierung - Tipps für beste Qualität

## 🎯 Optimale Audio-Sample Qualität

### Empfohlene Eigenschaften der Aufnahmen:

1. **Länge**: **10-30 Sekunden** pro Sample (mehr ist besser!)
   - Mehrere Samples (3-5) sind **deutlich** besser als ein einziges Sample
   - Die App verwendet bis zu **30 Sekunden** für GPT-Konditionierung
   - Längere Referenzen = bessere Stimmerfassung

2. **Audioqualität**:
   - **Sample Rate**: Mindestens 22050 Hz (besser 44100 Hz oder 48000 Hz)
   - **Format**: WAV (unkomprimiert) für beste Ergebnisse
   - **Bit Depth**: 16-bit oder höher
   - Kein MP3 unter 256kbps verwenden

3. **Aufnahmeumgebung**:
   - ✅ Ruhiger Raum ohne Hintergrundgeräusche
   - ✅ Kein Echo oder Hall
   - ✅ Keine Musik oder andere Sprecher
   - ✅ Keine Atemgeräusche am Anfang/Ende
   - ❌ Keine Kompressionsartefakte
   - ❌ Kein Clipping (zu laute Aufnahme)

4. **Sprechweise**:
   - Natürlicher, klarer Sprechstil
   - Konstante Lautstärke
   - Deutliche Aussprache
   - Verschiedene Satzarten (Aussage, Frage, Ausruf) in verschiedenen Samples

## 🔧 Audio-Vorverarbeitung (Optional)

Falls Sie Audacity oder ähnliche Software nutzen:

1. **Normalisierung**: Auf -3dB normalisieren
2. **Rauschreduzierung**: Leichte Rauschreduzierung anwenden (nicht übertreiben!)
3. **Trimmen**: Stille am Anfang/Ende entfernen
4. **EQ**: Leicht hochpassfiltern bei 80Hz (entfernt Rumpeln)

## 📝 Beispiel-Sätze für Aufnahmen

Gute Testsätze mit verschiedenen phonetischen Eigenschaften:

```
"Guten Tag, ich freue mich sehr, Sie kennenzulernen."
"Die Technologie entwickelt sich rasant weiter."
"Können Sie mir bitte bei dieser Frage helfen?"
"Was für ein wunderschöner Tag heute!"
```

## 🚀 Verwendung in FastSpeak

1. Bereiten Sie 3-5 Audio-Samples vor (je 6-10 Sekunden)
2. Laden Sie alle Samples über "Samples hochladen" hoch
3. Die App verwendet automatisch ALLE Samples für bessere Qualität
4. Parameter `split_sentences=True` sorgt für natürlichere Intonation

## ⚙️ Technische Optimierungen in FastSpeak

Die App nutzt jetzt **fortgeschrittene XTTS-Optimierungen**:

### Direkte Modell-Kontrolle
- ✅ **Direkter XTTS-Zugriff** statt nur TTS API (mehr Kontrolle)
- ✅ **Vorab-berechnete Speaker-Embeddings** (Caching für konsistente Qualität)
- ✅ **Audio-Normalisierung** der Referenz-Samples

### Optimierte Konditionierungs-Parameter
| Parameter | Standard | FastSpeak | Wirkung |
|-----------|----------|-----------|---------|
| `gpt_cond_len` | 12s | **30s** | Mehr Kontext für GPT |
| `gpt_cond_chunk_len` | 4s | **6s** | Stabilere Latent-Berechnung |
| `max_ref_len` | 10s | **60s** | Längere Decoder-Referenz |
| `sound_norm_refs` | False | **True** | Normalisierte Audio-Qualität |

### Optimierte Inference-Parameter
| Parameter | Standard | FastSpeak | Wirkung |
|-----------|----------|-----------|---------|
| `temperature` | 0.65 | **0.3** | Konsistentere, klarere Ausgabe |
| `repetition_penalty` | 2.0 | **5.0** | Verhindert Stottern/Wiederholungen |
| `top_k` | 50 | **30** | Stabilere Token-Auswahl |
| `top_p` | 0.8 | **0.75** | Weniger zufällige Variation |

### Hardware-Beschleunigung
- ✅ **GPU-Beschleunigung** mit NVIDIA RTX 4070 für schnellere Verarbeitung
- ✅ **Deterministischer Seed** für reproduzierbare Ergebnisse

## 🎤 Aufnahme-Tipps

### Smartphone-Aufnahme:
- Abstand 15-20cm zum Mund
- Voice Recorder App in höchster Qualität
- Danach auf PC übertragen und als WAV exportieren

### Mikrofon am PC:
- USB-Mikrofon oder gutes Headset verwenden
- Aufnahme-Software: Audacity (kostenlos)
- Direkt als WAV mit 44100 Hz aufnehmen

## 🔍 Qualitätsprüfung

Nach dem Upload sollten Sie sehen:
- `"3-5 Datei(en) ausgewählt"` (mehrere Samples)
- Beim ersten Vorlesen dauert es etwas länger (GPU-Verarbeitung)
- Die geklonte Stimme sollte deutlich erkennbar sein

Falls die Qualität nicht zufriedenstellend ist:
1. Prüfen Sie die Audio-Qualität Ihrer Samples (Rauschen? Echo?)
2. Nehmen Sie neue Samples in ruhigerer Umgebung auf
3. Verwenden Sie mehrere verschiedene Sätze
4. Achten Sie auf klare, deutliche Aussprache
