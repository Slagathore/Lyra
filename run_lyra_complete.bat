@echo off
cd /d %~dp0
REM Set up CUDA environment
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
set "CUDA_HOME=%CUDA_PATH%"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"
set "GGML_CUDA_NO_PINNED=1"
set "GGML_CUDA_FORCE_MMQ=1"
set "GGML_CUDA_MEM_PERCENT=90"

REM Original content below
cd /d %~dp0
echo ==== Lyra Complete Startup Script ====
echo.

REM Configure environment for G: drive
call configure_environment.bat

echo This script will:
echo 1. Fix any LLM errors
echo 2. Start the GPU-accelerated language model
echo 3. Wait for the LLM server to initialize
echo 4. Start the Lyra application
echo.

REM Fix any LLM errors first
echo Step 1: Running LLM error fix script...
call fix_llm_errors.bat

echo.
echo Step 2: Verifying model path...
call verify_model_path.bat

echo.
echo Step 3: Starting language model server...
echo.
echo Opening new window for the LLM server...
start "Lyra LLM Server" cmd /k "%~dp0run_gpu_llm_fixed.bat"

echo.
echo Waiting 15 seconds for LLM server to initialize...
timeout /t 15 /nobreak >nul

echo.
echo Step 4: Checking server availability...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 5; Write-Host 'LLM server is running!' } catch { Write-Host 'LLM server not responding. It may still be starting up...' }"

echo.
echo Step 5: Starting Lyra application...
echo.
echo Opening new window for Lyra...
start "Lyra AI" cmd /k "%~dp0start_lyra.bat"

echo.
echo All services should now be starting!
echo.
echo - LLM server is running in a separate window
echo - Lyra application is running in another window
echo.
echo You can close this window once everything is running smoothly.
pause
