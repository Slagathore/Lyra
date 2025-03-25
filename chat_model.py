"""
Simple interactive chat script for llama-cpp-python
"""
import os
import sys
import json
import time
import subprocess

# Try different versions of llama_cpp import
try:
    import llama_cpp
    print(f"Using llama-cpp-python version: {llama_cpp.__version__}")
except ImportError:
    print("Error: llama-cpp-python not installed or not accessible")
    sys.exit(1)

# Model path
MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf'

def install_compatible_version():
    """Attempt to install a version of llama-cpp-python that supports Qwen2"""
    print("\nAttempting to install a more recent version of llama-cpp-python with Qwen2 support...")
    
    # Try to uninstall current version
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "llama-cpp-python"])
    
    # Try to install a newer version with Qwen2 support
    result = subprocess.run([
        sys.executable, 
        "-m", 
        "pip", 
        "install", 
        "--prefer-binary",
        "--extra-index-url", 
        "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118",
        "llama-cpp-python==0.2.65+cu118"  # This version supports Qwen2
    ])
    
    if result.returncode == 0:
        print("Successfully installed llama-cpp-python 0.2.65+cu118")
        print("Please restart the script")
    else:
        # Try one more recent version
        result = subprocess.run([
            sys.executable, 
            "-m", 
            "pip", 
            "install", 
            "--prefer-binary",
            "--extra-index-url", 
            "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118",
            "llama-cpp-python==0.2.37+cu118"  # Alternative version
        ])
        
        if result.returncode == 0:
            print("Successfully installed llama-cpp-python 0.2.37+cu118")
            print("Please restart the script")
        else:
            print("Failed to install a compatible version")
    
    sys.exit(1)

def main():
    print('Loading model...')
    start_time = time.time()
    
    try:
        # Create model with CUDA acceleration and specify chat_format
        model = llama_cpp.Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,         # Context window size
            n_batch=512,        # Batch size for prompt processing
            n_gpu_layers=35,    # Number of layers to offload to GPU
            verbose=True,       # Show detailed loading info
            chat_format="chatml"  # Specify the chat format for Qwen models
        )
        
        print(f'Model loaded in {time.time() - start_time:.2f} seconds')
        
        # Basic chatbot loop
        print('\n===== Qwen 2.5 Chat =====')
        print('Type your messages and press Enter. Type "quit" to exit.')
        print()
        
        while True:
            user_input = input('You: ')
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
                
            # Generate response
            print('AI: ', end='', flush=True)
            start_time = time.time()
            
            try:
                # Stream the output token by token
                response = model.create_chat_completion(
                    messages=[
                        {'role': 'user', 'content': user_input}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    stream=True
                )
                
                # Print the streaming response
                full_response = ''
                for chunk in response:
                    if 'content' in chunk['choices'][0]['delta']:
                        content = chunk['choices'][0]['delta']['content']
                        print(content, end='', flush=True)
                        full_response += content
                
                print(f'\n[Generated {len(full_response)} chars in {time.time() - start_time:.2f} seconds]')
                print()
            
            except Exception as e:
                print(f"\nError generating response: {str(e)}")
                print("Trying to continue...")
    
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        if "unknown model architecture: 'qwen2'" in str(e) or "failed to load model" in str(e):
            print("\nError: Your version of llama-cpp-python doesn't support the Qwen2 architecture")
            install_compatible_version()

if __name__ == "__main__":
    main()
