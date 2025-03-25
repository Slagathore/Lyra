"""
Utility script to reset the model configuration file
"""
import os
from pathlib import Path
import json
import sys

CONFIG_FILE = Path('G:/AI/Lyra/model_config.json')

def reset_config():
    """Reset the model configuration file to a minimal valid state"""
    if os.path.exists(CONFIG_FILE):
        backup_path = str(CONFIG_FILE) + f".bak_{int(__import__('time').time())}"
        try:
            import shutil
            shutil.copy2(CONFIG_FILE, backup_path)
            print(f"Created backup of existing config at {backup_path}")
        except Exception as e:
            print(f"Warning: Could not create backup: {e}")
    
    # Create a minimal valid configuration
    minimal_config = {
        "models": []
    }
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(minimal_config, f, indent=2)
        print(f"Successfully reset configuration file at {CONFIG_FILE}")
        print("The next time you run model_config.py, it will scan for models and create a new configuration")
        return True
    except Exception as e:
        print(f"Error creating new configuration: {e}")
        return False

if __name__ == "__main__":
    print("This will reset your Lyra model configuration file.")
    print("Your existing models will not be affected, but you'll need to re-scan for them.")
    response = input("Continue? (y/n): ")
    
    if response.lower() in ('y', 'yes'):
        if reset_config():
            print("Configuration reset successful.")
        else:
            print("Configuration reset failed.")
    else:
        print("Operation cancelled.")
