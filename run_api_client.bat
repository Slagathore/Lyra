@echo off
echo Running API client for Qwen model...
echo.

:: Make sure we have a virtual environment
if not exist "venv" (
  echo Creating new virtual environment...
  python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Make sure requests is installed
pip install requests

:: Run the client
python api_client.py

pause
