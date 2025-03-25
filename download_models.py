"""
Utility for downloading large models for Lyra
"""
import os
import sys
import argparse
import requests
import logging
from pathlib import Path
from tqdm import tqdm
import concurrent.futures
import json
import hashlib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
MODELS_DIR = os.environ.get(
    "LYRA_MODEL_DIR",
    os.path.join("g:\\AI\\Lyra", "lyra_models")
)
HF_TOKEN = os.environ.get("HF_TOKEN", "")  # For private models
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for download

# Model definitions
DEFAULT_MODELS = {
    "text": {
        "name": "Qwen2.5-QwQ-37B-Eureka",
        "repo": "DavidAU/Qwen2.5-QwQ-37B-Eureka-Triple-Cubed-GGUF",
        "file": "q6_K.gguf",  # Quantized 6-bit version
        "size_gb": 20.5,
    },
    "video": {
        "name": "Wan2.1-I2V",
        "repo": "Wan-AI/Wan2.1-I2V-14B-480P",
        "file": "Wan2.1-I2V-14B-480P.safetensors",
        "size_gb": 14.0,
    }
}

def get_file_hash(filepath, hash_type="sha256"):
    """Calculate file hash to verify integrity"""
    h = hashlib.new(hash_type)
    with open(filepath, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def download_file(url, destination, expected_size=None, token=None):
    """
    Download a file with progress bar
    
    Args:
        url: URL to download from
        destination: Destination path
        expected_size: Expected file size in bytes (optional)
        token: HuggingFace token for private repos
        
    Returns:
        True if successful, False otherwise
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        
        # Check if file already exists and is complete
        if os.path.exists(destination):
            if expected_size and os.path.getsize(destination) == expected_size:
                logger.info(f"File already exists and is complete: {destination}")
                return True
            else:
                # File exists but may be incomplete, we'll resume the download
                current_size = os.path.getsize(destination)
                headers["Range"] = f"bytes={current_size}-"
                mode = "ab"  # Append binary mode
        else:
            current_size = 0
            mode = "wb"  # Write binary mode
        
        # Make request with proper headers
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        
        # Get total size for progress bar
        total_size = int(response.headers.get("content-length", 0))
        if current_size > 0:
            total_size += current_size
        
        # Download with progress bar
        with open(destination, mode) as f:
            with tqdm(
                total=total_size,
                initial=current_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=os.path.basename(destination)
            ) as progress:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
                        progress.update(len(chunk))
        
        return True
    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        return False

def download_hf_model(repo_id, filename, output_dir, token=None):
    """
    Download a file from Hugging Face using their API
    
    Args:
        repo_id: HuggingFace repository ID (e.g. "username/model-name")
        filename: Filename to download
        output_dir: Directory to save the file
        token: HuggingFace token for private repos
        
    Returns:
        Path to the downloaded file or None if it failed
    """
    # Construct the download URL
    url = f"https://huggingface.co/{repo_id}/resolve/main/{filename}"
    
    # Construct the output path
    repo_dir = os.path.join(output_dir, repo_id.replace("/", "_"))
    output_path = os.path.join(repo_dir, filename)
    
    # Create the output directory
    os.makedirs(repo_dir, exist_ok=True)
    
    # Download the file
    logger.info(f"Downloading {repo_id}/{filename} to {output_path}")
    if download_file(url, output_path, token=token):
        logger.info(f"Successfully downloaded {filename}")
        return output_path
    else:
        logger.error(f"Failed to download {filename}")
        return None

def download_model(model_type, output_dir=None, token=None):
    """
    Download a specific model type
    
    Args:
        model_type: Type of model to download ('text' or 'video')
        output_dir: Directory to save the model
        token: HuggingFace token for private repos
        
    Returns:
        Path to the downloaded model or None if it failed
    """
    if output_dir is None:
        output_dir = MODELS_DIR
        
    if model_type not in DEFAULT_MODELS:
        logger.error(f"Unknown model type: {model_type}")
        return None
        
    model_info = DEFAULT_MODELS[model_type]
    
    # Download the model
    return download_hf_model(
        model_info["repo"],
        model_info["file"],
        output_dir,
        token
    )

def main():
    """Main function to parse arguments and download models"""
    parser = argparse.ArgumentParser(description="Download models for Lyra")
    parser.add_argument("--model", choices=["text", "video", "all"], default="text",
                      help="Model type to download")
    parser.add_argument("--output-dir", type=str, default=MODELS_DIR,
                      help="Directory to save models")
    parser.add_argument("--token", type=str, default=HF_TOKEN,
                      help="HuggingFace token for private repos")
    
    args = parser.parse_args()
    
    # Create the output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Download the requested models
    if args.model == "all":
        for model_type in DEFAULT_MODELS:
            download_model(model_type, args.output_dir, args.token)
    else:
        download_model(args.model, args.output_dir, args.token)
    
    logger.info("Download complete!")

if __name__ == "__main__":
    main()
