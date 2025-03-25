import argparse
import logging
import sys
import time
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_gpu_layers")

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.model_manager import ModelManager

def test_gpu_layers(model_name, layer_values=None, prompt_length=512, output_tokens=128, repeats=3):
    """Test different GPU layer settings with the specified model."""
    if layer_values is None:
        layer_values = [0, 8, 16, 24, 32]  # Default values to test
    
    # Initialize model manager
    model_manager = ModelManager()
    
    # Check if model exists
    if model_name not in model_manager.model_configs:
        logger.error(f"Model '{model_name}' not found")
        return None
    
    config = model_manager.model_configs[model_name]
    original_layers = config.parameters.get("n_gpu_layers", 0)
    
    # Create test prompt (repeating text to reach desired length)
    base_prompt = "The quick brown fox jumps over the lazy dog. "
    prompt = base_prompt * (prompt_length // len(base_prompt) + 1)
    prompt = prompt[:prompt_length]
    
    results = []
    
    try:
        # Test each layer setting
        for layers in layer_values:
            logger.info(f"Testing with {layers} GPU layers")
            
            # Update config
            config.parameters["n_gpu_layers"] = layers
            model_manager.save_model_config(config)
            
            # Load model
            model_manager.load_model(model_name)
            
            # Warm-up generation (first run is often slower)
            model_manager.generate(prompt[:100], max_tokens=20)
            
            # Measure generation time (multiple runs for more accurate results)
            times = []
            for i in range(repeats):
                start_time = time.time()
                model_manager.generate(prompt, max_tokens=output_tokens)
                end_time = time.time()
                times.append(end_time - start_time)
                logger.info(f"Run {i+1}: {times[-1]:.2f}s")
            
            # Calculate average time
            avg_time = sum(times) / len(times)
            tokens_per_second = output_tokens / avg_time
            
            # Unload model to free memory
            model_manager.unload_model()
            
            # Add to results
            results.append({
                "gpu_layers": layers,
                "avg_time_seconds": avg_time,
                "tokens_per_second": tokens_per_second
            })
            
            logger.info(f"Layers: {layers}, Avg Time: {avg_time:.2f}s, Tokens/sec: {tokens_per_second:.2f}")
    
    finally:
        # Restore original config
        config.parameters["n_gpu_layers"] = original_layers
        model_manager.save_model_config(config)
    
    return results

def find_optimal_layers(results):
    """Find the optimal number of GPU layers based on test results."""
    if not results:
        return 0
    
    # Filter out any failed tests
    valid_results = [r for r in results if r.get("tokens_per_second", 0) > 0]
    
    if not valid_results:
        return 0
    
    # Sort by tokens per second (descending)
    valid_results.sort(key=lambda x: x.get("tokens_per_second", 0), reverse=True)
    
    # Return the layer setting with the highest tokens per second
    return valid_results[0]["gpu_layers"]

def main():
    parser = argparse.ArgumentParser(description="Test different GPU layer settings")
    parser.add_argument("--model", type=str, required=True, help="Model name to test")
    parser.add_argument("--layers", type=str, default="0,8,16,24,32", 
                        help="Comma-separated list of layer values to test")
    parser.add_argument("--prompt-length", type=int, default=512, 
                        help="Length of test prompt in characters")
    parser.add_argument("--output-tokens", type=int, default=128, 
                        help="Number of tokens to generate")
    parser.add_argument("--repeats", type=int, default=3, 
                        help="Number of test repeats per layer setting")
    args = parser.parse_args()
    
    # Parse layer values
    layer_values = [int(l) for l in args.layers.split(",")]
    
    print(f"Testing model {args.model} with GPU layers: {layer_values}")
    print(f"Using prompt length: {args.prompt_length}, generating {args.output_tokens} tokens")
    print(f"Each test will be repeated {args.repeats} times\n")
    
    # Run the tests
    results = test_gpu_layers(
        args.model, 
        layer_values,
        args.prompt_length,
        args.output_tokens,
        args.repeats
    )
    
    if not results:
        print("Test failed - check logs for details")
        return 1
    
    # Print results in table format
    print("\nResults:")
    print(f"{'GPU Layers':<12} {'Avg Time (s)':<15} {'Tokens/second':<15}")
    print("-" * 42)
    for r in results:
        print(f"{r['gpu_layers']:<12} {r['avg_time_seconds']:<15.2f} {r['tokens_per_second']:<15.2f}")
    
    # Find optimal setting
    optimal_layers = find_optimal_layers(results)
    print(f"\nOptimal setting: {optimal_layers} GPU layers")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
