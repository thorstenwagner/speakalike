"""
Audio-Vorverarbeitung für Voice Cloning
- Rauschunterdrückung
- Stille am Ende entfernen
- Kurze Samples zusammenfügen
"""
import os
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path


def reduce_noise(audio_data, sample_rate, prop_decrease=0.8):
    """
    Reduziert Hintergrundrauschen im Audio
    
    Args:
        audio_data: Audio als numpy array
        sample_rate: Sample-Rate
        prop_decrease: Stärke der Rauschunterdrückung (0-1)
    """
    try:
        import noisereduce as nr
        # Rauschprofil aus den letzten 0.5 Sekunden schätzen (oft Rauschen am Ende)
        noise_sample_length = min(int(sample_rate * 0.5), len(audio_data) // 4)
        noise_sample = audio_data[-noise_sample_length:]
        
        # Rauschen reduzieren
        reduced = nr.reduce_noise(
            y=audio_data, 
            sr=sample_rate,
            y_noise=noise_sample,
            prop_decrease=prop_decrease,
            stationary=True
        )
        return reduced
    except Exception as e:
        print(f"Warnung: Rauschunterdrückung fehlgeschlagen: {e}")
        return audio_data


def trim_silence(audio_data, sample_rate, threshold_db=-40, min_silence_duration=0.1):
    """
    Entfernt Stille am Anfang und Ende des Audios
    
    Args:
        audio_data: Audio als numpy array
        sample_rate: Sample-Rate
        threshold_db: Schwellwert in dB für Stille-Erkennung
        min_silence_duration: Minimale Stille-Dauer in Sekunden
    """
    # Zu Mono konvertieren falls Stereo
    if len(audio_data.shape) > 1:
        mono = np.mean(audio_data, axis=1)
    else:
        mono = audio_data
    
    # Amplitude zu dB
    amplitude = np.abs(mono)
    # Vermeiden von log(0)
    amplitude = np.maximum(amplitude, 1e-10)
    db = 20 * np.log10(amplitude / np.max(amplitude))
    
    # Finde Bereiche über dem Schwellwert
    above_threshold = db > threshold_db
    
    # Finde Start und Ende
    if not np.any(above_threshold):
        return audio_data  # Kein Signal gefunden
    
    start_idx = np.argmax(above_threshold)
    end_idx = len(above_threshold) - np.argmax(above_threshold[::-1])
    
    # Etwas Puffer lassen (50ms)
    buffer_samples = int(0.05 * sample_rate)
    start_idx = max(0, start_idx - buffer_samples)
    end_idx = min(len(audio_data), end_idx + buffer_samples)
    
    return audio_data[start_idx:end_idx]


def normalize_audio(audio_data, target_db=-3):
    """
    Normalisiert Audio auf einen Ziel-Pegel
    
    Args:
        audio_data: Audio als numpy array
        target_db: Ziel-Pegel in dB
    """
    # Aktueller Peak
    peak = np.max(np.abs(audio_data))
    if peak == 0:
        return audio_data
    
    # Ziel-Amplitude
    target_amplitude = 10 ** (target_db / 20)
    
    # Skalieren
    return audio_data * (target_amplitude / peak)


def process_audio_file(file_path, output_path=None, reduce_noise_enabled=True, 
                       trim_enabled=True, normalize_enabled=True):
    """
    Verarbeitet eine Audio-Datei mit allen Optimierungen
    
    Args:
        file_path: Pfad zur Eingabe-Datei
        output_path: Pfad für die Ausgabe (optional, sonst temp-Datei)
        reduce_noise_enabled: Rauschunterdrückung aktivieren
        trim_enabled: Stille entfernen
        normalize_enabled: Audio normalisieren
        
    Returns:
        Pfad zur verarbeiteten Datei
    """
    # Audio laden
    audio_data, sample_rate = sf.read(file_path)
    
    # Zu Mono konvertieren falls Stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Verarbeitungsschritte
    if trim_enabled:
        audio_data = trim_silence(audio_data, sample_rate)
    
    if reduce_noise_enabled:
        audio_data = reduce_noise(audio_data, sample_rate)
    
    if normalize_enabled:
        audio_data = normalize_audio(audio_data)
    
    # Speichern
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.wav')
    
    sf.write(output_path, audio_data, sample_rate)
    return output_path


def concatenate_audio_files(file_paths, output_path=None, target_sample_rate=22050,
                           add_silence_between=0.3):
    """
    Fügt mehrere Audio-Dateien zu einer zusammen
    
    Args:
        file_paths: Liste von Audio-Dateipfaden
        output_path: Pfad für die Ausgabe
        target_sample_rate: Ziel-Sample-Rate
        add_silence_between: Stille zwischen Clips in Sekunden
        
    Returns:
        Pfad zur zusammengefügten Datei
    """
    all_audio = []
    silence = np.zeros(int(add_silence_between * target_sample_rate))
    
    for i, file_path in enumerate(file_paths):
        audio_data, sample_rate = sf.read(file_path)
        
        # Zu Mono konvertieren
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Resample falls nötig
        if sample_rate != target_sample_rate:
            from scipy import signal
            num_samples = int(len(audio_data) * target_sample_rate / sample_rate)
            audio_data = signal.resample(audio_data, num_samples)
        
        all_audio.append(audio_data)
        
        # Stille zwischen Clips (außer nach dem letzten)
        if i < len(file_paths) - 1:
            all_audio.append(silence)
    
    # Zusammenfügen
    concatenated = np.concatenate(all_audio)
    
    # Speichern
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.wav')
    
    sf.write(output_path, concatenated, target_sample_rate)
    return output_path


def prepare_samples_for_cloning(file_paths, min_total_duration=10, 
                                reduce_noise_enabled=True):
    """
    Bereitet Audio-Samples für Voice Cloning vor:
    1. Verarbeitet jede Datei (Rauschen entfernen, trimmen, normalisieren)
    2. Fügt kurze Samples zusammen wenn nötig
    
    Args:
        file_paths: Liste von Audio-Dateipfaden
        min_total_duration: Minimale Gesamtdauer in Sekunden
        reduce_noise_enabled: Rauschunterdrückung aktivieren
        
    Returns:
        Liste von Pfaden zu verarbeiteten Dateien
    """
    processed_files = []
    total_duration = 0
    
    print(f"Verarbeite {len(file_paths)} Audio-Samples...")
    
    for file_path in file_paths:
        try:
            # Audio laden und Dauer prüfen
            audio_data, sample_rate = sf.read(file_path)
            duration = len(audio_data) / sample_rate
            
            print(f"  - {os.path.basename(file_path)}: {duration:.1f}s")
            
            # Verarbeiten
            processed_path = process_audio_file(
                file_path,
                reduce_noise_enabled=reduce_noise_enabled,
                trim_enabled=True,
                normalize_enabled=True
            )
            
            # Neue Dauer nach Verarbeitung
            processed_audio, _ = sf.read(processed_path)
            processed_duration = len(processed_audio) / sample_rate
            
            processed_files.append(processed_path)
            total_duration += processed_duration
            
            print(f"    → Verarbeitet: {processed_duration:.1f}s (Rauschen entfernt, getrimmt)")
            
        except Exception as e:
            print(f"  ✗ Fehler bei {file_path}: {e}")
    
    print(f"\nGesamtdauer: {total_duration:.1f}s")
    
    # Wenn Gesamtdauer zu kurz, Samples zusammenfügen
    if total_duration < min_total_duration and len(processed_files) > 1:
        print(f"Füge Samples zusammen für bessere Qualität...")
        combined_path = concatenate_audio_files(processed_files)
        
        combined_audio, sr = sf.read(combined_path)
        combined_duration = len(combined_audio) / sr
        print(f"Kombiniertes Sample: {combined_duration:.1f}s")
        
        # Kombiniertes Sample als erstes, einzelne als zusätzliche
        return [combined_path] + processed_files
    
    return processed_files


def get_audio_info(file_path):
    """
    Gibt Informationen über eine Audio-Datei zurück
    """
    try:
        audio_data, sample_rate = sf.read(file_path)
        duration = len(audio_data) / sample_rate
        channels = 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
        
        return {
            'path': file_path,
            'duration': duration,
            'sample_rate': sample_rate,
            'channels': channels,
            'samples': len(audio_data)
        }
    except Exception as e:
        return {'path': file_path, 'error': str(e)}
