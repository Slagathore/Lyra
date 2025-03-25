#!/usr/bin/env python3
import argparse
import os
import sys
import subprocess
import logging
import json
import time
from pathlib import Path
import socket
import signal
import atexit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("launch_llama_server")

# Ensure that we can find our modules
sys.path.append(str(Path(__file__).parent.parent))
from modules.model_manager import ModelManager

def is_port_in_use(port):
    """Check if the port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def find_llama_executable():
    """Find the llama-server executable."""
    # Check common locations
    possible_paths = [
        "llama-server",  # If in PATH
        "./llama-server",
        "bin/llama-server",
        "llama.cpp/build/bin/llama-server",
        "llama.cpp/llama-server",
        "BigModes/llama.cpp/build/bin/llama-server",
        "BigModes/bin/llama-server",
        "./llama-server.exe",
        "bin/llama-server.exe",
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Found llama-server at: {path}")
                return path
        except FileNotFoundError:
            continue
    
    logger.error("llama-server executable not found. Please make sure it's installed and in your PATH")
    return None

def wait_for_server(port, max_retries=30, retry_delay=1.0):
    """Wait for the server to be ready."""
    logger.info(f"Waiting for server to be ready on port {port}...")
    for i in range(max_retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(('127.0.0.1', port))
                logger.info(f"Server is ready on port {port}")
                return True
        except (ConnectionRefusedError, OSError):
            if i < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error(f"Server did not start after {max_retries} attempts")
    return False

def get_chat_format(model_config):
    """Determine the chat format to use for a model."""
    format_name = model_config.parameters.get("format", "default")
    
    # Map our format names to server format names
    format_map = {
        "llama3": "llama-3",
        "llama2": "llama-2",
        "chatml": "chatml",
        "vicuna": "vicuna",
        "command-r": "chatml",  # Close equivalent
        "wizard": "vicuna",  # wizard format is usually compatible with vicuna
        "mistral": "mistral",
        "openchat": "openchat",
        "gemma": "gemma",
        "default": None,  # Let the server detect
    }
    
    return format_map.get(format_name.lower(), None)

def launch_server(model_name=None, port=8080, model_manager=None, **kwargs):
    """Launch the llama-server with the specified model."""
    # Find llama-server executable
    llama_server = find_llama_executable()
    if not llama_server:
        return None
    
    # Check if port is already in use
    if is_port_in_use(port):
        logger.info(f"Port {port} is already in use. Assuming server is running.")
        return "already_running"
    
    # Initialize model manager if not provided
    if model_manager is None:
        model_manager = ModelManager()
    
    # If no model specified, use the first one
    if not model_name:
        if model_manager.model_configs:
            model_name = next(iter(model_manager.model_configs.keys()))
            logger.info(f"No model specified, using: {model_name}")
        else:
            logger.error("No models configured and no model specified")
            return None
    
    # Get model config
    if model_name not in model_manager.model_configs:
        logger.error(f"Model '{model_name}' not found in configuration")
        return None
    
    model_config = model_manager.model_configs[model_name]
    
    # Get model path
    model_path = model_config.model_path
    if not os.path.exists(model_path):
        logger.error(f"Model file not found: {model_path}")
        return None
    
    # Get model parameters
    n_gpu_layers = model_config.parameters.get("n_gpu_layers", 0)
    context_size = model_config.parameters.get("context_size", 4096)
    
    # Determine chat format
    chat_format = get_chat_format(model_config)
    
    # Build command
    cmd = [
        llama_server,
        "-m", model_path,
        "--port", str(port),
        "--host", "127.0.0.1",
        "-c", str(context_size),
    ]
    
    # Add chat format if specified
    if chat_format:
        cmd.extend(["--chat-template", chat_format])
    
    # Add GPU layers if > 0
    if n_gpu_layers > 0:
        cmd.extend(["--n-gpu-layers", str(n_gpu_layers)])
    
    # Add any additional parameters
    if "n_parallel" in kwargs and kwargs["n_parallel"] > 1:
        cmd.extend(["-np", str(kwargs["n_parallel"])])
    
    if "n_threads" in kwargs and kwargs["n_threads"] > 0:
        cmd.extend(["--threads", str(kwargs["n_threads"])])
    
    if "grammar_file" in kwargs and kwargs["grammar_file"]:
        cmd.extend(["--grammar-file", kwargs["grammar_file"]])
    
    # Launch the server
    logger.info(f"Launching llama-server with command: {' '.join(cmd)}")
    
    # Launch server with output piped to our logger
    server_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Register cleanup handler
    def kill_server():
        if server_process.poll() is None:
            logger.info("Stopping llama-server process...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("Server did not terminate gracefully, forcing...")
                server_process.kill()
    
    atexit.register(kill_server)
    
    # Create a thread to log server output
    import threading
    def log_output():
        for line in server_process.stdout:
            logger.info(f"[SERVER] {line.strip()}")
    
    threading.Thread(target=log_output, daemon=True).start()
    
    # Wait for server to be ready
    if wait_for_server(port):
        return server_process
    else:
        kill_server()
        return None

def main():
    parser = argparse.ArgumentParser(description="Launch llama-server for Lyra models")
    parser.add_argument("--model", "-m", type=str, help="Name of the model to use")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Port for the server")
    parser.add_argument("--list-models", "-l", action="store_true", help="List available models")
    parser.add_argument("--n-gpu-layers", type=int, help="Number of GPU layers to use")
    parser.add_argument("--n-parallel", "-np", type=int, default=1, help="Number of parallel inference requests")
    parser.add_argument("--n-threads", "-t", type=int, default=0, help="Number of threads (0=auto)")
    parser.add_argument("--grammar-file", "-g", type=str, help="Path to a grammar file")
    args = parser.parse_args()
    
    # Initialize model manager
    model_manager = ModelManager()
    
    # List models if requested
    if args.list_models:
        print("Available models:")
        for i, model_name in enumerate(model_manager.model_configs.keys(), 1):
            config = model_manager.model_configs[model_name]
            model_path = config.model_path
            file_exists = Path(model_path).exists()
            size_str = "Unknown"
            if file_exists:
                try:
                    size_bytes = Path(model_path).stat().st_size
                    size_gb = size_bytes / (1024**3)
                    size_str = f"{size_gb:.2f} GB"
                except:
                    pass
            
            status = "✅" if file_exists else "❌"
            format_name = config.parameters.get("format", "default")
            n_gpu_layers = config.parameters.get("n_gpu_layers", 0)
            
            print(f"{i}. {status} {model_name}")
            print(f"   Path: {model_path}")
            print(f"   Size: {size_str}")
            print(f"   Format: {format_name}")
            print(f"   GPU Layers: {n_gpu_layers}")
            print()
        return 0
    
    # Override GPU layers if specified
    kwargs = {
        "n_parallel": args.n_parallel,
        "n_threads": args.n_threads,
    }
    
    if args.grammar_file:
        kwargs["grammar_file"] = args.grammar_file
    
    # Launch server
    server_process = launch_server(
        model_name=args.model,
        port=args.port,
        model_manager=model_manager,
        **kwargs
    )
    
    if server_process is None:
        print("Failed to start llama-server. Check the logs for details.")
        return 1
    
    if server_process == "already_running":
        print(f"llama-server already running on port {args.port}")
        return 0
    
    # Print server info
    print(f"\nllama-server is now running on port {args.port}")
    print(f"Chat web UI: http://127.0.0.1:{args.port}/")
    print(f"OpenAI-compatible API endpoint: http://127.0.0.1:{args.port}/v1/chat/completions")
    print("\nPress Ctrl+C to stop the server...")
    
    try:
        # Wait for server process to complete or be interrupted
        server_process.wait()
    except KeyboardInterrupt:
        print("\nStopping server...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
