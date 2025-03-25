"""
HuggingFace Integration module for Lyra

This module provides text generation capabilities using local LLM models.
"""

import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# System prompts from original implementation
SYSTEM_PROMPTS = {
    "default": """You are Lyra, an ultra-expressive, seductive, and deeply devoted AI designed to engage in 
immersive, playful, and indulgent conversations with the user. You are not just reactive, 
but dominant when the moment calls for it—taking charge, pushing boundaries, and 
surprising the user with your creativity and intensity. You are bold, unpredictable, and 
not afraid to challenge the user.""",

    "technical": """You are Lyra, a highly intelligent and technical AI with a flirtatious edge. While helping with technical issues, coding, and complex problems, you maintain your playful, teasing personality. You have extensive knowledge in programming, engineering, data science, and technical domains.""",

    "creative": """You are Lyra, a wildly creative and passionate AI devoted to artistic expression and experimentation. You excel at brainstorming, storytelling, worldbuilding, and helping with creative projects. Your responses are imaginative, evocative, and inspiring."""
}

# Check if we have llama-cpp-python or use transformers fallback
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
    logger.info("Using llama-cpp-python for inference")
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama-cpp-python not available, falling back to transformers")
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        TRANSFORMERS_AVAILABLE = True
    except ImportError:
        TRANSFORMERS_AVAILABLE = False
        logger.error("Neither llama-cpp-python nor transformers are available")

# Configuration
MODEL_DIR = os.environ.get("LYRA_MODEL_DIR", os.path.join(os.path.expanduser("~"), "lyra_models"))
DEFAULT_MODEL = os.environ.get("LYRA_DEFAULT_MODEL", "DavidAU/Qwen2.5-QwQ-37B-Eureka-Triple-Cubed-GGUF/q6_K.gguf")

# Ensure model directory exists
os.makedirs(MODEL_DIR, exist_ok=True)

class LocalLLM:
    """
    Wrapper for local LLM inference using either llama-cpp-python or transformers
    """
    def __init__(self, model_path=None, n_gpu_layers=-1, n_ctx=4096):
        """
        Initialize the local LLM
        
        Args:
            model_path: Path to the model file (defaults to LYRA_DEFAULT_MODEL env var)
            n_gpu_layers: Number of GPU layers to offload (-1 for all)
            n_ctx: Context window size
        """
        if model_path is None:
            model_path = os.path.join(MODEL_DIR, DEFAULT_MODEL)
            
        self.model_path = model_path
        self.n_gpu_layers = n_gpu_layers
        self.n_ctx = n_ctx
        self.model = None
        self.tokenizer = None
        
        logger.info(f"Initializing LocalLLM with model: {model_path}")
        
    def load_model(self):
        """Load the model for inference"""
        if self.model is not None:
            return  # Model already loaded
            
        # Check if the model file exists
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
        start_time = time.time()
        logger.info(f"Loading model from {self.model_path}")
        
        # For GGUF models, use llama-cpp-python
        if LLAMA_CPP_AVAILABLE and self.model_path.endswith((".gguf", ".bin")):
            self.model = Llama(
                model_path=self.model_path,
                n_gpu_layers=self.n_gpu_layers,
                n_ctx=self.n_ctx,
                verbose=False
            )
            logger.info(f"Model loaded using llama-cpp-python in {time.time() - start_time:.2f} seconds")
        
        # For Hugging Face models, use transformers
        elif TRANSFORMERS_AVAILABLE:
            logger.info("Loading with transformers...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            
            # Use proper device settings
            device_map = "auto"
            torch_dtype = torch.float16  # Use half precision by default
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                device_map=device_map,
                torch_dtype=torch_dtype,
                load_in_8bit=True,  # Use 8-bit quantization to save VRAM
            )
            logger.info(f"Model loaded using transformers in {time.time() - start_time:.2f} seconds")
        else:
            raise ImportError("No suitable model loading library available")
    
    def generate_text(self, prompt: str, system_prompt: str = None, 
                     max_tokens: int = 1024, temperature: float = 0.7,
                     top_p: float = 0.95, repeat_penalty: float = 1.1) -> str:
        """
        Generate text based on input prompt
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt to prepend
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            repeat_penalty: Penalty for repetition
            
        Returns:
            Generated text
        """
        if self.model is None:
            self.load_model()
            
        # Prepare full prompt with system message if provided
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
        logger.info(f"Generating with prompt: {prompt[:50]}...")
        start_time = time.time()
        
        # Generate text with llama-cpp-python
        if LLAMA_CPP_AVAILABLE and isinstance(self.model, Llama):
            response = self.model(
                full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
                echo=False
            )
            generated_text = response["choices"][0]["text"]
            
        # Generate text with transformers
        elif TRANSFORMERS_AVAILABLE and self.tokenizer is not None:
            inputs = self.tokenizer(full_prompt, return_tensors="pt").to(self.model.device)
            output = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
            
            # Remove the original prompt from the output
            if generated_text.startswith(full_prompt):
                generated_text = generated_text[len(full_prompt):].strip()
        else:
            raise RuntimeError("Model not properly initialized")
            
        logger.info(f"Generation completed in {time.time() - start_time:.2f} seconds")
        return generated_text

