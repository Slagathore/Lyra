"""
Check if llama-cpp-python is correctly installed with CUDA support
"""
import importlib
import subprocess
import sys
from pathlib import Path
import os

def print_separator():
    print("-" * 60)

def run_cmd(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error running command: {e}"

print("Checking llama-cpp-python installation with CUDA support\n")
print_separator()

# Check Python environment
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print_separator()

# Check for PyTorch with CUDA
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        device_count = torch.cuda.device_count()
        print(f"CUDA device count: {device_count}")
        for i in range(device_count):
            print(f"CUDA device {i}: {torch.cuda.get_device_name(i)}")
        print(f"CUDA version: {torch.version.cuda}")
    else:
        print("CUDA not available for PyTorch")
except ImportError:
    print("PyTorch not installed")
print_separator()

# Check for llama-cpp-python
try:
    import llama_cpp
    print(f"llama_cpp version: {llama_cpp.__version__}")
    print(f"llama_cpp location: {llama_cpp.__file__}")
    
    # Check if CUDA is available in llama_cpp
    # Inspect for CUDA methods or attributes
    has_cuda_attrs = [attr for attr in dir(llama_cpp.Llama) if 'cuda' in attr.lower()]
    if has_cuda_attrs:
        print("CUDA-related attributes found in llama_cpp.Llama:")
        for attr in has_cuda_attrs:
            print(f"  - {attr}")
    else:
        print("No CUDA-related attributes found in llama_cpp.Llama")
    
    # Try to check backend compiled options by creating a minimal model
    # Note: This won't actually load a model, just check the class
    try:
        model_options = llama_cpp.Llama.__init__.__code__.co_varnames
        print("\nSupported model options:")
        print(", ".join(model_options))
    except:
        print("\nCould not inspect model options")
except ImportError:
    print("llama-cpp-python not installed")
print_separator()

# Check installed packages
print("Installed Python packages related to llama-cpp:")
pip_list = run_cmd(f"{sys.executable} -m pip list")
llama_packages = [line for line in pip_list.split('\n') if 'llama' in line.lower()]
for pkg in llama_packages:
    print(f"  {pkg}")
print_separator()

# Check CUDA environment variables
cuda_vars = [var for var in os.environ if 'CUDA' in var]
if cuda_vars:
    print("CUDA environment variables:")
    for var in cuda_vars:
        print(f"  {var}={os.environ[var]}")
else:
    print("No CUDA environment variables found")

# Check NVIDIA driver
nvidia_smi = run_cmd("nvidia-smi")
if "NVIDIA-SMI" in nvidia_smi:
    print("\nNVIDIA driver information:")
    print(nvidia_smi.split("+-")[0])  # Print just the first part with driver info
else:
    print("\nNVIDIA SMI not available or no NVIDIA GPU found")

print_separator()
print("\nConclusion:")
if 'llama_cpp' in sys.modules:
    if has_cuda_attrs:
        print("✅ llama-cpp-python appears to be installed with CUDA support")
    else:
        print("⚠️ llama-cpp-python is installed but may not have CUDA support enabled")
else:
    print("❌ llama-cpp-python is not installed")
