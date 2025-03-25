#!/usr/bin/env python
"""
Dependency resolver for Lyra

This script resolves dependency conflicts and sets up the proper environment for Lyra.
It handles different installation types (CPU/GPU) and optional dependencies.
"""

import os
import sys
import subprocess
import argparse
import platform
from pathlib import Path
import shutil
import venv
import importlib.metadata  # Use importlib.metadata instead of deprecated pkg_resources

# ANSI color codes for terminal output
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
ENDC = "\033[0m"
BOLD = "\033[1m"

def print_color(color, message, bold=False):
    """Print colored text to the console"""
    if os.name == 'nt':  # Windows doesn't support ANSI colors in cmd
        print(message)
    else:
        prefix = BOLD if bold else ""
        print(f"{prefix}{color}{message}{ENDC}")

def run_command(command, check=True, capture_output=False):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            command, 
            check=check, 
            shell=True, 
            text=True,
            capture_output=capture_output
        )
        return result
    except subprocess.CalledProcessError as e:
        print_color(RED, f"Command failed: {command}")
        print_color(RED, f"Error: {e}")
        if not check:
            return e
        sys.exit(1)

def check_gpu():
    """Check if GPU is available for PyTorch"""
    try:
        import torch
        has_cuda = torch.cuda.is_available()
        if has_cuda:
            device_count = torch.cuda.device_count()
            device_name = torch.cuda.get_device_name(0) if device_count > 0 else "Unknown"
            print_color(GREEN, f"CUDA is available! Found {device_count} device(s)")
            print_color(GREEN, f"GPU: {device_name}")
        else:
            print_color(YELLOW, "CUDA is not available. Using CPU only.")
        return has_cuda
    except ImportError:
        print_color(YELLOW, "PyTorch not installed yet. Cannot check GPU status.")
        return False

