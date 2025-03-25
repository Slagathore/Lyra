@echo off
echo =====================================================
echo Testing different chat formats with Qwen model
echo =====================================================
echo.

:: Activate the Conda environment
call "%UserProfile%\miniconda3\Scripts\activate.bat"
call conda activate llama-env

:: Create a test script
echo import llama_cpp > test_formats.py
echo import sys >> test_formats.py
echo. >> test_formats.py
echo MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf' >> test_formats.py
echo TEST_PROMPT = "Write a short haiku about coding." >> test_formats.py
echo. >> test_formats.py
echo def test_chat_format(format_name): >> test_formats.py
echo     print(f"\n\nTesting chat format: {format_name}") >> test_formats.py
echo     print("-" * 50) >> test_formats.py
echo     try: >> test_formats.py
echo         model = llama_cpp.Llama( >> test_formats.py
echo             model_path=MODEL_PATH, >> test_formats.py
echo             n_ctx=2048, >> test_formats.py
echo             n_batch=512, >> test_formats.py
echo             n_gpu_layers=35, >> test_formats.py
echo             chat_format=format_name, >> test_formats.py
echo             verbose=False >> test_formats.py
echo         ) >> test_formats.py
echo. >> test_formats.py
echo         # Test with chat completion API >> test_formats.py
echo         print(f"Generating response with '{format_name}' format...") >> test_formats.py
echo         response = model.create_chat_completion( >> test_formats.py
echo             messages=[ >> test_formats.py
echo                 {"role": "user", "content": TEST_PROMPT} >> test_formats.py
echo             ], >> test_formats.py
echo             temperature=0.7, >> test_formats.py
echo             max_tokens=500 >> test_formats.py
echo         ) >> test_formats.py
echo         print("\nResponse:") >> test_formats.py
echo         print(response["choices"][0]["message"]["content"]) >> test_formats.py
echo         return True >> test_formats.py
echo     except Exception as e: >> test_formats.py
echo         print(f"Error with format '{format_name}': {e}") >> test_formats.py
echo         return False >> test_formats.py
echo. >> test_formats.py
echo # List of formats to try >> test_formats.py
echo formats = [ >> test_formats.py
echo     "chatml",        # OpenAI style, common for newer models >> test_formats.py
echo     "llama-2",       # Meta's Llama-2 format >> test_formats.py
echo     "mistral",       # Mistral format >> test_formats.py
echo     "vicuna",        # Vicuna format >> test_formats.py
echo     "alpaca",        # Alpaca format >> test_formats.py
echo     "baichuan",      # Baichuan (closer to Chinese models) >> test_formats.py
echo     "qwen",          # Specific Qwen format >> test_formats.py
echo     "openchat",      # OpenChat format >> test_formats.py
echo     None             # No specific format >> test_formats.py
echo ] >> test_formats.py
echo. >> test_formats.py
echo # Try each format until one works >> test_formats.py
echo print("Testing different chat formats with your Qwen model...") >> test_formats.py
echo successful_formats = [] >> test_formats.py
echo. >> test_formats.py
echo for fmt in formats: >> test_formats.py
echo     success = test_chat_format(fmt) >> test_formats.py
echo     if success: >> test_formats.py
echo         successful_formats.append(fmt) >> test_formats.py
echo. >> test_formats.py
echo print("\n\nSUMMARY:") >> test_formats.py
echo print("-" * 50) >> test_formats.py
echo if successful_formats: >> test_formats.py
echo     print(f"Successful formats: {', '.join(str(f) for f in successful_formats)}") >> test_formats.py
echo     print(f"\nRecommended format: {successful_formats[0]}") >> test_formats.py
echo     print("\nAdd this format in your scripts:") >> test_formats.py
echo     print(f'model = llama_cpp.Llama(model_path=MODEL_PATH, chat_format="{successful_formats[0]}")') >> test_formats.py
echo     print("\nOr when running the server:") >> test_formats.py
echo     print(f'python -m llama_cpp.server --model "path/to/model.gguf" --chat_format {successful_formats[0]}') >> test_formats.py
echo else: >> test_formats.py
echo     print("No successful formats found. Try upgrading llama-cpp-python to a version that supports Qwen2 architecture.") >> test_formats.py

echo.
echo Running chat format tests...
python test_formats.py

echo.
echo Test complete! Check the results above to find the best format.
echo See chat_formats.md for more information on available formats.
pause
