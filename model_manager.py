#!/usr/bin/env python
"""
Model Manager CLI for Lyra
"""
import os
import sys
import argparse
import logging
import subprocess
from pathlib import Path
from tabulate import tabulate
from typing import List, Dict, Any, Optional

# Add Lyra to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

try:
    from lyra.config import get_config
    from lyra.download_models import download_model, DEFAULT_MODELS
except ImportError:
    print("Error importing Lyra modules")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_models(args):
    """List available models"""
    config = get_config()
    model_dir = config.get("llm", "model_dir")
    
    # Check if model directory exists
    if not os.path.exists(model_dir):
        print(f"Model directory does not exist: {model_dir}")
        return
    
    # Get model files
    local_models = []
    for root, _, files in os.walk(model_dir):
        for file in files:
            if file.endswith((".gguf", ".bin", ".safetensors")):
                model_path = os.path.join(root, file)
                model_size = os.path.getsize(model_path) / (1024 * 1024 * 1024)  # Size in GB
                local_models.append({
                    "name": file,
                    "path": model_path,
                    "size": f"{model_size:.2f} GB",
                    "active": model_path == config.get_llm_model_path() or model_path == config.get_video_model_path()
                })
    
    # Add default models section
    available_models = []
    for model_type, model_info in DEFAULT_MODELS.items():
        available_models.append({
            "type": model_type,
            "name": model_info["name"],
            "repo": model_info["repo"],
            "file": model_info["file"],
            "size": f"{model_info['size_gb']:.1f} GB"
        })
    
    # Display results
    print("\n=== Local Models ===")
    print(tabulate(local_models, headers="keys", tablefmt="pretty"))
    
    print("\n=== Available Models for Download ===")
    print(tabulate(available_models, headers="keys", tablefmt="pretty"))

def download_models(args):
    """Download specified models"""
    config = get_config()
    model_dir = config.get("llm", "model_dir")
    
    # Ensure model directory exists
    os.makedirs(model_dir, exist_ok=True)
    
    # Download specified models
    if args.type == "all":
        for model_type in DEFAULT_MODELS:
            print(f"\nDownloading {model_type} model...")
            download_model(model_type, model_dir, args.token)
    else:
        print(f"\nDownloading {args.type} model...")
        download_model(args.type, model_dir, args.token)

def set_active_model(args):
    """Set the active model"""
    config = get_config()
    
    if args.type == "text":
        # Update text model
        config.set("llm", "text_model", args.model_path)
        print(f"Set active text model to: {args.model_path}")
    elif args.type == "video":
        # Update video model
        config.set("video", "model", args.model_path)
        print(f"Set active video model to: {args.model_path}")
    else:
        print(f"Unknown model type: {args.type}")
        return
    
    # Save configuration
    config.save_config()

def test_model(args):
    """Test a model by generating text or video"""
    if args.type == "text":
        try:
            # Import the text generation module
            from lyra.huggingface_integration import get_huggingface_response
            
            # Generate text
            print(f"Testing text model with prompt: {args.prompt}")
            response = get_huggingface_response(
                args.prompt,
                model_path=args.model_path,
                max_tokens=100,
                temperature=0.7
            )
            print("\nModel response:")
            print("-------------")
            print(response)
            print("-------------")
        except Exception as e:
            print(f"Error testing text model: {e}")
    elif args.type == "video":
        try:
            # Import the video generation module
            from lyra.video_generation import generate_video
            
            # Generate video
            print(f"Testing video model with prompt: {args.prompt}")
            output_path = generate_video(args.prompt)
            if output_path:
                print(f"Video generated successfully: {output_path}")
            else:
                print("Video generation failed")
        except Exception as e:
            print(f"Error testing video model: {e}")
    else:
        print(f"Unknown model type: {args.type}")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Lyra Model Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available models")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download models")
    download_parser.add_argument("--type", choices=["text", "video", "all"], default="text", help="Model type to download")
    download_parser.add_argument("--token", type=str, help="HuggingFace token for private repos")
    
    # Set active model command
    set_parser = subparsers.add_parser("set", help="Set active model")
    set_parser.add_argument("--type", choices=["text", "video"], required=True, help="Model type to set")
    set_parser.add_argument("--model-path", required=True, help="Path to model file or repository ID")
    
    # Test model command
    test_parser = subparsers.add_parser("test", help="Test a model")
    test_parser.add_argument("--type", choices=["text", "video"], required=True, help="Model type to test")
    test_parser.add_argument("--model-path", help="Path to model file (optional)")
    test_parser.add_argument("--prompt", default="Hello, tell me about yourself", help="Prompt for generation")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_models(args)
    elif args.command == "download":
        download_models(args)
    elif args.command == "set":
        set_active_model(args)
    elif args.command == "test":
        test_model(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
