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
echo ==== Starting GPU-accelerated LLM Server (Fixed Version) ====
echo.

call lyra_env\Scripts\activate.bat

echo Testing llama_cpp module availability...
python -c "import llama_cpp; print('llama-cpp-python is available!')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: llama-cpp-python module not found or not working properly.
    echo Please run fix_llm_errors.bat first to install the required dependencies.
    echo.
    echo Press any key to exit...
    pause
    exit /b 1
)

echo Using reduced parameters for better stability...
set MODEL_PATH=G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf
set GPU_LAYERS=35
set CTX_SIZE=2048
set BATCH_SIZE=128

echo Model: %MODEL_PATH%
echo GPU Layers: %GPU_LAYERS%
echo Context Size: %CTX_SIZE%
echo Batch Size: %BATCH_SIZE%
echo.

echo Starting server...
echo If you encounter CUDA-related errors, try running alternative_gpu_llm.bat instead.
python -m llama_cpp.server --model %MODEL_PATH% --n_gpu_layers %GPU_LAYERS% --n_ctx %CTX_SIZE% --n_batch %BATCH_SIZE%

echo.
echo Server stopped. Press any key to exit...
pause
