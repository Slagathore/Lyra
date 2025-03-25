@echo off
SETLOCAL EnableDelayedExpansion

echo Lyra Tray App Debug Launcher
echo ===========================
echo.
echo This script will diagnose problems and help get the tray app running.

REM Set the working directory and Python path
cd /d %~dp0
SET PYTHONPATH=%~dp0

REM Check for required dependencies (fixed command)
echo Checking for required Python packages...
python -c "packages = {'pystray': False, 'PIL': False, 'tkinter': False, 'psutil': False}; missing = []; exec('try: import pystray; packages[\"pystray\"] = True\nexcept ImportError: pass'); exec('try: import PIL; packages[\"PIL\"] = True\nexcept ImportError: pass'); exec('try: import tkinter; packages[\"tkinter\"] = True\nexcept ImportError: pass'); exec('try: import psutil; packages[\"psutil\"] = True\nexcept ImportError: pass'); missing = [p for p, v in packages.items() if not v]; print('All dependencies installed.' if not missing else 'Missing: ' + ', '.join(missing))"

REM Check for port conflicts with better handling
echo Checking for port conflicts...
python -c "import socket; s=socket.socket(); result=s.connect_ex(('localhost', 37849)); print(f'Port 37849 is {\"busy - something is already using it\" if result==0 else \"available - good\"}'); s.close()"

set IS_PORT_BUSY=0
python -c "import socket; s=socket.socket(); result=s.connect_ex(('localhost', 37849)); exit(1 if result==0 else 0)" 2>nul
IF %ERRORLEVEL% EQU 1 set IS_PORT_BUSY=1

IF %IS_PORT_BUSY% EQU 1 (
    echo.
    echo WARNING: Another instance of Lyra appears to be running!
    echo.
    echo Options:
    echo 1. Try to focus the existing instance
    echo 2. Kill existing instances and start a new one
    echo 3. Continue anyway (not recommended)
    echo 4. Exit
    echo.
    set /p port_action="Enter your choice (1-4): "
    
    if "!port_action!"=="1" (
        echo Attempting to focus existing instance...
        python utils\service_manager.py focus
        echo If the window appeared, you can close this launcher.
        pause
        exit /b
    ) else if "!port_action!"=="2" (
        echo Killing existing Lyra instances...
        python utils\service_manager.py stop
        python -c "import psutil, time; [p.kill() for p in psutil.process_iter(['pid', 'name']) if 'python' in p.name().lower() and any('lyra' in c.lower() for c in p.cmdline()) if p.pid != os.getpid()]; time.sleep(1)"
        echo.
        echo Existing instances terminated. Continuing with startup...
        echo.
    ) else if "!port_action!"=="4" (
        echo Exiting.
        exit /b
    )
)

REM Check for existing Lyra processes (simplified)
echo Checking for running Lyra processes...
python -c "import psutil; count=0; lp=[]; [lp.append(p) for p in psutil.process_iter() if 'lyra' in p.name().lower()]; count=len(lp); print(f'Found {count} Lyra processes running' if count>0 else 'No Lyra processes found - good')"

REM Check for system tray capability - Fixed syntax completely
echo Checking if system tray is working...
python -c "import sys; has_pystray = False; has_pil = False; try: import pystray; has_pystray = True; except ImportError: pass; try: import PIL; has_pil = True; except ImportError: pass; print('System tray capability: ' + ('AVAILABLE' if has_pystray and has_pil else 'NOT AVAILABLE'))"

REM Check for NSSM services
echo Checking for NSSM services...
sc query LyraAIService >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo WARNING: LyraAIService is STILL REGISTERED as a Windows service!
    echo This is likely causing conflict with the tray app.
    echo.
    echo Please run transition_from_service.bat AS ADMINISTRATOR to remove it
    echo or manually remove it using:
    echo sc delete LyraAIService
    echo.
    echo Do you want to attempt to stop and remove the service now? (Y/N)
    set /p remove_service=
    if /i "!remove_service!"=="y" (
        echo Stopping and removing service...
        sc stop LyraAIService
        timeout /t 5 /nobreak > nul
        sc delete LyraAIService
    )
) ELSE (
    echo No LyraAIService found - good.
)

echo.
echo Ready to start Lyra tray app in DEBUG mode.
echo Look for an icon in your system tray when it starts!
echo A console window will stay open to show any error messages.
echo.
echo Start Lyra tray app now? (Y/N)
set /p start_app=
IF /i "!start_app!"=="y" (
    echo.
    echo Starting Lyra tray app with debug output...
    echo Log messages will appear below. Close this window to exit Lyra.
    echo.
    echo The system tray icon should appear momentarily.
    echo If you don't see it, check the notification area or hidden icons
    echo in your taskbar (click the up arrow in the taskbar)
    echo.
    echo --------------------------------------------------------
    echo.
    
    REM Run the simple test first to verify system tray works at all
    echo Testing system tray functionality first...
    python simple_tray_test.py
    
    echo.
    echo Now launching the full Lyra tray application...
    echo.
    python modules\persistent_module.py
) ELSE (
    echo Cancelled. No changes were made.
)

pause
