"""
Update environment configuration with correct CUDA paths
"""
import os
import json
import glob
import sys
from pathlib import Path

def find_cuda_path():
    """Find CUDA installation on the system"""
    # Standard location for CUDA 12.8
    std_path = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"
    if os.path.exists(std_path):
        return std_path
    
    # Check other versions in standard location
    cuda_paths = []
    potential_paths = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v*"
    ]
    
    for pattern in potential_paths:
        paths = glob.glob(pattern)
        if paths:
            cuda_paths.extend(paths)
    
    # If found in standard location, return the latest version
    if cuda_paths:
        # Sort by version number to get the latest
        cuda_paths.sort(reverse=True)
        return cuda_paths[0]
    
    # Fallback to check env vars
    cuda_path_env = os.environ.get("CUDA_PATH")
    if cuda_path_env and os.path.exists(cuda_path_env):
        return cuda_path_env
        
    # Return a default path if nothing found
    return r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.8"

def update_env_config():
    """Update environment configuration with correct CUDA paths"""
    cuda_path = find_cuda_path()
    env_config_path = "env_config.json"
    
    # Create or update env_config.json
    if os.path.exists(env_config_path):
        with open(env_config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}
    
    # Update CUDA paths
    config["cuda_path"] = cuda_path
    config["root_path"] = "G:\\AI\\Lyra"
    config["model_path"] = "G:\\AI\\Lyra\\BigModes\\Qwen2.5-QwQ-35B-Eureka-3-ablit-uncen-gguf\\Qwen2.5-QwQ-35B-Eureka-Cubed-abliterated-uncensored-D_AU-Q6_k.gguf"
    config["data_path"] = "G:\\AI\\Lyra\\data"
    config["logs_path"] = "G:\\AI\\Lyra\\logs"
    config["temp_path"] = "G:\\AI\\Lyra\\temp"
    config["use_c_drive"] = True
    config["environment_variables"] = {
        "CUDA_PATH": cuda_path,
        "CUDA_HOME": cuda_path,
        "PATH_ADDITIONS": [
            f"{cuda_path}\\bin", 
            f"{cuda_path}\\libnvvp"
        ],
        "GGML_CUDA_NO_PINNED": "1",
        "GGML_CUDA_FORCE_MMQ": "1",
        "GGML_CUDA_MEM_PERCENT": "90",
        "CUDA_VISIBLE_DEVICES": "0"
    }
    
    # Save config
    with open(env_config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"Environment configuration updated with CUDA path: {cuda_path}")

if __name__ == "__main__":
    update_env_config()
    print("Environment configuration updated successfully.")
