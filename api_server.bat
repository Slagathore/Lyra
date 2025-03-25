@echo off
echo ==========================================================
echo Starting API server for Qwen2.5 model with CUDA support
echo ==========================================================
echo.

:: Use local virtual environment
if not exist "venv" (
  echo Creating new virtual environment...
  python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Install known working versions
echo Installing latest server-compatible version...
pip install --force-reinstall --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python==0.2.65+cu118

echo.
echo Starting API Server...
echo The API will be available at http://localhost:8000/v1
echo.
echo Press Ctrl+C to stop the server
echo.

python -m llama_cpp.server --model "G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf" ^
  --n-gpu-layers 35 ^
  --n-batch 512 ^
  --n-ctx 4096 ^
  --host 127.0.0.1 ^
  --port 8000

pause
