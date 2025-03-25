@echo off
echo Starting llama-cpp-python REST API server with active model...
echo.

:: Activate the virtual environment
if exist "venv" (
  call venv\Scripts\activate.bat
) else if exist "lyra_env" (
  call lyra_env\Scripts\activate.bat
) else (
  :: Try conda
  call "%UserProfile%\miniconda3\Scripts\activate.bat"
  call conda activate llama-env 2>nul || call conda activate llama-cuda-env 2>nul
)

:: Create the API server launcher script
echo import sys > api_server.py
echo from model_config import get_manager >> api_server.py
echo import subprocess >> api_server.py
echo. >> api_server.py
echo def main(): >> api_server.py
echo     """Launch the API server with the active model""" >> api_server.py
echo     manager = get_manager() >> api_server.py
echo     active_model = manager.get_active_model() >> api_server.py
echo. >> api_server.py
echo     if not active_model: >> api_server.py
echo         print("No active model found!") >> api_server.py
echo         print("Use 'python select_model.py MODEL_NAME' to select a model") >> api_server.py
echo         return False >> api_server.py
echo. >> api_server.py
echo     if not active_model.file_exists: >> api_server.py
echo         print(f"Error: Model file not found at {active_model.path}") >> api_server.py
echo         return False >> api_server.py
echo. >> api_server.py
echo     print(f"Starting API server with active model: {active_model.name}") >> api_server.py
echo     print(f"Path: {active_model.path}") >> api_server.py
echo     print(f"Using chat format: {active_model.chat_format}") >> api_server.py
echo. >> api_server.py
echo     try: >> api_server.py
echo         import llama_cpp >> api_server.py
echo         # Check if server module exists >> api_server.py
echo         print(f"Using llama-cpp-python version: {llama_cpp.__version__}") >> api_server.py
echo. >> api_server.py
echo         # Install required server dependencies if needed >> api_server.py
echo         try: >> api_server.py
echo             import uvicorn >> api_server.py
echo             import fastapi >> api_server.py
echo         except ImportError: >> api_server.py
echo             print("Installing required server dependencies...") >> api_server.py
echo             subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn", "fastapi", "sse-starlette"]) >> api_server.py
echo. >> api_server.py
echo         # Build the server command >> api_server.py
echo         cmd = [ >> api_server.py
echo             sys.executable, "-m", "llama_cpp.server", >> api_server.py
echo             "--model", active_model.path, >> api_server.py
echo             "--n-gpu-layers", str(active_model.n_gpu_layers), >> api_server.py
echo             "--n-batch", str(active_model.n_batch), >> api_server.py
echo             "--n-ctx", str(active_model.n_ctx), >> api_server.py
echo             "--host", "127.0.0.1", >> api_server.py
echo             "--port", "8000", >> api_server.py
echo             "--chat-format", active_model.chat_format, >> api_server.py
echo             "--verbose" >> api_server.py
echo         ] >> api_server.py
echo. >> api_server.py
echo         print("\nStarting server with command:") >> api_server.py
echo         print(" ".join(cmd)) >> api_server.py 
echo         print("\nAPI will be available at: http://localhost:8000/v1") >> api_server.py
echo         print("Press Ctrl+C to stop the server") >> api_server.py
echo         print() >> api_server.py
echo. >> api_server.py
echo         # Start the server >> api_server.py
echo         subprocess.run(cmd) >> api_server.py
echo         return True >> api_server.py
echo. >> api_server.py
echo     except ImportError: >> api_server.py
echo         print("Error: llama-cpp-python not installed or not accessible") >> api_server.py
echo         return False >> api_server.py
echo     except Exception as e: >> api_server.py
echo         print(f"Error starting API server: {str(e)}") >> api_server.py
echo         return False >> api_server.py
echo. >> api_server.py
echo if __name__ == "__main__": >> api_server.py
echo     main() >> api_server.py

:: Run the API server
python api_server.py

echo.
pause
