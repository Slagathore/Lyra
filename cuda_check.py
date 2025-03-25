"""
CUDA Detection and Diagnostics Tool for Lyra
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

def print_separator():
    print("=" * 50)

def run_cmd(cmd):
    """Run a command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout
    except Exception as e:
        return f"Error running command: {e}"

print_separator()
print(" CUDA Detection and Diagnostics Tool for Lyra ")
print_separator()
print()

# System information
print(f"System: {platform.system()} {platform.machine()}")
print(f"Python: {sys.version}")
print()

# Check environment variables
print("CUDA Environment Variables:")
cuda_vars = {
    "CUDA_PATH": os.environ.get("CUDA_PATH", "Not set"),
    "CUDA_HOME": os.environ.get("CUDA_HOME", "Not set"),
    "CUDA_VISIBLE_DEVICES": os.environ.get("CUDA_VISIBLE_DEVICES", "Not set"),
    "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set"),
    "LD_LIBRARY_PATH": os.environ.get("LD_LIBRARY_PATH", "Not set")
}

for var, value in cuda_vars.items():
    print(f"{var}: {value}")

# Check NVIDIA driver
nvidia_smi = run_cmd("nvidia-smi")
if "NVIDIA-SMI" in nvidia_smi:
    print("NVIDIA System Management Interface detected:")
    print(nvidia_smi)
else:
    print("NVIDIA SMI not available or no NVIDIA GPU found")

# Check for CUDA DLLs
print("Searching for CUDA DLLs in common locations...")
cuda_paths = [
    r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA",
    os.environ.get("CUDA_PATH", ""),
    os.environ.get("CUDA_HOME", "")
]

cuda_dll_found = False
for base_path in cuda_paths:
    if not base_path:
        continue
    
    if isinstance(base_path, str) and ";" in base_path:
        # Handle paths with semicolons by splitting
        base_paths = base_path.split(';')
    else:
        base_paths = [base_path]
    
    for path in base_paths:
        if not path:
            continue
            
        for version in ["v12.1", "v12.0", "v11.8", "v11.7", "v11.6", "v11.5", "v11.4", "v11.3"]:
            cuda_dll = Path(path) / version / "bin" / "cudart64_12.dll"
            if not cuda_dll.exists():
                # Try version-specific naming
                version_num = version[1:].replace(".", "")
                cuda_dll = Path(path) / version / "bin" / f"cudart64_{version_num}.dll"
            
            if cuda_dll.exists():
                print(f"Found CUDA DLLs at: {cuda_dll}")
                print(f"Parent directory: {cuda_dll.parent}")
                cuda_dll_found = True
                break
        
        if cuda_dll_found:
            break
    
    if cuda_dll_found:
        break

if not cuda_dll_found:
    print("No CUDA DLLs found in standard locations")

# Check PyTorch CUDA information
print("\nPyTorch CUDA Information:")
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA device count: {torch.cuda.device_count()}")
        print(f"CUDA version: {torch.version.cuda}")
        print()
        
        # Get device properties
        for i in range(torch.cuda.device_count()):
            device_props = torch.cuda.get_device_properties(i)
            print(f"Device {i}: {device_props.name}")
            print(f"Capabilities: {device_props.major, device_props.minor}")
            print(f"Total memory: {device_props.total_memory / 1e9:.2f} GB")
except ImportError:
    print("PyTorch not installed")

# Check llama-cpp-python
try:
    import llama_cpp
    print(f"\nllama-cpp-python version: {llama_cpp.__version__}")
    print(f"Location: {llama_cpp.__file__}")
    
    has_cuda = any('cuda' in attr.lower() or 'gpu' in attr.lower() for attr in dir(llama_cpp.Llama))
    print(f"CUDA support detected: {has_cuda}")
    
    if has_cuda:
        print("CUDA-related attributes:")
        cuda_attrs = [attr for attr in dir(llama_cpp.Llama) if 'cuda' in attr.lower() or 'gpu' in attr.lower()]
        for attr in cuda_attrs:
            print(f"  - {attr}")
except ImportError:
    print("\nllama-cpp-python not installed")
except Exception as e:
    print(f"\nError with llama-cpp-python: {e}")

# Summary
print("\n" + "=" * 50)
print(" CUDA Check Summary")
print("=" * 50)
has_nvidia_drivers = "NVIDIA-SMI" in nvidia_smi
has_cuda_env_vars = cuda_vars["CUDA_PATH"] != "Not set" or cuda_vars["CUDA_HOME"] != "Not set"
has_torch_cuda = False
has_llama_cuda = False

try:
    import torch
    has_torch_cuda = torch.cuda.is_available()
except:
    pass

try:
    import llama_cpp
    has_llama_cuda = any('cuda' in attr.lower() or 'gpu' in attr.lower() for attr in dir(llama_cpp.Llama))
except:
    pass

print(f"NVIDIA drivers detected: {has_nvidia_drivers}")
print(f"CUDA environment variables found: {has_cuda_env_vars}")
print(f"CUDA DLLs found: {cuda_dll_found}")
print(f"PyTorch CUDA support: {has_torch_cuda}")
print(f"llama-cpp-python CUDA support: {has_llama_cuda}")
print()

if has_nvidia_drivers and not has_llama_cuda:
    print("Your GPU was detected, but llama-cpp-python CUDA support is not working.")
    print("Please run fix_llm_errors.bat to install a CUDA-enabled version.")
elif not has_nvidia_drivers:
    print("No NVIDIA GPU was detected. You'll need to use CPU mode.")
elif has_nvidia_drivers and has_llama_cuda:
    print("CUDA support is working correctly! You can run models on your GPU.")
