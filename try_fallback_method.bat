@echo off
echo =============================================
echo Fallback method for running Qwen models
echo =============================================
echo.
echo This script uses a different approach to run your model
echo through the llama-cpp-python REST API server.
echo.

:: Activate the conda environment
call "%UserProfile%\miniconda3\Scripts\activate.bat"
call conda activate llama-env

:: Install dependencies needed for the server
echo Installing required dependencies...
pip install uvicorn fastapi sse-starlette

:: Try multiple versions that support Qwen2 architecture
echo Installing a version that supports Qwen2 architecture...
echo Trying version 0.2.37+cu118...
pip install --prefer-binary --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python==0.2.37+cu118

:: Check if installation was successful
pip show llama-cpp-python >nul 2>&1
if %errorlevel% neq 0 (
    echo First attempt failed, trying newer version...
    pip install --prefer-binary --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python==0.2.26+cu118
    
    :: Check if installation was successful
    pip show llama-cpp-python >nul 2>&1
    if %errorlevel% neq 0 (
        echo All attempts failed, using standard pip install...
        pip install llama-cpp-python
    )
)

:: Create a simple test script to verify if model can be loaded
echo.
echo Testing model architecture compatibility...
echo import llama_cpp > test_model.py
echo import sys >> test_model.py
echo model_path = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf' >> test_model.py
echo try: >> test_model.py
echo     model = llama_cpp.Llama(model_path=model_path, verbose=True) >> test_model.py
echo     print("Model loaded successfully! This version supports Qwen2 architecture.") >> test_model.py
echo     sys.exit(0) >> test_model.py
echo except Exception as e: >> test_model.py
echo     print(f"Error loading model: {e}") >> test_model.py
echo     if "unknown model architecture: 'qwen2'" in str(e): >> test_model.py
echo         print("This version does not support the Qwen2 architecture.") >> test_model.py
echo     sys.exit(1) >> test_model.py

python test_model.py
set MODEL_SUPPORTED=%errorlevel%

:: Start the server if the model loaded successfully
if %MODEL_SUPPORTED% equ 0 (
    echo.
    echo Starting API server...
    echo. 
    echo The API will be available at http://localhost:8000/v1
    echo You can interact with it using the OpenAI-compatible API.
    echo.
    python -m llama_cpp.server --model "G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf" --n-gpu-layers 35 --n-ctx 4096 --host 127.0.0.1 --port 8000
) else (
    echo.
    echo The installed llama-cpp-python version does not support Qwen2 architecture.
    echo.
    echo Alternative options:
    echo 1. Try a different model (non-Qwen2 architecture)
    echo 2. Use a newer version of llama-cpp-python (0.2.37+ or newer)
    echo 3. Use the oobabooga UI instead
)

echo.
echo Server stopped
pause
