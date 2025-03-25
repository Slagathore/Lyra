@echo off
cd /d %~dp0
echo ====== CUDA ONE-CLICK FIX ======
echo.
echo This script will fix your CUDA setup in ONE step!
echo.
echo Press any key to start fixing CUDA...
pause > nul

REM Set up CUDA environment variables
echo.
echo [STEP 1/5] Setting up CUDA environment variables...
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
set "CUDA_HOME=%CUDA_PATH%"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"
set "GGML_CUDA_NO_PINNED=1"
set "GGML_CUDA_FORCE_MMQ=1" 
set "GGML_CUDA_MEM_PERCENT=90"
set "CUDA_VISIBLE_DEVICES=0"

REM Verify CUDA exists
if not exist "%CUDA_PATH%" (
    echo ERROR: CUDA not found at %CUDA_PATH%
    echo Searching for other CUDA installations...
    for /d %%G in ("C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*") do (
        echo Found CUDA at: %%G
        set "CUDA_PATH=%%G"
        set "CUDA_HOME=%%G"
        goto cuda_found
    )
    echo.
    echo ERROR: Could not find CUDA installation.
    echo Please make sure CUDA is installed before running this script.
    goto end
)

:cuda_found
echo [SUCCESS] Using CUDA found at: %CUDA_PATH%

REM Activate virtual environment
echo.
echo [STEP 2/5] Activating Python environment...
if not exist "lyra_env\Scripts\activate.bat" (
    echo ERROR: Could not find Python environment at lyra_env
    echo Please make sure you have created a virtual environment.
    goto end
)
call lyra_env\Scripts\activate.bat
echo [SUCCESS] Python environment activated

REM Install CUDA-compatible PyTorch
echo.
echo [STEP 3/5] Installing CUDA-compatible PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] PyTorch installation had some issues
) else (
    echo [SUCCESS] PyTorch installed successfully
)

REM Install pre-built CUDA llama-cpp-python
echo.
echo [STEP 4/5] Installing CUDA-enabled llama-cpp-python...
pip uninstall -y llama-cpp-python
pip install llama-cpp-python==0.2.38+cu121 --no-cache-dir --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu121
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] llama-cpp-python installation had some issues
    echo Trying alternative method...
    set CMAKE_ARGS=-DLLAMA_CUBLAS=on
    pip install llama-cpp-python --no-cache-dir --force-reinstall
) else (
    echo [SUCCESS] llama-cpp-python installed successfully
)

REM Test if CUDA is working
echo.
echo [STEP 5/5] Testing if CUDA is working...
echo.
echo Testing PyTorch CUDA...
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('GPU Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"

echo.
echo Testing llama-cpp-python CUDA...
python -c "from llama_cpp import Llama; devices = Llama.get_available_gpu_devices(); print('GPU Devices:', devices); print('CUDA Support:', 'WORKING' if devices else 'NOT WORKING')"

REM Update batch files for automatic CUDA setup
echo.
echo [BONUS] Updating your batch files to automatically set CUDA paths...
for %%F in (run_gpu_llm_fixed.bat run_lyra_complete.bat alternative_gpu_llm.bat) do (
    if exist "%%F" (
        echo Updating %%F...
        (
            echo @echo off
            echo cd /d %%~dp0
            echo REM Set up CUDA environment
            echo set "CUDA_PATH=%CUDA_PATH%"
            echo set "CUDA_HOME=%%CUDA_PATH%%"
            echo set "PATH=%%CUDA_PATH%%\bin;%%CUDA_PATH%%\libnvvp;%%PATH%%"
            echo set "GGML_CUDA_NO_PINNED=1"
            echo set "GGML_CUDA_FORCE_MMQ=1"
            echo set "GGML_CUDA_MEM_PERCENT=90"
            echo.
            echo REM Original content below
            type "%%F" | find /v "@echo off"
        ) > "%%F.new"
        move /y "%%F.new" "%%F"
    )
)

echo.
echo ====== ALL DONE! ======
echo.
echo If you see "CUDA Support: WORKING" above, your setup is complete!
echo.
echo Now you can run:
echo   run_lyra_complete.bat
echo.
echo If you don't see "WORKING", please run:
echo   install_llama_cpp_cuda121.bat
echo.
:end
pause
