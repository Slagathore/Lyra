@echo off
cd /d %~dp0
echo ==== Updating Batch Files for CUDA 12.8 Support ====
echo.

REM List of batch files to update
set BATCH_FILES=run_gpu_llm_fixed.bat run_lyra_complete.bat alternative_gpu_llm.bat check_cuda_install.bat run_with_self_improvement.bat

echo Updating the following batch files:
for %%F in (%BATCH_FILES%) do (
    echo - %%F
)

echo.
echo Applying changes...

for %%F in (%BATCH_FILES%) do (
    echo Processing %%F...
    
    REM Create a temporary file with updated content
    (
        echo @echo off
        echo cd /d %%~dp0
        echo REM Set up CUDA 12.8 environment
        echo set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
        echo set "CUDA_HOME=%%CUDA_PATH%%"
        echo set "PATH=%%CUDA_PATH%%\bin;%%CUDA_PATH%%\libnvvp;%%PATH%%"
        echo set "GGML_CUDA_NO_PINNED=1"
        echo set "GGML_CUDA_FORCE_MMQ=1"
        echo set "GGML_CUDA_MEM_PERCENT=90"
        echo.
        echo REM Original script content follows
        type %%F | find /v "@echo off"
    ) > %%F.new
    
    REM Replace the original file
    move /y %%F.new %%F
)

echo.
echo All batch files have been updated with CUDA 12.8 environment variables.
echo.
pause
