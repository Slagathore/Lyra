@echo off
cd /d %~dp0
echo ==== Lyra Complete Setup Script ====
echo.

REM Create and configure environment for G: drive usage
echo Setting up environment for G: drive...
call configure_environment.bat

REM Check for Python
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or newer and try again.
    goto end
)

echo Step 1: Creating virtual environment...
if not exist "lyra_env" (
    python -m venv lyra_env
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

REM Activate the environment
call lyra_env\Scripts\activate.bat

REM Create necessary directories
mkdir data 2>nul
mkdir logs 2>nul
mkdir temp 2>nul

echo Step 2: Installing required packages...
pip install -U pip setuptools wheel
pip install -r requirements.txt

echo Step 3: Installing CUDA-optimized packages...
pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu118

echo Step 4: Running LLM error fix script...
call fix_llm_errors.bat

echo Step 5: Checking CUDA installation...
call check_cuda_install.bat

echo Step 6: Updating configuration files...
call run_update_config.bat

echo.
echo Setup complete! You can now run Lyra with:
echo - run_lyra_complete.bat (for the full setup)
echo - run_gpu_llm_fixed.bat (for just the LLM server)
echo - start_lyra.bat (for just the Lyra application)

:end
echo.
echo Press any key to exit...
pause
