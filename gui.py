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
    """Hauptfenster der Anwendung - optimiert für Eye-Tracking
    
    Design-Prinzipien (learnui.design):
    1. Light comes from the sky - subtile Schatten
    2. Black and white first - neutrale Farben, Akzentfarbe sparsam
    3. Double your whitespace - großzügige Abstände
    4. Good fonts - klare, lesbare Schrift
    5. Make text pop/un-pop - visuelle Hierarchie
    """
    
    # Design-Konstanten
    BUTTON_WIDTH = 18
    BUTTON_HEIGHT = 2
    
    # Farben - minimalistisch mit einer Akzentfarbe
    COLOR_BG = "#f5f5f5"           # Heller Hintergrund
    COLOR_PRIMARY = "#2563eb"       # Blau als Akzent
    COLOR_PRIMARY_HOVER = "#1d4ed8" # Dunkleres Blau
    COLOR_SUCCESS = "#16a34a"       # Grün für Vorlesen
    COLOR_DANGER = "#dc2626"        # Rot für Stop
    COLOR_TEXT = "#1f2937"          # Fast-Schwarz für Text
    COLOR_TEXT_MUTED = "#6b7280"    # Grau für sekundären Text
    COLOR_BORDER = "#e5e7eb"        # Subtile Rahmen
    
    # Fonts - konsistent
    FONT_FAMILY = "Segoe UI"        # Moderner als Arial
    FONT_LARGE = ("Segoe UI", 14, "bold")
    FONT_MEDIUM = ("Segoe UI", 12)
    FONT_BUTTON = ("Segoe UI", 13, "bold")
    FONT_SMALL = ("Segoe UI", 11)
    FONT_TINY = ("Segoe UI", 10)
    
    # Spacing - großzügig (Rule 3: Double your whitespace)
    PADDING_LARGE = 20
    PADDING_MEDIUM = 15
    PADDING_SMALL = 10
    PADDING_TINY = 5
    
    def __init__(self, root):
        self.root = root
        self.root.title("FastSpeak")
        self.root.geometry("750x520")  # Kompaktes Fenster
        self.root.minsize(650, 480)    # Mindestgröße
        self.root.resizable(True, True)
        self.root.configure(bg=self.COLOR_BG)
        
        # TTS Engine initialisieren
        self.tts = TextToSpeech()
        self.current_thread = None
        self.speaker_wav_files = []
        self.last_audio_path = None  # Pfad zur letzten generierten Audio-Datei
        
        # Style für Elemente
        self.setup_styles()
        self.setup_ui()
        
        # Versuche zuletzt genutztes Voice-Modell zu laden
        self.load_last_model_on_startup()
    
    def setup_styles(self):
        """Konfiguriert ttk Styles - minimalistisch und konsistent"""
        style = ttk.Style()
        style.theme_use('clam')  # Modernes Theme als Basis
        
        # Haupt-Frame Hintergrund
        style.configure("TFrame", background=self.COLOR_BG)
        
        # Preset-Buttons - neutral mit subtilen Effekten
        style.configure("Preset.TButton", 
                       font=self.FONT_BUTTON, 
                       padding=(20, 12),
                       background="#ffffff",
                       foreground=self.COLOR_TEXT)
        
        # Sekundäre Buttons
        style.configure("Secondary.TButton", 
                       font=self.FONT_MEDIUM, 
                       padding=(15, 10))
        
        # Labels - verschiedene Hierarchien
        style.configure("TLabel", 
                       font=self.FONT_SMALL,
                       background=self.COLOR_BG,
                       foreground=self.COLOR_TEXT)
        
        style.configure("Heading.TLabel", 
                       font=self.FONT_LARGE,
                       background=self.COLOR_BG,
                       foreground=self.COLOR_TEXT)
        
        style.configure("Muted.TLabel", 
                       font=self.FONT_SMALL,
                       background=self.COLOR_BG,
                       foreground=self.COLOR_TEXT_MUTED)
        
        style.configure("Accent.TLabel", 
                       font=self.FONT_MEDIUM,
                       background=self.COLOR_BG,
                       foreground=self.COLOR_PRIMARY)
        
        # LabelFrames
        style.configure("Card.TLabelframe", 
                       font=self.FONT_MEDIUM,
                       background=self.COLOR_BG,
                       padding=self.PADDING_MEDIUM)
        style.configure("Card.TLabelframe.Label", 
                       font=(self.FONT_FAMILY, 11),
                       foreground=self.COLOR_TEXT_MUTED,
                       background=self.COLOR_BG)
        
        # Checkbuttons
        style.configure("TCheckbutton", 
                       font=self.FONT_SMALL,
                       background=self.COLOR_BG)
        
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche - clean und minimalistisch"""
        
        # Hauptcontainer mit großzügigem Padding (Rule 3)
        main_frame = ttk.Frame(self.root, padding=self.PADDING_LARGE)
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Konfiguriere Grid-Gewichtung
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)  # Textfeld bekommt den Platz
        
        # ===== TEXTFELD - Hauptelement mit subtiler Karte =====
        text_frame = ttk.LabelFrame(main_frame, text="Text eingeben", 
                                    padding=self.PADDING_MEDIUM, style="Card.TLabelframe")
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), 
                        pady=(0, self.PADDING_MEDIUM))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        # Textfeld mit weißem Hintergrund und subtiler Border
        self.text_input = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=60,
            height=7,
            font=(self.FONT_FAMILY, 13),
            bg="#ffffff",
            fg=self.COLOR_TEXT,
            insertbackground=self.COLOR_PRIMARY,  # Cursor-Farbe
            relief=tk.FLAT,
            borderwidth=0,
            padx=12,
            pady=10
        )
        self.text_input.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.text_input.insert(1.0, "Text hier eingeben...")
        self.text_input.config(fg=self.COLOR_TEXT_MUTED)  # Placeholder grau
        self.text_input.bind("<FocusIn>", self.clear_placeholder)
        
        # ===== HAUPTBUTTONS - mit großzügigem Spacing =====
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=1, column=0, pady=self.PADDING_SMALL)
        
        # Vorlesen Button - Primäre Aktion (Akzentfarbe)
        self.speak_button = tk.Button(
            button_frame,
            text="▶  Vorlesen",
            command=self.speak_text,
            font=self.FONT_BUTTON,
            bg=self.COLOR_SUCCESS,
            fg="white",
            activebackground="#15803d",
            activeforeground="white",
            width=16,
            height=2,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.speak_button.grid(row=0, column=0, padx=self.PADDING_SMALL, pady=self.PADDING_TINY)
        
        # Stop Button - Destruktive Aktion
        self.stop_button = tk.Button(
            button_frame,
            text="⏹  Stop",
            command=self.stop_speaking,
            state=tk.DISABLED,
            font=self.FONT_BUTTON,
            bg=self.COLOR_DANGER,
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            disabledforeground="#9ca3af",
            width=16,
            height=2,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.stop_button.grid(row=0, column=1, padx=self.PADDING_SMALL, pady=self.PADDING_TINY)
        
        # Sekundäre Buttons - weniger prominent (neutral)
        secondary_frame = ttk.Frame(button_frame)
        secondary_frame.grid(row=0, column=2, padx=(self.PADDING_LARGE, 0))
        
        self.clear_button = tk.Button(
            secondary_frame,
            text="Text löschen",
            command=self.clear_text,
            font=self.FONT_SMALL,
            bg="#e5e7eb",
            fg=self.COLOR_TEXT,
            activebackground="#d1d5db",
            width=14,
            height=1,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.clear_button.grid(row=0, column=0, pady=2)
        
        self.download_button = tk.Button(
            secondary_frame,
            text="Als MP3 speichern",
            command=self.download_audio,
            state=tk.DISABLED,
            font=self.FONT_SMALL,
            bg="#e5e7eb",
            fg=self.COLOR_TEXT,
            activebackground="#d1d5db",
            disabledforeground="#9ca3af",
            width=14,
            height=1,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.download_button.grid(row=1, column=0, pady=2)
        
        # ===== OPTIONEN - horizontale Leiste mit mehr Whitespace =====
        options_frame = ttk.Frame(main_frame)
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(self.PADDING_MEDIUM, self.PADDING_SMALL))
        
        # Stimme
        voice_section = ttk.Frame(options_frame)
        voice_section.grid(row=0, column=0, padx=(0, self.PADDING_LARGE))
        
        ttk.Label(voice_section, text="Stimme", 
                  style="Muted.TLabel").grid(row=0, column=0, sticky=tk.W)
        
        self.model_name_label = ttk.Label(voice_section, text="Standard", 
                                          style="Accent.TLabel")
        self.model_name_label.grid(row=0, column=1, sticky=tk.W, padx=(self.PADDING_SMALL, 0))
        
        self.voice_menu_button = tk.Button(
            voice_section,
            text="Ändern",
            command=self.open_voice_cloning_menu,
            font=self.FONT_TINY,
            bg="#ffffff",
            fg=self.COLOR_PRIMARY,
            activebackground="#eff6ff",
            width=8,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.voice_menu_button.grid(row=0, column=2, padx=self.PADDING_SMALL)
        
        # Trennlinie (visuell)
        ttk.Label(options_frame, text="│", style="Muted.TLabel").grid(row=0, column=1)
        
        # Interne Labels für Voice Cloning Status (werden im Menü genutzt)
        self.files_label = None
        self.embedding_label = None
        self.denoise_var = tk.BooleanVar(value=True)
        
        # ===== QUALITÄT - inline neben Stimme =====
        quality_section = ttk.Frame(options_frame)
        quality_section.grid(row=0, column=2, padx=(self.PADDING_LARGE, 0))
        
        ttk.Label(quality_section, text="Qualität", 
                  style="Muted.TLabel").grid(row=0, column=0, sticky=tk.W)
        
        self.current_preset_label = ttk.Label(quality_section, text="Klar", 
                                              style="Accent.TLabel")
        self.current_preset_label.grid(row=0, column=1, sticky=tk.W, padx=(self.PADDING_SMALL, 0))
        
        # Preset-Buttons in einer Zeile - kompakt
        preset_frame = ttk.Frame(quality_section)
        preset_frame.grid(row=0, column=2, padx=self.PADDING_SMALL)
        
        # Kompakte Preset-Buttons
        for i, (key, label) in enumerate([('clear', 'Klar'), ('natural', 'Natürlich'), ('creative', 'Kreativ')]):
            btn = tk.Button(
                preset_frame,
                text=label,
                command=lambda k=key: self.apply_preset(k),
                font=self.FONT_TINY,
                bg="#ffffff",
                fg=self.COLOR_TEXT,
                activebackground="#f3f4f6",
                width=8,
                cursor="hand2",
                relief=tk.FLAT,
                bd=0
            )
            btn.grid(row=0, column=i, padx=2)
        
        # Erweitert Button - sehr subtil
        self.quality_menu_button = tk.Button(
            quality_section,
            text="⚙",
            command=self.open_quality_menu,
            font=self.FONT_SMALL,
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT_MUTED,
            activebackground="#e5e7eb",
            width=3,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.quality_menu_button.grid(row=0, column=3, padx=self.PADDING_TINY)
        
        # Interne Variablen für Qualität (werden im Menü genutzt)
        self.temp_var = tk.DoubleVar(value=0.2)
        self.tts_speed_var = tk.DoubleVar(value=1.0)
        self.rep_var = tk.DoubleVar(value=7.0)
        self.streaming_var = tk.BooleanVar(value=False)
        self.consistent_var = tk.BooleanVar(value=True)
        self.speed_var = tk.IntVar(value=150)
        self.language_var = tk.StringVar(value="de")
        
        # Initiale Werte an TTS übertragen
        self.update_quality_values()
        
        # Statusleiste - subtil am unteren Rand
        self.status_var = tk.StringVar(value="Bereit")
        status_bar = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            style="Muted.TLabel",
            anchor=tk.W
        )
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(self.PADDING_MEDIUM, 0))
    
    def update_quality_values(self):
        """Überträgt Qualitätswerte an TTS-Engine"""
        self.tts.temperature = self.temp_var.get()
        self.tts.speed = self.tts_speed_var.get()
        self.tts.repetition_penalty = self.rep_var.get()
        self.tts.use_streaming = self.streaming_var.get()
    
    def open_quality_menu(self):
        """Öffnet das erweiterte Qualitäts-Menü"""
        menu_window = tk.Toplevel(self.root)
        menu_window.title("Erweiterte Qualitätseinstellungen")
        menu_window.geometry("550x450")
        menu_window.transient(self.root)
        menu_window.grab_set()
        
        # Hauptcontainer
        main_frame = ttk.Frame(menu_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titel
        ttk.Label(main_frame, text="Feineinstellungen", 
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # === Slider Frame ===
        slider_frame = ttk.LabelFrame(main_frame, text="Sprachqualität", padding="15")
        slider_frame.pack(fill=tk.X, pady=10)
        
        # Temperature / Kreativität
        temp_row = ttk.Frame(slider_frame)
        temp_row.pack(fill=tk.X, pady=8)
        ttk.Label(temp_row, text="Kreativität:", font=("Arial", 11), width=15).pack(side=tk.LEFT)
        temp_slider = ttk.Scale(temp_row, from_=0.1, to=1.0, orient=tk.HORIZONTAL, 
                               variable=self.temp_var, length=200)
        temp_slider.pack(side=tk.LEFT, padx=10)
        self.menu_temp_label = ttk.Label(temp_row, text=f"{self.temp_var.get():.2f}", 
                                         font=("Arial", 11), width=6)
        self.menu_temp_label.pack(side=tk.LEFT)
        temp_slider.configure(command=lambda v: self._update_menu_labels())
        
        # Tempo
        speed_row = ttk.Frame(slider_frame)
        speed_row.pack(fill=tk.X, pady=8)
        ttk.Label(speed_row, text="Tempo:", font=("Arial", 11), width=15).pack(side=tk.LEFT)
        speed_slider = ttk.Scale(speed_row, from_=0.5, to=1.5, orient=tk.HORIZONTAL, 
                                variable=self.tts_speed_var, length=200)
        speed_slider.pack(side=tk.LEFT, padx=10)
        self.menu_speed_label = ttk.Label(speed_row, text=f"{self.tts_speed_var.get():.2f}x", 
                                          font=("Arial", 11), width=6)
        self.menu_speed_label.pack(side=tk.LEFT)
        speed_slider.configure(command=lambda v: self._update_menu_labels())
        
        # Anti-Stottern
        rep_row = ttk.Frame(slider_frame)
        rep_row.pack(fill=tk.X, pady=8)
        ttk.Label(rep_row, text="Anti-Stottern:", font=("Arial", 11), width=15).pack(side=tk.LEFT)
        rep_slider = ttk.Scale(rep_row, from_=1.0, to=10.0, orient=tk.HORIZONTAL, 
                              variable=self.rep_var, length=200)
        rep_slider.pack(side=tk.LEFT, padx=10)
        self.menu_rep_label = ttk.Label(rep_row, text=f"{self.rep_var.get():.1f}", 
                                        font=("Arial", 11), width=6)
        self.menu_rep_label.pack(side=tk.LEFT)
        rep_slider.configure(command=lambda v: self._update_menu_labels())
        
        # === Optionen ===
        options_frame = ttk.LabelFrame(main_frame, text="Optionen", padding="15")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Streaming
        ttk.Checkbutton(
            options_frame,
            text="⚡ Streaming-Modus (schnellere Ausgabe)",
            variable=self.streaming_var,
            style="Big.TCheckbutton"
        ).pack(anchor=tk.W, pady=5)
        
        # Konsistente Betonung
        ttk.Checkbutton(
            options_frame,
            text="🎯 Konsistente Betonung (gleicher Seed)",
            variable=self.consistent_var,
            command=self.toggle_consistency,
            style="Big.TCheckbutton"
        ).pack(anchor=tk.W, pady=5)
        
        # === Fallback Einstellungen ===
        fallback_frame = ttk.LabelFrame(main_frame, text="Fallback (pyttsx3)", padding="15")
        fallback_frame.pack(fill=tk.X, pady=10)
        
        fb_row = ttk.Frame(fallback_frame)
        fb_row.pack(fill=tk.X, pady=5)
        
        ttk.Label(fb_row, text="Geschwindigkeit:", font=("Arial", 11)).pack(side=tk.LEFT)
        fb_speed_slider = ttk.Scale(fb_row, from_=50, to=300, orient=tk.HORIZONTAL, 
                                   variable=self.speed_var, length=150)
        fb_speed_slider.pack(side=tk.LEFT, padx=10)
        self.menu_fb_speed_label = ttk.Label(fb_row, text=f"{self.speed_var.get()} WPM", 
                                             font=("Arial", 11))
        self.menu_fb_speed_label.pack(side=tk.LEFT)
        fb_speed_slider.configure(command=lambda v: self._update_menu_labels())
        
        ttk.Label(fb_row, text="Sprache:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(20, 5))
        language_combo = ttk.Combobox(fb_row, textvariable=self.language_var,
                                      values=["de", "en", "fr", "es"],
                                      state="readonly", width=6, font=("Arial", 11))
        language_combo.pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="✓  Übernehmen",
            command=lambda: self._apply_quality_settings(menu_window),
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=15,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="Schließen",
            command=menu_window.destroy,
            font=("Arial", 12),
            width=15,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
    
    def _update_menu_labels(self):
        """Aktualisiert die Labels im Qualitäts-Menü"""
        if hasattr(self, 'menu_temp_label'):
            self.menu_temp_label.config(text=f"{self.temp_var.get():.2f}")
        if hasattr(self, 'menu_speed_label'):
            self.menu_speed_label.config(text=f"{self.tts_speed_var.get():.2f}x")
        if hasattr(self, 'menu_rep_label'):
            self.menu_rep_label.config(text=f"{self.rep_var.get():.1f}")
        if hasattr(self, 'menu_fb_speed_label'):
            self.menu_fb_speed_label.config(text=f"{int(self.speed_var.get())} WPM")
    
    def _apply_quality_settings(self, menu_window):
        """Wendet die Qualitätseinstellungen an"""
        self.update_quality_values()
        self.current_preset_label.config(text="Aktiv: Benutzerdefiniert")
        self.status_var.set("Qualitätseinstellungen übernommen")
        menu_window.destroy()
    
    def apply_preset(self, preset_name):
        """Wendet ein Qualitäts-Preset an"""
        presets = {
            'clear': {'temp': 0.2, 'speed': 1.0, 'rep': 7.0, 'label': 'Klar'},
            'natural': {'temp': 0.4, 'speed': 1.0, 'rep': 5.0, 'label': 'Natürlich'},
            'creative': {'temp': 0.7, 'speed': 1.0, 'rep': 3.0, 'label': 'Kreativ'}
        }
        
        if preset_name in presets:
            p = presets[preset_name]
            self.temp_var.set(p['temp'])
            self.tts_speed_var.set(p['speed'])
            self.rep_var.set(p['rep'])
            self.update_quality_values()
            self.current_preset_label.config(text=p['label'])
            self.status_var.set(f"Qualität: {p['label']}")
    
    def open_voice_cloning_menu(self):
        """Öffnet das Voice Cloning Menü als separates Fenster"""
        menu_window = tk.Toplevel(self.root)
        menu_window.title("Stimme verwalten - Voice Cloning")
        menu_window.geometry("600x500")
        menu_window.transient(self.root)
        menu_window.grab_set()
        
        # Hauptcontainer
        main_frame = ttk.Frame(menu_window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Titel
        ttk.Label(main_frame, text="Voice Cloning Optionen", 
                  font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # === Neue Stimme erstellen ===
        new_voice_frame = ttk.LabelFrame(main_frame, text="Neue Stimme erstellen", 
                                          padding="15")
        new_voice_frame.pack(fill=tk.X, pady=10)
        
        # Upload Button
        upload_btn = tk.Button(
            new_voice_frame,
            text="📁  Audio-Samples hochladen",
            command=lambda: self._upload_samples_in_menu(menu_window),
            font=("Arial", 12, "bold"),
            width=25,
            height=2,
            cursor="hand2"
        )
        upload_btn.pack(pady=10)
        
        # Status Labels im Menü
        self.menu_files_label = ttk.Label(new_voice_frame, text="Keine Dateien ausgewählt", 
                                          foreground="gray", font=("Arial", 11))
        self.menu_files_label.pack(pady=5)
        
        self.menu_embedding_label = ttk.Label(new_voice_frame, text="", 
                                              foreground="gray", font=("Arial", 10))
        self.menu_embedding_label.pack(pady=5)
        
        # Rauschunterdrückung Checkbox
        ttk.Checkbutton(
            new_voice_frame,
            text="🔇 Rauschen beim Hochladen entfernen",
            variable=self.denoise_var,
            style="Big.TCheckbutton"
        ).pack(pady=10)
        
        # Buttons: Speichern und Löschen
        btn_frame = ttk.Frame(new_voice_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="💾  Stimme speichern",
            command=lambda: self._save_voice_in_menu(menu_window),
            font=("Arial", 11, "bold"),
            width=18,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="✕  Samples löschen",
            command=lambda: self._clear_samples_in_menu(menu_window),
            font=("Arial", 11, "bold"),
            width=18,
            height=2,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        # === Gespeicherte Stimmen laden ===
        load_frame = ttk.LabelFrame(main_frame, text="Gespeicherte Stimmen", 
                                    padding="15")
        load_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Liste der gespeicherten Stimmen
        models = self.tts.list_saved_voice_models()
        
        if models:
            listbox_frame = ttk.Frame(load_frame)
            listbox_frame.pack(fill=tk.BOTH, expand=True)
            
            self.voice_listbox = tk.Listbox(listbox_frame, font=("Arial", 12), height=6)
            self.voice_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
            
            for model in models:
                self.voice_listbox.insert(tk.END, model['name'])
            
            if models:
                self.voice_listbox.selection_set(0)
            
            list_btn_frame = ttk.Frame(load_frame)
            list_btn_frame.pack(pady=10)
            
            tk.Button(
                list_btn_frame,
                text="📂  Laden",
                command=lambda: self._load_voice_from_menu(menu_window, models),
                font=("Arial", 12, "bold"),
                width=12,
                height=2,
                bg="#4CAF50",
                fg="white",
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=10)
            
            tk.Button(
                list_btn_frame,
                text="🗑  Löschen",
                command=lambda: self._delete_voice_from_menu(menu_window, models),
                font=("Arial", 12, "bold"),
                width=12,
                height=2,
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=10)
        else:
            ttk.Label(load_frame, text="Noch keine Stimmen gespeichert.", 
                      font=("Arial", 11), foreground="gray").pack(pady=20)
        
        # Schließen Button
        tk.Button(
            main_frame,
            text="Schließen",
            command=menu_window.destroy,
            font=("Arial", 12),
            width=15,
            height=2,
            cursor="hand2"
        ).pack(pady=15)
    
    def _upload_samples_in_menu(self, menu_window):
        """Lädt Samples im Voice Cloning Menü hoch"""
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
            self.menu_files_label.config(
                text=f"{file_count} Datei(en) werden verarbeitet...",
                foreground="orange"
            )
            self.status_var.set("Verarbeite Audio-Samples...")
            menu_window.update()
            self.root.update()
            
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
                
                self.menu_files_label.config(
                    text=f"{file_count} → {len(processed_files)} Sample(s), {total_duration:.1f}s",
                    foreground="green"
                )
                
                self.status_var.set("Berechne Speaker-Embeddings...")
                menu_window.update()
                self.root.update()
                
                self.tts.set_speaker_wav(self.speaker_wav_files)
                
                if hasattr(self.tts, 'gpt_cond_latent') and self.tts.gpt_cond_latent is not None:
                    self.menu_embedding_label.config(
                        text="✓ Speaker-Embeddings berechnet",
                        foreground="green"
                    )
                    self.status_var.set(f"Voice Cloning bereit ({total_duration:.1f}s Audio)")
                else:
                    self.menu_embedding_label.config(
                        text="✓ Samples verarbeitet",
                        foreground="green"
                    )
                    self.status_var.set(f"Voice Cloning aktiviert ({total_duration:.1f}s Audio)")
                    
            except Exception as e:
                self.menu_files_label.config(text="Fehler bei Verarbeitung", foreground="red")
                self.menu_embedding_label.config(text=str(e)[:50], foreground="red")
                self.status_var.set("Fehler bei Audio-Verarbeitung")
    
    def _save_voice_in_menu(self, menu_window):
        """Speichert die aktuelle Stimme aus dem Menü"""
        if not hasattr(self.tts, 'gpt_cond_latent') or self.tts.gpt_cond_latent is None:
            messagebox.showwarning(
                "Keine Stimme", 
                "Bitte laden Sie zuerst Audio-Samples hoch!"
            )
            return
        
        from tkinter import simpledialog
        name = simpledialog.askstring(
            "Stimme speichern",
            "Geben Sie einen Namen für die Stimme ein:",
            initialvalue=self.tts.current_voice_name or "meine_stimme"
        )
        
        if name:
            result = self.tts.save_voice_model(name)
            if result:
                self.model_name_label.config(text=f"📢 {name}")
                self.status_var.set(f"Voice-Modell '{name}' gespeichert")
                messagebox.showinfo("Erfolg", f"Voice-Modell '{name}' wurde gespeichert!")
                menu_window.destroy()
                self.open_voice_cloning_menu()  # Menü neu öffnen
            else:
                messagebox.showerror("Fehler", "Konnte Voice-Modell nicht speichern!")
    
    def _clear_samples_in_menu(self, menu_window):
        """Löscht die Samples aus dem Menü"""
        self.speaker_wav_files = []
        self.tts.set_speaker_wav(None)
        self.menu_files_label.config(text="Keine Dateien ausgewählt", foreground="gray")
        self.menu_embedding_label.config(text="", foreground="gray")
        self.model_name_label.config(text="Standard-Stimme")
        self.status_var.set("Voice Cloning deaktiviert")
    
    def _load_voice_from_menu(self, menu_window, models):
        """Lädt eine Stimme aus der Liste im Menü"""
        if hasattr(self, 'voice_listbox'):
            selection = self.voice_listbox.curselection()
            if selection:
                model_name = models[selection[0]]['name']
                menu_window.destroy()
                
                self.status_var.set(f"Lade Voice-Modell '{model_name}'...")
                self.root.update()
                
                if self.tts.load_voice_model(model_name):
                    self.model_name_label.config(text=f"📢 {model_name}")
                    self.status_var.set(f"Stimme '{model_name}' geladen!")
                else:
                    messagebox.showerror("Fehler", f"Konnte '{model_name}' nicht laden!")
    
    def _delete_voice_from_menu(self, menu_window, models):
        """Löscht eine Stimme aus dem Menü"""
        if hasattr(self, 'voice_listbox'):
            selection = self.voice_listbox.curselection()
            if selection:
                model_name = models[selection[0]]['name']
                if messagebox.askyesno("Löschen", f"'{model_name}' wirklich löschen?"):
                    if self.tts.delete_voice_model(model_name):
                        self.voice_listbox.delete(selection[0])
                        models.pop(selection[0])
                        self.status_var.set(f"'{model_name}' gelöscht")
        
    def load_last_model_on_startup(self):
        """Lädt beim Start automatisch das zuletzt genutzte Voice-Modell"""
        try:
            if self.tts.load_last_model():
                name = self.tts.current_voice_name
                self.model_name_label.config(text=name)
                self.status_var.set(f"Stimme '{name}' geladen")
        except Exception as e:
            print(f"Fehler beim automatischen Laden des Voice-Modells: {e}")
    
    def clear_placeholder(self, event):
        """Entfernt den Platzhalter-Text beim ersten Klick und setzt Textfarbe"""
        current_text = self.text_input.get(1.0, tk.END).strip()
        if current_text == "Text hier eingeben...":
            self.text_input.delete(1.0, tk.END)
            self.text_input.config(fg=self.COLOR_TEXT)
    
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
