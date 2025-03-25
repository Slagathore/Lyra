"""Script to set up HuggingFace tokens"""
import os
import sys
import json
from huggingface_hub import login
from pathlib import Path

def setup_tokens():
    print("HuggingFace Token Setup")
    print("======================")
    
    # Load tokens from secure credentials
    creds_path = Path(__file__).parent.parent / 'secure_credentials.json'
    if not creds_path.exists():
        print("Error: secure_credentials.json not found")
        return False
        
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            
        hf_creds = creds.get('huggingface', {})
        read_token = hf_creds.get('read_token')
        write_token = hf_creds.get('write_token')
        
        if not read_token and not write_token:
            print("No HuggingFace tokens found in credentials")
            return False
            
        # Set up environment variables
        os.environ['HF_TOKEN'] = write_token or read_token  # Prefer write token if available
        os.environ['HF_READ_TOKEN'] = read_token if read_token else ""
        os.environ['HF_WRITE_TOKEN'] = write_token if write_token else ""
        
        # Log in to HuggingFace with the write token if available, otherwise use read token
        token_to_use = write_token or read_token
        login(token_to_use, add_to_git_credential=True)
        
        # Save tokens to environment file
        env_path = Path(__file__).parent.parent / '.env'
        env_content = []
        if read_token:
            env_content.append(f"HF_READ_TOKEN={read_token}")
        if write_token:
            env_content.append(f"HF_WRITE_TOKEN={write_token}")
            env_content.append(f"HF_TOKEN={write_token}")  # Set main token to write token
        elif read_token:
            env_content.append(f"HF_TOKEN={read_token}")  # Set main token to read token if no write token
            
        with open(env_path, 'a') as f:
            f.write('\n'.join(env_content) + '\n')
            
        print("\nTokens successfully configured!")
        print(f"Read token {'configured' if read_token else 'not found'}")
        print(f"Write token {'configured' if write_token else 'not found'}")
        print("You may need to restart any running instances for the changes to take effect.")
        return True
        
    except Exception as e:
        print(f"\nError setting up tokens: {str(e)}")
        return False

if __name__ == "__main__":
    setup_tokens()