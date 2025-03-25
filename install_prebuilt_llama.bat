@echo off
cd /d %~dp0
echo ====== Install Pre-built llama-cpp-python ======
echo.
echo This script will try several versions of pre-built llama-cpp-python packages
echo.

REM Activate virtual environment
call lyra_env\Scripts\activate.bat

REM Remove existing installation
pip uninstall -y llama-cpp-python

echo Trying standard llama-cpp-python installation (0.2.56)...
pip install llama-cpp-python==0.2.56

echo.
echo Testing installation...
python -c "from llama_cpp import Llama; print('Available GPU devices:', Llama.get_available_gpu_devices())"

if %ERRORLEVEL% NEQ 0 (
    echo Installation or import failed.
    echo.
    echo Trying alternative - wheels from OneDrive...
    mkdir temp_wheels 2>nul
    cd temp_wheels
    
    REM Get OneDrive auth key from credentials
    for /f "tokens=2 delims=:" %%a in ('python -c "import json; print(json.load(open('../credentials.yml'))['onedrive_auth_key'])"') do set ONEDRIVE_KEY=%%a
    set ONEDRIVE_KEY=%ONEDRIVE_KEY:"=%
    set ONEDRIVE_KEY=%ONEDRIVE_KEY: =%
    
    echo Downloading pre-built wheel...
    curl -L -o llama_cpp_python-0.2.31-cp310-cp310-win_amd64.whl https://onedrive.live.com/download?cid=9DEDF3C1E2D7304C^&resid=9DEDF3C1E2D7304C%%2133034^&authkey=%ONEDRIVE_KEY%
    
    echo Installing downloaded wheel...
    pip install llama_cpp_python-0.2.31-cp310-cp310-win_amd64.whl
    cd ..
    
    echo Testing installation again...
    python -c "from llama_cpp import Llama; print('Available GPU devices:', Llama.get_available_gpu_devices())"
)

echo.
echo If you see GPU devices listed above, installation succeeded.
echo If not, please consider creating a clean Python environment with:
echo   python -m venv fresh_env
echo   fresh_env\Scripts\activate.bat
echo   pip install torch==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121
echo   pip install llama-cpp-python==0.2.56
echo.
pause
