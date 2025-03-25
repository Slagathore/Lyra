@echo off
echo Running oobabooga web UI with already installed llama-cpp-python...
echo.

:: Change to oobabooga directory
cd "%~dp0oobabooga"

:: Check if run_qwen_webui.bat exists
if not exist "run_qwen_webui.bat" (
    echo ERROR: run_qwen_webui.bat not found in oobabooga directory
    echo Please run setup_oobabooga.bat first
    goto end
)

echo Creating diagnostic script...
echo @echo off > check_llama_cpp.bat
echo echo Checking if llama-cpp-python is installed... >> check_llama_cpp.bat
echo call "%UserProfile%\miniconda3\Scripts\activate.bat" >> check_llama_cpp.bat
echo python -c "import os; os.environ['CUDA_VISIBLE_DEVICES']='0'; import llama_cpp; print('llama-cpp-python version:', llama_cpp.__version__); print('Module path:', llama_cpp.__file__); print('Has CUDA support:', any('cuda' in attr.lower() for attr in dir(llama_cpp.Llama)))" >> check_llama_cpp.bat

:: Create modified webui starter script that sets CUDA device
echo @echo off > run_qwen_cuda.bat
echo echo Setting CUDA_VISIBLE_DEVICES to use first GPU... >> run_qwen_cuda.bat
echo set CUDA_VISIBLE_DEVICES=0 >> run_qwen_cuda.bat
echo call "%UserProfile%\miniconda3\Scripts\activate.bat" >> run_qwen_cuda.bat
echo python server.py --model "G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf" --loader llama.cpp --n-gpu-layers 50 --threads 8 --n_batch 512 --n-ctx 4096 --api --verbose >> run_qwen_cuda.bat

echo.
echo Running llama-cpp-python check...
call check_llama_cpp.bat

echo.
echo You have the following options:
echo 1. Run the web UI with custom GPU parameters
echo 2. Check CUDA installation details
echo.

set /p option="Enter option (1 or 2): "

if "%option%"=="1" (
    echo.
    echo Running web UI with GPU acceleration...
    call run_qwen_cuda.bat
) else if "%option%"=="2" (
    echo.
    echo Checking CUDA installation...
    cd ..
    python check_llama_cpp_installation.py
    echo.
    echo Now you can return to the oobabooga directory and run run_qwen_cuda.bat
) else (
    echo Invalid option
)

:end
pause
