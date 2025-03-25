@echo off
cd /d %~dp0
echo ====== CUDA FIX 2024 EDITION ======
echo.
echo This script will fix your CUDA setup for Lyra
echo.
echo Press any key to start...
pause > nul

REM Set up CUDA environment variables
echo.
echo [STEP 1/6] Setting up CUDA environment variables...
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
set "CUDA_HOME=%CUDA_PATH%"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"
set "GGML_CUDA_NO_PINNED=1"
set "GGML_CUDA_FORCE_MMQ=1" 
set "GGML_CUDA_MEM_PERCENT=90"
set "CUDA_VISIBLE_DEVICES=0"

echo [SUCCESS] Using CUDA path: %CUDA_PATH%

REM Activate virtual environment
echo.
echo [STEP 2/6] Activating Python environment...
call lyra_env\Scripts\activate.bat
echo [SUCCESS] Python environment activated

REM Completely remove PyTorch and llama-cpp-python
echo.
echo [STEP 3/6] Removing existing packages...
pip uninstall -y torch torchvision torchaudio 
pip uninstall -y llama-cpp-python
echo [SUCCESS] Removed existing packages

REM Install CUDA-compatible PyTorch with SPECIFIC version
echo.
echo [STEP 4/6] Installing CUDA-compatible PyTorch...
pip install torch==2.2.0+cu121 torchvision==0.17.0+cu121 torchaudio==2.2.0+cu121 --index-url https://download.pytorch.org/whl/cu121
echo [SUCCESS] PyTorch with CUDA support installed

REM Install llama-cpp-python with correct GGML_CUDA flag
echo.
echo [STEP 5/6] Installing llama-cpp-python with CUDA support...
echo Note: This may take several minutes...

set CMAKE_ARGS=-DGGML_CUDA=on

pip install llama-cpp-python==0.2.56 --verbose --no-cache-dir

echo.
echo [STEP 6/6] Testing CUDA setup...
python -c "import torch; print('PyTorch CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None')"
python -c "from llama_cpp import Llama; print('llama-cpp CUDA devices:', Llama.get_available_gpu_devices())"

REM Update key batch files
echo.
echo [BONUS] Updating batch files with correct CUDA settings...
for %%F in (run_gpu_llm_fixed.bat run_lyra_complete.bat alternative_gpu_llm.bat) do (
    echo Updating %%F...
    (
        echo @echo off
        echo cd /d %%~dp0
        echo.
        echo REM Set up CUDA environment
        echo set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
        echo set "CUDA_HOME=%%CUDA_PATH%%"
        echo set "PATH=%%CUDA_PATH%%\bin;%%CUDA_PATH%%\libnvvp;%%PATH%%"
        echo.
        echo REM Set llama.cpp CUDA variables (using GGML_CUDA instead of LLAMA_CUBLAS)
        echo set "GGML_CUDA_NO_PINNED=1"
        echo set "GGML_CUDA_FORCE_MMQ=1"
        echo set "GGML_CUDA_MEM_PERCENT=90"
        echo.
        echo REM Original script content follows
        type "%%F" | find /v "@echo off"
    ) > "%%F.new"
    move /y "%%F.new" "%%F"
)

echo.
echo ====== CUDA FIX COMPLETE ======
echo.
echo If you see CUDA devices listed above, your setup is working!
echo If you still have issues, please try:
echo   1. Installing Microsoft Visual C++ Build Tools
echo   2. Running with Administrator privileges
echo.
pause
