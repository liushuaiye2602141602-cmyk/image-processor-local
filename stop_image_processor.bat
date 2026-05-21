@echo off
chcp 65001 >nul
title Stop Image Processor

echo ========================================
echo   Stopping Image Processor
echo ========================================
echo.

echo Searching for process on port 8000...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    echo Found process PID: %%a
    taskkill /PID %%a /F
    if errorlevel 1 (
        echo Failed to stop process %%a
    ) else (
        echo Process %%a stopped successfully.
    )
)

echo.
echo Done. If the server is still running, close the startup window manually.
echo ========================================
pause
