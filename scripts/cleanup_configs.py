import os
import json
from pathlib import Path
import shutil
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("cleanup_configs")

def clean_model_configs(config_dir="configs", dry_run=False):
    """
    Clean up model configurations that reference non-existent model files.
    
    Args:
        config_dir: Directory containing model configuration JSON files
        dry_run: If True, only report what would be done without making changes
    
    Returns:
        tuple: (cleaned_count, total_count)
    """
    config_path = Path(config_dir)
    if not config_path.exists():
        logger.error(f"Config directory not found: {config_path}")
        return 0, 0
    
    # Create backup directory
    backup_path = config_path / "invalid_configs"
    if not dry_run:
        backup_path.mkdir(exist_ok=True)
    
    cleaned_count = 0
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
                if not model_path.exists():
                    logger.info(f"Found invalid config: {config_file.name} (model not found: {model_path})")
                    
                    if not dry_run:
                        # Backup the file
                        shutil.copy(config_file, backup_path / config_file.name)
                        
                        # Remove the original
                        config_file.unlink()
                        logger.info(f"Removed invalid config: {config_file}")
                    
                    cleaned_count += 1
        except Exception as e:
            logger.error(f"Error processing {config_file}: {e}")
    
    action = "Would remove" if dry_run else "Removed"
    logger.info(f"{action} {cleaned_count} invalid configurations out of {total_count} total")
    
    return cleaned_count, total_count

def main():
    parser = argparse.ArgumentParser(description="Clean up invalid model configurations")
    parser.add_argument("--config-dir", type=str, default="configs",
                        help="Directory containing model configurations")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only show what would be done without making changes")
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("Running in dry-run mode - no changes will be made")
    
    cleaned, total = clean_model_configs(args.config_dir, args.dry_run)
    
    if args.dry_run:
        print(f"Would remove {cleaned} invalid configurations out of {total} total")
    else:
        print(f"Removed {cleaned} invalid configurations out of {total} total")
        print(f"Backups saved to {Path(args.config_dir) / 'invalid_configs'}")

if __name__ == "__main__":
    main()
