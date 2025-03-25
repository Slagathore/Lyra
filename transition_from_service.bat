@echo off
SETLOCAL EnableDelayedExpansion

echo Lyra Service Transition Tool
echo ===========================
echo.
echo This tool will help you transition from the NSSM Windows service
echo to the new system tray application.
echo.
echo Steps that will be performed:
echo 1. Check for and forcefully stop the LyraAIService
echo 2. Remove the Windows service registration
echo 3. Kill any remaining NSSM processes
echo 4. Clean up registry entries
echo 5. Start the new system tray application
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause > nul

REM Set the working directory and Python path
cd /d %~dp0
SET PYTHONPATH=%~dp0

REM Check for Administrator privileges
NET SESSION >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERROR: Administrator privileges required!
    echo Please right-click this batch file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo.
echo Step 1: Checking for LyraAIService...
sc query LyraAIService >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo FOUND: LyraAIService is registered
    
    echo Stopping service with SC command...
    sc stop LyraAIService
    
    echo Waiting for service to stop (10 seconds)...
    timeout /t 10 /nobreak > nul
    
    echo Removing service registration...
    sc delete LyraAIService
    
    echo Forcefully killing any NSSM processes for Lyra...
    python -c "import psutil; [p.kill() for p in psutil.process_iter() if 'nssm' in p.name().lower() and any('lyra' in str(c).lower() for c in p.cmdline())]"
) ELSE (
    echo Service not found in registry.
)

echo.
echo Step 2: Cleaning up any remaining processes...
python utils\service_manager.py kill

echo.
echo Step 3: Checking registry for remnants...
reg query "HKLM\SYSTEM\CurrentControlSet\Services\LyraAIService" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo Found service in registry - removing...
    reg delete "HKLM\SYSTEM\CurrentControlSet\Services\LyraAIService" /f
) ELSE (
    echo No remnants found in registry.
)

echo.
echo Step 4: Clean up process completed.
echo Checking for any remaining Lyra processes...
python utils\service_manager.py status

echo.
echo Step 5: Installing tray application as regular application...
echo.
echo Options:
echo 1. Start Lyra tray application now
echo 2. Create desktop shortcut for future use
echo 3. Skip this step
echo.
set /p choice="Enter choice (1-3): "

IF "!choice!"=="1" (
    echo Starting Lyra tray application...
    start "" python modules\persistent_module.py
)

IF "!choice!"=="2" (
    echo Creating desktop shortcut...
    
    set SCRIPT_PATH=%~dp0modules\persistent_module.py
    set SHORTCUT_PATH=%USERPROFILE%\Desktop\Lyra.lnk
    
    echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
    echo sLinkFile = "%SHORTCUT_PATH%" >> CreateShortcut.vbs
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
    echo oLink.TargetPath = "python.exe" >> CreateShortcut.vbs
    echo oLink.Arguments = "%SCRIPT_PATH%" >> CreateShortcut.vbs
    echo oLink.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
    echo oLink.Description = "Lyra AI Assistant" >> CreateShortcut.vbs
    echo oLink.Save >> CreateShortcut.vbs
    
    cscript //nologo CreateShortcut.vbs
    del CreateShortcut.vbs
    
    echo Shortcut created on desktop.
)

echo.
echo Transition complete!
echo.
echo You can now run Lyra using the run_lyra_tray.bat script.
echo.
pause
