@echo off
cd /d %~dp0
echo ====== COMPLETE CUDA FIX FOR STANDARD C: DRIVE INSTALLATION ======
echo.
echo This script will fix all CUDA-related issues:
echo 1. Update environment configuration to use CUDA 12.8 from C: drive
echo 2. Configure paths and environment variables
echo 3. Install CUDA-compatible packages
echo 4. Rebuild llama-cpp-python with proper CUDA support
echo 5. Test CUDA functionality
echo.
echo Press any key to start...
pause > nul

echo.
echo Step 1: Creating correct environment configuration...
python update_cuda_environment.py

echo.
echo Step 2: Setting up CUDA environment...
call setup_cuda_env.bat

echo.
echo Step 3: Creating CUDA configuration file...
echo Creating lyra_cuda_config.json...
(
echo {
echo   "cuda": {
echo     "path": "%CUDA_PATH%",
echo     "version": "%CUDA_PATH:~-5%",
echo     "enabled": true,
echo     "bin_path": "%CUDA_PATH%\\bin",
echo     "nvcc_path": "%CUDA_PATH%\\bin\\nvcc.exe",
echo     "cudnn_path": "%CUDA_PATH%\\lib\\x64"
echo   },
echo   "llama_cpp": {
echo     "cuda_layers": 35,
echo     "env_vars": {
echo       "GGML_CUDA_NO_PINNED": "1",
echo       "GGML_CUDA_FORCE_MMQ": "1",
echo       "GGML_CUDA_MEM_PERCENT": "90"
echo     }
echo   }
echo }
) > lyra_cuda_config.json
echo Configuration file created.

echo.
echo Step 4: Activating Python environment...
call lyra_env\Scripts\activate.bat

echo.
echo Step 5: Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --no-cache-dir

echo.
echo Step 6: Installing pre-built CUDA llama-cpp-python...
pip uninstall -y llama-cpp-python
pip install llama-cpp-python==0.2.38+cu121 --no-cache-dir --force-reinstall --extra-index-url https://download.pytorch.org/whl/cu121

echo.
echo Step 7: Testing PyTorch CUDA...
python -c "import torch; print('PyTorch CUDA available:', torch.cuda.is_available()); print('Device count:', torch.cuda.device_count()); print('Device name:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

echo.
echo Step 8: Testing llama-cpp-python CUDA...
python -c "from llama_cpp import Llama; print('Available GPU devices:', Llama.get_available_gpu_devices())"

echo.
echo Step 9: Running comprehensive CUDA diagnostics...
python cuda_check.py > cuda_diagnostic_report_after_fix.txt

echo.
echo ====== CUDA FIX PROCEDURE COMPLETE ======
echo.
echo If you see GPU devices listed above, your CUDA setup is working correctly.
echo If not, please run rebuild_llama_cpp_cuda.bat to try a different installation method.
echo.
echo Diagnostic results have been saved to cuda_diagnostic_report_after_fix.txt
echo.
pause
