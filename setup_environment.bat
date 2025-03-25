@echo off
echo Lyra Environment Setup
echo =====================
echo.
echo This script will install required dependencies for Lyra.
echo.

SET PYTHONPATH=%~dp0
cd /d %~dp0

echo Checking Python installation...
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo Python not found. Please install Python 3.8 or newer.
    pause
    exit /b 1
)

echo.
echo Installing required packages...
python -m pip install -r requirements.txt

echo.
echo Setting up Lyra environment...
echo.

IF NOT EXIST data (
    mkdir data
    echo Created data directory
)

IF NOT EXIST logs (
    mkdir logs
    echo Created logs directory
)

IF NOT EXIST media (
    mkdir media
    echo Created media directory
)

IF NOT EXIST config (
    mkdir config
    echo Created config directory
)

echo.
echo Installation complete!
echo You can now run Lyra using run_lyra_tray.bat
echo.
pause
