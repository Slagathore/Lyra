import os
import json
import subprocess
import sys
import argparse
import importlib.util

# Ensure G: drive is used for all operations
os.environ["PYTHONPATH"] = f"G:\\AI\\Lyra;G:\\AI\\Lyra\\src;{os.environ.get('PYTHONPATH', '')}"
os.environ["TEMP"] = "G:\\AI\\Lyra\\temp"
os.environ["TMP"] = "G:\\AI\\Lyra\\temp"

# Create temp directory if it doesn't exist
if not os.path.exists("temp"):
    os.makedirs("temp", exist_ok=True)

def load_config():
    # Try to load environment-specific config first
    try:
        if os.path.exists("env_config.json"):
            with open("env_config.json", "r") as f:
                env_config = json.load(f)
                print("Using environment configuration from env_config.json")
                return env_config
    except Exception as e:
        print(f"Error loading env_config.json: {e}")
        
    # Fall back to regular config file
    try:
        with open("lyra_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: lyra_config.json not found. Creating a default one.")
        default_config = {
            "model": {
                "path": "G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf",
                "ctx_size": 2048, 
                "gpu_layers": 35,
                "n_batch": 128,
                "n_threads": 6
            },
            "server": {
                "host": "127.0.0.1",
                "port": 8000
            },
            "environment": {
                "cuda_visible_devices": "0",
                "ggml_cuda_no_pinned": "1",
                "ggml_cuda_force_mmq": "1",
                "ggml_cuda_mem_percent": "90",
                "ggml_cuda_dmmv_x": "32"
            },
            "paths": {
                "root": "G:\\AI\\Lyra",
                "data": "G:\\AI\\Lyra\\data",
                "logs": "G:\\AI\\Lyra\\logs",
                "temp": "G:\\AI\\Lyra\\temp"
            }
        }
        with open("lyra_config.json", "w") as f:
            json.dump(default_config, f, indent=2)
        return default_config

def check_cuda():
    """
    Check if CUDA is available for PyTorch and/or llama-cpp-python
    Returns True if any CUDA support is detected
    """
    cuda_available = False
    results = {"torch_cuda": False, "llama_cpp_cuda": False}
    
    # Try to check PyTorch CUDA
    try:
        import torch
        torch_cuda = torch.cuda.is_available()
        results["torch_cuda"] = torch_cuda
        
        if torch_cuda:
            print(f"PyTorch CUDA available: Yes")
            print(f"CUDA device count: {torch.cuda.device_count()}")
            print(f"CUDA version: {torch.version.cuda if hasattr(torch.version, 'cuda') else 'Unknown'}")
            print(f"Device name: {torch.cuda.get_device_name(0)}")
            
            try:
                memory_allocated = torch.cuda.memory_allocated() / 1024**3
                memory_reserved = torch.cuda.memory_reserved() / 1024**3
                print(f"Memory allocated: {memory_allocated:.2f} GB")
                print(f"Memory reserved: {memory_reserved:.2f} GB")
            except Exception as e:
                print(f"Could not get GPU memory info: {e}")
                
            cuda_available = True
        else:
            print("PyTorch CUDA available: No")
    except ImportError:
        print("PyTorch not installed. Cannot check PyTorch CUDA availability.")
    except Exception as e:
        print(f"Error checking PyTorch CUDA: {e}")
    
    # Try to check llama-cpp-python CUDA
    try:
        from llama_cpp import Llama
        gpu_devices = Llama.get_available_gpu_devices()
        has_gpu = len(gpu_devices) > 0
        results["llama_cpp_cuda"] = has_gpu
        
        print(f"llama-cpp-python CUDA available: {has_gpu}")
        if has_gpu:
            print(f"Available GPU devices: {gpu_devices}")
            cuda_available = True
        else:
            print("llama-cpp-python doesn't have CUDA support enabled.")
            print("Consider running fix_llm_errors.bat to install a CUDA-enabled version.")
    except ImportError:
        print("llama-cpp-python not installed. Cannot check its CUDA support.")
    except Exception as e:
        print(f"Error checking llama-cpp-python CUDA: {e}")
    
    # If we have nvidia-smi but no CUDA in libraries, show a warning
    if not cuda_available:
        try:
            import subprocess
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=3)
            if result.returncode == 0:
                print("\nWARNING: NVIDIA GPU detected, but CUDA libraries aren't working properly.")
                print("Run check_cuda_install.bat for a full diagnosis and fix_llm_errors.bat to fix issues.")
        except:
            pass
    
    return cuda_available