def detect_cuda_version():
    """Detect the installed CUDA version"""
    if os.name == 'nt':
        # On Windows, check environmental variables
        cuda_path = os.environ.get("CUDA_PATH")
        if cuda_path:
            # Extract version from path (e.g., C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8)
            parts = cuda_path.split('\\')
            for part in parts:
                if part.startswith('v'):
                    return part[1:]  # Remove the 'v' prefix
        
        # Try nvcc
        try:
            result = run_command("nvcc --version", capture_output=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'release' in line and 'V' in line:
                        # Extract version like "V11.8.89"
                        parts = line.split('V')[1].split(' ')[0].split('.')
                        return f"{parts[0]}.{parts[1]}"
        except Exception:
            pass
    else:
        # On Linux/Mac, try to find nvcc or look in common locations
        try:
            result = run_command("nvcc --version", capture_output=True, check=False)
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if 'release' in line and ', V' in line:
                        version = line.split(', V')[1].split(' ')[0]
                        major, minor = version.split('.')[:2]
                        return f"{major}.{minor}"
        except Exception:
            pass
        
        # Check common CUDA locations
        for cuda_path in ['/usr/local/cuda', '/usr/cuda']:
            if os.path.exists(cuda_path):
                # Check if it's a symlink to a version
                if os.path.islink(cuda_path):
                    target = os.readlink(cuda_path)
                    if 'cuda-' in target:
                        return target.split('cuda-')[1]
                
                # Try to find version file
                version_file = os.path.join(cuda_path, 'version.txt')
                if os.path.exists(version_file):
                    with open(version_file, 'r') as f:
                        content = f.read()
                        if 'CUDA Version ' in content:
                            return content.split('CUDA Version ')[1].strip().split(' ')[0]
    
    return None

class EnhancedEnvBuilder(venv.EnvBuilder):
    """Enhanced virtual environment builder that ensures pip is installed properly"""
    
    def post_setup(self, context):
        # Always install or upgrade pip using ensurepip
        subprocess.check_call([context.env_exe, '-m', 'ensurepip', '--upgrade'])
        
def setup_venv(venv_path="lyra_env", use_existing=True):
    """Set up a virtual environment"""
    venv_path = Path(venv_path)
    
    # Check if venv already exists
    if venv_path.exists() and use_existing:
        print_color(BLUE, f"Using existing virtual environment at {venv_path}")
        
        # Make sure pip is installed in existing environment
        python_path = get_venv_python(venv_path)
        try:
            subprocess.run([python_path, '-m', 'pip', '--version'], check=True, capture_output=True)
        except:
            print_color(YELLOW, "Pip not working in existing environment. Reinstalling pip...")
            subprocess.run([python_path, '-m', 'ensurepip', '--upgrade'], check=False)
            
        return venv_path
    
    # Create a new venv with our enhanced builder to ensure pip works
    print_color(BLUE, f"Creating virtual environment at {venv_path}")
    builder = EnhancedEnvBuilder(with_pip=True)
    builder.create(venv_path)
    
    return venv_path

def get_venv_python(venv_path):
    """Get the path to the Python executable in a virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:  # Unix
        return os.path.join(venv_path, "bin", "python")

def get_venv_pip(venv_path):
    """Get the path to the pip executable in a virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Unix
        return os.path.join(venv_path, "bin", "pip")

def activate_venv_commands(venv_path):
    """Return activation commands for the virtual environment"""
    if os.name == 'nt':  # Windows
        return f"{venv_path}\\Scripts\\activate.bat"
    else:  # Unix
        return f"source {venv_path}/bin/activate"

def update_pip_safely(python_path):
    """Update pip using the Python executable to avoid permission issues"""
    print_color(BLUE, "Updating pip safely...", bold=True)
    
    # Use the Python executable to run pip, which avoids the locked executable issue on Windows
    run_command(f'"{python_path}" -m pip install --upgrade pip setuptools wheel', check=False)

def install_core_dependencies(pip_path, python_path):
    """Install core dependencies"""
    print_color(BLUE, "Installing core dependencies...", bold=True)
    
    # Update pip using the safer method first
    update_pip_safely(python_path)
    
    # Install non-conflicting base dependencies
    try:
        # Always use the Python module approach which is more reliable
        run_command(f'"{python_path}" -m pip install python-dotenv requests tqdm numpy pandas matplotlib')
    except Exception as e:
        print_color(RED, f"Error installing core dependencies: {e}")
        return False
        
    return True

def install_llm_dependencies(pip_path, python_path, use_gpu=False, cuda_version=None):
    """Install LLM dependencies"""
    print_color(BLUE, "Installing LLM dependencies...", bold=True)
    
    # Install PyTorch with appropriate CUDA support
    if use_gpu and cuda_version:
        # Map CUDA version to PyTorch index URL
        cuda_map = {
            "11.8": "cu118",
            "11.7": "cu117", 
            "11.6": "cu116",
            "11.3": "cu113",
            "10.2": "cu102",
        }
        
        # Find the closest match for CUDA version
        cuda_key = None
        for key in cuda_map.keys():
            if cuda_version.startswith(key):
                cuda_key = key
                break
        
        if cuda_key:
            print_color(GREEN, f"Installing PyTorch with CUDA {cuda_key} support")
            torch_command = f'"{python_path}" -m pip install torch --index-url https://download.pytorch.org/whl/{cuda_map[cuda_key]}'
            run_command(torch_command)
        else:
            print_color(YELLOW, f"Unknown CUDA version: {cuda_version}, falling back to latest PyTorch")
            run_command(f'"{python_path}" -m pip install torch')
    else:
        # CPU-only PyTorch
        print_color(YELLOW, "Installing CPU-only PyTorch")
        run_command(f'"{python_path}" -m pip install torch --index-url https://download.pytorch.org/whl/cpu')
    
    # Install transformers (but not dependencies yet to avoid conflicts)
    run_command(f'"{python_path}" -m pip install transformers --no-deps')
    
    # Install LangChain community and core
    run_command(f'"{python_path}" -m pip install "langchain>=0.1.0" "langchain-community>=0.0.8"')
    
    # Install special packages with specific flags
    if use_gpu:
        # Install bitsandbytes for GPU quantization
        run_command(f'"{python_path}" -m pip install bitsandbytes --no-build-isolation')
        
        # Install llama-cpp-python with CUDA support
        print_color(BLUE, "Installing llama-cpp-python with CUDA support...")
        cuda_args = "CMAKE_ARGS=\"-DLLAMA_CUBLAS=on\" FORCE_CMAKE=1"
        run_command(f'{cuda_args} "{python_path}" -m pip install llama-cpp-python --no-cache-dir')
        
        # Install accelerate for efficient transformer loading
        run_command(f'"{python_path}" -m pip install accelerate')
    else:
        # Install CPU-only llama-cpp-python
        print_color(BLUE, "Installing CPU-only llama-cpp-python...")
        run_command(f'"{python_path}" -m pip install llama-cpp-python --no-cache-dir')
    
    # Finally add common NLP packages
    run_command(f'"{python_path}" -m pip install "sentence-transformers>=2.2.2"')

def install_rasa_dependencies(python_path, use_gpu=False):
    """Install Rasa and its dependencies"""
    print_color(BLUE, "Installing Rasa dependencies...", bold=True)
    
    # Install Rasa with proper constraints to avoid conflicts
    run_command(f'"{python_path}" -m pip install "rasa>=3.6.21,<4.0.0" --no-deps')
    
    # Install Rasa dependencies manually to avoid conflicts
    run_command(f'"{python_path}" -m pip install "sqlalchemy<2.0.0" "sqlalchemy-utils"')
    
    # Install more Rasa dependencies
    run_command(f'"{python_path}" -m pip install coloredlogs fbmessenger mattermostwrapper')
    run_command(f'"{python_path}" -m pip install spacy nltk')

def install_video_dependencies(python_path, use_gpu=False):
    """Install video generation dependencies"""
    print_color(BLUE, "Installing video generation dependencies...", bold=True)
    
    # Install diffusers library
    run_command(f'"{python_path}" -m pip install diffusers')
    
    # Install additional components
    if use_gpu:
        run_command(f'"{python_path}" -m pip install xformers')

def install_openai_dependencies(python_path):
    """Install OpenAI API dependencies"""
    print_color(BLUE, "Installing OpenAI API dependencies...", bold=True)
    
    # Install OpenAI and LangChain OpenAI
    run_command(f'"{python_path}" -m pip install "openai>=1.0.0" "langchain-openai>=0.0.1"')

def check_package_conflicts(python_path):
    """Check for any package conflicts"""
    print_color(BLUE, "Checking for package conflicts...", bold=True)
    
    result = run_command(f'"{python_path}" -m pip check', check=False, capture_output=True)
    if result.returncode != 0:
        print_color(YELLOW, "Detected package conflicts:")
        print(result.stdout)
        return True
    
    print_color(GREEN, "No package conflicts detected!")
    return False

def fix_common_conflicts(python_path):
    """Fix common known conflicts"""
    print_color(BLUE, "Fixing common package conflicts...", bold=True)
    
    # Fix common issues with specific packages
    fixes = [
        # Fix protobuf version issues
        f'"{python_path}" -m pip install "protobuf>=3.20.1,<4.0.0"',
        
        # Ensure compatible numpy
        f'"{python_path}" -m pip install "numpy>=1.22.0"',
        
        # Fix tensorflow/torch conflicts
        f'"{python_path}" -m pip install "tensorflow<2.16.0" "tensorflow-probability<0.22.0"'
    ]
    
    for fix in fixes:
        run_command(fix, check=False)

def validate_installation(python_path):
    """Validate that key components are working properly"""
    print_color(BLUE, "Validating installation...", bold=True)
    
    checks = [
        # Check LangChain imports
        "from langchain.chains import ConversationChain",
        
        # Check LLAMA-CPP import
        "try:\n    from langchain_community.llms import LlamaCpp\nexcept ImportError:\n    from langchain.llms import LlamaCpp",
        
        # Check transformers import
        "import transformers",
        
        # Check OpenAI import
        "import openai",
        
        # Check torch import
        "import torch; print('CUDA Available:', torch.cuda.is_available())",
    ]
    
    success = True
    for check in checks:
        try:
            result = run_command(f'"{python_path}" -c "{check}"', check=False, capture_output=True)
            if result.returncode == 0:
                module = check.split()[1] if "import " in check else check.split("\n")[0].split()[1]
                print_color(GREEN, f"✓ {module} imports successfully")
            else:
                print_color(YELLOW, f"✗ Failed to import: {check}")
                print_color(YELLOW, f"  Error: {result.stderr.strip()}")
                success = False
        except Exception as e:
            print_color(RED, f"Error checking {check}: {e}")
            success = False
    
    return success

def install_local_package(python_path):
    """Install the local Lyra package in development mode"""
    print_color(BLUE, "Installing Lyra package in development mode...", bold=True)
    run_command(f'"{python_path}" -m pip install -e .')

def main():
    parser = argparse.ArgumentParser(description='Resolve dependencies for Lyra')
    parser.add_argument('--venv', default='lyra_env', help='Path to virtual environment')
    parser.add_argument('--use-existing-venv', action='store_true', 
                        help='Use existing virtual environment if it exists')
    parser.add_argument('--force-cpu', action='store_true', 
                        help='Force CPU-only installation even if GPU is available')
    parser.add_argument('--with-rasa', action='store_true', 
                        help='Install Rasa dependencies')
    parser.add_argument('--with-video', action='store_true', 
                        help='Install video generation dependencies')
    parser.add_argument('--with-openai', action='store_true', 
                        help='Install OpenAI API dependencies')
    parser.add_argument('--all', action='store_true', 
                        help='Install all optional dependencies')
    parser.add_argument('--no-venv', action='store_true',
                        help='Install directly without using a virtual environment')
    
    args = parser.parse_args()
    
    print_color(GREEN, "▶ Lyra Dependency Resolver", bold=True)
    print_color(BLUE, "This script will set up all required dependencies for Lyra.")
    print()
    
    # Set up paths based on whether we use venv or not
    if args.no_venv:
        print_color(YELLOW, "Installing without virtual environment (not recommended)")
        python_path = sys.executable
        pip_path = f'"{python_path}" -m pip'
    else:
        # Set up virtual environment
        venv_path = setup_venv(args.venv, args.use_existing_venv)
        python_path = get_venv_python(venv_path)
        pip_path = get_venv_pip(venv_path)
    
    # Check for GPU and CUDA version
    use_gpu = not args.force_cpu and check_gpu()
    cuda_version = None
    if use_gpu:
        cuda_version = detect_cuda_version()
        if cuda_version:
            print_color(GREEN, f"Detected CUDA version: {cuda_version}")
        else:
            print_color(YELLOW, "Could not detect CUDA version. Will attempt to use latest.")
    
    # Install dependencies using the Python interpreter directly to avoid permission issues
    success = install_core_dependencies(pip_path, python_path)
    if not success:
        print_color(RED, "Failed to install core dependencies. Exiting.")
        sys.exit(1)
        
    install_llm_dependencies(pip_path, python_path, use_gpu, cuda_version)
    
    if args.with_rasa or args.all:
        install_rasa_dependencies(python_path, use_gpu)
    
    if args.with_video or args.all:
        install_video_dependencies(python_path, use_gpu)
    
    if args.with_openai or args.all:
        install_openai_dependencies(python_path)
    
    # Fix any remaining conflicts
    fix_common_conflicts(python_path)
    conflicts = check_package_conflicts(python_path)
    
    if conflicts:
        print_color(YELLOW, "Some package conflicts were detected. They might not affect functionality.")
    
    # Install Lyra itself in development mode
    install_local_package(python_path)
    
    # Validate installation
    if validate_installation(python_path):
        print_color(GREEN, "✅ Lyra dependencies installed successfully!", bold=True)
    else:
        print_color(YELLOW, "⚠️ Some components may not be working correctly. See warnings above.", bold=True)
    
    # Show activation instructions
    if not args.no_venv:
        print()
        print_color(BLUE, "To activate the environment, use:", bold=True)
        print_color(GREEN, f"  {activate_venv_commands(venv_path)}")
        
        print()
        print_color(BLUE, "To run Lyra with the new environment:", bold=True)
        print_color(GREEN, f"  {activate_venv_commands(venv_path)}")
        print_color(GREEN, "  python -m lyra.main")
    else:
        print()
        print_color(BLUE, "To run Lyra:", bold=True)
        print_color(GREEN, "  python -m lyra.main")
    print()

if __name__ == "__main__":
    main()
