@echo off
cd /d "%~dp0"
python gui_app.py
if errorlevel 1 (
    echo.
    echo Python failed. Make sure Python is installed and requirements are installed:
    echo   pip install -r requirements.txt
    pause
)
