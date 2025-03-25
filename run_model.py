import os 
import time 
import llama_cpp 
 
print("Using llama-cpp-python version:", llama_cpp.__version__) 
 
MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf' 
 
print("Loading model...") 
start_time = time.time() 
 
try: 
    model = llama_cpp.Llama( 
        model_path=MODEL_PATH, 
        n_ctx=2048, 
        n_batch=512, 
        n_gpu_layers=35, 
    ) 
    print(f"Model loaded in {time.time() - start_time:.2f} seconds") 
 
    while True: 
        prompt = input("\nEnter prompt (or 'quit' to exit): ") 
        if prompt.lower() == "quit": 
            break 
 
        print("Generating...") 
        gen_start = time.time() 
        output = model.complete(prompt) 
        print(f"Generated in {time.time() - gen_start:.2f} seconds") 
        print("\nOutput:", output) 
 
except Exception as e: 
    print(f"Error: {e}") 
    print("\nPossible solutions:") 
    print("1. Try a different version of llama-cpp-python (0.2.26+cu118, 0.2.65+cu118)") 
    print("2. Run with fewer GPU layers (n_gpu_layers=20)") 
    print("3. Start the API server with api_server.bat instead") 
