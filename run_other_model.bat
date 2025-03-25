@echo off
echo =============================================
echo Running a compatible model with llama-cpp-python
echo =============================================
echo.
echo This script will download and run a model that is compatible
echo with your current version of llama-cpp-python.
echo.

:: Activate the conda environment
call "%UserProfile%\miniconda3\Scripts\activate.bat"
call conda activate llama-env

:: Create models directory if it doesn't exist
if not exist "models" mkdir models

:: Check current version of llama-cpp-python
python -c "import llama_cpp; print('Current llama-cpp-python version:', llama_cpp.__version__)"

echo.
echo Downloading a compatible model...
echo This will download a ~4GB model file (Mistral 7B), please be patient...

:: Only download if file doesn't exist
if not exist "models\mistral-7b-instruct-v0.2.Q4_K_M.gguf" (
    curl -L https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -o models\mistral-7b-instruct-v0.2.Q4_K_M.gguf
) else (
    echo Model file already exists, skipping download.
)

echo.
echo Starting the server with the compatible model...
echo.
echo The API will be available at http://localhost:8000/v1
echo.

:: Install dependencies needed for the server
pip install uvicorn fastapi sse-starlette

:: Start the server
python -m llama_cpp.server --model "models\mistral-7b-instruct-v0.2.Q4_K_M.gguf" --n-gpu-layers 35 --n-ctx 4096 --host 127.0.0.1 --port 8000

echo.
echo Server stopped
pause
