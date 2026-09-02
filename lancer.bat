@echo off
chcp 65001 >nul
cd /d "%~dp0"
title GT7 TuneLab
echo.
echo   GT7 TuneLab — installation des dependances...
python -m pip install -q -r requirements.txt
echo   Lancement sur http://127.0.0.1:8765
start "" "http://127.0.0.1:8765"
python app.py
pause