def check_llama_gpu():
    try:
        try:
            from llama_cpp import Llama
            supports_gpu = Llama.supports_gpu_offload()
            print(f"llama-cpp-python supports GPU offload: {supports_gpu}")
            return supports_gpu
        except ImportError as e:
            print(f"llama-cpp-python import error: {e}")
            print("llama-cpp-python not installed. Attempting to install...")
            try:
                print("Installing basic version. For GPU support, cancel and run:")
                print("pip install llama-cpp-python --extra-index-url https://download.pytorch.org/whl/cu121")
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "llama-cpp-python", "--upgrade", "--no-cache-dir"
                ])
                print("Installation complete. Please restart the script.")
                return False
            except subprocess.CalledProcessError as install_error:
                print(f"Failed to install llama-cpp-python: {install_error}")
                print("Common issues:")
                print("1. No internet connection")
                print("2. Insufficient permissions (try running as administrator/sudo)")
                print("3. Python environment issues")
                print("Please manually install llama-cpp-python with: pip install llama-cpp-python")
                return False
    except Exception as e:
        print(f"Error checking/installing llama-cpp GPU support: {e}")
        print("Please manually install llama-cpp-python with: pip install llama-cpp-python")
        return False

def start_server(config):
    model_path = config["model"]["path"]
    ctx_size = config["model"]["ctx_size"]
    gpu_layers = config["model"]["gpu_layers"]
    host = config["server"]["host"]
    port = config["server"]["port"]
    n_batch = config["model"]["n_batch"]
    n_threads = config["model"]["n_threads"]
    
    # Set environment variables
    for key, value in config["environment"].items():
        os.environ[key.upper()] = str(value)
    
    # Check if model exists
    if not os.path.exists(model_path):
        print(f"Error: Model file not found at {model_path}")
        return False
    
    print(f"\nStarting Lyra LLM server with the following settings:")
    print(f"- Model: {os.path.basename(model_path)}")
    print(f"- GPU Layers: {gpu_layers}")
    print(f"- Context Size: {ctx_size}")
    print(f"- Batch Size: {n_batch}")
    print(f"- Server: http://{host}:{port}")
    
    try:
        cmd = [
            "python", "-m", "llama_cpp.server",
            "--model", model_path,
            "--n_ctx", str(ctx_size),
            "--n_gpu_layers", str(gpu_layers),
            "--host", host,
            "--port", str(port),
            "--n_batch", str(n_batch),
            "--n_threads", str(n_threads),
            "--rope_scaling_type", "2"
        ]
        
        process = subprocess.Popen(cmd)
        print(f"\nLyra server started at http://{host}:{port}")
        print("Keep this window open to maintain the server connection.")
        return process
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

def check_module_exists(module_name):
    """Check if a module exists without importing it"""
    return importlib.util.find_spec(module_name) is not None

def main():
    parser = argparse.ArgumentParser(description='Launch Lyra AI with optional features')
    parser.add_argument('--with-self-improvement', action='store_true', help='Enable self-improvement capabilities', default=True)
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--server-only', action='store_true', help="Don't start the bot, only setup server connections")
    parser.add_argument('--advisor', choices=['local', 'deepseek', 'openai', 'anthropic'], 
                      help='Enable a specific LLM advisor for code improvement')
    parser.add_argument('--no-self-improvement', action='store_true', help='Disable self-improvement capabilities')
    args = parser.parse_args()
    
    # If explicitly disabled, turn off self-improvement
    if args.no_self_improvement:
        args.with_self_improvement = False
        
    # Add the current directory to the Python path
    sys.path.append(os.getcwd())
    
    if args.with_self_improvement:
        # Check if self-improvement module exists
        if not os.path.exists(os.path.join('src', 'lyra', 'self_improvement')):
            print("Self-improvement module not found. Creating it now...")
            subprocess.run(["self_improvement.bat"], shell=True)
        
        try:
            # First ensure the src directory is in the Python path
            src_path = os.path.join(os.getcwd(), 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
                
            # Import the self-improvement module
            from lyra.self_improvement import CodeManager, VintixRL
            
            print("Self-improvement module loaded successfully.")
            print("Lyra now has the ability to analyze and modify its own code.")
            
            # Initialize the code manager and RL system
            code_manager = CodeManager()
            vintix_rl = VintixRL()
            
            # Store these in the global namespace for interactive use
            globals()['code_manager'] = code_manager
            globals()['vintix_rl'] = vintix_rl
            
        except ImportError as e:
            print(f"Failed to import self-improvement module: {e}")
            print("Starting Lyra without self-improvement capabilities.")
    
    try:
        # Import and run the main Lyra entry point
        from lyra.main import main as run_lyra
        
        # Start Lyra with appropriate arguments
        run_args = {}
        if args.debug:
            run_args['debug'] = True
        if args.server_only:
            run_args['server_only'] = True
            
        # Add self-improvement capabilities if enabled
        if args.with_self_improvement and 'code_manager' in globals():
            run_args['code_manager'] = globals()['code_manager']
            run_args['vintix_rl'] = globals()['vintix_rl']
            
        run_lyra(**run_args)
        
    except ImportError as e:
        print(f"Error: Could not import Lyra main module: {e}")
        print("Please ensure Lyra is properly installed.")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting Lyra: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
