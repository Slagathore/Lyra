@echo off
echo Lyra Emergency Instance Killer
echo =============================
echo.
echo This utility will kill ALL running Lyra Python instances
echo including the tray app and any services.
echo.
echo WARNING: This will forcefully terminate all Lyra processes!
echo Use this only if you can't stop Lyra normally.
echo.
echo 1. Kill all Lyra processes
echo 2. Exit without doing anything
echo.
set /p action="Enter choice (1-2): "

if "%action%"=="1" (
    echo.
    echo Killing all Lyra processes...
    
    REM Set Python path and working directory
    SET PYTHONPATH=%~dp0
    cd /d %~dp0
    
    REM Try to stop nicely first
    python utils\service_manager.py stop
    
    REM Now force kill any remaining Python processes with Lyra in the cmdline
    python -c "import os, psutil, time; print('Found these Lyra processes:'); [print(f'PID {p.pid}: {p.name()}') for p in psutil.process_iter(['pid', 'name', 'cmdline']) if any('lyra' in str(c).lower() for c in p.cmdline()) if p.pid != os.getpid()]; [p.kill() for p in psutil.process_iter(['pid', 'name', 'cmdline']) if any('lyra' in str(c).lower() for c in p.cmdline()) if p.pid != os.getpid()]; time.sleep(1); print('Kill operations completed.')"
    
    REM Check if port 37849 is now free
    python -c "import socket; s=socket.socket(); result=s.connect_ex(('localhost', 37849)); print(f'Port 37849 is now {\\'free\\' if result != 0 else \\'still in use - you may need to restart your computer\\'}'); s.close()"
    
    echo.
    echo All Lyra processes should be terminated.
    echo If you still have issues, try restarting your computer.
) else (
    echo Operation cancelled.
)

pause
