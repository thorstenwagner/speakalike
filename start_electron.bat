@echo off
echo ========================================
echo   SpeakAlike Electron App
echo ========================================
echo.

cd /d "%~dp0"

echo Pruefe Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo FEHLER: Node.js ist nicht installiert!
    echo Bitte installieren Sie Node.js von: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo Pruefe npm Pakete...
cd electron-app
if not exist "node_modules" (
    echo Installiere Abhaengigkeiten...
    call npm install
)

echo.
echo Starte SpeakAlike...
call npm start

pause
