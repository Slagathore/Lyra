@echo off
SETLOCAL EnableDelayedExpansion

echo Lyra Real Core Finder
echo ====================
echo.
echo This utility will help you locate and connect to your real Lyra core installation
echo.

REM Set the working directory and Python path
cd /d %~dp0
SET PYTHONPATH=%~dp0

REM Check if the core location file already exists
if exist config\core_location.json (
    echo Existing core configuration found. Options:
    echo 1. Test existing configuration
    echo 2. Remove configuration and search again
    echo 3. Manually specify Lyra core location
    echo.
    set /p choice="Enter choice (1-3): "
    
    if "!choice!"=="1" (
        echo.
        echo Testing existing configuration...
        python test_core_connection.py
        goto end
    ) else if "!choice!"=="2" (
        echo.
        echo Removing existing configuration...
        del /q config\core_location.json
        echo Done. Will search for core again.
    )
) else (
    echo No existing core configuration found.
    echo.
    echo Options:
    echo 1. Automatically search for Lyra core
    echo 2. Manually specify Lyra core location
    echo.
    set /p choice="Enter choice (1-2): "
    
    if "!choice!"=="1" (
        goto auto_search
    )
)

if "%choice%"=="3" || "%choice%"=="2" (
    echo.
    echo Please enter the full path to your Lyra installation directory
    echo Example: C:\Users\YourName\Documents\Lyra
    echo.
    set /p core_path="Lyra installation path: "
    
    REM Validate the path
    if not exist "!core_path!" (
        echo.
        echo ERROR: Path does not exist: !core_path!
        goto end
    )
    
    REM Create config directory if needed
    if not exist config mkdir config
    
    REM Save the path to config file
    echo {"core_path": "!core_path!", "manual_setup": true, "setup_date": "%date% %time%"} > config\core_location.json
    echo.
    echo Configuration saved. Now testing the connection...
    python test_core_connection.py
    goto end
)

:auto_search
echo.
echo Searching for Lyra core installation...
echo This may take a minute...
echo.
python test_core_connection.py

:end
echo.
echo If the real core was found, the tray application should now
echo be able to connect to it automatically.
echo.
pause
