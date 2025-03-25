"""
Model manager for Lyra - helps download, manage and test models
"""
import os
import sys
import time
import argparse
import json
import shutil
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import requests
from tqdm import tqdm
import hashlib
from huggingface_hub import hf_hub_download, snapshot_download, list_repo_files
from huggingface_hub.utils import RepositoryNotFoundError, RevisionNotFoundError

# Import local LLM integration
from .langchain_local_integration import (
    get_available_models, get_model_info, create_local_llm,
    MODEL_DIR, DEFAULT_MODEL, validate_model_path
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_model_from_hf(repo_id: str, filename: Optional[str] = None, revision: str = "main") -> str:
    """
    Download a model from Hugging Face Hub
    
    Args:
        repo_id: Repository ID on Hugging Face (e.g., 'TheBloke/Llama-2-7B-GGUF')
        filename: Specific filename to download (if None, downloads entire repo)
        revision: The git revision to download (branch, tag, commit hash)
        
    Returns:
        Path to downloaded model
    """
    try:
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        # Determine target directory
        target_dir = os.path.join(MODEL_DIR, repo_id.replace("/", "_"))
        
        if filename:
            # Download specific file
            logger.info(f"Downloading {filename} from {repo_id}...")
            file_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                revision=revision,
                cache_dir=MODEL_DIR,
                local_dir=target_dir,
                local_dir_use_symlinks=False
            )
            logger.info(f"Downloaded to {file_path}")
            return file_path
        else:
            # Download entire repository
            logger.info(f"Downloading entire repository {repo_id}...")
            repo_path = snapshot_download(
                repo_id=repo_id,
                revision=revision,
                cache_dir=MODEL_DIR,
                local_dir=target_dir,
                local_dir_use_symlinks=False
            )
            logger.info(f"Downloaded to {repo_path}")
            return repo_path
    
    except RepositoryNotFoundError:
        logger.error(f"Repository {repo_id} not found on Hugging Face Hub")
        raise
    except RevisionNotFoundError:
        logger.error(f"Revision {revision} not found for repository {repo_id}")
        raise
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        raise

def list_hf_model_files(repo_id: str, revision: str = "main") -> List[Dict[str, Any]]:
    """
    List files in a Hugging Face repository
    
    Args:
        repo_id: Repository ID on Hugging Face
        revision: The git revision
        
    Returns:
        List of file information dictionaries
    """
    try:
        files = list_repo_files(repo_id, revision=revision)
        
        # Filter for common model file extensions
        model_extensions = ['.gguf', '.bin', '.safetensors', '.ckpt', '.pt', '.pth']
        model_files = []
        
        for file in files:
            if any(file.endswith(ext) for ext in model_extensions):
                # Get file info
                model_files.append({
                    "filename": file,
                    "repo_id": repo_id,
                    "revision": revision
                })
        
        return model_files
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return []

