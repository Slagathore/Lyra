"""Test Phi-4 model loading with HuggingFace initialization"""
import os
import sys
import json
import logging
import torch
from pathlib import Path
from huggingface_hub import login, HfApi
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_credentials():
    """Load HuggingFace credentials"""
    creds_path = Path(__file__).parent.parent / 'secure_credentials.json'
    try:
        with open(creds_path, 'r') as f:
            creds = json.load(f)
            return creds.get('huggingface', {})
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return {}

def init_huggingface():
    """Initialize HuggingFace environment"""
    creds = load_credentials()
    write_token = creds.get('write_token')
    read_token = creds.get('read_token')
    
    token = write_token or read_token
    if not token:
        logger.error("No HuggingFace token found")
        return False
    
    try:
        login(token)
        logger.info("Successfully logged in to HuggingFace Hub")
        return True
    except Exception as e:
        logger.error(f"Failed to login to HuggingFace Hub: {e}")
        return False

def test_phi4_load():
    """Test loading Phi-4 model"""
    model_path = r"G:\AI\Lyra\BigModes\Phi-4-multimodal-instruct-abliterated"
    
    try:
        logger.info("Loading Phi-4 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        logger.info("Loading Phi-4 model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
            trust_remote_code=True,
            attn_implementation="flash_attention_2"
        )
        
        # Test basic generation
        logger.info("Testing model generation...")
        prompt = "Hello! What can you help me with today?"
        
        # Format input with mode specification
        formatted_input = {
            "input_ids": tokenizer(prompt, return_tensors="pt").input_ids.to(model.device),
            "input_mode": "text",  # Specify text mode
            "return_dict": True
        }
        
        outputs = model.generate(
            **formatted_input,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True
        )
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Test response: {response}")
        
        return True, "Model loaded and tested successfully"
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, str(e)

if __name__ == "__main__":
    if not init_huggingface():
        sys.exit(1)
        
    success, message = test_phi4_load()
    if not success:
        logger.error(f"Test failed: {message}")
        sys.exit(1)
    
    logger.info("All tests passed successfully")