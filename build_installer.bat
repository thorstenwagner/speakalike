@echo off
echo ========================================
echo   SpeakAlike - Windows Installer Build
echo ========================================
echo.

cd /d "%~dp0"

REM === Schritt 1: Python Backend buendeln ===
echo [1/3] Python Backend wird mit PyInstaller gebuendelt...
echo       (Das kann einige Minuten dauern)
echo.

REM PyInstaller installieren falls noetig
.conda-py311\python.exe -m pip install pyinstaller --quiet 2>nul

REM Alten Build aufraeumen
if exist "dist\backend" rmdir /s /q "dist\backend"
if exist "build" rmdir /s /q "build"

.conda-py311\python.exe -m PyInstaller backend.spec --noconfirm
if errorlevel 1 (
    echo.
    echo FEHLER: PyInstaller Build fehlgeschlagen!
    pause
    exit /b 1
)

echo.
echo       Backend erfolgreich gebuendelt.
echo.

REM === Schritt 2: Node-Module installieren ===
echo [2/3] Electron-Builder Abhaengigkeiten werden installiert...
echo.

cd electron-app
call npm install --save-dev electron-builder
if errorlevel 1 (
    echo.
    echo FEHLER: npm install fehlgeschlagen!
    pause
    exit /b 1
)

echo.

REM === Schritt 3: Electron Installer erstellen ===
echo [3/3] Windows Installer wird erstellt...
echo.

set CSC_IDENTITY_AUTO_DISCOVERY=false
call npx electron-builder --win --project .
if errorlevel 1 (
    echo.
    echo FEHLER: electron-builder fehlgeschlagen!
    pause
    exit /b 1
)

cd ..

echo.
echo ========================================
echo   Build abgeschlossen!
echo   Installer liegt unter: dist\
echo ========================================
echo.

dir /b dist\*.exe 2>nul
echo.
pause
