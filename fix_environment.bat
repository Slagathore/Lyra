@echo off
echo ===================================
echo Fixing environment for Llama-cpp
echo ===================================
echo.

:: Check which Python environment we're using
echo Checking Python environment...
where python
python --version
echo.

:: Check if we have a lyra_env directory
if exist "lyra_env" (
    echo Found local environment at lyra_env. Activating...
    call lyra_env\Scripts\activate.bat
) else (
    echo No local environment found. Checking for conda...
    
    :: Check for conda/miniconda
    where conda >nul 2>&1
    if %errorlevel% equ 0 (
        echo Conda found. Activating llama-env...
        call conda activate llama-env
        if %errorlevel% neq 0 (
            echo Failed to activate conda environment. Creating new one...
            call conda create -y -n llama-env python=3.10
            call conda activate llama-env
        )
    ) else (
        echo Neither conda nor local environment found. Creating local venv...
        python -m venv lyra_env
        call lyra_env\Scripts\activate.bat
    )
)

echo.
echo Current Python: 
where python
echo.

:: Install llama-cpp-python
echo Installing llama-cpp-python...
pip install llama-cpp-python

:: Try pre-built wheels if installation failed
pip show llama-cpp-python >nul 2>&1
if %errorlevel% neq 0 (
    echo Standard installation failed. Trying pre-built wheels...
    pip install --prefer-binary --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python
)

:: Verify installation
echo.
echo Verifying installation...
python -c "import llama_cpp; print(f'Successfully installed llama-cpp-python version: {llama_cpp.__version__}')"

:: Create a helper script to activate this environment in the future
echo.
echo Creating activation script...
echo @echo off > activate_llama_env.bat
echo echo Activating llama-cpp environment... >> activate_llama_env.bat

:: Add the appropriate activation command based on what worked
if exist "lyra_env" (
    echo call "%~dp0lyra_env\Scripts\activate.bat" >> activate_llama_env.bat
) else (
    echo call conda activate llama-env >> activate_llama_env.bat
)

echo echo Environment activated. Run Python scripts with this environment now. >> activate_llama_env.bat
echo cmd /k >> activate_llama_env.bat

echo.
echo Environment setup complete!
echo In the future, run activate_llama_env.bat before running your scripts.
echo.

pause
