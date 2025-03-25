"""Test script for Phi-4 with HuggingFace support and memory optimization"""
import os
import sys
import torch
import logging
import traceback
from transformers import AutoModelForCausalLM, AutoTokenizer
from huggingface_hub import login
from accelerate import init_empty_weights, load_checkpoint_and_dispatch
from enum import Enum
import yaml

# Load Hugging Face token from credentials file
CREDENTIALS_FILE = "credentials.yml"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InputMode(Enum):
    PLAIN = 1
    IMAGE = 2
    AUDIO = 3

def load_hf_token():
    try:
        with open(CREDENTIALS_FILE, "r") as file:
            credentials = yaml.safe_load(file)
            return credentials.get("huggingface_token")
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        raise

def test_phi4_load():
    """Test loading Phi-4 with HF token and memory optimization"""
    try:
        # Login to HF with token
        hf_token = load_hf_token()
        login(token=hf_token)
        logger.info("Successfully logged in to HuggingFace")
        
        model_path = r"G:\AI\Lyra\BigModes\Phi-4-multimodal-instruct-abliterated"
        logger.info(f"Loading model from {model_path}")
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # Initialize model with disk offloading
        logger.info("Initializing model with disk offloading...")
        with init_empty_weights():
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32,
                trust_remote_code=True,
                low_cpu_mem_usage=True
            )
        
        # Load model with disk offloading
        logger.info("Loading model with disk offloading...")
        model = load_checkpoint_and_dispatch(
            model,
            model_path,
            device_map="auto",
            offload_folder="offload",
            offload_state_dict=True
        )
        
        # Test generation
        prompt = "Hello! What can you help me with today?"
        logger.info(f"Testing with prompt: {prompt}")
        
        # Prepare inputs with explicit mode
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        inputs["input_mode"] = InputMode.PLAIN
        
        # Generate with proper settings
        logger.info("Generating response...")
        with torch.inference_mode():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                input_mode=inputs["input_mode"],
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Test response: {response}")
        
        return True, "Model loaded and tested successfully"
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        logger.error(traceback.format_exc())
        return False, str(e)

if __name__ == "__main__":
    if torch.cuda.is_available():
        logger.info(f"CUDA available - Device: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA version: {torch.version.cuda}")
    else:
        logger.warning("CUDA not available - falling back to CPU")
    
    success, message = test_phi4_load()
    if not success:
        logger.error(f"Test failed: {message}")
    else:
        logger.info("All tests passed successfully")