@echo off
cd /d %~dp0
echo ==== Rebuilding llama-cpp-python with CUDA 12.8 Support ====
echo.

REM Make sure we're using the correct environment
call configure_environment.bat

REM Activate the virtual environment
call lyra_env\Scripts\activate.bat

echo Using standard CUDA 12.8 installation path...
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"

if not exist "%CUDA_PATH%" (
    echo Standard CUDA 12.8 path not found. Searching for alternatives...
    
    for /d %%G in ("C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*") do (
        set "CUDA_PATH=%%G"
        echo Found CUDA at: %%G
        goto cuda_found
    )
    
    echo CUDA not found in standard locations.
    echo Please enter the path to your CUDA installation:
    set /p CUDA_PATH="CUDA Path: "
)

:cuda_found
echo Using CUDA path: %CUDA_PATH%
echo CUDA version: %CUDA_PATH:~-5%

echo Setting environment variables...
set "CUDA_HOME=%CUDA_PATH%"
set "CUDACXX=%CUDA_PATH%\bin\nvcc.exe"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"

echo Uninstalling previous llama-cpp-python...
pip uninstall -y llama-cpp-python

echo Installing build dependencies...
pip install -U pip
pip install setuptools wheel build scikit-build cmake ninja pytest pytest-xdist pybind11

echo Setting compiler options for llama.cpp...
set CMAKE_ARGS=-DLLAMA_CUBLAS=on -DLLAMA_CUDA_F16=on

echo Installing llama-cpp-python with CUDA support...
pip install llama-cpp-python==0.2.38+cu121 --no-cache-dir --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu121

echo Testing CUDA support...
python -c "from llama_cpp import Llama; print('Available GPU Devices:', Llama.get_available_gpu_devices())"

if %ERRORLEVEL% NEQ 0 (
    echo Direct wheel install failed, trying alternative build method...
    
    REM Set additional environment variables for cuda 12.x
    set "CUDA_VERSION=%CUDA_PATH:~-5%"
    echo Building for CUDA %CUDA_VERSION%...
    
    pip install llama-cpp-python --no-cache-dir --verbose --force-reinstall
    
    echo Testing CUDA support again...
    python -c "from llama_cpp import Llama; print('Available GPU Devices:', Llama.get_available_gpu_devices())"
)

echo.
echo Installation complete!
echo.
pause
