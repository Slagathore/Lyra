@echo off
echo Fixing CUDA setup for Phi-4...
echo.

REM Run diagnostic first
python utils\check_cuda_setup.py
if %ERRORLEVEL% NEQ 0 goto error

REM Uninstall existing torch and related packages
pip uninstall -y torch torchvision torchaudio bitsandbytes

REM Install CUDA-enabled PyTorch
pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121

REM Install other required packages
pip install bitsandbytes --prefer-binary
pip install transformers
pip install accelerate

REM Run diagnostic again to verify
echo.
echo Verifying installation...
python utils\check_cuda_setup.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Setup completed successfully.
    echo You can now try running run_lyra_tray.bat
) else (
    goto error
)

goto end

:error
echo.
echo Error during setup. Please check the error messages above.
pause
exit /b 1

:end
pause