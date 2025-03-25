"""Initialize HuggingFace token and environment"""
import os
import sys
from pathlib import Path
from huggingface_hub import login, HfFolder
import logging
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Hugging Face token from credentials file
CREDENTIALS_FILE = "credentials.yml"

def load_hf_token():
    try:
        with open(CREDENTIALS_FILE, "r") as file:
            credentials = yaml.safe_load(file)
            return credentials.get("huggingface_token")
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        raise

def init_huggingface():
    """Initialize HuggingFace environment with token"""
    token = load_hf_token()
    
    try:
        # Save token to HuggingFace folder
        HfFolder.save_token(token)
        
        # Set environment variable
        os.environ['HF_TOKEN'] = token
        
        # Login to HuggingFace
        login(token, add_to_git_credential=True)
        
        # Save to .env file for persistence
        env_path = Path(__file__).parent.parent / '.env'
        env_content = f"HF_TOKEN={token}\n"
        
        # Check if .env exists and if token is already there
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
                if "HF_TOKEN=" not in content:
                    with open(env_path, 'a') as f:
                        f.write(f"\n{env_content}")
        else:
            with open(env_path, 'w') as f:
                f.write(env_content)
        
        logger.info("HuggingFace token configured successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up HuggingFace token: {e}")
        return False

if __name__ == "__main__":
    init_huggingface()