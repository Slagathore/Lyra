@echo off
echo =====================================================
echo Running Qwen with latest compatible llama-cpp version
echo =====================================================
echo.

:: Use local virtual environment instead of conda
if not exist "venv" (
  echo Creating new virtual environment...
  python -m venv venv
)

:: Activate the virtual environment
call venv\Scripts\activate.bat

:: Install a known compatible version
echo Installing known working version of llama-cpp-python...
pip install --force-reinstall --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118 llama-cpp-python==0.2.37+cu118

:: Create a simple test script
echo import os > run_model.py
echo import time >> run_model.py
echo import llama_cpp >> run_model.py
echo. >> run_model.py
echo print("Using llama-cpp-python version:", llama_cpp.__version__) >> run_model.py
echo. >> run_model.py
echo MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf' >> run_model.py
echo. >> run_model.py
echo print("Loading model...") >> run_model.py
echo start_time = time.time() >> run_model.py
echo. >> run_model.py
echo try: >> run_model.py
echo     model = llama_cpp.Llama( >> run_model.py
echo         model_path=MODEL_PATH, >> run_model.py
echo         n_ctx=2048, >> run_model.py
echo         n_batch=512, >> run_model.py
echo         n_gpu_layers=35, >> run_model.py
echo     ) >> run_model.py
echo     print(f"Model loaded in {time.time() - start_time:.2f} seconds") >> run_model.py
echo. >> run_model.py
echo     while True: >> run_model.py
echo         prompt = input("\nEnter prompt (or 'quit' to exit): ") >> run_model.py
echo         if prompt.lower() == "quit": >> run_model.py
echo             break >> run_model.py
echo. >> run_model.py
echo         print("Generating...") >> run_model.py
echo         gen_start = time.time() >> run_model.py
echo         output = model.complete(prompt) >> run_model.py
echo         print(f"Generated in {time.time() - gen_start:.2f} seconds") >> run_model.py
echo         print("\nOutput:", output) >> run_model.py
echo. >> run_model.py
echo except Exception as e: >> run_model.py
echo     print(f"Error: {e}") >> run_model.py
echo     print("\nPossible solutions:") >> run_model.py
echo     print("1. Try a different version of llama-cpp-python (0.2.26+cu118, 0.2.65+cu118)") >> run_model.py
echo     print("2. Run with fewer GPU layers (n_gpu_layers=20)") >> run_model.py
echo     print("3. Start the API server with api_server.bat instead") >> run_model.py

:: Run the script
echo.
echo Running model...
python run_model.py

pause
