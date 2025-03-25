@echo off
echo Setting up oobabooga/text-generation-webui for Qwen model...
echo.

:: Check if Python is installed
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found! Please install Python 3.10 or newer.
    echo Visit: https://www.python.org/downloads/
    goto end
)

:: Check Python version
python --version
echo.

:: Check if Miniconda is installed
set "MINICONDA_PATH=%UserProfile%\miniconda3"
set "MINICONDA_HOOK=%MINICONDA_PATH%\Scripts\activate.bat"

if not exist "%MINICONDA_HOOK%" (
    echo Miniconda not found. Installing Miniconda...
    
    :: Create a temporary directory for the installer
    if not exist "temp" mkdir temp
    cd temp
    
    :: Download Miniconda installer
    echo Downloading Miniconda installer...
    curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe
    
    :: Install Miniconda silently
    echo Installing Miniconda...
    start /wait "" Miniconda3-latest-Windows-x86_64.exe /InstallationType=JustMe /RegisterPython=0 /S /D=%MINICONDA_PATH%
    
    cd ..
    rmdir /S /Q temp
    
    echo Miniconda installed to %MINICONDA_PATH%
) else (
    echo Found Miniconda at %MINICONDA_PATH%
)

:: Create directory for oobabooga if it doesn't exist
if not exist "oobabooga" (
    echo Creating directory for oobabooga...
    mkdir oobabooga
    cd oobabooga

    echo Cloning the repository...
    git clone https://github.com/oobabooga/text-generation-webui.git .
) else (
    cd oobabooga
    echo Directory already exists, checking for updates...
    git pull
)

:: Determine GPU type for requirements
echo.
echo Checking for GPU type to select appropriate requirements file...
set REQ_FILE=requirements.txt

:: Check for NVIDIA GPU
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected.
    set REQ_FILE=requirements.txt
    goto install_reqs
)

:: Check for AMD GPU
for /f "tokens=*" %%i in ('where amdgpu-pro-install 2^>NUL') do (
    echo AMD GPU detected.
    set REQ_FILE=requirements_amd.txt
    goto install_reqs
)

:: No GPU detected or couldn't determine
echo Could not automatically detect GPU. Using CPU-only requirements.
echo If you have a GPU, you may need to manually specify requirements later.
set REQ_FILE=requirements_cpu_only.txt

:install_reqs
echo.
echo Installing Python requirements from %REQ_FILE%...
pip install -r %REQ_FILE%

:: Now run the original start_windows.bat but with the miniconda hook added
echo.
echo Creating starter script with direct Miniconda hook reference...

:: Create a standalone webui-user.bat file with correct environment paths
echo @echo off > webui-user.bat
echo set PYTHON=%MINICONDA_PATH%\python.exe >> webui-user.bat
echo set GIT= >> webui-user.bat
echo set VENV_DIR= >> webui-user.bat
echo set CUDA_VERSION=11.8 >> webui-user.bat
echo set COMMANDLINE_ARGS= >> webui-user.bat

:: Create a customized run script that activates Miniconda directly
echo @echo off > run_qwen_webui.bat
echo call "%MINICONDA_HOOK%" >> run_qwen_webui.bat
echo python server.py --model "G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf" --loader llama.cpp --api --verbose >> run_qwen_webui.bat

echo.
echo Setup complete!
echo.
echo To run the web UI with your model:
echo 1. Go to the G:\AI\Lyra\oobabooga folder
echo 2. Run run_qwen_webui.bat
echo.
echo This will:
echo - Load your Qwen model automatically
echo - Enable the API for integrations
echo - Start the web interface at http://localhost:7860
echo.
echo For API usage, see: https://github.com/oobabooga/text-generation-webui/wiki/12-%E2%80%90-OpenAI-API
echo.
echo NOTE: On first run, Miniconda will be set up and dependencies will be installed.
echo This may take some time, please be patient.

:end
pause
