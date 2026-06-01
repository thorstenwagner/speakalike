# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec für SpeakAlike Backend
Bündelt backend_api.py + alle Abhängigkeiten als backend_api.exe
"""
import os
import sys
from pathlib import Path

block_cipher = None
project_root = os.path.abspath('.')

# Daten-Dateien die mit eingepackt werden
datas = [
    ('prompt_de.txt', '.'),
    ('prompt_en.txt', '.'),
    ('electron-app/typing-sound.mp3', 'electron-app'),
]

# Versteckte Imports die PyInstaller nicht automatisch findet
hiddenimports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.responses',
    'pydantic',
    'pydantic._internal',
    'sounddevice',
    'soundfile',
    'scipy',
    'scipy.signal',
    'scipy.io',
    'scipy.io.wavfile',
    'lameenc',
    'noisereduce',
    'pyttsx3',
    'pyttsx3.drivers',
    'pyttsx3.drivers.sapi5',
    'torch',
    'torchaudio',
    'TTS',
    'TTS.api',
    'TTS.tts',
    'TTS.tts.configs',
    'TTS.tts.models',
    'TTS.utils',
    'elevenlabs',
    'spacy',
    'httpx',
    'anyio',
    'sniffio',
    'h11',
    'httpcore',
    'certifi',
    'multipart',
    'python_multipart',
]

a = Analysis(
    ['backend_api.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'PIL',
        'notebook',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend_api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # Konsole für Logs
    icon='electron-app/icons/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='backend',
)
