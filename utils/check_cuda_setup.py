"""
Diagnostic script to check CUDA setup for Phi-4 model
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_cuda_setup():
    """Check CUDA and related library setup"""
    results = {
        "cuda_available": False,
        "torch_cuda": False,
        "cuda_version": None,
        "gpu_name": None,
        "gpu_memory": None,
        "bits_and_bytes": False,
        "transformers": False
    }
    
    # Check PyTorch CUDA
    try:
        import torch
        results["torch_cuda"] = torch.cuda.is_available()
        if results["torch_cuda"]:
            results["cuda_version"] = torch.version.cuda
            results["gpu_name"] = torch.cuda.get_device_name(0)
            results["gpu_memory"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # Convert to GB
    except ImportError:
        logger.error("PyTorch not installed")
    except Exception as e:
        logger.error(f"Error checking PyTorch CUDA: {e}")

    # Check bitsandbytes
    try:
        import bitsandbytes as bnb
        results["bits_and_bytes"] = True
        try:
            if hasattr(bnb, "__cuda_runtime_version__"):
                logger.info(f"bitsandbytes CUDA version: {bnb.__cuda_runtime_version__}")
        except:
            pass
    except ImportError:
        logger.error("bitsandbytes not installed")
    except Exception as e:
        logger.error(f"Error checking bitsandbytes: {e}")

    # Check transformers
    try:
        import transformers
        results["transformers"] = True
    except ImportError:
        logger.error("transformers not installed")

    return results

def print_results(results):
    """Print diagnostic results"""
    print("\nCUDA Setup Diagnostic Results")
    print("============================")
    print(f"PyTorch CUDA available: {results['torch_cuda']}")
    if results["cuda_version"]:
        print(f"CUDA version: {results['cuda_version']}")
    if results["gpu_name"]:
        print(f"GPU: {results['gpu_name']}")
    if results["gpu_memory"]:
        print(f"GPU Memory: {results['gpu_memory']:.2f} GB")
    print(f"bitsandbytes installed: {results['bits_and_bytes']}")
    print(f"transformers installed: {results['transformers']}")
    
    print("\nRecommended Actions:")
    if not results["torch_cuda"]:
        print("- Install CUDA-enabled PyTorch: pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cu121")
    if not results["bits_and_bytes"]:
        print("- Install bitsandbytes: pip install bitsandbytes")
    if not results["transformers"]:
        print("- Install transformers: pip install transformers")

if __name__ == "__main__":
    results = check_cuda_setup()
    print_results(results)