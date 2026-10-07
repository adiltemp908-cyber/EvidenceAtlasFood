@echo off
cd /d "%~dp0"
python scripts\open_app.py
if errorlevel 1 pause
