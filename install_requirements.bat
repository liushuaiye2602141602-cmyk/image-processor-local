@echo off
chcp 65001 >nul
title Install Requirements

cd /d "%~dp0"

echo ========================================
echo   Install Dependencies
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo Virtual environment already exists.
    echo Upgrading pip and reinstalling requirements...
) else (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Please make sure Python 3.8+ is installed and in PATH.
        pause
        exit /b 1
    )
)

echo.
echo Upgrading pip...
.\.venv\Scripts\python.exe -m pip install --upgrade pip

echo.
echo Installing requirements...
.\.venv\Scripts\pip.exe install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation complete!
echo   Now run start_image_processor.bat
echo ========================================
pause
