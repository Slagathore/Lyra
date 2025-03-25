@echo off
echo Running model with environment verification...
echo.

:: First run the installation check/fix script
echo Checking Python environment and installing packages if needed...
python install_packages.py

:: Check if the installation was successful
python -c "import llama_cpp; exit(0)" >nul 2>&1
if %errorlevel% neq 0 (
    echo Failed to install llama_cpp.
    echo Please run fix_environment.bat before running this script.
    pause
    exit /b 1
)

:: Run the model
echo.
echo Running chat model...
python chat_model.py

pause
