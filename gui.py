"""
FastSpeak GUI - Grafische Benutzeroberfläche für Text-to-Speech
"""
import os
# Füge espeak-ng zum PATH hinzu
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from main import TextToSpeech


class FastSpeakGUI:
    """Hauptfenster der Anwendung"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("FastSpeak - Text vorlesen")
        self.root.geometry("700x550")
        self.root.resizable(True, True)
        
        # TTS Engine initialisieren
        self.tts = TextToSpeech()
        self.current_thread = None
        self.speaker_wav_files = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        
        # Hauptcontainer
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguriere Grid-Gewichtung
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Titel
        title_label = ttk.Label(
            main_frame, 
            text="FastSpeak - Text-to-Speech", 
            font=("Helvetica", 16, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # Textfeld für Eingabe
        text_frame = ttk.LabelFrame(main_frame, text="Text eingeben", padding="5")
        text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.text_input = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=60,
            height=12,
            font=("Arial", 11)
        )
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.text_input.insert(1.0, "Geben Sie hier Ihren Text ein, der vorgelesen werden soll...")
        self.text_input.bind("<FocusIn>", self.clear_placeholder)
        
        # Einstellungen Frame
        settings_frame = ttk.LabelFrame(main_frame, text="Einstellungen", padding="5")
        settings_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Voice Cloning Frame
        voice_frame = ttk.LabelFrame(main_frame, text="Voice Cloning (Optional)", padding="5")
        voice_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(voice_frame, text="Audio-Samples:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.files_label = ttk.Label(voice_frame, text="Keine Dateien ausgewählt", foreground="gray")
        self.files_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        upload_button = ttk.Button(
            voice_frame,
            text="📁 Samples hochladen",
            command=self.upload_samples
        )
        upload_button.grid(row=0, column=2, padx=5)
        
        clear_button = ttk.Button(
            voice_frame,
            text="✕ Löschen",
            command=self.clear_samples,
            width=10
        )
        clear_button.grid(row=0, column=3, padx=5)
        
        # Geschwindigkeit
        ttk.Label(settings_frame, text="Geschwindigkeit:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.speed_var = tk.IntVar(value=150)
        speed_slider = ttk.Scale(
            settings_frame,
            from_=50,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.speed_var,
            length=200
        )
        speed_slider.grid(row=0, column=1, padx=5)
        self.speed_label = ttk.Label(settings_frame, text="150 WPM")
        self.speed_label.grid(row=0, column=2, padx=5)
        speed_slider.configure(command=self.update_speed_label)
        
        # Sprache
        ttk.Label(settings_frame, text="Sprache:").grid(row=0, column=3, sticky=tk.W, padx=(20, 5))
        self.language_var = tk.StringVar(value="de")
        language_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.language_var,
            values=["de", "en", "fr", "es"],
            state="readonly",
            width=10
        )
        language_combo.grid(row=0, column=4, padx=5)
        
        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=10)
        
        # Vorlesen Button
        self.speak_button = ttk.Button(
            button_frame,
            text="▶ Vorlesen",
            command=self.speak_text,
            width=15
        )
        self.speak_button.grid(row=0, column=0, padx=5)
        
        # Stop Button
        self.stop_button = ttk.Button(
            button_frame,
            text="⏹ Stop",
            command=self.stop_speaking,
            state=tk.DISABLED,
            width=15
        )
        self.stop_button.grid(row=0, column=1, padx=5)
        
        # Clear Button
        clear_button = ttk.Button(
            button_frame,
            text="🗑 Löschen",
            command=self.clear_text,
            width=15
        )
        clear_button.grid(row=0, column=2, padx=5)
        
        # Statusleiste
        self.status_var = tk.StringVar(value="Bereit")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def clear_placeholder(self, event):
        """Entfernt den Platzhalter-Text beim ersten Klick"""
        current_text = self.text_input.get(1.0, tk.END).strip()
        if current_text == "Geben Sie hier Ihren Text ein, der vorgelesen werden soll...":
            self.text_input.delete(1.0, tk.END)
    
    def upload_samples(self):
        """Lädt Audio-Samples für Voice Cloning hoch"""
        files = filedialog.askopenfilenames(
            title="Audio-Samples auswählen",
            filetypes=[
                ("Audio-Dateien", "*.wav *.mp3 *.flac *.ogg"),
                ("WAV-Dateien", "*.wav"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if files:
            self.speaker_wav_files = list(files)
            self.tts.set_speaker_wav(self.speaker_wav_files)
            file_count = len(self.speaker_wav_files)
            self.files_label.config(
                text=f"{file_count} Datei(en) ausgewählt",
                foreground="green"
            )
            self.status_var.set(f"Voice Cloning aktiviert ({file_count} Sample(s))")
    
    def clear_samples(self):
        """Entfernt die Voice Cloning Samples"""
        self.speaker_wav_files = []
        self.tts.set_speaker_wav(None)
        self.files_label.config(
            text="Keine Dateien ausgewählt",
            foreground="gray"
        )
        self.status_var.set("Voice Cloning deaktiviert")
    
    def update_speed_label(self, value):
        """Aktualisiert das Geschwindigkeits-Label"""
        self.speed_label.config(text=f"{int(float(value))} WPM")
    
    def speak_text(self):
        """Liest den eingegebenen Text vor"""
        text = self.text_input.get(1.0, tk.END).strip()
        
        if not text or text == "Geben Sie hier Ihren Text ein, der vorgelesen werden soll...":
            messagebox.showwarning("Kein Text", "Bitte geben Sie einen Text ein!")
            return
        
        # UI während des Sprechens aktualisieren
        self.speak_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set(f"Spreche Text ({len(text)} Zeichen)...")
        
        # Text asynchron vorlesen
        def speak_and_update():
            self.tts.speak(text, self.speed_var.get(), self.language_var.get())
            self.root.after(0, self.speaking_finished)
        
        import threading
        self.current_thread = threading.Thread(target=speak_and_update)
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def speaking_finished(self):
        """Wird aufgerufen, wenn das Sprechen beendet ist"""
        self.speak_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("Bereit")
    
    def stop_speaking(self):
        """Stoppt das Vorlesen"""
        self.tts.stop()
        self.speaking_finished()
        self.status_var.set("Gestoppt")
    
    def clear_text(self):
        """Löscht den Text im Eingabefeld"""
        self.text_input.delete(1.0, tk.END)
        self.status_var.set("Text gelöscht")


def main():
    """Startet die GUI-Anwendung"""
    root = tk.Tk()
    app = FastSpeakGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
