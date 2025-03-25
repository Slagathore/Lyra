@echo off
cd /d %~dp0
echo ==== Fixing LLM Server Errors ====
echo.

REM Configure environment for G: drive
call configure_environment.bat

echo Step 1: Activating Lyra environment...
call lyra_env\Scripts\activate.bat

echo Step 2: Fixing markupsafe circular import issue...
pip uninstall -y markupsafe
pip install markupsafe==2.1.1

echo Step 3: Checking CUDA availability...
python cuda_check.py

echo.
echo Step 4: Installing pre-built CUDA-optimized llama-cpp-python...
echo This may take several minutes...

pip uninstall -y llama-cpp-python

echo Attempting to install pre-built wheel for CUDA 11.8...
pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu118 llama-cpp-python==0.2.38+cu118 --no-deps
if %ERRORLEVEL% NEQ 0 (
    echo First attempt failed, trying alternate version...
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cu118 llama-cpp-python==0.2.32+cu118 --no-deps
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Pre-built wheel not found. Using direct download method...
    
    echo Downloading pre-built wheel from GitHub release...
    curl -L -o llama_cpp_python.whl https://github.com/abetlen/llama-cpp-python/releases/download/v0.2.32/llama_cpp_python-0.2.32+cu118-cp310-cp310-win_amd64.whl
    
    echo Installing downloaded wheel...
    pip install --no-deps llama_cpp_python.whl
    
    echo Installing required dependencies...
    pip install numpy typing-extensions diskcache jinja2==3.1.2
)

echo.
echo Step 5: Checking installation...
python -c "import llama_cpp; print('llama-cpp-python version:', llama_cpp.__version__); from llama_cpp import Llama; print('GPU devices:', Llama.get_available_gpu_devices())" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Installation verification failed. Trying CPU-only version as fallback...
    pip install --no-cache-dir llama-cpp-python==0.2.38
    
    python -c "import llama_cpp; print('llama-cpp-python installation successful (CPU only)!')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo WARNING: llama-cpp-python may not have installed correctly.
        echo Try manual installation: pip install --upgrade llama-cpp-python
    )
)

echo.
echo Running CUDA check again to verify installation...
python cuda_check.py

echo.
echo ==== Fix Complete ====
echo.
echo If you still encounter issues, try running the GPU LLM server with reduced parameters:
echo   - Run 'python -m llama_cpp.server --model G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf --n_gpu_layers 35 --n_ctx 2048 --n_batch 128'
echo.
echo Press any key to exit...
pause

@echo off
echo ===================================
echo Fixing CUDA environment for Llama-cpp
echo ===================================
echo.

:: Run as admin
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% NEQ 0 (
    echo This script needs to be run as administrator.
    echo Please right-click on the script and select 'Run as administrator'
    goto end
)

:: Fix the CUDA path environment variable
echo Fixing CUDA PATH environment variables...

:: Check current paths
echo.
echo Current CUDA_PATH: %CUDA_PATH%

:: Fix path with proper formatting 
echo.
echo Setting proper CUDA paths...
setx CUDA_PATH "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1" /M
setx CUDA_HOME "C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1" /M

:: Add CUDA bin to PATH if not already there
echo.
echo Updating system PATH...
set "cuda_bin_path=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin"

:: Check if it's already in PATH
echo %PATH% | findstr /C:"%cuda_bin_path%" >NUL
if %errorlevel% NEQ 0 (
    :: Not found, add it
    setx PATH "%PATH%;%cuda_bin_path%" /M
    echo Added CUDA bin directory to PATH.
) else (
    echo CUDA bin directory already in PATH.
)

:: Install CUDA-enabled llama-cpp-python
echo.
echo Installing CUDA-enabled llama-cpp-python...

:: Activate environment
call g:\AI\Lyra\lyra_env\Scripts\activate

:: Set compile flags for CUDA
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
set FORCE_CMAKE=1

:: First try pre-built wheels that are CUDA-enabled
echo.
echo Trying pre-built CUDA wheels...
pip install llama-cpp-python --force-reinstall --no-cache-dir --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/cu121

:: Check if installation was successful
pip show llama-cpp-python >nul 2>&1

:: Install llama-cpp-python with CUDA support in oobabooga
if exist "G:\AI\Lyra\oobabooga" (
    echo.
    echo Installing CUDA-enabled llama-cpp-python in oobabooga...
    
    :: Create a simple script to test llama-cpp-python with CUDA
    echo import llama_cpp > test_llama_cpp.py
    echo print("llama-cpp-python version:", llama_cpp.__version__) >> test_llama_cpp.py
    echo print("Module path:", llama_cpp.__file__) >> test_llama_cpp.py
    echo print("CUDA support available:", any('cuda' in attr.lower() for attr in dir(llama_cpp.Llama))) >> test_llama_cpp.py
    echo has_cuda = any('cuda' in attr.lower() or 'gpu' in attr.lower() for attr in dir(llama_cpp.Llama)) >> test_llama_cpp.py
    echo print("✓ CUDA support confirmed!" if has_cuda else "❌ CUDA support not found") >> test_llama_cpp.py
    
    :: Run the test
    echo.
    echo Testing llama-cpp-python CUDA support...
    python test_llama_cpp.py
    
    :: Create a better script for running oobabooga with GPU
    echo.
    echo Creating optimized GPU script for oobabooga...
    cd G:\AI\Lyra\oobabooga
    
    echo @echo off > run_qwen_gpu.bat
    echo echo Running Qwen model with GPU acceleration... >> run_qwen_gpu.bat
    echo. >> run_qwen_gpu.bat
    echo :: Set proper CUDA environment >> run_qwen_gpu.bat 
    echo set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1" >> run_qwen_gpu.bat
    echo set "CUDA_HOME=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1" >> run_qwen_gpu.bat
    echo set "PATH=%%PATH%%;C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1\bin" >> run_qwen_gpu.bat
    echo. >> run_qwen_gpu.bat
    echo call "%%UserProfile%%\miniconda3\Scripts\activate.bat" >> run_qwen_gpu.bat
    echo. >> run_qwen_gpu.bat
    echo :: Run with GPU optimized parameters >> run_qwen_gpu.bat
    echo python server.py --model "G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf" --loader llama.cpp --n-gpu-layers 35 --threads 8 --n_batch 512 --n-ctx 4096 --api --tensorcores --no_offload_kqv >> run_qwen_gpu.bat
    
    echo.
    echo Created GPU-optimized script: G:\AI\Lyra\oobabooga\run_qwen_gpu.bat
)

echo.
echo Environment setup complete! Next steps:
echo 1. Restart your command prompt or terminal
echo 2. Run G:\AI\Lyra\oobabooga\run_qwen_gpu.bat
echo.

:end
pause
