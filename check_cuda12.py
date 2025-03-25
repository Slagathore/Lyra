"""
CUDA 12.8 Detection and Diagnostics Tool for Lyra
"""
import os
import sys
import platform
import subprocess
import glob
from pathlib import Path

def find_cuda_path():
    """Find the CUDA installation path"""
    # Check standard path first
    std_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
    if os.path.exists(std_path):
        return std_path
    
    # Check for any CUDA version
    for path in glob.glob(r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*"):
        return path
    
    # Check environment variable
    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path and os.path.exists(cuda_path):
        return cuda_path
        
    return None

def check_paths_in_env():
    """Check if CUDA paths are correctly set in PATH environment variable"""
    path_var = os.environ.get("PATH", "")
    cuda_path = find_cuda_path()
    
    if not cuda_path:
        return False, "CUDA installation not found"
    
    required_paths = [
        os.path.join(cuda_path, "bin"),
        os.path.join(cuda_path, "libnvvp")
    ]
    
    missing_paths = []
    for req_path in required_paths:
        if req_path.lower() not in path_var.lower():
            missing_paths.append(req_path)
    
    if missing_paths:
        return False, f"Missing CUDA paths in PATH: {', '.join(missing_paths)}"
    
    return True, "All required CUDA paths are in PATH environment variable"

def check_cuda_toolkit():
    """Check if CUDA toolkit is properly installed"""
    cuda_path = find_cuda_path()
    if not cuda_path:
        return False, "CUDA installation not found"
    
    # Check for nvcc compiler
    nvcc_path = os.path.join(cuda_path, "bin", "nvcc.exe")
    if not os.path.exists(nvcc_path):
        return False, f"NVCC compiler not found at {nvcc_path}"
    
    # Check version
    try:
        output = subprocess.check_output([nvcc_path, "--version"], text=True)
        cuda_version = "unknown"
        for line in output.split("\n"):
            if "release" in line.lower() and "v" in line:
                cuda_version = line.strip()
                break
        return True, f"CUDA toolkit installed: {cuda_version}"
    except subprocess.SubprocessError:
        return False, "Failed to get NVCC version"

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60)

def main():
    """Run the CUDA 12.8 diagnostic tool"""
    print_section("CUDA 12.8 DIAGNOSTIC TOOL")
    
    print(f"System: {platform.system()} {platform.release()} {platform.machine()}")
    print(f"Python: {sys.version}")
    
    print_section("1. CUDA INSTALLATION PATH")
    cuda_path = find_cuda_path()
    if cuda_path:
        print(f"✅ CUDA found at: {cuda_path}")
        print(f"   CUDA version: {os.path.basename(cuda_path)}")
        
        # List key files
        nvcc_path = os.path.join(cuda_path, "bin", "nvcc.exe")
        if os.path.exists(nvcc_path):
            print(f"✅ NVCC compiler: {nvcc_path}")
        else:
            print("❌ NVCC compiler not found")
            
        cudart_path = os.path.join(cuda_path, "bin", "cudart64_*.dll")
        cudart_files = glob.glob(cudart_path)
        if cudart_files:
            print(f"✅ CUDA Runtime: {cudart_files[0]}")
        else:
            print("❌ CUDA Runtime not found")
    else:
        print("❌ CUDA installation not found")
    
    print_section("2. ENVIRONMENT VARIABLES")
    
    # Check PATH
    path_ok, path_msg = check_paths_in_env()
    if path_ok:
        print(f"✅ {path_msg}")
    else:
        print(f"❌ {path_msg}")
    
    # Check CUDA_PATH
    cuda_path_env = os.environ.get("CUDA_PATH", "Not set")
    if cuda_path_env != "Not set" and os.path.exists(cuda_path_env):
        print(f"✅ CUDA_PATH: {cuda_path_env}")
    else:
        print(f"❌ CUDA_PATH: {cuda_path_env}")
    
    print_section("3. CUDA TOOLKIT")
    toolkit_ok, toolkit_msg = check_cuda_toolkit()
    if toolkit_ok:
        print(f"✅ {toolkit_msg}")
    else:
        print(f"❌ {toolkit_msg}")
    
    print_section("4. PYTORCH CUDA")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ PyTorch CUDA is available")
            print(f"   Devices: {torch.cuda.device_count()}")
            print(f"   CUDA version: {torch.version.cuda}")
            print(f"   Device name: {torch.cuda.get_device_name(0)}")
        else:
            print("❌ PyTorch CUDA is not available")
    except ImportError:
        print("❌ PyTorch not installed")
    except Exception as e:
        print(f"❌ Error checking PyTorch: {e}")
    
    print_section("5. LLAMA-CPP-PYTHON CUDA")
    try:
        from llama_cpp import Llama
        devices = Llama.get_available_gpu_devices()
        if devices:
            print(f"✅ llama-cpp-python CUDA is available")
            print(f"   GPU devices: {devices}")
        else:
            print("❌ llama-cpp-python CUDA is not available")
            print("   This could be because:")
            print("   - llama-cpp-python was not built with CUDA support")
            print("   - CUDA drivers are not compatible")
            print("   - Environment variables are incorrect")
    except ImportError:
        print("❌ llama-cpp-python not installed")
    except Exception as e:
        print(f"❌ Error checking llama-cpp-python: {e}")
    
    print_section("6. GPU INFORMATION")
    try:
        output = subprocess.check_output(["nvidia-smi"], text=True)
        print("✅ NVIDIA GPU detected:")
        print("\n".join("   " + line for line in output.split('\n')[:10]))
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ nvidia-smi failed - GPU information not available")
    
    print_section("DIAGNOSTIC SUMMARY")
    print(f"CUDA path: {cuda_path or 'Not found'}")
    print(f"CUDA in PATH: {'Yes' if path_ok else 'No'}")
    print(f"CUDA toolkit: {'Yes' if toolkit_ok else 'No'}")
    
    try:
        import torch
        torch_cuda = torch.cuda.is_available()
        print(f"PyTorch CUDA: {'Yes' if torch_cuda else 'No'}")
    except:
        print("PyTorch CUDA: Not installed")
        
    try:
        from llama_cpp import Llama
        llama_cuda = bool(Llama.get_available_gpu_devices())
        print(f"llama-cpp CUDA: {'Yes' if llama_cuda else 'No'}")
    except:
        print("llama-cpp CUDA: Not installed")
        
    print("\nIf you're experiencing issues with CUDA support in llama-cpp-python,")
    print("run the following command to install a CUDA-optimized version:")
    print("\npip install llama-cpp-python==0.2.38+cu121 --force-reinstall")
    print("   --extra-index-url https://download.pytorch.org/whl/cu121\n")

if __name__ == "__main__":
    main()
