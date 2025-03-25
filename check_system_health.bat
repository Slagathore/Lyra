@echo off
cd /d %~dp0
echo ==== Lyra System Health Check ====
echo.

call lyra_env\Scripts\activate.bat

echo Running comprehensive health check on all components...
echo.

echo 1. Environment:
python -c "import sys; print(f'Python version: {sys.version}')"
python -c "import os; print(f'Current directory: {os.getcwd()}')"
echo.

echo 2. Critical Dependencies:
python -c "import importlib.util; modules = ['torch', 'llama_cpp', 'langchain', 'sqlalchemy']; [print(f'{m}: {'✓ Installed' if importlib.util.find_spec(m) else '✗ Missing'}') for m in modules]"
echo.

echo 3. Model Files:
set MODEL_PATH=G:\AI\Lyra\BigModes\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf
if exist "%MODEL_PATH%" (
    echo ✓ Main LLM model found (%MODEL_PATH%)
) else (
    echo ✗ Main LLM model missing (%MODEL_PATH%)
)
echo.

echo 4. LLM Server:
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 1; Write-Host '✓ LLM server is running' } catch { Write-Host '✗ LLM server is not running' }"
echo.

echo 5. Disk Space:
powershell -Command "Get-PSDrive G | Select-Object Used,Free | ForEach-Object { $usedGB = [math]::Round($_.Used/1GB, 2); $freeGB = [math]::Round($_.Free/1GB, 2); $totalGB = $usedGB + $freeGB; $percentFree = [math]::Round(($_.Free/($_.Used+$_.Free))*100, 1); Write-Host \"Drive G: $usedGB GB used, $freeGB GB free ($percentFree% available)\" }"
echo.

echo 6. GPU Stats:
nvidia-smi --query-gpu=name,memory.used,memory.total,temperature.gpu --format=csv,noheader 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ✗ GPU information unavailable
)
echo.

echo 7. Self-Improvement Module:
if exist "src\lyra\self_improvement" (
    echo ✓ Self-improvement module is installed
    python -c "import sys; sys.path.append('.'); from lyra.self_improvement.reinforcement_learning import VintixRL; rl = VintixRL(); print(f'  - Recorded code changes: {len(rl.experience_data[\"code_changes\"])}'); print(f'  - Feedback entries: {len(rl.experience_data[\"feedback\"])}')" 2>nul
    if %ERRORLEVEL% NEQ 0 (
        echo   ✗ Error loading the module
    )
) else (
    echo ✗ Self-improvement module is not installed
)
echo.

echo 8. Database:
python -c "import sys; sys.path.append('.'); import os; from sqlalchemy import create_engine; from sqlalchemy.exc import SQLAlchemyError; db_path = os.path.join('data', 'lyra.db'); exists = os.path.exists(db_path); print(f'Database file: {'✓ Found' if exists else '✗ Missing'} ({db_path})'); if exists: print(f'  - Size: {os.path.getsize(db_path)/1024:.1f} KB')" 2>nul
echo.

echo Health check complete!
pause
