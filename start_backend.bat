@echo off
echo ========================================
echo   SpeakAlike - Starte Backend...
echo ========================================

cd /d "%~dp0"
.conda-py311\python.exe backend_api.py

pause
