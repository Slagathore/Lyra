@echo off
echo Checking GPU and CUDA configuration...
echo.

:: Make sure we have a virtual environment
if not exist "venv" (
  echo Creating new virtual environment...
  python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Run the GPU check
python check_gpu.py

pause
