"""
Test script for llama-cpp-python with CUDA support
"""
import os
import time
import llama_cpp
from pathlib import Path

MODEL_PATH = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf'

def print_section(title):
    print(f"\n{'-' * 50}")
    print(f" {title}")
    print(f"{'-' * 50}")

def main():
    print_section("LLAMA-CPP-PYTHON TEST")
    print(f"Using llama-cpp-python version: {llama_cpp.__version__}")
    print(f"Module location: {llama_cpp.__file__}")
    
    # Check CUDA support
    print_section("CUDA SUPPORT CHECK")
    cuda_attrs = [attr for attr in dir(llama_cpp.Llama) if 'cuda' in attr.lower() or 'gpu' in attr.lower()]
    if cuda_attrs:
        print("CUDA related attributes found in llama_cpp.Llama:")
        for attr in cuda_attrs:
            print(f"  - {attr}")
        print("\n✅ CUDA support is available")
    else:
        print("❌ No CUDA attributes found - CUDA support might not be enabled")
        print("Check your installation with: pip show llama-cpp-python")
    
    # Check model file
    print_section("MODEL FILE CHECK")
    model_path = Path(MODEL_PATH)
    
    if not model_path.exists():
        print(f"❌ Model file not found at: {MODEL_PATH}")
        return
    
    print(f"✅ Model file found: {model_path.name}")
    print(f"   Size: {model_path.stat().st_size / 1024 / 1024 / 1024:.2f} GB")
    
    # Test model loading and inference
    print_section("LOADING MODEL WITH CUDA")
    print("Loading model... (this may take a minute)")
    print("Model path:", MODEL_PATH)
    
    # Create parameters with CUDA enabled
    params = {
        "model_path": MODEL_PATH,
        "n_ctx": 2048,
        "n_batch": 512,
        "n_gpu_layers": 35,  # Adjust based on your VRAM
        "seed": 42,
        "use_mlock": False
    }
    
    start_time = time.time()
    try:
        # Load the model
        print("Creating model with parameters:", params)
        model = llama_cpp.Llama(**params)
        
        load_time = time.time() - start_time
        print(f"✅ Model loaded successfully in {load_time:.2f} seconds")
        
        # Simple generation test
        print_section("GENERATING TEXT")
        prompt = "Write a short poem about artificial intelligence:"
        print(f"Prompt: {prompt}\n")
        
        start_time = time.time()
        output = model.generate(
            prompt,
            max_tokens=100,
            temperature=0.7,
            top_p=0.95,
            repeat_penalty=1.1,
            top_k=40
        )
        
        # Print output
        print(output['choices'][0]['text'])
        gen_time = time.time() - start_time
        print(f"\nGeneration completed in {gen_time:.2f} seconds")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTry adjusting n_gpu_layers or other parameters based on your GPU's VRAM")

if __name__ == "__main__":
    main()
