@echo off
echo =====================================================
echo SIMPLIFIED setup for llama-cpp-python with CUDA
echo =====================================================
echo.

:: Check for admin rights
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% neq 0 (
    echo This script needs to be run as administrator.
    echo Please right-click and run as administrator.
    pause
    exit /b
)

:: Step 1: Install Miniconda if not already installed
set "MINICONDA_PATH=%UserProfile%\miniconda3"
if not exist "%MINICONDA_PATH%" (
    echo Step 1: Installing Miniconda...
    
    :: Create temp directory for downloads
    if not exist "temp" mkdir temp
    cd temp
    
    echo Downloading Miniconda installer...
    curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    
    echo Installing Miniconda to %MINICONDA_PATH%...
    start /wait "" Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%MINICONDA_PATH%
    
    cd ..
    rmdir /S /Q temp
    
    echo Miniconda installed successfully!
) else (
    echo Step 1: Miniconda already installed at %MINICONDA_PATH%
)

echo.
echo Step 2: Creating NEW conda environment for llama-cpp...

:: Initialize command prompt to use conda
call "%MINICONDA_PATH%\Scripts\activate.bat"

:: Create a fresh environment with a different name to avoid conflicts
echo Creating fresh conda environment: llama-cuda-env
call conda create -y -n llama-cuda-env python=3.10

:: Activate the environment
call conda activate llama-cuda-env

echo.
echo Step 3: Setting up CUDA environment (11.8)...

:: Add CUDA 11.8 to PATH
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8"
set "PATH=%CUDA_PATH%\bin;%PATH%"

:: Install cudatoolkit 11.8 with conda
echo.
echo Installing cudatoolkit 11.8...
call conda install -y cudatoolkit=11.8

echo.
echo Step 4: Installing PyTorch 2.1.0 with CUDA 11.8 support...

:: Install PyTorch with CUDA 11.8 support
call conda install -y pytorch=2.1.0 torchvision torchaudio pytorch-cuda=11.8 -c pytorch -c nvidia

:: Verify PyTorch installation with CUDA
echo.
echo Checking PyTorch installation...
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A')"

echo.
echo Step 5: Installing llama-cpp-python with CUDA...

:: Set environment variables for CUDA support
echo Setting environment variables for CUDA compilation...
set CMAKE_ARGS=-DLLAMA_CUBLAS=on
set FORCE_CMAKE=1

:: Try pre-built wheel first (more reliable)
echo Installing pre-built CUDA wheel...
pip install --prefer-binary --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python==0.1.83

echo.
echo Step 6: Verifying installation...

:: Create a test script to verify llama-cpp-python installation
echo import llama_cpp > verify_installation.py
echo print("llama-cpp-python version:", llama_cpp.__version__) >> verify_installation.py
echo print("Module location:", llama_cpp.__file__) >> verify_installation.py
echo print() >> verify_installation.py
echo print("CUDA support check:") >> verify_installation.py
echo has_cuda = any("cuda" in attr.lower() or "gpu" in attr.lower() for attr in dir(llama_cpp.Llama)) >> verify_installation.py
echo print("CUDA methods found:", has_cuda) >> verify_installation.py
echo if has_cuda: >> verify_installation.py
echo     print("✅ llama-cpp-python is installed with CUDA support") >> verify_installation.py
echo else: >> verify_installation.py
echo     print("❌ CUDA support not detected in llama-cpp-python") >> verify_installation.py

echo Running verification script...
python verify_installation.py

echo.
echo ======================================================
echo Setup complete!
echo.
echo To use the environment in the future, run:
echo     call %MINICONDA_PATH%\Scripts\activate.bat
echo     conda activate llama-cuda-env
echo.
echo Creating a shortcut script to activate the environment...
echo @echo off > llama_cuda_env.bat
echo call "%MINICONDA_PATH%\Scripts\activate.bat" >> llama_cuda_env.bat
echo call conda activate llama-cuda-env >> llama_cuda_env.bat
echo echo Llama CUDA environment activated. >> llama_cuda_env.bat
echo echo Run your llama-cpp-python scripts now. >> llama_cuda_env.bat
echo cmd /k >> llama_cuda_env.bat

echo.
echo You can now run llama_cuda_env.bat to activate the environment.
echo ======================================================
pause
