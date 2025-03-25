import argparse
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_template")

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.model_manager import ModelManager

def main():
    """Test different chat templates with models."""
    parser = argparse.ArgumentParser(description="Test chat templates")
    parser.add_argument("--model", type=str, required=True, help="Model name to test")
    parser.add_argument("--format", type=str, choices=["default", "llama3", "command-r", "wizard", "chatml"], 
                       default="llama3", help="Template format to test")
    parser.add_argument("--prompt", type=str, default="Tell me a short story about a robot", 
                        help="Test prompt")
    args = parser.parse_args()
    
    # Initialize model manager
    model_manager = ModelManager()
    
    # Check if model exists
    if args.model not in model_manager.model_configs:
        print(f"Error: Model '{args.model}' not found. Available models:")
        for model in model_manager.model_configs.keys():
            print(f"  - {model}")
        return 1
    
    # Update model format if needed
    config = model_manager.model_configs[args.model]
    original_format = config.parameters.get("format", "default")
    
    if original_format != args.format:
        print(f"Updating model format from {original_format} to {args.format}")
        config.parameters["format"] = args.format
        model_manager.save_model_config(config)
    
    # Load model
    print(f"Loading model {args.model} with {args.format} format...")
    model = model_manager.load_model(args.model)
    if not model:
        print(f"Error: Failed to load model {args.model}")
        return 1
    
    # Format prompt
    if args.format == "llama3":
        prompt = f"<|system|>\nYou are a helpful AI assistant.</s>\n<|user|>\n{args.prompt}</s>\n<|assistant|>\n"
    elif args.format == "command-r":
        prompt = f"<|im_start|>system\nYou are a helpful AI assistant.<|im_end|>\n\n<|im_start|>user\n{args.prompt}<|im_end|>\n\n<|im_start|>assistant\n"
    elif args.format == "wizard":
        prompt = f"You are a helpful AI assistant.\n\nUSER: {args.prompt}\nASSISTANT:"
    elif args.format == "chatml":
        prompt = f"<|im_start|>system\nYou are a helpful AI assistant.<|im_end|>\n<|im_start|>user\n{args.prompt}<|im_end|>\n<|im_start|>assistant\n"
    else:
        prompt = f"You are a helpful AI assistant.\n\nUser: {args.prompt}\nAssistant:"
    
    # Generate response
    print(f"\nGenerating with prompt:\n{prompt}\n")
    response = model_manager.generate(prompt, temperature=0.7, max_tokens=200)
    
    # Print response
    print(f"\nResponse:\n{response}\n")
    
    # Restore original format if changed
    if original_format != args.format:
        print(f"Restoring original format: {original_format}")
        config.parameters["format"] = original_format
        model_manager.save_model_config(config)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
