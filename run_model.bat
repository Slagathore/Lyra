@echo off
echo Running Qwen model with CUDA acceleration...
echo.

:: Make sure we have the right version of llama-cpp-python
echo Checking llama-cpp-python version...
python -c "import pkg_resources; print('Current llama-cpp-python version:', pkg_resources.get_distribution('llama-cpp-python').version)"

echo.
echo If the script fails with "unknown model architecture: 'qwen2'", 
echo it will automatically attempt to install a compatible version.
echo.

:: Activate the Conda environment
call "%UserProfile%\miniconda3\Scripts\activate.bat"
call conda activate llama-env

echo Environment activated. Running model...
echo.

:: Run the Python script directly
python "%~dp0chat_model.py"

echo.
echo Session ended.
pause
