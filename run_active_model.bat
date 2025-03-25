@echo off
echo Running currently active model...
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

:: Create the launcher script
echo import os > launcher.py
echo import sys >> launcher.py
echo import subprocess >> launcher.py
echo from model_config import get_manager >> launcher.py
echo. >> launcher.py
echo def main(): >> launcher.py
echo     """Launch the currently active model""" >> launcher.py
echo     manager = get_manager() >> launcher.py
echo     active_model = manager.get_active_model() >> launcher.py
echo. >> launcher.py
echo     if not active_model: >> launcher.py
echo         print("No active model found!") >> launcher.py
echo         print("Use 'python select_model.py MODEL_NAME' to select a model") >> launcher.py
echo         return False >> launcher.py
echo. >> launcher.py
echo     if not active_model.file_exists: >> launcher.py
echo         print(f"Error: Model file not found at {active_model.path}") >> launcher.py
echo         return False >> launcher.py
echo. >> launcher.py
echo     print(f"Launching active model: {active_model.name}") >> launcher.py
echo     print(f"Path: {active_model.path}") >> launcher.py
echo     print(f"Using chat format: {active_model.chat_format}") >> launcher.py
echo. >> launcher.py
echo     try: >> launcher.py
echo         # Import and create model >> launcher.py
echo         import llama_cpp >> launcher.py
echo         print(f"Using llama-cpp-python version: {llama_cpp.__version__}") >> launcher.py
echo. >> launcher.py
echo         print("Loading model...") >> launcher.py
echo         model = llama_cpp.Llama( >> launcher.py
echo             model_path=active_model.path, >> launcher.py
echo             n_ctx=active_model.n_ctx, >> launcher.py
echo             n_batch=active_model.n_batch, >> launcher.py
echo             n_gpu_layers=active_model.n_gpu_layers, >> launcher.py
echo             chat_format=active_model.chat_format, >> launcher.py
echo             verbose=True >> launcher.py
echo         ) >> launcher.py
echo. >> launcher.py
echo         print("Model loaded successfully!") >> launcher.py
echo         print("Starting chat session...") >> launcher.py
echo         print() >> launcher.py
echo         print("=" * 50) >> launcher.py
echo         print(f" {active_model.name} Chat") >> launcher.py
echo         print("=" * 50) >> launcher.py
echo         print("Type your messages and press Enter. Type 'quit' to exit.") >> launcher.py
echo         print() >> launcher.py
echo. >> launcher.py
echo         # Start chat loop >> launcher.py
echo         import time >> launcher.py
echo         while True: >> launcher.py
echo             user_input = input('You: ') >> launcher.py
echo             if user_input.lower() in ['quit', 'exit', 'q']: >> launcher.py
echo                 break >> launcher.py
echo. >> launcher.py
echo             # Generate response >> launcher.py
echo             print('AI: ', end='', flush=True) >> launcher.py
echo             start_time = time.time() >> launcher.py
echo. >> launcher.py
echo             try: >> launcher.py
echo                 # Stream the output token by token >> launcher.py
echo                 response = model.create_chat_completion( >> launcher.py
echo                     messages=[ >> launcher.py
echo                         {'role': 'user', 'content': user_input} >> launcher.py
echo                     ], >> launcher.py
echo                     temperature=0.7, >> launcher.py
echo                     max_tokens=2000, >> launcher.py
echo                     stream=True >> launcher.py
echo                 ) >> launcher.py
echo. >> launcher.py
echo                 # Print the streaming response >> launcher.py
echo                 full_response = '' >> launcher.py
echo                 for chunk in response: >> launcher.py
echo                     if 'content' in chunk['choices'][0]['delta']: >> launcher.py
echo                         content = chunk['choices'][0]['delta']['content'] >> launcher.py
echo                         print(content, end='', flush=True) >> launcher.py
echo                         full_response += content >> launcher.py
echo. >> launcher.py
echo                 print(f'\n[Generated {len(full_response)} chars in {time.time() - start_time:.2f} seconds]') >> launcher.py
echo                 print() >> launcher.py
echo             except Exception as e: >> launcher.py
echo                 print(f"\nError generating response: {str(e)}") >> launcher.py
echo                 print("This could be due to incompatibility between the model and llama-cpp-python version.") >> launcher.py
echo                 print("Try a different model or update llama-cpp-python.") >> launcher.py
echo. >> launcher.py
echo         return True >> launcher.py
echo. >> launcher.py
echo     except ImportError: >> launcher.py
echo         print("Error: llama-cpp-python not installed or not accessible") >> launcher.py
echo         return False >> launcher.py
echo     except Exception as e: >> launcher.py
echo         print(f"Error loading model: {str(e)}") >> launcher.py
echo         if "unknown model architecture" in str(e).lower(): >> launcher.py
echo             print("\nThis error occurs when your llama-cpp-python version doesn't support this model architecture.") >> launcher.py
echo             print("Try running: pip install --upgrade llama-cpp-python") >> launcher.py
echo         return False >> launcher.py
echo. >> launcher.py
echo if __name__ == "__main__": >> launcher.py
echo     success = main() >> launcher.py
echo     if not success: >> launcher.py
echo         print("\nFailed to run the model. Consider using the API server instead:") >> launcher.py
echo         print("  run_api_server.bat") >> launcher.py

:: Run the launcher script
python launcher.py

echo.
pause
