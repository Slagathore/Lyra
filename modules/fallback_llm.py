"""
Fallback LLM module for Lyra
Provides a lightweight, always-on LLM that can be used when other models are unavailable
"""

import os
import time
import logging
import json
import threading
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Set up logging
logger = logging.getLogger("fallback_llm")

class FallbackLLM:
    """
    Provides a lightweight, always-on LLM capability for Lyra
    Uses a smaller model (like Phi-2 or similar) for fast, reliable responses
    """
    
    def __init__(self, model_path: str = None):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.initialized = False
        self.lock = threading.Lock()
        self.max_tokens = 512
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_length": 512
        }
        
        # Initialize model in background
        self.initialize_thread = threading.Thread(target=self.initialize_model)
        self.initialize_thread.daemon = True
        self.initialize_thread.start()
    
    def initialize_model(self) -> bool:
        """Initialize the fallback model"""
        with self.lock:
            if self.initialized:
                return True
                
            try:
                # Try to import the transformers library
                try:
                    import torch
                    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
                    self.transformers_available = True
                except ImportError:
                    logger.warning("Transformers library not available for fallback LLM")
                    self.transformers_available = False
                    return False
                
                # Look for a default model path if none provided
                if not self.model_path:
                    # Try common locations
                    potential_paths = [
                        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "phi-2"),
                        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "phi3"),
                        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "gemma-2b"),
                        "microsoft/phi-2",
                        "microsoft/phi-1_5",
                        "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
                    ]
                    
                    for path in potential_paths:
                        # Check if local path exists or use model name directly
                        if os.path.exists(path) or "/" in path:
                            self.model_path = path
                            logger.info(f"Using model at: {self.model_path}")
                            break
                
                if not self.model_path:
                    logger.error("No suitable fallback model found")
                    return False
                
                # Load in 8-bit if available to save memory
                try:
                    import bitsandbytes
                    logger.info("Loading 8-bit quantized model to save memory")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        device_map="auto",
                        load_in_8bit=True,
                        torch_dtype=torch.float16
                    )
                except ImportError:
                    # Fall back to regular loading if bitsandbytes not available
                    logger.info("Loading model in standard mode")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        self.model_path,
                        device_map="auto",
                        torch_dtype=torch.float16
                    )
                
                # Load tokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                
                # Set up text generation pipeline
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model,
                    tokenizer=self.tokenizer
                )
                
                logger.info(f"Fallback LLM initialized successfully with model: {self.model_path}")
                self.initialized = True
                return True
                
            except Exception as e:
                logger.error(f"Error initializing fallback LLM: {e}")
                return False
    
    def wait_for_initialization(self, timeout: int = 30) -> bool:
        """
        Wait for model initialization to complete
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            True if initialization complete, False if timed out
        """
        start_time = time.time()
        while not self.initialized:
            if time.time() - start_time > timeout:
                return False
            time.sleep(0.1)
        return True
    
    def generate_text(self, prompt: str, max_tokens: int = None) -> str:
        """
        Generate text based on a prompt
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated text
        """
        if not self.initialized:
            if not self.wait_for_initialization():
                return "Fallback LLM not yet initialized. Please try again in a moment."
        
        try:
            # Apply token limit
            actual_max_tokens = max_tokens or self.max_tokens
            
            # Format prompt for better results
            formatted_prompt = self._format_prompt(prompt)
            
            # Generate text
            with self.lock:
                result = self.pipeline(
                    formatted_prompt,
                    max_new_tokens=actual_max_tokens,
                    temperature=self.generation_config["temperature"],
                    top_p=self.generation_config["top_p"],
                    repetition_penalty=1.1,
                    do_sample=True
                )[0]["generated_text"]
            
            # Extract just the generated part (remove the prompt)
            if result.startswith(formatted_prompt):
                generated_text = result[len(formatted_prompt):]
            else:
                generated_text = result
                
            return generated_text.strip()
            
        except Exception as e:
            logger.error(f"Error generating text with fallback LLM: {e}")
            return f"Error generating response: {str(e)}"
    
    def _format_prompt(self, prompt: str) -> str:
        """
        Format the prompt for better results with the specific model
        
        Args:
            prompt: The original prompt
            
        Returns:
            Formatted prompt
        """
        # For Phi-based models, use a simple instruction format
        if "phi" in self.model_path.lower():
            return f"Instruction: {prompt}\n\nResponse:"
        # For Gemma-based models
        elif "gemma" in self.model_path.lower():
            return f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        # For TinyLlama or general case
        else:
            return f"USER: {prompt}\nASSISTANT:"
    
    def update_generation_config(self, **kwargs) -> None:
        """
        Update generation configuration
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if key in self.generation_config:
                self.generation_config[key] = value
        
        logger.info(f"Updated generation config: {self.generation_config}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about the fallback LLM"""
        return {
            "initialized": self.initialized,
            "model_path": self.model_path,
            "generation_config": self.generation_config
        }

# Singleton instance
_fallback_llm_instance = None

def get_instance(model_path: str = None):
    """Get the singleton instance of FallbackLLM"""
    global _fallback_llm_instance
    if _fallback_llm_instance is None:
        _fallback_llm_instance = FallbackLLM(model_path)
    elif model_path is not None and _fallback_llm_instance.model_path != model_path:
        # Create a new instance if model path changes
        _fallback_llm_instance = FallbackLLM(model_path)
    return _fallback_llm_instance
