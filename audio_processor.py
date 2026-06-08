"""
Audio preprocessing for voice cloning
- Noise reduction
- Stille am Ende entfernen
- Joining short samples
"""
import os
import sys
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

# Windows Konsole auf UTF-8 setzen, um Unicode-Fehler zu vermeiden
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # reconfigure may not be available on older Python versions


def reduce_noise(audio_data, sample_rate, prop_decrease=0.8, use_spectral_gating=True):
    """
    Reduziert Hintergrundrauschen im Audio mit mehreren Methoden
    
    Args:
        audio_data: Audio als numpy array
        sample_rate: Sample-Rate
        prop_decrease: strength of noise reduction (0-1)
        use_spectral_gating: uses spectral gating for better results
    """
    try:
        import noisereduce as nr
        
        # Estimate noise profile from the last 0.5 seconds (often noise at the end)
        noise_sample_length = min(int(sample_rate * 0.5), len(audio_data) // 4)
        noise_sample = audio_data[-noise_sample_length:]
        
        # Reduce noise using stationary method
        reduced = nr.reduce_noise(
            y=audio_data, 
            sr=sample_rate,
            y_noise=noise_sample,
            prop_decrease=prop_decrease,
            stationary=True,
            n_fft=2048,  # Better frequency resolution
            hop_length=512
        )
        
        # Optional: second pass with non-stationary method for better quality
        if use_spectral_gating:
            reduced = nr.reduce_noise(
                y=reduced,
                sr=sample_rate,
                prop_decrease=prop_decrease * 0.5,  # Sanfter im zweiten Durchgang
                stationary=False,
                n_fft=2048,
                hop_length=512
            )
        
        return reduced
    except Exception as e:
        print(f"Warning: noise reduction failed: {e}")
        return audio_data


def trim_silence(audio_data, sample_rate, threshold_db=-40, min_silence_duration=0.1):
    """
    Entfernt Stille am Anfang und Ende des Audios
    
    Args:
        audio_data: Audio als numpy array
        sample_rate: Sample-Rate
        threshold_db: threshold in dB for silence detection
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
    
    # Find regions above the threshold
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


def apply_highpass_filter(audio_data, sample_rate, cutoff_freq=80):
    """
    Wendet einen Hochpassfilter an um tieffrequentes Brummen zu entfernen
    
    Args:
        audio_data: Audio als numpy array
        sample_rate: Sample-Rate
        cutoff_freq: Grenzfrequenz in Hz (Standard: 80Hz entfernt Brummen)
    """
    try:
        from scipy import signal
        
        # Butterworth Hochpassfilter 4. Ordnung
        nyquist = sample_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        # Ensure the value is valid
        if normalized_cutoff >= 1:
            normalized_cutoff = 0.9
        
        b, a = signal.butter(4, normalized_cutoff, btype='high')
        filtered = signal.filtfilt(b, a, audio_data)
        
        return filtered
    except Exception as e:
        print(f"Warnung: Hochpassfilter fehlgeschlagen: {e}")
        return audio_data


def apply_deesser(audio_data, sample_rate, threshold_db=-20, freq_range=(4000, 9000)):
    """
    Reduziert scharfe S-Laute (De-Esser)
    
    Args:
        audio_data: Audio als numpy array
        sample_rate: Sample-Rate  
        threshold_db: threshold for de-essing
        freq_range: frequency range for sibilants
    """
    try:
        from scipy import signal
        from scipy.fft import fft, ifft
        
        # Bandpass for sibilant detection
        nyquist = sample_rate / 2
        low = min(freq_range[0] / nyquist, 0.99)
        high = min(freq_range[1] / nyquist, 0.99)
        
        b, a = signal.butter(2, [low, high], btype='band')
        sibilant = signal.filtfilt(b, a, audio_data)
        
        # Envelope des Sibilant-Signals
        envelope = np.abs(signal.hilbert(sibilant))
        
        # Schwellwert
        threshold = 10 ** (threshold_db / 20) * np.max(np.abs(audio_data))
        
        # Gain Reduction berechnen
        gain = np.ones_like(envelope)
        mask = envelope > threshold
        gain[mask] = threshold / envelope[mask]
        
        # Smooth
        window_size = int(0.01 * sample_rate)
        gain = np.convolve(gain, np.ones(window_size)/window_size, mode='same')
        
        # Anwenden (nur auf Sibilant-Bereich)
        result = audio_data - sibilant * (1 - gain)
        
        return result
    except Exception as e:
        print(f"Warnung: De-Esser fehlgeschlagen: {e}")
        return audio_data


def process_audio_file(file_path, output_path=None, reduce_noise_enabled=True, 
                       trim_enabled=True, normalize_enabled=True,
                       highpass_enabled=True, deesser_enabled=False):
    """
    Verarbeitet eine Audio-Datei mit allen Optimierungen
    
    Args:
        file_path: Pfad zur Eingabe-Datei
        output_path: path for output (optional, defaults to temp file)
        reduce_noise_enabled: enable noise reduction
        trim_enabled: Stille entfernen
        normalize_enabled: Audio normalisieren
        highpass_enabled: Hochpassfilter gegen Brummen
        deesser_enabled: de-esser for harsh sibilants
        
    Returns:
        Pfad zur verarbeiteten Datei
    """
    # Audio laden
    audio_data, sample_rate = sf.read(file_path)
    
    # Zu Mono konvertieren falls Stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)
    
    # Verarbeitungsschritte in optimaler Reihenfolge
    
    # 1. Hochpassfilter zuerst (entfernt DC-Offset und Brummen)
    if highpass_enabled:
        audio_data = apply_highpass_filter(audio_data, sample_rate, cutoff_freq=80)
    
    # 2. Stille trimmen
    if trim_enabled:
        audio_data = trim_silence(audio_data, sample_rate)
    
    # 3. Noise reduction
    if reduce_noise_enabled:
        audio_data = reduce_noise(audio_data, sample_rate)
    
    # 4. De-esser (optional, can improve speech quality)
    if deesser_enabled:
        audio_data = apply_deesser(audio_data, sample_rate)
    
    # 5. Normalisierung zum Schluss
    if normalize_enabled:
        audio_data = normalize_audio(audio_data)
    
    # Speichern
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.wav')
    
    sf.write(output_path, audio_data, sample_rate)
    return output_path


def resample_audio(audio_data, original_sr, target_sr):
    """
    Resamples audio without pitch change
    
    Uses librosa for high-quality resampling that preserves pitch.
    
    Args:
        audio_data: Audio als numpy array
        original_sr: Original Sample-Rate
        target_sr: Ziel Sample-Rate
        
    Returns:
        Resampeltes Audio
    """
    if original_sr == target_sr:
        return audio_data
    
    try:
        import librosa
        # librosa.resample preserves pitch correctly
        resampled = librosa.resample(
            audio_data, 
            orig_sr=original_sr, 
            target_sr=target_sr,
            res_type='soxr_hq'  # Hochwertiges Resampling
        )
        return resampled
    except ImportError:
        # Fallback auf scipy mit korrekter Implementierung
        from scipy import signal
        
        # Compute the exact ratio
        ratio = target_sr / original_sr
        num_samples = int(len(audio_data) * ratio)
        
        # Use polyphase resampling for better quality
        gcd = np.gcd(int(target_sr), int(original_sr))
        up = int(target_sr // gcd)
        down = int(original_sr // gcd)
        
        resampled = signal.resample_poly(audio_data, up, down)
        return resampled


def concatenate_audio_files(file_paths, output_path=None, target_sample_rate=None,
                           add_silence_between=0.3):
    """
    Concatenates multiple audio files into one
    
    Args:
        file_paths: Liste von Audio-Dateipfaden
        output_path: path for output
        target_sample_rate: Ziel-Sample-Rate (None = erste Datei bestimmt)
        add_silence_between: Stille zwischen Clips in Sekunden
        
    Returns:
        Path to the concatenated file
    """
    if not file_paths:
        return None
    
    # Erste Datei laden um Sample-Rate zu bestimmen
    first_audio, first_sr = sf.read(file_paths[0])
    
    # Wenn keine Ziel-Sample-Rate angegeben, Original beibehalten
    # XTTS macht das Resampling intern korrekt
    if target_sample_rate is None:
        target_sample_rate = first_sr
        print(f"Behalte Original-Sample-Rate: {target_sample_rate} Hz")
    
    all_audio = []
    silence = np.zeros(int(add_silence_between * target_sample_rate))
    
    for i, file_path in enumerate(file_paths):
        audio_data, sample_rate = sf.read(file_path)
        
        # Zu Mono konvertieren
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Resample only if needed (different sample rates in files)
        if sample_rate != target_sample_rate:
            print(f"  Resample {file_path}: {sample_rate} -> {target_sample_rate} Hz")
            audio_data = resample_audio(audio_data, sample_rate, target_sample_rate)
        
        all_audio.append(audio_data)
        
        # Silence between clips (except after the last one)
        if i < len(file_paths) - 1:
            all_audio.append(silence)
    
    # Concatenate
    concatenated = np.concatenate(all_audio)
    
    # Speichern
    if output_path is None:
        output_path = tempfile.mktemp(suffix='.wav')
    
    sf.write(output_path, concatenated, target_sample_rate)
    return output_path


def prepare_samples_for_cloning(file_paths, min_total_duration=10, 
                                reduce_noise_enabled=True):
    """
    Prepares audio samples for voice cloning:
    1. Verarbeitet jede Datei (Rauschen entfernen, trimmen, normalisieren)
    2. Joins short samples if needed
    
    Args:
        file_paths: Liste von Audio-Dateipfaden
        min_total_duration: Minimale Gesamtdauer in Sekunden
        reduce_noise_enabled: enable noise reduction
        
    Returns:
        Liste von Pfaden zu verarbeiteten Dateien
    """
    processed_files = []
    total_duration = 0
    
    print(f"Verarbeite {len(file_paths)} Audio-Samples...")
    
    for file_path in file_paths:
        try:
            # Load audio and check duration
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
            
            print(f"    -> Verarbeitet: {processed_duration:.1f}s (Rauschen entfernt, getrimmt)")
            
        except Exception as e:
            print(f"  [X] Fehler bei {file_path}: {e}")
    
    print(f"\nGesamtdauer: {total_duration:.1f}s")
    
    # If total duration too short, join samples
    if total_duration < min_total_duration and len(processed_files) > 1:
        print(f"Joining samples for better quality...")
        combined_path = concatenate_audio_files(processed_files)
        
        combined_audio, sr = sf.read(combined_path)
        combined_duration = len(combined_audio) / sr
        print(f"Kombiniertes Sample: {combined_duration:.1f}s")
        
        # Combined sample first, individual ones as additional
        return [combined_path] + processed_files
    
    return processed_files


def get_audio_info(file_path):
    """
    Returns information about an audio file
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
