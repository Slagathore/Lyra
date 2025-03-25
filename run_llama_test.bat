@echo off
echo Running llama-cpp-python test with CUDA...
echo.

:: Activate the conda environment
call "%UserProfile%\miniconda3\Scripts\activate.bat"
call conda activate llama-env

:: Run the test script
python llama_cpp_test.py

echo.
pause
