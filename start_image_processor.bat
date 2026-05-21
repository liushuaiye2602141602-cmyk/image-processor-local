@echo off
chcp 65001 >nul
title Local Image Processor

cd /d "%~dp0"

echo ========================================
echo   Local Image Processor
echo ========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Please make sure Python 3.8+ is installed and in PATH.
        pause
        exit /b 1
    )
    echo Installing requirements...
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
    echo.
)

echo Starting local image processor...
echo Open: http://127.0.0.1:8000
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

start "" "http://127.0.0.1:8000"

.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
