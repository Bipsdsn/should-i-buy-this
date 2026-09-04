@echo off
REM One-click launcher (Windows). Double-click this file, or run: start.bat
cd /d "%~dp0"
python run.py
if errorlevel 1 py run.py
pause
