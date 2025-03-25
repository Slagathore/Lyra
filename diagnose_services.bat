@echo off
echo Lyra Service Diagnostic Tool
echo ===========================
echo.
echo This tool will check for service-related issues and generate a diagnostic report.
echo.

REM Set the working directory and Python path
cd /d %~dp0
SET PYTHONPATH=%~dp0

echo Creating report file...
SET REPORT_FILE=lyra_service_diagnostic_%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%.txt
SET REPORT_FILE=%REPORT_FILE: =0%

echo Lyra Service Diagnostic Report > %REPORT_FILE%
echo Date: %date% Time: %time% >> %REPORT_FILE%
echo. >> %REPORT_FILE%

echo Checking for Administrator rights >> %REPORT_FILE%
echo ----------------------------- >> %REPORT_FILE%
NET SESSION >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo Running with Administrator rights >> %REPORT_FILE%
) ELSE (
    echo NOT running with Administrator rights >> %REPORT_FILE%
)
echo. >> %REPORT_FILE%

echo Checking Python installation >> %REPORT_FILE%
echo ----------------------------- >> %REPORT_FILE%
python --version >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Checking for services named "Lyra" or "LyraAI" >> %REPORT_FILE%
echo ------------------------------------------------ >> %REPORT_FILE%
sc query state= all | findstr /i "lyra" >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Checking registry for service entries >> %REPORT_FILE%
echo -------------------------------------- >> %REPORT_FILE%
reg query "HKLM\SYSTEM\CurrentControlSet\Services" /s /f "lyra" >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Checking for NSSM processes >> %REPORT_FILE%
echo ---------------------------- >> %REPORT_FILE%
tasklist /FI "IMAGENAME eq nssm*" >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Running service manager status check >> %REPORT_FILE%
echo ------------------------------------ >> %REPORT_FILE%
python utils\service_manager.py status >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Testing socket port 37849 availability >> %REPORT_FILE%
echo ------------------------------------ >> %REPORT_FILE%
python -c "import socket; s=socket.socket(); result=s.connect_ex(('localhost', 37849)); print(f'Port 37849 is {"busy" if result==0 else "available"}'); s.close()" >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Generating process list >> %REPORT_FILE%
echo ----------------------- >> %REPORT_FILE%
tasklist /v >> %REPORT_FILE% 2>&1
echo. >> %REPORT_FILE%

echo Diagnostic report complete and saved to %REPORT_FILE%
echo.
echo What would you like to do next?
echo 1. Open the diagnostic report
echo 2. Run emergency service cleanup
echo 3. Nothing, just exit
echo.
set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    start notepad %REPORT_FILE%
)

if "%choice%"=="2" (
    echo.
    echo Running emergency cleanup...
    echo WARNING: This will attempt to forcefully remove any Lyra services
    echo and kill related processes.
    echo.
    python utils\service_manager.py emergency-kill
)

echo.
echo Diagnostics complete.
pause
