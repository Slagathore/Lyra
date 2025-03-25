"""
Simple script to install and run Lyra in one step
"""
import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_gpu():
    """Check if GPU is available for acceleration"""
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        if gpu_available:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            logger.info(f"GPU available: {gpu_name} with {gpu_memory:.2f} GB memory")
            return True, gpu_name, gpu_memory
        else:
            logger.info("No GPU detected, using CPU mode")
            return False, None, None
    except ImportError:
        logger.info("PyTorch not found, cannot check GPU status")
        return False, None, None
    except Exception as e:
        logger.info(f"Error checking GPU: {e}")
        return False, None, None

def setup_environment(args):
    """Set up environment for Lyra"""
    # Create virtual environment if it doesn't exist
    env_name = args.env_name
    env_path = Path(env_name)
    
    if not env_path.exists():
        logger.info(f"Creating virtual environment: {env_name}")
        try:
            subprocess.run([sys.executable, "-m", "venv", env_name], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating virtual environment: {e}")
            return False
    
    # Determine pip path based on platform
    if platform.system() == "Windows":
        pip_path = env_path / "Scripts" / "pip"
        python_path = env_path / "Scripts" / "python"
    else:
        pip_path = env_path / "bin" / "pip"
        python_path = env_path / "bin" / "python"
    
    # Install dependencies using resolve_dependencies.py
    dependencies = ["--langchain"]
    if args.with_video:
        dependencies.append("--video")
    if args.dev_tools:
        dependencies.append("--dev")
    
    logger.info("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "resolve_dependencies.py", "--env-name", env_name] + dependencies, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing dependencies: {e}")
        return False
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        logger.info("Creating .env file")
        with open(".env", "w") as f:
            f.write("# Lyra environment variables\n")
            f.write("LYRA_MODEL_DIR=~/lyra_models\n")
            if args.openai_key:
                f.write(f"OPENAI_API_KEY={args.openai_key}\n")
            else:
                f.write("# OPENAI_API_KEY=your_api_key_here\n")
    
    # Download models if requested
    if args.download_models:
        logger.info("Downloading models (this may take a while)...")
        model_types = []
        if args.text_model:
            model_types.append("text")
        if args.video_model:
            model_types.append("video")
        
        for model_type in model_types:
            try:
                logger.info(f"Downloading {model_type} model...")
                subprocess.run([str(python_path), "model_manager.py", "download", "--type", model_type], check=True)
            except subprocess.CalledProcessError as e:
                logger.warning(f"Error downloading {model_type} model: {e}")
    
    return True

def run_lyra(args):
    """Run Lyra"""
    # Find python executable in virtual environment
    if platform.system() == "Windows":
        python_path = os.path.join(args.env_name, "Scripts", "python")
    else:
        python_path = os.path.join(args.env_name, "bin", "python")
    
    # Run Lyra
    logger.info("Starting Lyra...")
    try:
        subprocess.run([python_path, "-m", "lyra.main"], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Lyra: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("Lyra stopped by user")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Install and run Lyra")
    parser.add_argument("--env-name", default="lyra_env", help="Virtual environment name")
    parser.add_argument("--setup-only", action="store_true", help="Only set up environment, don't run Lyra")
    parser.add_argument("--with-video", action="store_true", help="Include video generation dependencies")
    parser.add_argument("--dev-tools", action="store_true", help="Install development tools")
    parser.add_argument("--openai-key", help="OpenAI API key")
    parser.add_argument("--download-models", action="store_true", help="Download models automatically")
    parser.add_argument("--text-model", action="store_true", help="Download text model")
    parser.add_argument("--video-model", action="store_true", help="Download video model")
    
    args = parser.parse_args()
    
    # Check if any model should be downloaded
    if args.download_models and not (args.text_model or args.video_model):
        args.text_model = True  # Default to text model if --download-models is specified
    
    # Check GPU availability
    gpu_available, gpu_name, gpu_memory = check_gpu()
    
    # Set up environment
    if not setup_environment(args):
        logger.error("Failed to set up environment")
        return 1
    
    logger.info("Environment setup complete")
    
    # Run Lyra if not setup only
    if not args.setup_only:
        if not run_lyra(args):
            logger.error("Failed to run Lyra")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
