@echo off
cd /d %~dp0
echo ==== CUDA Installation Checker ====
echo.

REM Configure environment for G: drive
call configure_environment.bat

echo Checking for CUDA installation...
where nvcc >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo CUDA found in PATH.
    nvcc --version
) else (
    echo CUDA not found in PATH. Checking common installation locations...
    
    if exist "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA" (
        echo CUDA toolkit found at C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA
        dir "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA"
    ) else if exist "G:\NVIDIA\CUDA" (
        echo CUDA toolkit found at G:\NVIDIA\CUDA
        dir "G:\NVIDIA\CUDA"
    ) else if exist "G:\AI\CUDA" (
        echo CUDA toolkit found at G:\AI\CUDA
        dir "G:\AI\CUDA"
    ) else if exist "G:\CUDA" (
        echo CUDA toolkit found at G:\CUDA
        dir "G:\CUDA"
    ) else (
        echo CUDA toolkit not found in common locations.
        echo Searching for CUDA on G: drive (this may take a moment)...
        
        where /r G:\ cuda*.dll >nul 2>nul
        if %ERRORLEVEL% EQU 0 (
            echo CUDA DLLs found on G: drive. Run "where /r G:\ cuda*.dll" for locations.
        ) else (
            echo No CUDA DLLs found on G: drive.
            echo Please install CUDA toolkit from: https://developer.nvidia.com/cuda-downloads
        )
    )
    
    echo.
    echo To add CUDA to PATH:
    echo 1. Right-click on Start and select "System"
    echo 2. Click "Advanced system settings"
    echo 3. Click "Environment Variables..."
    echo 4. Under "System variables", find and select "Path", then click "Edit..."
    echo 5. Click "New" and add the path to CUDA bin directory
    echo 6. Click "OK" on all dialogs
)

echo.
echo Checking for GPU information...
nvidia-smi >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo GPU information:
    nvidia-smi
) else (
    echo nvidia-smi not found. Trying with full path...
    
    for %%d in (C G) do (
        for /f "delims=" %%a in ('dir /b /s "%%d:\*nvidia-smi.exe" 2^>nul') do (
            echo Found nvidia-smi at: %%a
            "%%a"
            goto found_nvidia_smi
        )
    )
    
    :found_nvidia_smi
    if %ERRORLEVEL% NEQ 0 (
        echo nvidia-smi not found. Cannot display GPU information.
        echo Make sure you have NVIDIA drivers installed.
    )
)

echo.
echo Checking if llama-cpp-python is installed and working...
call lyra_env\Scripts\activate.bat
python -c "import llama_cpp; print('llama-cpp-python version:', llama_cpp.__version__)" 2>nul
if %ERRORLEVEL% EQU 0 (
    echo llama-cpp-python is properly installed.
    
    echo.
    echo Checking CUDA availability in llama-cpp-python...
    python %~dp0\cuda_check.py
) else (
    echo llama-cpp-python is not installed or not working properly.
    echo Run fix_llm_errors.bat to fix this issue.
)

echo.
echo Press any key to exit...
pause
