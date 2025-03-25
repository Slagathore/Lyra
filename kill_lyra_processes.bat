@echo off
REM Emergency utility to forcefully kill all Lyra processes

echo Lyra Emergency Process Killer
echo ============================
echo.
echo This will forcefully terminate all Lyra processes including services.
echo Use only if normal shutdown methods aren't working.
echo.
echo 1. Search for and kill all Lyra processes
echo 2. Exit without killing anything
echo.

set /p choice="Enter choice (1-2): "

if "%choice%"=="1" (
    echo.
    echo Searching for all Lyra processes...
    
    REM Set Python path
    SET PYTHONPATH=%~dp0
    
    REM Change to the script directory
    cd /d %~dp0
    
    REM Run the kill command
    python utils\service_manager.py kill
    
    echo.
    echo Process complete. If Lyra is still running, you may need to:
    echo 1. Use Windows Task Manager to kill remaining processes
    echo 2. Restart your computer to fully reset everything
) else (
    echo Operation cancelled.
)

pause
