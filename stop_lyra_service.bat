@echo off
REM Utility to manage Lyra services and processes

echo Lyra Service Manager
echo ===================
echo.

REM Set the Python path to the current directory
SET PYTHONPATH=%~dp0

REM Change to the script directory to ensure correct imports
cd /d %~dp0

REM Check if pywin32 is installed
python -c "import win32service" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: pywin32 is not installed. Windows service management may not work correctly.
    echo To install pywin32, run: pip install pywin32
    echo.
    pause
)

REM Check for NSSM services specifically
echo Checking for Lyra services...
sc query LyraAIService >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo.
    echo FOUND: Lyra is installed as a Windows service (LyraAIService)
    echo This requires special handling to remove.
    echo.
    echo Options:
    echo 1. Stop and remove Windows service
    echo 2. Forcefully kill all Lyra processes
    echo 3. Continue to interactive menu
    echo.
    
    set /p action="Enter choice (1-3): "
    
    if "%action%"=="1" (
        echo Stopping and removing Lyra service...
        python utils\service_manager.py uninstall-service
    ) else if "%action%"=="2" (
        echo Forcefully killing all Lyra processes...
        python utils\service_manager.py kill
    )
    echo.
)

REM Run the service manager in interactive mode
python utils\service_manager.py interactive
exit /b
