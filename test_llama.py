import os
import sys

def check_environment():
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}\n")
    
    # Test PyTorch with CUDA
    try:
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available for PyTorch: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
            print(f"GPU device: {torch.cuda.get_device_name(0)}\n")
        else:
            print("CUDA not available for PyTorch\n")
    except ImportError:
        print("PyTorch is not installed\n")
    
    # Test llama-cpp-python with CUDA
    try:
        import llama_cpp
        print(f"llama-cpp-python version: {llama_cpp.__version__}")
        
        # Check CUDA support in llama-cpp
        llama_methods = dir(llama_cpp.Llama)
        print("CUDA methods in llama_cpp.Llama:")
        cuda_methods = [m for m in llama_methods if 'cuda' in m.lower()]
        if cuda_methods:
            for method in cuda_methods:
                print(f"  - {method}")
            print("\nllama-cpp-python appears to have CUDA support")
        else:
            print("llama-cpp-python might not have CUDA support enabled\n")
    except ImportError:
        print("llama-cpp-python is not installed\n")

if __name__ == "__main__":
    check_environment()
