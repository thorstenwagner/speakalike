"""
SpeakAlike GUI - Grafische Benutzeroberfläche für Text-to-Speech
"""
import os
import base64
from io import BytesIO
from PIL import Image, ImageTk

# Füge espeak-ng zum PATH hinzu
os.environ["PATH"] = r"C:\Program Files\eSpeak NG" + os.pathsep + os.environ.get("PATH", "")

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from main import TextToSpeech
from audio_processor import prepare_samples_for_cloning, get_audio_info
from catalog import MessageCatalog
from tag_generator import generate_tags

# Icon als Base64 (Mikrofon/Lautsprecher Symbol - 32x32 PNG)
ICON_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAAlwSFlz
AAAOxAAADsQBlSsOGwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAANFSURB
VFiF7ZdLbExRGMd/596ZzjzaaWdKp0qNR4hHPBIPEhYkFjYWNhYSKxYSCwsLKwsLsRCxsLDwWBCx
EBYeQYgQj4hHPOJRrYdptTPtzNx7/y7m3s6dzkynLSSs/Jfb8/2/7/ud75xz7oGRGIl/HOSPah/L
VFmFxPMA/nQVT49d85bZk7YBcHV0YXNRifp3QKcTx9OjC/IfRc+6aV5Xv8kB0NEWYHxZKWbA
/y0JAKvGjaPo0iV0Q4Nh/4TaEYRg7coVBPz+3wKIwGVbLJb1kqq6EIIrxcU8O38e4+jRIT5/A0D/
4EHS4+Pp0+kHBC4fD8epK+wK1u4OAzW1gN/tZm9NDQ2qlppAQGJXUxPnz52j+rPPr18FQCvFj95e
Lh47xofa2mGvl1VXE/D7h+0HsEqKz/v7qVm+nA+bNw8PAJj87BmnFywYnoCUFt4fOMC7JUuGLG/4
5BPm+HjKjh/ncV5e+gBSymFxDMDU+nqKk5LSTkAhGZJVu3cvdRER6QEAJJ8fNwwMYOjsZERREeE5
OT8G0LZvz48pXMHPj+EbNvxUPKYglV9Z+F3xgLQ0PHE/6LIEPz+hBw5w6+xZrLa2H4oD7G1spPzg
wYzr04WPp0/zt6oK35cvPywuBHu6ulh36hRfxowZPgCA9b6e5X19NJw8ybT6+mGLT/7wgTMFBXQ6
nRkBCKmxauxY7hUXZ7Q/Agcam5nh9zPd4ciIQUjNz8hILo8bR6fDMWxyBaDe4+Gx283n8PCMxgCE
EmK9z8fC7m5K7HYWBYMZjetrbuZ1cTFnXS5qnM7hAdxrbKQ8O5veIetHh4fzpqSEW1FRnI6IyGg9
hBqoXLsWNWnSj1ECfj8LurpY0NnJzPb2jJkJR0dTGxtLq8fDGZeL8qioYefDuLo6tJ4eCAQGT0NC
sKe5mY0dHfjj45njdGYE4Fi/Hhob6bfbB+dLu506n49Wm42Wrq7B7eWVlXSNGkW/0zkIsFsIxOdP
PIqIoNxqpcTvz2hegD1C4Hj5kv1Sy+C7I3RqOJ2cdDopcThoF+Kn9ej7A6D55Us+DdmX2rH8cFsb
C1tbKRMCm8uV0RGUoHv/x/X/E0biP4lvOT/4qBmPh2QAAAAASUVORK5CYII=
"""


class SpeakAlikeGUI:
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
        self.root.title("SpeakAlike")
        self.root.geometry("1050x520")  # Breiter für 4. Spalte
        self.root.minsize(900, 480)     # Mindestgröße
        self.root.resizable(True, True)
        self.root.configure(bg=self.COLOR_BG)
        
        # Icon setzen
        self._set_icon()
        
        # TTS Engine initialisieren
        self.tts = TextToSpeech()
        self.current_thread = None
        self.speaker_wav_files = []
        self.last_audio_path = None  # Pfad zur letzten generierten Audio-Datei
        self.last_generated_text = None  # Text der letzten Generierung
        
        # Katalog initialisieren
        self.catalog = MessageCatalog()
        
        # Style für Elemente
        self.setup_styles()
        self.setup_ui()
        
        # Versuche zuletzt genutztes Voice-Modell zu laden
        self.load_last_model_on_startup()
    
    def _set_icon(self):
        """Setzt das Anwendungs-Icon"""
        try:
            icon_data = base64.b64decode(ICON_BASE64)
            image = Image.open(BytesIO(icon_data))
            self.icon_image = ImageTk.PhotoImage(image)
            self.root.iconphoto(True, self.icon_image)
        except Exception as e:
            print(f"Icon konnte nicht geladen werden: {e}")
    
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
        main_frame.columnconfigure(0, weight=3)  # Linker Bereich (Hauptinhalt)
        main_frame.columnconfigure(1, weight=1)  # Rechter Bereich (Schnellzugriff)
        main_frame.rowconfigure(0, weight=1)  # Beide Bereiche bekommen den Platz
        
        # ===== LINKER BEREICH - Hauptinhalt =====
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, self.PADDING_MEDIUM))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)  # Textfeld expandiert
        
        # ===== TEXTFELD - Hauptelement mit subtiler Karte =====
        text_frame = ttk.LabelFrame(left_frame, text="Text eingeben", 
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
        button_frame = ttk.Frame(left_frame)
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
        
        # Katalog-Buttons
        self.catalog_add_button = tk.Button(
            secondary_frame,
            text="📁 Zum Katalog",
            command=self.add_to_catalog,
            state=tk.DISABLED,
            font=self.FONT_SMALL,
            bg="#dbeafe",
            fg=self.COLOR_PRIMARY,
            activebackground="#bfdbfe",
            disabledforeground="#9ca3af",
            width=14,
            height=1,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.catalog_add_button.grid(row=2, column=0, pady=2)
        
        # Katalog öffnen Button - immer aktiv
        self.catalog_open_button = tk.Button(
            secondary_frame,
            text="📚 Katalog öffnen",
            command=self.open_catalog,
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
        self.catalog_open_button.grid(row=3, column=0, pady=2)
        
        # ===== OPTIONEN - horizontale Leiste mit mehr Whitespace =====
        options_frame = ttk.Frame(left_frame)
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
            left_frame,
            textvariable=self.status_var,
            style="Muted.TLabel",
            anchor=tk.W
        )
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(self.PADDING_MEDIUM, 0))
        
        # ===== RECHTE SPALTE - Schnellzugriff auf Katalog/Favoriten =====
        self.setup_quick_access_panel(main_frame)
    
    def update_quality_values(self):
        """Überträgt Qualitätswerte an TTS-Engine"""
        self.tts.temperature = self.temp_var.get()
        self.tts.speed = self.tts_speed_var.get()
        self.tts.repetition_penalty = self.rep_var.get()
        self.tts.use_streaming = self.streaming_var.get()
    
    def setup_quick_access_panel(self, parent):
        """Erstellt die rechte Spalte für Schnellzugriff auf Katalog/Favoriten"""
        # Schnellzugriff-Frame
        quick_frame = ttk.LabelFrame(parent, text="Schnellzugriff", 
                                     padding=self.PADDING_MEDIUM, style="Card.TLabelframe")
        quick_frame.grid(row=0, column=1, sticky="nsew")
        quick_frame.columnconfigure(0, weight=1)
        quick_frame.rowconfigure(1, weight=1)
        
        # Variable für Anzeige-Modus
        self.quick_access_mode = tk.StringVar(value="favorites")
        
        # Button-Frame für Auswahl
        mode_frame = ttk.Frame(quick_frame)
        mode_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, self.PADDING_SMALL))
        mode_frame.columnconfigure(0, weight=1)
        mode_frame.columnconfigure(1, weight=1)
        
        # Favoriten-Button
        self.fav_mode_btn = tk.Button(
            mode_frame,
            text="⭐ Favoriten",
            command=lambda: self.set_quick_access_mode("favorites"),
            font=self.FONT_SMALL,
            bg=self.COLOR_PRIMARY,
            fg="white",
            activebackground=self.COLOR_PRIMARY_HOVER,
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.fav_mode_btn.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 2))
        
        # Katalog-Button
        self.cat_mode_btn = tk.Button(
            mode_frame,
            text="📚 Katalog",
            command=lambda: self.set_quick_access_mode("catalog"),
            font=self.FONT_SMALL,
            bg="#e5e7eb",
            fg=self.COLOR_TEXT,
            activebackground="#d1d5db",
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        self.cat_mode_btn.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(2, 0))
        
        # Scrollbarer Bereich für Nachrichten
        list_container = ttk.Frame(quick_frame)
        list_container.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)
        
        # Canvas für Scrolling
        self.quick_canvas = tk.Canvas(list_container, bg=self.COLOR_BG, 
                                       highlightthickness=0, width=220)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, 
                                  command=self.quick_canvas.yview)
        
        self.quick_messages_frame = ttk.Frame(self.quick_canvas)
        
        self.quick_canvas.create_window((0, 0), window=self.quick_messages_frame, 
                                         anchor=tk.NW, tags="quick_messages")
        self.quick_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.quick_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Mausrad-Scrolling
        self.quick_canvas.bind('<MouseWheel>', self._on_quick_mousewheel)
        self.quick_messages_frame.bind('<Configure>', 
                                        lambda e: self.quick_canvas.configure(
                                            scrollregion=self.quick_canvas.bbox("all")))
        
        # Canvas-Breite anpassen
        list_container.bind('<Configure>', self._on_quick_canvas_configure)
        
        # Aktualisieren-Button
        refresh_btn = tk.Button(
            quick_frame,
            text="🔄 Aktualisieren",
            command=self.refresh_quick_access,
            font=self.FONT_TINY,
            bg="#e5e7eb",
            fg=self.COLOR_TEXT,
            activebackground="#d1d5db",
            cursor="hand2",
            relief=tk.FLAT,
            bd=0
        )
        refresh_btn.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(self.PADDING_SMALL, 0))
        
        # Initiale Befüllung
        self.refresh_quick_access()
    
    def _on_quick_canvas_configure(self, event):
        """Passt die Breite des inneren Frames an"""
        self.quick_canvas.itemconfig("quick_messages", width=event.width - 20)
    
    def _on_quick_mousewheel(self, event):
        """Mausrad-Scrolling für Schnellzugriff"""
        self.quick_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def set_quick_access_mode(self, mode):
        """Wechselt zwischen Favoriten und Katalog"""
        self.quick_access_mode.set(mode)
        
        # Button-Styles aktualisieren
        if mode == "favorites":
            self.fav_mode_btn.configure(bg=self.COLOR_PRIMARY, fg="white")
            self.cat_mode_btn.configure(bg="#e5e7eb", fg=self.COLOR_TEXT)
        else:
            self.cat_mode_btn.configure(bg=self.COLOR_PRIMARY, fg="white")
            self.fav_mode_btn.configure(bg="#e5e7eb", fg=self.COLOR_TEXT)
        
        self.refresh_quick_access()
    
    def refresh_quick_access(self):
        """Aktualisiert die Schnellzugriff-Liste"""
        # Alte Widgets entfernen
        for widget in self.quick_messages_frame.winfo_children():
            widget.destroy()
        
        # Nachrichten laden
        mode = self.quick_access_mode.get()
        if mode == "favorites":
            messages = self.catalog.search(favorites_only=True, limit=20)
        else:
            messages = self.catalog.search(order_by="play_count", limit=20)
        
        if not messages:
            empty_label = ttk.Label(self.quick_messages_frame, 
                                    text="Keine Nachrichten\nverfügbar.",
                                    style="Muted.TLabel",
                                    justify=tk.CENTER)
            empty_label.pack(pady=30, padx=10)
            
            hint_label = ttk.Label(self.quick_messages_frame,
                                   text="Speichere Nachrichten\nim Katalog und markiere\nsie als Favoriten ⭐",
                                   style="Muted.TLabel",
                                   justify=tk.CENTER)
            hint_label.pack(pady=10, padx=10)
            return
        
        # Nachrichten-Karten erstellen
        for msg in messages:
            self.create_quick_message_card(msg)
    
    def create_quick_message_card(self, msg):
        """Erstellt eine kompakte Karte für Schnellzugriff"""
        card = tk.Frame(self.quick_messages_frame, bg="#ffffff", 
                        relief=tk.FLAT, bd=1, padx=8, pady=6)
        card.pack(fill=tk.X, pady=3, padx=2)
        
        # Text (stark gekürzt)
        text = msg['text']
        if len(text) > 40:
            text = text[:40] + "..."
        
        text_label = tk.Label(card, text=text, 
                              font=self.FONT_TINY,
                              bg="#ffffff", fg=self.COLOR_TEXT,
                              anchor=tk.W, justify=tk.LEFT,
                              wraplength=180)
        text_label.pack(fill=tk.X, anchor=tk.W)
        
        # Button-Frame
        btn_frame = tk.Frame(card, bg="#ffffff")
        btn_frame.pack(fill=tk.X, pady=(4, 0))
        
        # Abspielen-Button
        play_btn = tk.Button(
            btn_frame,
            text="▶",
            command=lambda m=msg: self.quick_play_message(m),
            font=self.FONT_SMALL,
            bg=self.COLOR_SUCCESS,
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            width=3,
            bd=0
        )
        play_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Text übernehmen Button
        use_btn = tk.Button(
            btn_frame,
            text="📝",
            command=lambda m=msg: self.quick_use_text(m),
            font=self.FONT_SMALL,
            bg="#e5e7eb",
            fg=self.COLOR_TEXT,
            cursor="hand2",
            relief=tk.FLAT,
            width=3,
            bd=0
        )
        use_btn.pack(side=tk.LEFT, padx=(0, 4))
        
        # Favoriten-Toggle
        fav_text = "⭐" if msg['is_favorite'] else "☆"
        fav_color = "#f59e0b" if msg['is_favorite'] else "#9ca3af"
        fav_btn = tk.Button(
            btn_frame,
            text=fav_text,
            command=lambda m=msg: self.quick_toggle_favorite(m),
            font=self.FONT_SMALL,
            bg="#ffffff",
            fg=fav_color,
            cursor="hand2",
            relief=tk.FLAT,
            width=3,
            bd=0
        )
        fav_btn.pack(side=tk.RIGHT)
    
    def quick_play_message(self, msg):
        """Spielt eine Nachricht aus dem Schnellzugriff ab"""
        if os.path.exists(msg['audio_path']):
            # Play-Count erhöhen
            self.catalog.update_play_count(msg['id'])
            
            # Audio abspielen
            import threading
            def play():
                try:
                    import sounddevice as sd
                    import soundfile as sf
                    data, sr = sf.read(msg['audio_path'])
                    sd.play(data, sr)
                    sd.wait()
                except Exception as e:
                    print(f"Fehler beim Abspielen: {e}")
            
            threading.Thread(target=play, daemon=True).start()
            self.status_var.set(f"▶ Spiele: {msg['text'][:30]}...")
        else:
            messagebox.showerror("Fehler", "Audio-Datei nicht gefunden!")
    
    def quick_use_text(self, msg):
        """Übernimmt Text aus Schnellzugriff ins Eingabefeld"""
        self.text_input.delete(1.0, tk.END)
        self.text_input.insert(1.0, msg['text'])
        self.text_input.config(fg=self.COLOR_TEXT)
        self.status_var.set("Text übernommen")
    
    def quick_toggle_favorite(self, msg):
        """Favoriten-Status aus Schnellzugriff umschalten"""
        self.catalog.toggle_favorite(msg['id'])
        self.refresh_quick_access()

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
        
        # Text für Katalog speichern
        self.last_generated_text = text
        
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
        # Download- und Katalog-Button aktivieren wenn Audio vorhanden
        if self.last_audio_path and os.path.exists(self.last_audio_path):
            self.download_button.config(state=tk.NORMAL)
            self.catalog_add_button.config(state=tk.NORMAL)
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
    
    # ========== KATALOG-FUNKTIONEN ==========
    
    def add_to_catalog(self):
        """Öffnet Dialog zum Hinzufügen der Sprachnachricht zum Katalog"""
        if not self.last_audio_path or not os.path.exists(self.last_audio_path):
            messagebox.showwarning("Keine Audio", "Bitte erst einen Text vorlesen lassen!")
            return
        
        # Dialog erstellen
        dialog = tk.Toplevel(self.root)
        dialog.title("Zum Katalog hinzufügen")
        dialog.geometry("500x480")
        dialog.configure(bg=self.COLOR_BG)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Zentrieren
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 500) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 480) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content Frame
        content = ttk.Frame(dialog, padding=self.PADDING_LARGE)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Titel
        ttk.Label(content, text="Sprachnachricht speichern", 
                  font=self.FONT_LARGE).pack(anchor=tk.W)
        
        ttk.Label(content, text="Die generierte Sprachnachricht wird im Katalog gespeichert.",
                  style="Muted.TLabel").pack(anchor=tk.W, pady=(5, 15))
        
        # Text-Vorschau
        text_frame = ttk.Frame(content)
        text_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(text_frame, text="Text:", style="Muted.TLabel").pack(anchor=tk.W)
        
        text_preview = tk.Text(text_frame, height=3, wrap=tk.WORD, 
                               font=self.FONT_SMALL, bg="#ffffff",
                               relief=tk.FLAT, bd=1)
        text_preview.pack(fill=tk.X, pady=5)
        text_preview.insert(1.0, self.last_generated_text or "")
        text_preview.config(state=tk.DISABLED)
        
        # Tags-Eingabe
        tags_frame = ttk.Frame(content)
        tags_frame.pack(fill=tk.X, pady=10)
        
        tags_label_frame = ttk.Frame(tags_frame)
        tags_label_frame.pack(fill=tk.X)
        
        ttk.Label(tags_label_frame, text="Schlagworte (mit Komma trennen):", 
                  style="Muted.TLabel").pack(side=tk.LEFT)
        
        # Auto-Generate Button
        def auto_generate_tags():
            """Generiert Tags automatisch mit Claude"""
            generate_btn.config(state=tk.DISABLED, text="⏳ Generiere...")
            dialog.update()
            
            # Vorhandene Tags für Wiederverwendung
            existing_tag_names = [t[0] for t in self.catalog.get_all_tags()]
            
            # Tags generieren
            import threading
            def generate():
                try:
                    generated = generate_tags(
                        text=self.last_generated_text or "",
                        existing_tags=existing_tag_names,
                        num_tags=5
                    )
                    dialog.after(0, lambda: update_tags_entry(generated))
                except Exception as e:
                    print(f"Tag-Generierung fehlgeschlagen: {e}")
                    dialog.after(0, lambda: generate_btn.config(state=tk.NORMAL, text="🤖 Auto-Tags"))
            
            def update_tags_entry(generated):
                if generated:
                    current = tags_entry.get().strip()
                    if current:
                        # Bestehende Tags behalten, neue hinzufügen
                        existing = [t.strip().lower() for t in current.split(',')]
                        new_tags = [t for t in generated if t.lower() not in existing]
                        if new_tags:
                            tags_entry.delete(0, tk.END)
                            tags_entry.insert(0, current + ", " + ", ".join(new_tags))
                    else:
                        tags_entry.delete(0, tk.END)
                        tags_entry.insert(0, ", ".join(generated))
                generate_btn.config(state=tk.NORMAL, text="🤖 Auto-Tags")
            
            threading.Thread(target=generate, daemon=True).start()
        
        generate_btn = tk.Button(
            tags_label_frame,
            text="🤖 Auto-Tags",
            command=auto_generate_tags,
            font=self.FONT_TINY,
            bg="#d1fae5",
            fg="#065f46",
            activebackground="#a7f3d0",
            cursor="hand2",
            relief=tk.FLAT,
            padx=8
        )
        generate_btn.pack(side=tk.RIGHT)
        
        tags_entry = tk.Entry(tags_frame, font=self.FONT_MEDIUM, 
                              bg="#ffffff", relief=tk.FLAT, bd=1)
        tags_entry.pack(fill=tk.X, pady=5, ipady=8)
        tags_entry.focus_set()
        
        # Vorschläge basierend auf häufigen Tags
        existing_tags = self.catalog.get_all_tags()
        if existing_tags:
            ttk.Label(tags_frame, text="Vorhandene Tags:", 
                      style="Muted.TLabel").pack(anchor=tk.W, pady=(10, 5))
            
            tags_suggest_frame = ttk.Frame(tags_frame)
            tags_suggest_frame.pack(fill=tk.X)
            
            for tag_name, count in existing_tags[:10]:
                tag_btn = tk.Button(
                    tags_suggest_frame,
                    text=f"{tag_name} ({count})",
                    command=lambda t=tag_name: self._add_tag_to_entry(tags_entry, t),
                    font=self.FONT_TINY,
                    bg="#e0e7ff",
                    fg="#4338ca",
                    relief=tk.FLAT,
                    cursor="hand2",
                    padx=8, pady=2
                )
                tag_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_to_catalog():
            tags_text = tags_entry.get().strip()
            tags = [t.strip() for t in tags_text.split(',') if t.strip()]
            
            # Sprache automatisch als Tag hinzufügen
            language = self.language_var.get()
            lang_names = {"de": "deutsch", "en": "englisch", "es": "spanisch", "fr": "französisch", "it": "italienisch", "pt": "portugiesisch", "pl": "polnisch", "tr": "türkisch", "ru": "russisch", "nl": "niederländisch", "cs": "tschechisch", "ar": "arabisch", "zh-cn": "chinesisch", "ja": "japanisch", "hu": "ungarisch", "ko": "koreanisch", "hi": "hindi"}
            lang_tag = lang_names.get(language, language)
            if lang_tag not in [t.lower() for t in tags]:
                tags.insert(0, lang_tag)
            
            # Voice-Model Name holen
            voice_model = self.model_name_label.cget("text")
            if voice_model == "Standard":
                voice_model = None
            
            # Audio-Länge berechnen
            try:
                import soundfile as sf
                data, sr = sf.read(self.last_audio_path)
                duration = len(data) / sr
            except:
                duration = None
            
            # Zum Katalog hinzufügen
            message_id = self.catalog.add_message(
                text=self.last_generated_text or "",
                source_audio_path=self.last_audio_path,
                tags=tags,
                voice_model=voice_model,
                duration_seconds=duration
            )
            
            dialog.destroy()
            self.status_var.set(f"Zum Katalog hinzugefügt (ID: {message_id})")
            
            # Schnellzugriff aktualisieren
            self.refresh_quick_access()
            
            messagebox.showinfo("Gespeichert", 
                              f"Sprachnachricht wurde zum Katalog hinzugefügt!\n\n"
                              f"Tags: {', '.join(tags) if tags else 'keine'}")
        
        save_btn = tk.Button(
            button_frame,
            text="Speichern",
            command=save_to_catalog,
            font=self.FONT_BUTTON,
            bg=self.COLOR_PRIMARY,
            fg="white",
            activebackground=self.COLOR_PRIMARY_HOVER,
            width=15,
            cursor="hand2",
            relief=tk.FLAT
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Abbrechen",
            command=dialog.destroy,
            font=self.FONT_BUTTON,
            bg="#e5e7eb",
            fg=self.COLOR_TEXT,
            width=15,
            cursor="hand2",
            relief=tk.FLAT
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def _add_tag_to_entry(self, entry, tag):
        """Fügt einen Tag zur Entry hinzu"""
        current = entry.get().strip()
        if current:
            if tag.lower() not in [t.strip().lower() for t in current.split(',')]:
                entry.delete(0, tk.END)
                entry.insert(0, f"{current}, {tag}")
        else:
            entry.insert(0, tag)
    
    def open_catalog(self):
        """Öffnet das Katalog-Fenster"""
        CatalogWindow(self.root, self.catalog, self.tts, self.speed_var, self.language_var)


class CatalogWindow:
    """Fenster zum Durchsuchen und Abspielen gespeicherter Sprachnachrichten"""
    
    def __init__(self, parent, catalog, tts, speed_var, language_var):
        self.catalog = catalog
        self.tts = tts
        self.speed_var = speed_var
        self.language_var = language_var
        self.current_messages = []
        
        # Fenster erstellen
        self.window = tk.Toplevel(parent)
        self.window.title("SpeakAlike - Katalog")
        self.window.geometry("900x600")
        self.window.configure(bg=SpeakAlikeGUI.COLOR_BG)
        
        self.setup_ui()
        self.refresh_messages()
    
    def setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        # Hauptframe
        main_frame = ttk.Frame(self.window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Linke Seite: Suche und Filter
        left_frame = ttk.Frame(main_frame, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))
        left_frame.pack_propagate(False)
        
        # Titel
        ttk.Label(left_frame, text="📚 Katalog", 
                  font=SpeakAlikeGUI.FONT_LARGE).pack(anchor=tk.W, pady=(0, 15))
        
        # Suchfeld
        ttk.Label(left_frame, text="Suche:", 
                  style="Muted.TLabel").pack(anchor=tk.W)
        
        self.search_entry = tk.Entry(left_frame, font=SpeakAlikeGUI.FONT_MEDIUM,
                                     bg="#ffffff", relief=tk.FLAT, bd=1)
        self.search_entry.pack(fill=tk.X, pady=5, ipady=5)
        self.search_entry.bind('<Return>', lambda e: self.search())
        self.search_entry.bind('<KeyRelease>', lambda e: self.search_delayed())
        
        # Such-Timer für verzögerte Suche
        self.search_timer = None
        
        # Such-Button
        search_btn = tk.Button(
            left_frame,
            text="🔍 Suchen",
            command=self.search,
            font=SpeakAlikeGUI.FONT_SMALL,
            bg=SpeakAlikeGUI.COLOR_PRIMARY,
            fg="white",
            cursor="hand2",
            relief=tk.FLAT
        )
        search_btn.pack(fill=tk.X, pady=5)
        
        # Filter: Favoriten
        self.favorites_var = tk.BooleanVar(value=False)
        favorites_cb = ttk.Checkbutton(
            left_frame,
            text="⭐ Nur Favoriten",
            variable=self.favorites_var,
            command=self.search
        )
        favorites_cb.pack(anchor=tk.W, pady=10)
        
        # Sortierung
        ttk.Label(left_frame, text="Sortierung:", 
                  style="Muted.TLabel").pack(anchor=tk.W, pady=(10, 5))
        
        self.sort_var = tk.StringVar(value="created_at")
        sort_options = [
            ("Neueste zuerst", "created_at"),
            ("Häufig abgespielt", "play_count"),
            ("Zuletzt abgespielt", "last_played_at")
        ]
        for text, value in sort_options:
            rb = ttk.Radiobutton(
                left_frame,
                text=text,
                variable=self.sort_var,
                value=value,
                command=self.search
            )
            rb.pack(anchor=tk.W)
        
        # Tags
        ttk.Label(left_frame, text="Tags:", 
                  style="Muted.TLabel").pack(anchor=tk.W, pady=(15, 5))
        
        self.tags_frame = ttk.Frame(left_frame)
        self.tags_frame.pack(fill=tk.X)
        
        self.selected_tags = []
        self.refresh_tags()
        
        # Alle anzeigen Button
        show_all_btn = tk.Button(
            left_frame,
            text="Alle anzeigen",
            command=self.show_all,
            font=SpeakAlikeGUI.FONT_SMALL,
            bg="#e5e7eb",
            fg=SpeakAlikeGUI.COLOR_TEXT,
            cursor="hand2",
            relief=tk.FLAT
        )
        show_all_btn.pack(fill=tk.X, pady=15)
        
        # Statistiken
        stats = self.catalog.get_stats()
        stats_text = f"📊 {stats['total_messages']} Nachrichten\n"
        stats_text += f"🏷️ {stats['total_tags']} Tags\n"
        stats_text += f"▶️ {stats['total_plays']} Wiedergaben"
        
        ttk.Label(left_frame, text=stats_text, 
                  style="Muted.TLabel").pack(anchor=tk.W, pady=10)
        
        # Rechte Seite: Nachrichten-Liste
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbare Liste
        self.canvas = tk.Canvas(right_frame, bg=SpeakAlikeGUI.COLOR_BG, 
                                highlightthickness=0)
        scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, 
                                  command=self.canvas.yview)
        
        self.messages_frame = ttk.Frame(self.canvas)
        
        self.canvas.create_window((0, 0), window=self.messages_frame, 
                                  anchor=tk.NW, tags="messages")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mausrad-Scrolling
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.messages_frame.bind('<Configure>', 
                                 lambda e: self.canvas.configure(
                                     scrollregion=self.canvas.bbox("all")))
        
        # Canvas-Breite anpassen
        right_frame.bind('<Configure>', self._on_canvas_configure)
    
    def _on_canvas_configure(self, event):
        """Passt die Breite des inneren Frames an"""
        self.canvas.itemconfig("messages", width=event.width - 20)
    
    def _on_mousewheel(self, event):
        """Mausrad-Scrolling"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def refresh_tags(self):
        """Aktualisiert die Tag-Liste"""
        for widget in self.tags_frame.winfo_children():
            widget.destroy()
        
        tags = self.catalog.get_all_tags()
        for tag_name, count in tags[:15]:
            is_selected = tag_name in self.selected_tags
            bg = "#4338ca" if is_selected else "#e0e7ff"
            fg = "white" if is_selected else "#4338ca"
            
            tag_btn = tk.Button(
                self.tags_frame,
                text=f"{tag_name}",
                command=lambda t=tag_name: self.toggle_tag(t),
                font=SpeakAlikeGUI.FONT_TINY,
                bg=bg,
                fg=fg,
                relief=tk.FLAT,
                cursor="hand2",
                padx=6, pady=2
            )
            tag_btn.pack(side=tk.LEFT, padx=2, pady=2)
    
    def toggle_tag(self, tag):
        """Tag an/abwählen"""
        if tag in self.selected_tags:
            self.selected_tags.remove(tag)
        else:
            self.selected_tags.append(tag)
        self.refresh_tags()
        self.search()
    
    def show_all(self):
        """Zeigt alle Nachrichten"""
        self.search_entry.delete(0, tk.END)
        self.selected_tags.clear()
        self.favorites_var.set(False)
        self.sort_var.set("created_at")
        self.refresh_tags()
        self.search()
    
    def search_delayed(self):
        """Verzögerte Suche für bessere Performance"""
        if self.search_timer:
            self.window.after_cancel(self.search_timer)
        self.search_timer = self.window.after(300, self.search)
    
    def search(self):
        """Führt die Suche aus"""
        query = self.search_entry.get().strip() or None
        
        self.current_messages = self.catalog.search(
            query=query,
            tags=self.selected_tags if self.selected_tags else None,
            favorites_only=self.favorites_var.get(),
            order_by=self.sort_var.get()
        )
        
        self.refresh_messages()
    
    def refresh_messages(self):
        """Aktualisiert die Nachrichten-Anzeige"""
        # Alte Widgets entfernen
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        if not self.current_messages:
            ttk.Label(self.messages_frame, 
                      text="Keine Nachrichten gefunden.",
                      style="Muted.TLabel").pack(pady=20)
            return
        
        # Nachrichten anzeigen
        for msg in self.current_messages:
            self.create_message_card(msg)
    
    def create_message_card(self, msg):
        """Erstellt eine Karte für eine Nachricht"""
        card = tk.Frame(self.messages_frame, bg="#ffffff", 
                        relief=tk.FLAT, bd=1, padx=15, pady=12)
        card.pack(fill=tk.X, pady=5, padx=5)
        
        # Obere Zeile: Text + Favorit
        top_frame = tk.Frame(card, bg="#ffffff")
        top_frame.pack(fill=tk.X)
        
        # Favorit-Stern
        fav_text = "⭐" if msg['is_favorite'] else "☆"
        fav_btn = tk.Button(
            top_frame,
            text=fav_text,
            command=lambda m=msg: self.toggle_favorite(m),
            font=SpeakAlikeGUI.FONT_MEDIUM,
            bg="#ffffff",
            fg="#f59e0b" if msg['is_favorite'] else "#9ca3af",
            relief=tk.FLAT,
            cursor="hand2",
            bd=0
        )
        fav_btn.pack(side=tk.LEFT)
        
        # Text (gekürzt)
        text = msg['text']
        if len(text) > 100:
            text = text[:100] + "..."
        
        text_label = tk.Label(top_frame, text=text, 
                              font=SpeakAlikeGUI.FONT_MEDIUM,
                              bg="#ffffff", fg=SpeakAlikeGUI.COLOR_TEXT,
                              anchor=tk.W, justify=tk.LEFT)
        text_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Mittlere Zeile: Tags + Info
        middle_frame = tk.Frame(card, bg="#ffffff")
        middle_frame.pack(fill=tk.X, pady=(8, 0))
        
        # Tags
        if msg['tags']:
            for tag in msg['tags'][:5]:
                tag_label = tk.Label(
                    middle_frame,
                    text=tag,
                    font=SpeakAlikeGUI.FONT_TINY,
                    bg="#e0e7ff",
                    fg="#4338ca",
                    padx=6, pady=2
                )
                tag_label.pack(side=tk.LEFT, padx=(0, 4))
        
        # Info (Datum, Wiedergaben)
        created = msg['created_at'][:10] if msg['created_at'] else ""
        plays = msg['play_count'] or 0
        duration = f"{msg['duration_seconds']:.1f}s" if msg['duration_seconds'] else ""
        
        info_text = f"📅 {created}  ▶️ {plays}x"
        if duration:
            info_text += f"  ⏱️ {duration}"
        
        info_label = tk.Label(middle_frame, text=info_text,
                              font=SpeakAlikeGUI.FONT_TINY,
                              bg="#ffffff", fg=SpeakAlikeGUI.COLOR_TEXT_MUTED)
        info_label.pack(side=tk.RIGHT)
        
        # Untere Zeile: Buttons
        button_frame = tk.Frame(card, bg="#ffffff")
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Abspielen
        play_btn = tk.Button(
            button_frame,
            text="▶ Abspielen",
            command=lambda m=msg: self.play_message(m),
            font=SpeakAlikeGUI.FONT_SMALL,
            bg=SpeakAlikeGUI.COLOR_SUCCESS,
            fg="white",
            cursor="hand2",
            relief=tk.FLAT,
            padx=12
        )
        play_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # In Eingabe übernehmen
        use_btn = tk.Button(
            button_frame,
            text="📝 Text verwenden",
            command=lambda m=msg: self.use_text(m),
            font=SpeakAlikeGUI.FONT_SMALL,
            bg="#e5e7eb",
            fg=SpeakAlikeGUI.COLOR_TEXT,
            cursor="hand2",
            relief=tk.FLAT,
            padx=12
        )
        use_btn.pack(side=tk.LEFT, padx=5)
        
        # Tags bearbeiten
        edit_tags_btn = tk.Button(
            button_frame,
            text="🏷️ Tags",
            command=lambda m=msg: self.edit_tags(m),
            font=SpeakAlikeGUI.FONT_SMALL,
            bg="#fef3c7",
            fg="#92400e",
            cursor="hand2",
            relief=tk.FLAT,
            padx=8
        )
        edit_tags_btn.pack(side=tk.LEFT, padx=5)
        
        # Löschen
        delete_btn = tk.Button(
            button_frame,
            text="🗑️",
            command=lambda m=msg: self.delete_message(m),
            font=SpeakAlikeGUI.FONT_SMALL,
            bg="#fee2e2",
            fg=SpeakAlikeGUI.COLOR_DANGER,
            cursor="hand2",
            relief=tk.FLAT,
            padx=8
        )
        delete_btn.pack(side=tk.RIGHT)
    
    def play_message(self, msg):
        """Spielt eine gespeicherte Nachricht ab"""
        if os.path.exists(msg['audio_path']):
            # Play-Count erhöhen
            self.catalog.update_play_count(msg['id'])
            
            # Audio abspielen
            import threading
            def play():
                try:
                    import sounddevice as sd
                    import soundfile as sf
                    data, sr = sf.read(msg['audio_path'])
                    sd.play(data, sr)
                    sd.wait()
                except Exception as e:
                    print(f"Fehler beim Abspielen: {e}")
            
            threading.Thread(target=play, daemon=True).start()
        else:
            messagebox.showerror("Fehler", "Audio-Datei nicht gefunden!")
    
    def use_text(self, msg):
        """Übernimmt den Text in das Hauptfenster"""
        # Finde das Hauptfenster
        for widget in self.window.master.winfo_children():
            if hasattr(widget, 'text_input'):
                widget.text_input.delete(1.0, tk.END)
                widget.text_input.insert(1.0, msg['text'])
                break
        
        # Alternativ: Schließe Katalog und setze Text
        self.window.destroy()
    
    def edit_tags(self, msg):
        """Öffnet Dialog zum Bearbeiten der Tags einer Nachricht"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Tags bearbeiten")
        dialog.geometry("450x300")
        dialog.configure(bg=SpeakAlikeGUI.COLOR_BG)
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Zentrieren
        dialog.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 450) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 300) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        content = ttk.Frame(dialog, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Titel
        ttk.Label(content, text="🏷️ Tags bearbeiten", 
                  font=SpeakAlikeGUI.FONT_LARGE).pack(anchor=tk.W)
        
        # Text-Vorschau (gekürzt)
        text_preview = msg['text'][:80] + "..." if len(msg['text']) > 80 else msg['text']
        ttk.Label(content, text=text_preview, 
                  style="Muted.TLabel", wraplength=400).pack(anchor=tk.W, pady=(5, 15))
        
        # Tags-Eingabe
        ttk.Label(content, text="Schlagworte (mit Komma trennen):", 
                  style="Muted.TLabel").pack(anchor=tk.W)
        
        tags_entry = tk.Entry(content, font=SpeakAlikeGUI.FONT_MEDIUM,
                              bg="#ffffff", relief=tk.FLAT, bd=1)
        tags_entry.pack(fill=tk.X, pady=5, ipady=8)
        
        # Aktuelle Tags einfügen
        if msg['tags']:
            tags_entry.insert(0, ', '.join(msg['tags']))
        tags_entry.focus_set()
        
        # Vorhandene Tags als Vorschläge
        existing_tags = self.catalog.get_all_tags()
        if existing_tags:
            ttk.Label(content, text="Vorhandene Tags:", 
                      style="Muted.TLabel").pack(anchor=tk.W, pady=(10, 5))
            
            tags_suggest_frame = ttk.Frame(content)
            tags_suggest_frame.pack(fill=tk.X)
            
            def add_tag(tag):
                current = tags_entry.get().strip()
                if current:
                    existing = [t.strip().lower() for t in current.split(',')]
                    if tag.lower() not in existing:
                        tags_entry.delete(0, tk.END)
                        tags_entry.insert(0, f"{current}, {tag}")
                else:
                    tags_entry.insert(0, tag)
            
            for tag_name, count in existing_tags[:12]:
                tag_btn = tk.Button(
                    tags_suggest_frame,
                    text=f"{tag_name}",
                    command=lambda t=tag_name: add_tag(t),
                    font=SpeakAlikeGUI.FONT_TINY,
                    bg="#e0e7ff",
                    fg="#4338ca",
                    relief=tk.FLAT,
                    cursor="hand2",
                    padx=6, pady=2
                )
                tag_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(content)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_tags():
            tags_text = tags_entry.get().strip()
            tags = [t.strip() for t in tags_text.split(',') if t.strip()]
            
            self.catalog.update_tags(msg['id'], tags)
            dialog.destroy()
            
            # Liste aktualisieren
            self.search()
            self.refresh_tags()
        
        save_btn = tk.Button(
            button_frame,
            text="Speichern",
            command=save_tags,
            font=SpeakAlikeGUI.FONT_BUTTON,
            bg=SpeakAlikeGUI.COLOR_PRIMARY,
            fg="white",
            activebackground=SpeakAlikeGUI.COLOR_PRIMARY_HOVER,
            width=12,
            cursor="hand2",
            relief=tk.FLAT
        )
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Abbrechen",
            command=dialog.destroy,
            font=SpeakAlikeGUI.FONT_BUTTON,
            bg="#e5e7eb",
            fg=SpeakAlikeGUI.COLOR_TEXT,
            width=12,
            cursor="hand2",
            relief=tk.FLAT
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
    
    def toggle_favorite(self, msg):
        """Schaltet Favoriten-Status um"""
        self.catalog.toggle_favorite(msg['id'])
        self.search()  # Aktualisieren
    
    def delete_message(self, msg):
        """Löscht eine Nachricht"""
        if messagebox.askyesno("Löschen bestätigen", 
                               "Möchten Sie diese Nachricht wirklich löschen?"):
            self.catalog.delete_message(msg['id'])
            self.search()  # Aktualisieren
            self.refresh_tags()


def main():
    """Startet die GUI-Anwendung"""
    root = tk.Tk()
    app = SpeakAlikeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
