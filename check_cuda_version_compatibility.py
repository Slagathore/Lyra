"""
Check CUDA version compatibility across the system components
"""
import os
import subprocess
import sys
from pathlib import Path

def print_header(title):
    print(f"\n{'=' * 60}")
    print(f" {title} ".center(60, "="))
    print(f"{'=' * 60}")

def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

print_header("CUDA VERSION COMPATIBILITY CHECK")

# CUDA Toolkit Version
print("Checking CUDA Toolkit...")
cuda_path = os.environ.get("CUDA_PATH", "C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v12.8")
if os.path.exists(cuda_path):
    nvcc_path = Path(cuda_path) / "bin" / "nvcc.exe"
    if nvcc_path.exists():
        nvcc_version = run_command([str(nvcc_path), "--version"])
        print(f"CUDA Toolkit: {nvcc_version.splitlines()[3] if len(nvcc_version.splitlines()) >= 4 else nvcc_version}")
    else:
        print(f"NVCC not found at {nvcc_path}")
else:
    print(f"CUDA Toolkit not found at {cuda_path}")

# NVIDIA Driver Version
print("\nChecking NVIDIA Driver...")
driver_version = run_command(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"])
print(f"NVIDIA Driver: {driver_version}")

# PyTorch CUDA version
print("\nChecking PyTorch CUDA support...")
try:
    import torch
    cuda_available = torch.cuda.is_available()
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {cuda_available}")
    if cuda_available:
        print(f"PyTorch CUDA version: {torch.version.cuda}")
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
except ImportError:
    print("PyTorch not installed")
except Exception as e:
    print(f"Error checking PyTorch: {e}")

# llama-cpp-python CUDA support
print("\nChecking llama-cpp-python CUDA support...")
try:
    from llama_cpp import Llama
    devices = Llama.get_available_gpu_devices()
    print(f"llama-cpp-python version: {Llama.__version__ if hasattr(Llama, '__version__') else 'Unknown'}")
    print(f"CUDA devices: {devices}")
except ImportError:
    print("llama-cpp-python not installed")
except Exception as e:
    print(f"Error checking llama-cpp-python: {e}")

# Environment variables
print("\nCUDA-related Environment Variables:")
for var in ["CUDA_PATH", "CUDA_HOME", "GGML_CUDA_NO_PINNED", "GGML_CUDA_FORCE_MMQ"]:
    print(f"{var}: {os.environ.get(var, 'Not set')}")

print_header("SUMMARY")
print("Your system needs compatible versions across all components:")
print("1. NVIDIA Driver must support your CUDA version (12.8 → Driver 525+)")
print("2. PyTorch should be installed with CUDA support (not CPU-only)")
print("3. llama-cpp-python should be built with GGML_CUDA=on (not LLAMA_CUBLAS)")
print("\nIf any component shows issues, run cuda_fix_2024.bat")
