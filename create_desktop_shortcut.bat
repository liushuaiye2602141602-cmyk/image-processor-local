@echo off
chcp 65001 >nul
title Create Desktop Shortcut

cd /d "%~dp0"

echo ========================================
echo   Creating Desktop Shortcut
echo ========================================
echo.

set "TARGET=%~dp0start_image_processor.bat"
set "SHORTCUT=%USERPROFILE%\Desktop\Local Image Processor.lnk"

echo Set ws = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo Set lnk = ws.CreateShortcut("%SHORTCUT%") >> "%TEMP%\create_shortcut.vbs"
echo lnk.TargetPath = "%TARGET%" >> "%TEMP%\create_shortcut.vbs"
echo lnk.WorkingDirectory = "%~dp0" >> "%TEMP%\create_shortcut.vbs"
echo lnk.Description = "Local Image Processor" >> "%TEMP%\create_shortcut.vbs"
echo lnk.Save >> "%TEMP%\create_shortcut.vbs"

cscript //nologo "%TEMP%\create_shortcut.vbs"
del "%TEMP%\create_shortcut.vbs"

if exist "%SHORTCUT%" (
    echo Shortcut created on desktop: Local Image Processor
) else (
    echo Failed to create shortcut.
    echo.
    echo Alternative: Right-click start_image_processor.bat
    echo -^> Send to -^> Desktop (create shortcut)
)

echo ========================================
pause
