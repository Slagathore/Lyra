@echo off
cd /d %~dp0
echo ==== Installing llama-cpp-python with CUDA 12.1 Support ====
echo.

REM Make sure we're using the correct environment
call configure_environment.bat

REM Activate the virtual environment
call lyra_env\Scripts\activate.bat

REM Uninstall any existing llama-cpp-python
echo Uninstalling existing llama-cpp-python...
pip uninstall -y llama-cpp-python

echo Installing CUDA 12.1 binary wheel of llama-cpp-python...
pip install llama-cpp-python==0.2.38+cu121 --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu121

echo.
echo Testing CUDA support...
python -c "from llama_cpp import Llama; devices = Llama.get_available_gpu_devices(); print(f'Available GPU devices: {devices}'); print(f'CUDA support {"WORKING" if devices else "NOT WORKING"}')"

echo.
if %ERRORLEVEL% NEQ 0 (
    echo Installation failed. Trying alternative approach...
    
    REM Set environment variable to force CUDA builds
    set CMAKE_ARGS=-DLLAMA_CUBLAS=on
    set FORCE_CMAKE=1
    
    REM Try installing from source with CUDA enabled
    pip install llama-cpp-python --no-cache-dir --verbose --force-reinstall
    
    echo Testing CUDA support again...
    python -c "from llama_cpp import Llama; devices = Llama.get_available_gpu_devices(); print(f'Available GPU devices: {devices}'); print(f'CUDA support {"WORKING" if devices else "NOT WORKING"}')"
)

echo.
echo Installation complete.
echo.
pause
