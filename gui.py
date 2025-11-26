"""
FastSpeak GUI - Grafische Benutzeroberfläche für Text-to-Speech
"""
import os
# Füge espeak-ng zum PATH hinzu
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from main import TextToSpeech
from audio_processor import prepare_samples_for_cloning, get_audio_info


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
        self.last_audio_path = None  # Pfad zur letzten generierten Audio-Datei
        
        self.setup_ui()
        
        # Versuche zuletzt genutztes Voice-Modell zu laden
        self.load_last_model_on_startup()
        
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
        
        ttk.Label(voice_frame, text="(Kurze Samples werden automatisch zusammengefügt, Rauschen wird entfernt)", 
                  foreground="blue", font=("Arial", 8)).grid(row=1, column=0, columnspan=5, sticky=tk.W, padx=5, pady=(0, 5))
        
        self.files_label = ttk.Label(voice_frame, text="Keine Dateien ausgewählt", foreground="gray")
        self.files_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Embedding-Status Label
        self.embedding_label = ttk.Label(voice_frame, text="", foreground="gray", font=("Arial", 8))
        self.embedding_label.grid(row=2, column=0, columnspan=5, sticky=tk.W, padx=5)
        
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
        
        # Checkbox für Rauschunterdrückung
        self.denoise_var = tk.BooleanVar(value=True)
        denoise_check = ttk.Checkbutton(
            voice_frame,
            text="🔇 Rauschen entfernen",
            variable=self.denoise_var
        )
        denoise_check.grid(row=0, column=4, padx=5)
        
        # Voice-Modell speichern/laden Buttons
        save_model_button = ttk.Button(
            voice_frame,
            text="💾 Stimme speichern",
            command=self.save_voice_model,
            width=18
        )
        save_model_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        load_model_button = ttk.Button(
            voice_frame,
            text="📂 Stimme laden",
            command=self.load_voice_model,
            width=18
        )
        load_model_button.grid(row=3, column=2, padx=5, pady=5)
        
        # Label für geladenes Modell
        self.model_name_label = ttk.Label(voice_frame, text="", foreground="blue", font=("Arial", 9, "bold"))
        self.model_name_label.grid(row=3, column=3, columnspan=2, sticky=tk.W, padx=5)
        
        # Qualitätseinstellungen Frame
        quality_frame = ttk.LabelFrame(main_frame, text="Qualitätseinstellungen", padding="5")
        quality_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Temperature (Kreativität)
        ttk.Label(quality_frame, text="Kreativität:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.temp_var = tk.DoubleVar(value=0.3)
        temp_slider = ttk.Scale(
            quality_frame,
            from_=0.1,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.temp_var,
            length=120
        )
        temp_slider.grid(row=0, column=1, padx=5)
        self.temp_label = ttk.Label(quality_frame, text="0.30", width=5)
        self.temp_label.grid(row=0, column=2, padx=2)
        temp_slider.configure(command=lambda v: self.update_quality_labels())
        
        # Speed (Geschwindigkeit)
        ttk.Label(quality_frame, text="Tempo:").grid(row=0, column=3, sticky=tk.W, padx=(15, 5))
        self.tts_speed_var = tk.DoubleVar(value=1.0)
        speed_tts_slider = ttk.Scale(
            quality_frame,
            from_=0.5,
            to=1.5,
            orient=tk.HORIZONTAL,
            variable=self.tts_speed_var,
            length=120
        )
        speed_tts_slider.grid(row=0, column=4, padx=5)
        self.tts_speed_label = ttk.Label(quality_frame, text="1.00x", width=5)
        self.tts_speed_label.grid(row=0, column=5, padx=2)
        speed_tts_slider.configure(command=lambda v: self.update_quality_labels())
        
        # Repetition Penalty
        ttk.Label(quality_frame, text="Anti-Stottern:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.rep_var = tk.DoubleVar(value=5.0)
        rep_slider = ttk.Scale(
            quality_frame,
            from_=1.0,
            to=10.0,
            orient=tk.HORIZONTAL,
            variable=self.rep_var,
            length=120
        )
        rep_slider.grid(row=1, column=1, padx=5)
        self.rep_label = ttk.Label(quality_frame, text="5.0", width=5)
        self.rep_label.grid(row=1, column=2, padx=2)
        rep_slider.configure(command=lambda v: self.update_quality_labels())
        
        # Preset-Buttons
        ttk.Button(
            quality_frame, text="📖 Klar", width=8,
            command=lambda: self.apply_preset('clear')
        ).grid(row=1, column=3, padx=5)
        
        ttk.Button(
            quality_frame, text="🎭 Natürlich", width=9,
            command=lambda: self.apply_preset('natural')
        ).grid(row=1, column=4, padx=5)
        
        ttk.Button(
            quality_frame, text="🎨 Kreativ", width=8,
            command=lambda: self.apply_preset('creative')
        ).grid(row=1, column=5, padx=5)
        
        # Streaming-Modus Checkbox (Zeile 2)
        self.streaming_var = tk.BooleanVar(value=False)
        streaming_check = ttk.Checkbutton(
            quality_frame,
            text="⚡ Streaming (schneller)",
            variable=self.streaming_var,
            command=self.update_streaming_mode
        )
        streaming_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Info-Label für Performance
        self.perf_label = ttk.Label(
            quality_frame, 
            text="💡 Tipp: Streaming für schnellere erste Ausgabe",
            foreground="gray",
            font=("Arial", 8)
        )
        self.perf_label.grid(row=2, column=2, columnspan=4, sticky=tk.W, padx=5)
        
        # Geschwindigkeit (für pyttsx3 Fallback)
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
        
        # Konsistente Betonung Checkbox
        self.consistent_var = tk.BooleanVar(value=True)
        consistent_check = ttk.Checkbutton(
            settings_frame,
            text="Konsistente Betonung",
            variable=self.consistent_var,
            command=self.toggle_consistency
        )
        consistent_check.grid(row=0, column=5, padx=(20, 5))
        
        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, pady=10)
        
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
        
        # Download Button
        self.download_button = ttk.Button(
            button_frame,
            text="💾 Als MP3 speichern",
            command=self.download_audio,
            state=tk.DISABLED,
            width=18
        )
        self.download_button.grid(row=0, column=3, padx=5)
        
        # Statusleiste
        self.status_var = tk.StringVar(value="Bereit")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def update_quality_labels(self):
        """Aktualisiert die Qualitäts-Labels und überträgt Werte an TTS"""
        temp = self.temp_var.get()
        speed = self.tts_speed_var.get()
        rep = self.rep_var.get()
        
        self.temp_label.config(text=f"{temp:.2f}")
        self.tts_speed_label.config(text=f"{speed:.2f}x")
        self.rep_label.config(text=f"{rep:.1f}")
        
        # Werte an TTS-Engine übertragen
        self.tts.temperature = temp
        self.tts.speed = speed
        self.tts.repetition_penalty = rep
    
    def update_streaming_mode(self):
        """Aktiviert/deaktiviert den Streaming-Modus"""
        self.tts.use_streaming = self.streaming_var.get()
        mode = "aktiviert" if self.tts.use_streaming else "deaktiviert"
        self.status_var.set(f"⚡ Streaming-Modus {mode}")
    
    def apply_preset(self, preset_name):
        """Wendet ein Qualitäts-Preset an"""
        presets = {
            'clear': {'temp': 0.2, 'speed': 1.0, 'rep': 7.0},    # Sehr klar, wenig Variation
            'natural': {'temp': 0.4, 'speed': 1.0, 'rep': 5.0},  # Ausgewogen, natürlich
            'creative': {'temp': 0.7, 'speed': 1.0, 'rep': 3.0}  # Mehr Variation, expressiv
        }
        
        if preset_name in presets:
            p = presets[preset_name]
            self.temp_var.set(p['temp'])
            self.tts_speed_var.set(p['speed'])
            self.rep_var.set(p['rep'])
            self.update_quality_labels()
            self.status_var.set(f"Preset '{preset_name}' angewendet")
        
    def load_last_model_on_startup(self):
        """Lädt beim Start automatisch das zuletzt genutzte Voice-Modell"""
        try:
            if self.tts.load_last_model():
                name = self.tts.current_voice_name
                self.model_name_label.config(text=f"📢 Geladen: {name}")
                self.embedding_label.config(
                    text=f"✓ Voice-Modell '{name}' automatisch geladen",
                    foreground="green"
                )
                self.files_label.config(
                    text=f"Gespeicherte Stimme aktiv",
                    foreground="blue"
                )
                self.status_var.set(f"Voice-Modell '{name}' automatisch geladen - bereit!")
        except Exception as e:
            print(f"Fehler beim automatischen Laden des Voice-Modells: {e}")
    
    def clear_placeholder(self, event):
        """Entfernt den Platzhalter-Text beim ersten Klick"""
        current_text = self.text_input.get(1.0, tk.END).strip()
        if current_text == "Geben Sie hier Ihren Text ein, der vorgelesen werden soll...":
            self.text_input.delete(1.0, tk.END)
    
    def upload_samples(self):
        """Lädt Audio-Samples für Voice Cloning hoch und verarbeitet sie"""
        files = filedialog.askopenfilenames(
            title="Audio-Samples auswählen",
            filetypes=[
                ("Audio-Dateien", "*.wav *.mp3 *.flac *.ogg"),
                ("WAV-Dateien", "*.wav"),
                ("Alle Dateien", "*.*")
            ]
        )
        
        if files:
            file_count = len(files)
            self.files_label.config(
                text=f"{file_count} Datei(en) werden verarbeitet...",
                foreground="orange"
            )
            self.status_var.set("Verarbeite Audio-Samples (Rauschen entfernen, trimmen)...")
            self.root.update()
            
            # Audio-Samples vorverarbeiten (Rauschen entfernen, trimmen, zusammenfügen)
            try:
                processed_files = prepare_samples_for_cloning(
                    list(files),
                    min_total_duration=10,
                    reduce_noise_enabled=self.denoise_var.get()
                )
                
                self.speaker_wav_files = processed_files
                
                # Berechne Gesamtdauer
                total_duration = 0
                for f in processed_files:
                    info = get_audio_info(f)
                    if 'duration' in info:
                        total_duration += info['duration']
                
                self.files_label.config(
                    text=f"{file_count} → {len(processed_files)} Sample(s), {total_duration:.1f}s",
                    foreground="green"
                )
                
                self.status_var.set("Berechne Speaker-Embeddings...")
                self.root.update()
                
                # Setze Samples und berechne Embeddings
                self.tts.set_speaker_wav(self.speaker_wav_files)
                
                # Zeige Embedding-Status
                if hasattr(self.tts, 'gpt_cond_latent') and self.tts.gpt_cond_latent is not None:
                    self.embedding_label.config(
                        text="✓ Samples verarbeitet & Speaker-Embeddings berechnet",
                        foreground="green"
                    )
                    self.status_var.set(f"Voice Cloning bereit ({total_duration:.1f}s Audio, optimiert)")
                else:
                    self.embedding_label.config(
                        text="✓ Samples verarbeitet (Rauschen entfernt, getrimmt)",
                        foreground="green"
                    )
                    self.status_var.set(f"Voice Cloning aktiviert ({total_duration:.1f}s Audio)")
                    
            except Exception as e:
                self.files_label.config(
                    text=f"Fehler bei Verarbeitung",
                    foreground="red"
                )
                self.embedding_label.config(
                    text=f"Fehler: {str(e)[:50]}",
                    foreground="red"
                )
                self.status_var.set("Fehler bei Audio-Verarbeitung")
                print(f"Fehler bei Audio-Verarbeitung: {e}")
                import traceback
                traceback.print_exc()
    
    def clear_samples(self):
        """Entfernt die Voice Cloning Samples"""
        self.speaker_wav_files = []
        self.tts.set_speaker_wav(None)
        self.files_label.config(
            text="Keine Dateien ausgewählt",
            foreground="gray"
        )
        self.embedding_label.config(text="", foreground="gray")
        self.status_var.set("Voice Cloning deaktiviert")
    
    def update_speed_label(self, value):
        """Aktualisiert das Geschwindigkeits-Label"""
        self.speed_label.config(text=f"{int(float(value))} WPM")
    
    def toggle_consistency(self):
        """Schaltet konsistente Betonung um"""
        if self.consistent_var.get():
            # Fester Seed für konsistente Ausgabe
            self.tts.seed = 42
            self.status_var.set("Konsistente Betonung aktiviert")
        else:
            # Zufälliger Seed für variierende Betonung
            import random
            self.tts.seed = random.randint(0, 999999)
            self.status_var.set("Variierende Betonung aktiviert")
    
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
        
        # Text asynchron vorlesen und Audio speichern
        def speak_and_update():
            # Generiere Audio und speichere Pfad
            audio_path = self.tts.speak_and_save(text, self.speed_var.get(), self.language_var.get())
            if audio_path:
                self.last_audio_path = audio_path
            self.root.after(0, self.speaking_finished)
        
        import threading
        self.current_thread = threading.Thread(target=speak_and_update)
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def speaking_finished(self):
        """Wird aufgerufen, wenn das Sprechen beendet ist"""
        self.speak_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        # Download-Button aktivieren wenn Audio vorhanden
        if self.last_audio_path and os.path.exists(self.last_audio_path):
            self.download_button.config(state=tk.NORMAL)
        self.status_var.set("Bereit - Audio kann gespeichert werden")
    
    def stop_speaking(self):
        """Stoppt das Vorlesen"""
        self.tts.stop()
        self.speaking_finished()
        self.status_var.set("Gestoppt")
    
    def clear_text(self):
        """Löscht den Text im Eingabefeld"""
        self.text_input.delete(1.0, tk.END)
        self.status_var.set("Text gelöscht")
    
    def save_voice_model(self):
        """Speichert das aktuelle Voice-Modell"""
        # Prüfe ob Embeddings vorhanden sind
        if not hasattr(self.tts, 'gpt_cond_latent') or self.tts.gpt_cond_latent is None:
            messagebox.showwarning(
                "Keine Stimme", 
                "Bitte laden Sie zuerst Audio-Samples hoch, um eine Stimme zu erstellen!"
            )
            return
        
        # Name für das Modell abfragen
        from tkinter import simpledialog
        name = simpledialog.askstring(
            "Stimme speichern",
            "Geben Sie einen Namen für die Stimme ein:",
            initialvalue=self.tts.current_voice_name or "meine_stimme"
        )
        
        if name:
            result = self.tts.save_voice_model(name)
            if result:
                self.model_name_label.config(text=f"✓ Gespeichert: {name}")
                self.status_var.set(f"Voice-Modell '{name}' gespeichert")
                messagebox.showinfo(
                    "Erfolg", 
                    f"Voice-Modell '{name}' wurde gespeichert!\n\n"
                    f"Es wird beim nächsten Start automatisch verfügbar sein."
                )
            else:
                messagebox.showerror("Fehler", "Konnte Voice-Modell nicht speichern!")
    
    def load_voice_model(self):
        """Lädt ein gespeichertes Voice-Modell"""
        # Liste der verfügbaren Modelle abrufen
        models = self.tts.list_saved_voice_models()
        
        if not models:
            messagebox.showinfo(
                "Keine Modelle",
                "Es sind noch keine gespeicherten Stimmen vorhanden.\n\n"
                "Laden Sie zuerst Audio-Samples hoch und speichern Sie die Stimme."
            )
            return
        
        # Auswahldialog erstellen
        select_window = tk.Toplevel(self.root)
        select_window.title("Stimme laden")
        select_window.geometry("400x300")
        select_window.transient(self.root)
        select_window.grab_set()
        
        ttk.Label(
            select_window, 
            text="Wählen Sie eine gespeicherte Stimme:",
            font=("Arial", 10, "bold")
        ).pack(pady=10)
        
        # Listbox mit Modellen
        listbox = tk.Listbox(select_window, font=("Arial", 11), height=10)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)
        
        for model in models:
            listbox.insert(tk.END, model['name'])
        
        if models:
            listbox.selection_set(0)
        
        def on_load():
            selection = listbox.curselection()
            if selection:
                model_name = models[selection[0]]['name']
                select_window.destroy()
                
                self.status_var.set(f"Lade Voice-Modell '{model_name}'...")
                self.root.update()
                
                if self.tts.load_voice_model(model_name):
                    self.model_name_label.config(text=f"📢 Geladen: {model_name}")
                    self.embedding_label.config(
                        text=f"✓ Voice-Modell '{model_name}' geladen (bereit zum Vorlesen)",
                        foreground="green"
                    )
                    self.files_label.config(
                        text=f"Gespeicherte Stimme aktiv",
                        foreground="blue"
                    )
                    self.status_var.set(f"Voice-Modell '{model_name}' geladen und bereit!")
                else:
                    messagebox.showerror("Fehler", f"Konnte Voice-Modell '{model_name}' nicht laden!")
                    self.status_var.set("Fehler beim Laden")
        
        def on_delete():
            selection = listbox.curselection()
            if selection:
                model_name = models[selection[0]]['name']
                if messagebox.askyesno("Löschen bestätigen", f"Voice-Modell '{model_name}' wirklich löschen?"):
                    if self.tts.delete_voice_model(model_name):
                        listbox.delete(selection[0])
                        models.pop(selection[0])
                        self.status_var.set(f"Voice-Modell '{model_name}' gelöscht")
        
        button_frame = ttk.Frame(select_window)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="✓ Laden", command=on_load, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑 Löschen", command=on_delete, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Abbrechen", command=select_window.destroy, width=12).pack(side=tk.LEFT, padx=5)
    
    def download_audio(self):
        """Speichert die letzte Sprachausgabe als MP3"""
        if not self.last_audio_path or not os.path.exists(self.last_audio_path):
            messagebox.showwarning("Keine Audio", "Bitte erst einen Text vorlesen lassen!")
            return
        
        # Speicherdialog öffnen
        save_path = filedialog.asksaveasfilename(
            title="Audio speichern als",
            defaultextension=".mp3",
            filetypes=[
                ("MP3-Dateien", "*.mp3"),
                ("WAV-Dateien", "*.wav"),
                ("Alle Dateien", "*.*")
            ],
            initialfile="sprachausgabe.mp3"
        )
        
        if save_path:
            try:
                self.status_var.set("Speichere Audio...")
                self.root.update()
                
                if save_path.lower().endswith('.mp3'):
                    # Konvertiere WAV zu MP3 mit lameenc (kein ffmpeg nötig)
                    self._convert_wav_to_mp3(self.last_audio_path, save_path)
                else:
                    # WAV direkt kopieren
                    import shutil
                    shutil.copy2(self.last_audio_path, save_path)
                
                self.status_var.set(f"Audio gespeichert: {os.path.basename(save_path)}")
                messagebox.showinfo("Erfolg", f"Audio wurde gespeichert:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern:\n{str(e)}")
                self.status_var.set("Fehler beim Speichern")
    
    def _convert_wav_to_mp3(self, wav_path, mp3_path):
        """Konvertiert WAV zu MP3 mit lameenc (ohne ffmpeg)"""
        import soundfile as sf
        import lameenc
        
        # WAV-Datei lesen
        data, samplerate = sf.read(wav_path)
        
        # Falls Stereo, zu Mono konvertieren oder richtig handhaben
        import numpy as np
        if len(data.shape) == 1:
            # Mono
            channels = 1
            samples = data
        else:
            # Stereo
            channels = data.shape[1]
            samples = data
        
        # Zu 16-bit Integer konvertieren
        samples_int16 = (samples * 32767).astype(np.int16)
        
        # MP3 Encoder initialisieren
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(192)
        encoder.set_in_sample_rate(samplerate)
        encoder.set_channels(channels)
        encoder.set_quality(2)  # 2 = hohe Qualität
        
        # Enkodieren
        mp3_data = encoder.encode(samples_int16.tobytes())
        mp3_data += encoder.flush()
        
        # MP3 speichern
        with open(mp3_path, 'wb') as f:
            f.write(mp3_data)


def main():
    """Startet die GUI-Anwendung"""
    root = tk.Tk()
    app = FastSpeakGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
