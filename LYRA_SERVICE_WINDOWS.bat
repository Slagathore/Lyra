@echo off
:: Lyra AI Persistence Service Installer
:: This batch file will install Lyra as a Windows service for background operation
title Lyra AI Service Installer

echo ===============================================
echo         LYRA AI PERSISTENCE INSTALLER
echo ===============================================
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: This script requires administrator privileges.
    echo Please right-click this batch file and select "Run as administrator".
    echo.
    pause
    exit /b 1
)

echo Checking Python environment...
:: Get the path to the Python environment used for Lyra
set PYTHON_EXE="%~dp0lyra_env\Scripts\python.exe"
if not exist %PYTHON_EXE% (
    echo ERROR: Python environment not found at %PYTHON_EXE%
    echo Please make sure you've set up the Lyra environment correctly.
    echo.
    pause
    exit /b 1
)

:: Verify dependencies
echo Checking required packages...
%PYTHON_EXE% -c "import pip; pip.main(['install', '--quiet', 'pystray', 'pillow', 'keyboard', 'requests', 'pywin32'])" >nul 2>&1
if %errorLevel% neq 0 (
    echo WARNING: Some dependencies could not be installed. Service may have limited functionality.
)

:: Create config directory if it doesn't exist
if not exist "%~dp0config" mkdir "%~dp0config"

:: Verify persistence_setup.py exists
if not exist "%~dp0persistence_setup.py" (
    echo ERROR: persistence_setup.py not found.
    echo Please make sure all Lyra files are properly installed.
    echo.
    pause
    exit /b 1
)

echo.
echo Installing Lyra AI as a Windows service...
%PYTHON_EXE% "%~dp0persistence_setup.py" --install

if %errorLevel% equ 0 (
    echo.
    echo ===============================================
    echo      LYRA AI SERVICE INSTALLED SUCCESSFULLY
    echo ===============================================
    echo.
    echo The service will start automatically when you log in.
    echo You can also start it manually from Services (services.msc) or by running:
    echo     net start LyraAIService
    echo.
    echo To uninstall the service, run:
    echo     "%~dp0uninstall_lyra_service.bat"
    echo.
    echo To access Lyra:
    echo  - Use Alt+Shift+L to open the UI from anywhere
    echo  - Use the system tray icon in the notification area
    echo  - Connect through Telegram if configured
    echo.
) else (
    echo.
    echo ERROR: Failed to install Lyra AI service.
    echo.
    echo You can check the log at:
    echo     "%~dp0persistence_setup.log"
    echo.
    echo Common issues:
    echo  1. Make sure you're running with Administrator privileges
    echo  2. Check if the service already exists (use services.msc)
    echo  3. Try the manual command: %PYTHON_EXE% "%~dp0persistence_setup.py" --install --debug
    echo.
)

pause