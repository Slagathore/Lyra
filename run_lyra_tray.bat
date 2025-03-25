@echo off
REM Run Lyra system tray application with Phi-4 model (basic test)

echo Lyra System Tray Application Manager
echo ===================================
echo.

REM Check for existing instance
python -c "import socket; s=socket.socket(); result=s.connect_ex(('localhost', 37849)); exit(1 if result==0 else 0)"
IF %ERRORLEVEL% EQU 1 (
    echo An instance of Lyra is already running.
    echo.
    echo Options:
    echo 1. Focus the existing instance
    echo 2. Stop the existing instance and start a new one
    echo 3. Exit
    echo.
    set /p choice="Enter choice (1-3): "
    
    if "%choice%"=="1" (
        echo Focusing existing instance...
        python utils\service_manager.py focus
        goto end
    ) else if "%choice%"=="2" (
        echo Stopping existing instance...
        python utils\service_manager.py stop
        echo Starting new instance...
        goto start_new
    ) else (
        echo Exiting.
        goto end
    )
) else (
    goto start_new
)

:start_new
echo Starting Lyra System Tray Application...

REM Check for admin rights
NET SESSION >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo Running with administrator privileges
) ELSE (
    echo Note: Running without administrator privileges.
    echo Some features like autostart configuration will require admin rights.
    echo.
    echo Options:
    echo 1. Continue without admin rights
    echo 2. Restart with admin rights
    echo 3. Exit
    echo.
    set /p admin_choice="Enter choice (1-3): "
    
    if "%admin_choice%"=="2" (
        echo Requesting administrator privileges...
        powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
        goto end
    ) else if "%admin_choice%"=="3" (
        echo Exiting.
        goto end
    )
)

REM Set Python path and change directory
SET PYTHONPATH=%~dp0
cd /d %~dp0

REM Create necessary directories
if not exist "config" mkdir config
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo Testing Phi-4 model loading...
python -c "from model_loader import get_instance; loader = get_instance(); config = {'name': 'phi-4', 'path': r'G:\AI\Lyra\BigModes\Phi-4-multimodal-instruct-abliterated', 'type': 'phi'}; result = loader.load_model(config); print('Model loaded successfully' if result else 'Failed to load model')"

if %ERRORLEVEL% NEQ 0 (
    echo Model loading test failed
    echo Check if all required dependencies are installed:
    echo - torch with CUDA support
    echo - transformers
    echo - accelerate
    pause
    exit /b 1
)

echo Starting Lyra with basic Phi-4 configuration...

REM Set minimal environment variables
SET LYRA_PREFERRED_MODEL=phi-4
SET LYRA_MODEL_PATH=G:\AI\Lyra\BigModes\Phi-4-multimodal-instruct-abliterated

REM Start the application with basic features first
python modules\persistent_module.py

echo Lyra System Tray Application closed.

:end
pause
