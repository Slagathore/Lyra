@echo off
echo Listing available models and scanning for new ones...
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

:: Create the list_models.py script if it doesn't exist
if not exist "list_models.py" (
  echo import sys > list_models.py
  echo from model_config import get_manager >> list_models.py
  echo. >> list_models.py
  echo def format_size(size_gb): >> list_models.py
  echo     if size_gb ^< 1: >> list_models.py
  echo         return f"{size_gb * 1024:.0f} MB" >> list_models.py
  echo     return f"{size_gb:.1f} GB" >> list_models.py
  echo. >> list_models.py
  echo def main(): >> list_models.py
  echo     """List all available models and scan for new ones""" >> list_models.py
  echo     manager = get_manager() >> list_models.py
  echo     active_model = manager.get_active_model() >> list_models.py
  echo. >> list_models.py
  echo     # First scan for any new models >> list_models.py
  echo     new_models = manager.scan_for_new_models() >> list_models.py
  echo     if new_models: >> list_models.py
  echo         print(f"Found {len(new_models)} new models:") >> list_models.py
  echo         for model in new_models: >> list_models.py
  echo             print(f"  - {model.name} ({format_size(model.file_size_gb)})") >> list_models.py
  echo         print() >> list_models.py
  echo. >> list_models.py
  echo     # Print header >> list_models.py
  echo     print(f"{'ACTIVE':^6} {'NAME':40} {'FORMAT':10} {'SIZE':8} {'TYPE':10} {'GPU':4} {'CTX':6}") >> list_models.py
  echo     print("-" * 80) >> list_models.py
  echo. >> list_models.py
  echo     # Print each model >> list_models.py
  echo     for model in manager.models: >> list_models.py
  echo         active_mark = "*" if model.active else "" >> list_models.py
  echo         exists_mark = "✓" if model.file_exists else "✗" >> list_models.py
  echo         name_field = f"{exists_mark} {model.name}" >> list_models.py
  echo         size_field = format_size(model.file_size_gb) >> list_models.py
  echo. >> list_models.py
  echo         print(f"{active_mark:^6} {name_field:40} {model.chat_format:10} " + >> list_models.py
  echo               f"{size_field:8} {model.type:10} {model.n_gpu_layers:4} {model.n_ctx:6}") >> list_models.py
  echo. >> list_models.py
  echo     if not active_model: >> list_models.py
  echo         print("\nNo active model selected!") >> list_models.py
  echo         print("Use 'python select_model.py MODEL_NAME' to select a model") >> list_models.py
  echo     else: >> list_models.py
  echo         print(f"\nCurrent active model: {active_model.name}") >> list_models.py
  echo. >> list_models.py
  echo     print("\nTo change the active model, run:") >> list_models.py
  echo     print("  python select_model.py MODEL_NAME") >> list_models.py
  echo     print("\nTo launch the selected model, run:") >> list_models.py
  echo     print("  run_active_model.bat") >> list_models.py
  echo. >> list_models.py
  echo if __name__ == "__main__": >> list_models.py
  echo     main() >> list_models.py
)

:: Run the list_models.py script
python list_models.py

echo.
pause
