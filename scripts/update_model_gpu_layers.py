import os
import json
import logging
from pathlib import Path
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("update_model_gpu_layers")

def update_model_configs(config_dir="configs", dry_run=False):
    """
    Update all model configurations to use appropriate GPU layers.
    
    Args:
        config_dir: Directory containing model configuration JSON files
        dry_run: If True, only report what would be done without making changes
    
    Returns:
        int: Number of configurations updated
    """
    config_path = Path(config_dir)
    if not config_path.exists():
        logger.error(f"Config directory not found: {config_path}")
        return 0
    
    updated_count = 0
    total_count = 0
    
    # Process each JSON file in the config directory
    for config_file in config_path.glob("*.json"):
        total_count += 1
        try:
            # Load the config
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check if the model file exists
            if "model_path" in config:
                model_path = Path(config["model_path"])
                if model_path.exists():
                    # Get current n_gpu_layers value
                    current_gpu_layers = config.get("n_gpu_layers", 0)
                    
                    # Calculate new value based on model size
                    model_size_bytes = os.stat(model_path).st_size  # Fix: Use st_size attribute
                    model_size_gb = model_size_bytes / (1024**3)
                    
                    # Estimate appropriate GPU layers
                    new_gpu_layers = estimate_gpu_layers(model_path, config.get("model_name", config_file.stem))
                    
                    if new_gpu_layers != current_gpu_layers:
                        logger.info(f"Updating {config_file.name}: changing n_gpu_layers from {current_gpu_layers} to {new_gpu_layers}")
                        
                        if not dry_run:
                            # Update the config
                            config["n_gpu_layers"] = new_gpu_layers
                            with open(config_file, 'w') as f:
                                json.dump(config, f, indent=2)
                            
                        updated_count += 1
                else:
                    logger.warning(f"Model file not found for {config_file.name}: {model_path}")
        except Exception as e:
            logger.error(f"Error processing {config_file}: {e}")
    
    action = "Would update" if dry_run else "Updated"
    logger.info(f"{action} {updated_count} out of {total_count} model configurations")
    
    return updated_count

def estimate_gpu_layers(model_file: Path, model_name: str) -> int:
    """
    Estimate appropriate number of GPU layers based on model size and available VRAM.
    """
    try:
        # Get model size in bytes - FIX: use st_size
        model_size_bytes = os.stat(model_file).st_size  # Fixed to use st_size instead of size
        model_size_gb = model_size_bytes / (1024**3)
        model_name_lower = model_name.lower()
        
        # Base estimation on model size
        if model_size_gb < 5:
            # Small models (<5GB) can usually be fully loaded to GPU
            gpu_layers = 32  # Full model or close to it
        elif model_size_gb < 10:
            # Medium models (5-10GB)
            gpu_layers = 24
        elif model_size_gb < 20:
            # Large models (10-20GB)
            gpu_layers = 20
        elif model_size_gb < 30:
            # XL models (20-30GB)
            gpu_layers = 16
        elif model_size_gb < 40:
            # XXL models (30-40GB)
            gpu_layers = 8
        else:
            # Extremely large models (>40GB)
            gpu_layers = 4  # Just a few layers for attention
            
        # Adjust based on model name indicators
        # Increase for models known to perform well with GPU acceleration
        if "moe" in model_name_lower or "mixture" in model_name_lower:
            # MOE models generally need more GPU layers
            gpu_layers = min(gpu_layers + 8, 40)
        
        # Q4/Q5 quantized models can fit more layers on GPU
        if any(q in model_name_lower for q in ["q4", "q5", "q8"]):
            gpu_layers = min(gpu_layers + 4, 45)
            
        # Small bit models can fit even more
        if any(q in model_name_lower for q in ["q2", "q3"]):
            gpu_layers = min(gpu_layers + 8, 50)
            
        logger.info(f"Estimated {gpu_layers} GPU layers for {model_name} ({model_size_gb:.2f} GB)")
        return gpu_layers
        
    except Exception as e:
        logger.error(f"Error estimating GPU layers: {e}")
        # Default fallback: use a moderate number of layers
        return 8

def main():
    parser = argparse.ArgumentParser(description="Update model configurations with appropriate GPU layers")
    parser.add_argument("--config-dir", type=str, default="configs",
                        help="Directory containing model configurations")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only show what would be done without making changes")
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no changes will be made")
    
    updated = update_model_configs(args.config_dir, args.dry_run)
    
    if args.dry_run:
        print(f"Would update {updated} model configurations with appropriate GPU layers")
    else:
        print(f"Updated {updated} model configurations with appropriate GPU layers")
        print("You'll need to reload models for changes to take effect")

if __name__ == "__main__":
    main()