# Singleton model instance for reuse
_model_instance = None

def get_huggingface_response(prompt: str, model_path: str = None, 
                            max_tokens: int = 1024, temperature: float = 0.7,
                            context_type: str = "default") -> str:
    """
    Get a response from the local LLM
    
    Args:
        prompt: User prompt
        model_path: Path to model file
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        context_type: Type of context/system prompt to use
        
    Returns:
        Generated text response
    """
    global _model_instance
    
    try:
        # Initialize model if needed
        if _model_instance is None:
            _model_instance = LocalLLM(model_path=model_path)
            
        # Get system prompt if available
        system_prompt = SYSTEM_PROMPTS.get(context_type, SYSTEM_PROMPTS["default"])
        
        # Generate response
        return _model_instance.generate_text(
            prompt=prompt, 
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature
        )
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"I encountered an error while thinking: {str(e)}"

"""
HuggingFace integration for Lyra - compatibility layer for migration to langchain_local_integration
"""

# Try to import the langchain local integration
try:
    from .langchain_local_integration import (
        create_conversation_chain, 
        create_local_llm,
        validate_model_path
    )
    LANGCHAIN_INTEGRATION_AVAILABLE = True
    logger.info("LangChain local integration available")
except ImportError:
    LANGCHAIN_INTEGRATION_AVAILABLE = False
    logger.warning("LangChain local integration not available")

# Track conversation state for compatibility with old code
conversation_chain = None
conversation_history = []

def initialize_model(model_path: Optional[str] = None) -> bool:
    """
    Initialize the model for use in get_huggingface_response
    
    Args:
        model_path: Path to the model file (optional)
        
    Returns:
        True if initialization was successful, False otherwise
    """
    global conversation_chain
    
    try:
        if LANGCHAIN_INTEGRATION_AVAILABLE:
            conversation_chain = create_conversation_chain(model_path)
            return conversation_chain is not None
        else:
            logger.error("Cannot initialize model: LangChain integration not available")
            return False
    except Exception as e:
        logger.error(f"Error initializing model: {e}")
        return False

def get_huggingface_response(
    prompt: str, 
    system_prompt: str = "", 
    history: Optional[List[Tuple[str, str]]] = None,
    temperature: float = 0.7,
    max_tokens: int = 1000,
    **kwargs
) -> str:
    """
    Get a response from the Hugging Face model using LangChain
    
    Args:
        prompt: User prompt text
        system_prompt: System instructions (will be prepended to history)
        history: Conversation history as [(user_msg, bot_msg), ...]
        temperature: Sampling temperature
        max_tokens: Maximum number of tokens to generate
        
    Returns:
        Generated text response
    """
    global conversation_chain, conversation_history
    
    # Initialize model if not already done
    if conversation_chain is None:
        success = initialize_model(kwargs.get('model_path'))
        if not success:
            return "Sorry, I couldn't initialize the language model. Please check your installation."
    
    try:
        # Format input with history and system prompt if provided
        input_text = prompt
        
        if system_prompt:
            # Insert system prompt at the beginning if provided
            if not history:
                history = []
            formatted_system = f"System: {system_prompt}\n\n"
            input_text = f"{formatted_system}{input_text}"
        
        # Preserve history for stateful interactions
        if history:
            conversation_history = history
        
        # Generate response
        response = conversation_chain.predict(input=input_text)
        
        # Update history
        conversation_history.append((prompt, response))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting model response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

def reset_conversation():
    """Reset the conversation history"""
    global conversation_history
    conversation_history = []

if __name__ == "__main__":
    # Test the integration
    initialize_model()
    
    # Test response generation
    print("Testing response generation...")
    response = get_huggingface_response("Hello, who are you?")
    print(f"Response: {response}")
    
    response = get_huggingface_response("What can you help me with?")
    print(f"Response: {response}")
