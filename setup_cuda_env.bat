@echo off
cd /d %~dp0
echo Setting up CUDA environment variables...

REM Use the standard CUDA 12.8 installation path on C: drive
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"

if not exist "%CUDA_PATH%" (
    echo CUDA not found at standard location. Searching for alternatives...
    
    for /d %%G in ("C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*") do (
        set "CUDA_PATH=%%G"
        echo Found CUDA at: %%G
        goto cuda_found
    )
    
    echo Warning: Could not find CUDA installation.
    echo Please make sure CUDA is installed correctly.
)

:cuda_found
echo Using CUDA path: %CUDA_PATH%

REM Set environment variables
set "CUDA_HOME=%CUDA_PATH%"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"

REM Set llama.cpp specific environment variables
set "GGML_CUDA_NO_PINNED=1"
set "GGML_CUDA_FORCE_MMQ=1"
set "GGML_CUDA_MEM_PERCENT=90"
set "CUDA_VISIBLE_DEVICES=0"

echo CUDA environment configured!
echo Please restart your command prompt for changes to take effect.
pause
