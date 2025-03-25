@echo off
cd /d %~dp0
echo ==== Configuring Lyra Environment ====
echo.

REM Set environment variables to ensure G: drive usage for Lyra
set PYTHONPATH=G:\AI\Lyra;G:\AI\Lyra\src;%PYTHONPATH%
set PYTHONHOME=G:\AI\Lyra\lyra_env
set TEMP=G:\AI\Lyra\temp
set TMP=G:\AI\Lyra\temp

REM Set CUDA paths for standard C: drive installation
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
set "CUDA_HOME=%CUDA_PATH%"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"

REM Create temp directory if it doesn't exist
if not exist "temp" mkdir temp

REM Create configuration to ensure correct paths
echo Creating custom environment configuration...
(
echo {
echo   "root_path": "G:\\AI\\Lyra",
echo   "model_path": "G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf",
echo   "data_path": "G:\\AI\\Lyra\\data",
echo   "logs_path": "G:\\AI\\Lyra\\logs",
echo   "temp_path": "G:\\AI\\Lyra\\temp",
echo   "cuda_path": "%CUDA_PATH%",
echo   "use_c_drive_cuda": true
echo }
) > env_config.json

echo Environment configured for G: drive usage with C: drive CUDA!
echo.
echo Add this line to the beginning of your batch files:
echo call configure_environment.bat
echo.
echo Press any key to exit...
pause
