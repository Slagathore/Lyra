import llama_cpp 
import sys 
model_path = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf' 
try: 
    model = llama_cpp.Llama(model_path=model_path, verbose=True) 
    print("Model loaded successfully! This version supports Qwen2 architecture.") 
    sys.exit(0) 
except Exception as e: 
    print(f"Error loading model: {e}") 
    if "unknown model architecture: 'qwen2'" in str(e): 
        print("This version does not support the Qwen2 architecture.") 
    sys.exit(1) 
