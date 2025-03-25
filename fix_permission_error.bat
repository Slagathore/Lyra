@echo off
echo Fixing permission error during package installation...
echo.

:: Run as admin
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if %errorlevel% NEQ 0 (
    echo This script needs to be run as administrator.
    echo Please right-click on the script and select 'Run as administrator'
    goto end
)

echo Re-installing packages with administrator privileges...
echo.

:: Change to directory with venv
cd G:\AI\Lyra

:: Activate environment
call lyra_env\Scripts\activate

:: Install packages that failed with proper permissions
echo Installing gradio...
pip install --force-reinstall gradio==4.37.2

echo.
echo Installing datasets...
pip install --force-reinstall datasets

echo.
echo Installing altair...
pip install --force-reinstall altair==5.5.0

:: Check llama-cpp-python installation
echo.
echo Verifying llama-cpp-python installation:
pip show llama-cpp-python
if %errorlevel% NEQ 0 (
    echo llama-cpp-python not found, reinstalling...
    pip install llama-cpp-python-cuda==0.3.8+cu121
) else (
    echo llama-cpp-python is installed.
)

:: Check llama-cpp-python-cuda installation
echo.
echo Verifying llama-cpp-python-cuda installation:
pip show llama-cpp-python-cuda
if %errorlevel% NEQ 0 (
    echo llama-cpp-python-cuda not found, reinstalling...
    pip install llama-cpp-python-cuda==0.3.8+cu121 --force-reinstall
) else (
    echo llama-cpp-python-cuda is installed.
)

echo.
echo Installation completed.
echo You can now return to the oobabooga setup.

:end
pause
