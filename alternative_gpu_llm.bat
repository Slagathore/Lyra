@echo off
cd /d %~dp0
REM Set up CUDA environment
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
set "CUDA_HOME=%CUDA_PATH%"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"
set "GGML_CUDA_NO_PINNED=1"
set "GGML_CUDA_FORCE_MMQ=1"
set "GGML_CUDA_MEM_PERCENT=90"

REM Original content below
cd /d %~dp0
echo ==== Starting Alternative GPU-accelerated LLM Server ====
echo.

call lyra_env\Scripts\activate.bat

echo This script will try to run the server using a different approach.
echo Using the most compatible settings for stability...

set MODEL_PATH=G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf

echo Model: %MODEL_PATH%
echo.

echo Starting server with minimal GPU parameters...
echo.

REM Attempt to use CPU fallback if CUDA isn't working properly
echo Setting environment variables to force CPU fallback if needed...
set GGML_CUDA_NO_PINNED=1
set CUDA_VISIBLE_DEVICES=0

echo Starting server... (This may take some time to initialize)

REM Try using server.py directly if available
if exist "models\server.py" (
    python "models\server.py" --model "%MODEL_PATH%" --cpu
) else (
    REM Try direct llama-cpp-python with proper path escaping
    python -c "from llama_cpp import Llama; model = Llama(r'%MODEL_PATH%', n_ctx=2048, verbose=False); from llama_cpp.server.app import create_app; app = create_app(model); import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8000)"
)

echo.
echo Server stopped. Press any key to exit...
pause