def download_url(url: str, target_path: str) -> str:
    """
    Download a file from URL to target path with progress bar
    
    Args:
        url: URL to download
        target_path: Target file path
        
    Returns:
        Path to downloaded file
    """
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        total_size = int(response.headers.get("content-length", 0))
        
        with open(target_path, "wb") as f, tqdm(
            desc=os.path.basename(target_path),
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as progress_bar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                progress_bar.update(len(chunk))
    
    return target_path

def verify_model_file(file_path: str, expected_hash: Optional[str] = None, hash_type: str = "md5") -> bool:
    """
    Verify a model file by checking its hash
    
    Args:
        file_path: Path to the file
        expected_hash: Expected hash value
        hash_type: Hash algorithm (md5, sha256)
        
    Returns:
        True if verification succeeds, False otherwise
    """
    if not os.path.exists(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False
    
    if not expected_hash:
        logger.info(f"No hash provided, skipping verification for {file_path}")
        return True
    
    logger.info(f"Verifying {file_path}...")
    
    # Calculate hash
    hash_func = hashlib.md5() if hash_type == "md5" else hashlib.sha256()
    
    with open(file_path, "rb") as f, tqdm(
        desc=f"Calculating {hash_type}",
        total=os.path.getsize(file_path),
        unit="B",
        unit_scale=True,
        unit_divisor=1024,
    ) as progress_bar:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_func.update(chunk)
            progress_bar.update(len(chunk))
    
    file_hash = hash_func.hexdigest()
    
    if file_hash == expected_hash:
        logger.info(f"Hash verification successful: {file_hash}")
        return True
    else:
        logger.error(f"Hash verification failed! Expected: {expected_hash}, Got: {file_hash}")
        return False

def test_model(model_path: str, prompt: str = "Hello, please introduce yourself briefly.") -> bool:
    """
    Test a model by running a simple inference
    
    Args:
        model_path: Path to the model
        prompt: Test prompt
        
    Returns:
        True if test succeeds, False otherwise
    """
    try:
        logger.info(f"Testing model: {model_path}")
        logger.info(f"Test prompt: {prompt}")
        
        llm = create_local_llm(model_path, temperature=0.7, max_tokens=100)
        if llm is None:
            logger.error("Failed to create LLM")
            return False
        
        start_time = time.time()
        response = llm(prompt)
        end_time = time.time()
        
        logger.info(f"Response: {response}")
        logger.info(f"Inference time: {end_time - start_time:.2f} seconds")
        
        return True
    except Exception as e:
        logger.error(f"Error testing model: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Lyra Model Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available models")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for models on Hugging Face")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--type", choices=["text", "video", "all"], default="all", help="Model type to search for")
    
    # Download command
    download_parser = subparsers.add_parser("download", help="Download a model")
    download_parser.add_argument("repo_id", help="Repository ID on Hugging Face")
    download_parser.add_argument("--filename", help="Specific filename to download")
    download_parser.add_argument("--revision", default="main", help="The git revision")
    download_parser.add_argument("--type", choices=["text", "video"], default="text", 
                                help="Model type (used for organizing models)")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get info about a model")
    info_parser.add_argument("model_path", help="Path to the model")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test a model")
    test_parser.add_argument("model_path", help="Path to the model")
    test_parser.add_argument("--prompt", default="Hello, please introduce yourself briefly.", help="Test prompt")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete a model")
    delete_parser.add_argument("model_path", help="Path to the model")
    
    # Set default command
    set_default_parser = subparsers.add_parser("set-default", help="Set default model")
    set_default_parser.add_argument("model_path", help="Path to the model")
    
    args = parser.parse_args()
    
    if args.command == "list":
        models = get_available_models()
        if not models:
            print("No models available")
            return
        
        print(f"Found {len(models)} models:")
        for i, model in enumerate(models):
            print(f"{i+1}. {model['name']} ({model['type']}, {model['size']})")
            print(f"   Path: {model['path']}")
            if os.path.normpath(model['path']) == os.path.normpath(validate_model_path(None)):
                print("   [DEFAULT]")
            print()
    
    elif args.command == "search":
        try:
            from huggingface_hub import HfApi
            api = HfApi()
            
            model_type = "text-generation" if args.type in ["text", "all"] else None
            if args.type == "video":
                model_type = "text-to-video"
            
            print(f"Searching for models matching '{args.query}'...")
            models = api.list_models(filter=model_type, search=args.query, limit=10)
            
            print(f"Found {len(models)} models:")
            for i, model in enumerate(models):
                print(f"{i+1}. {model.id} - {model.downloads:,} downloads")
                print(f"   Last modified: {model.last_modified}")
                if model.tags:
                    print(f"   Tags: {', '.join(model.tags[:5])}")
                print()
        except Exception as e:
            print(f"Search failed: {e}")
    
    elif args.command == "download":
        try:
            # Create type-specific subdirectory
            target_dir = os.path.join(MODEL_DIR, args.type)
            os.makedirs(target_dir, exist_ok=True)
            
            if args.filename:
                print(f"Downloading {args.filename} from {args.repo_id}...")
                path = download_model_from_hf(args.repo_id, args.filename, args.revision)
            else:
                print(f"Downloading repository {args.repo_id}...")
                path = download_model_from_hf(args.repo_id, revision=args.revision)
            
            print(f"Download successful: {path}")
        except Exception as e:
            print(f"Download failed: {e}")
    
    elif args.command == "info":
        try:
            info = get_model_info(args.model_path)
            print(json.dumps(info, indent=2))
        except Exception as e:
            print(f"Failed to get model info: {e}")
    
    elif args.command == "test":
        success = test_model(args.model_path, args.prompt)
        if success:
            print("Test successful!")
        else:
            print("Test failed!")
    
    elif args.command == "delete":
        try:
            model_path = validate_model_path(args.model_path)
            if os.path.isdir(model_path):
                shutil.rmtree(model_path)
            else:
                os.remove(model_path)
            print(f"Deleted {model_path}")
        except Exception as e:
            print(f"Failed to delete model: {e}")
    
    elif args.command == "set-default":
        try:
            model_path = validate_model_path(args.model_path)
            default_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env.local")
            
            with open(default_path, "a+") as f:
                f.seek(0)
                content = f.read()
                if "LYRA_DEFAULT_MODEL" in content:
                    # Replace existing value
                    lines = content.splitlines()
                    new_lines = []
                    for line in lines:
                        if line.startswith("LYRA_DEFAULT_MODEL="):
                            new_lines.append(f"LYRA_DEFAULT_MODEL={model_path}")
                        else:
                            new_lines.append(line)
                    
                    f.seek(0)
                    f.truncate()
                    f.write("\n".join(new_lines))
                else:
                    # Add new value
                    f.write(f"\nLYRA_DEFAULT_MODEL={model_path}\n")
            
            print(f"Set default model to: {model_path}")
        except Exception as e:
            print(f"Failed to set default model: {e}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
