@echo off
cd /d %~dp0
echo ==== Comprehensive CUDA Diagnostics ====
echo.

REM Make sure we're using G: drive configuration
call configure_environment.bat

echo Running CUDA verification tool...
python cuda_check.py > cuda_diagnostic_report.txt

echo Checking NVIDIA driver version...
nvidia-smi > nvidia_info.txt

echo Testing torch CUDA availability...
python -c "import torch; print('CUDA Available:', torch.cuda.is_available()); print('Device Count:', torch.cuda.device_count()); print('Current Device:', torch.cuda.current_device()); print('Device Name:', torch.cuda.get_device_name(0))" >> cuda_diagnostic_report.txt

echo Checking if llama-cpp can detect CUDA...
python -c "from llama_cpp import Llama; print('Available GPU Devices:', Llama.get_available_gpu_devices())" >> cuda_diagnostic_report.txt

echo.
echo Diagnostic complete! Results saved to cuda_diagnostic_report.txt and nvidia_info.txt
echo.
echo Press any key to view the diagnostic report...
pause > nul
type cuda_diagnostic_report.txt
echo.
pause
