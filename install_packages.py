"""
Script to install required packages in the current Python environment
"""
import subprocess
import sys
import os
import platform

def run_command(cmd):
    """Run a command and return exit code, stdout, stderr"""
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return process.returncode, stdout, stderr

def check_package(package_name):
    """Check if a package is installed"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def main():
    print("=" * 60)
    print(f"Python version: {platform.python_version()}")
    print(f"Python executable: {sys.executable}")
    print(f"Platform: {platform.platform()}")
    print("=" * 60)
    
    # Check for llama_cpp
    if check_package("llama_cpp"):
        import llama_cpp
        print(f"llama_cpp is already installed. Version: {llama_cpp.__version__}")
        
        # Check if the installed version supports Qwen2 architecture
        try:
            # Try to load model metadata without actually loading the model
            model_path = 'G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf'
            if hasattr(llama_cpp, "get_model_metadata"):
                metadata = llama_cpp.get_model_metadata(model_path)
                architecture = metadata.get("general.architecture", "")
                if architecture == "qwen2":
                    print("✓ This version supports Qwen2 architecture")
                else:
                    print(f"⚠️ Unknown if this version supports Qwen2 (detected: {architecture})")
            else:
                print("⚠️ Cannot verify Qwen2 support (get_model_metadata not available)")
                
            # Check if version is known to support Qwen2
            version = llama_cpp.__version__
            if version >= "0.2.37" and "+cu" in version:
                print("✓ Version should support Qwen2 architecture")
            else:
                print("⚠️ Version may not support Qwen2 architecture")
                print("   Known working versions: 0.2.37+cu118, 0.2.65+cu118")
                
        except Exception as e:
            print(f"⚠️ Cannot check for Qwen2 support: {e}")
    else:
        print("llama_cpp not found. Installing...")
        
        # First try to install a version known to support Qwen2
        print("Trying to install a version known to support Qwen2 architecture...")
        code, out, err = run_command([
            sys.executable, "-m", "pip", "install", 
            "--prefer-binary", "--extra-index-url", 
            "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118",
            "llama-cpp-python==0.2.65+cu118"
        ])
        
        if code == 0:
            print("Successfully installed llama-cpp-python 0.2.65+cu118")
        else:
            print("Failed to install specific version. Trying alternative version...")
            code, out, err = run_command([
                sys.executable, "-m", "pip", "install", 
                "--prefer-binary", "--extra-index-url", 
                "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118",
                "llama-cpp-python==0.2.37+cu118"
            ])
            
            if code == 0:
                print("Successfully installed llama-cpp-python 0.2.37+cu118")
            else:
                print("Failed to install known good versions. Trying latest version...")
                # If specific versions fail, try the regular install
                code, out, err = run_command([
                    sys.executable, "-m", "pip", "install", 
                    "--prefer-binary", "--extra-index-url", 
                    "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu118",
                    "llama-cpp-python"
                ])
                
                if code == 0:
                    print("Successfully installed latest available llama-cpp-python")
                else:
                    print(f"Failed to install llama-cpp-python: {err}")
                    sys.exit(1)
    
    # Check if torch is installed and has CUDA
    if check_package("torch"):
        import torch
        print(f"PyTorch version: {torch.__version__}")
        print(f"CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"CUDA version: {torch.version.cuda}")
    else:
        print("PyTorch not installed. It's recommended for many LLM applications.")
    
    # Final verification
    try:
        import llama_cpp
        print("\nVerification successful!")
        print(f"llama_cpp is now installed. Version: {llama_cpp.__version__}")
        print(f"Module location: {llama_cpp.__file__}")
        
        # Check for CUDA support
        cuda_attrs = [attr for attr in dir(llama_cpp.Llama) if 'cuda' in attr.lower() or 'gpu' in attr.lower()]
        if cuda_attrs:
            print("\nCUDA support detected! The following attributes are available:")
            for attr in cuda_attrs:
                print(f"  - {attr}")
            print("\n✅ You're all set for GPU acceleration!")
        else:
            print("\n⚠️ CUDA support not detected in llama_cpp.")
            print("   You might be running a CPU-only version.")
    except ImportError:
        print("\nFailed to verify llama_cpp installation.")

if __name__ == "__main__":
    main()
