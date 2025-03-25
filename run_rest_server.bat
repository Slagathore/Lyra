@echo off
echo Starting llama-cpp-python REST API server...
echo This will provide an OpenAI-compatible API at http://localhost:8000
echo.

:: Activate the Conda environment
call "%UserProfile%\miniconda3\Scripts\activate.bat"
call conda activate llama-env

:: Check if llama-cpp-python is properly installed
python -c "import llama_cpp; print(f'Using llama-cpp-python version {llama_cpp.__version__}')"
if %ERRORLEVEL% NEQ 0 goto error

:: Run the server
echo Starting server with GPU acceleration...
echo API will be available at: http://localhost:8000/v1
echo.
echo Press Ctrl+C to stop the server
echo.

python -m llama_cpp.server --model "G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf" ^
  --n_gpu_layers 35 ^
  --n_batch 512 ^
  --n_ctx 4096 ^
  --host 127.0.0.1 ^
  --port 8000 ^
  --chat_format chatml ^
  --verbose

goto end

:error
echo.
echo Error: llama-cpp-python is not installed correctly.
echo Please run setup_llama_cuda_simplified.bat first.

:end
pause
