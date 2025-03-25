"""
Phi-4 Multimodal Processor
Provides processor class for the Phi-4 multimodal model in Lyra
"""

import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple

# Set up logging
logger = logging.getLogger(__name__)

class Phi4MMProcessor:
    """
    Processor for Phi-4 Multimodal model
    This is a wrapper around the transformers AutoProcessor
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the Phi-4 multimodal processor
        
        Args:
            model_path: Path to the model (optional, will use environment variable or default path if not provided)
        """
        self.model_path = self._get_model_path(model_path)
        self.processor = None
        self.tokenizer = None
        self.initialized = False
        
    def _get_model_path(self, model_path: Optional[str] = None) -> str:
        """
        Get the path to the Phi-4 multimodal model.
        
        Args:
            model_path: Path to the model (optional)
            
        Returns:
            The path to the model
        """
        # Priority:
        # 1. Explicitly provided path
        # 2. Environment variable
        # 3. Default locations
        
        if model_path:
            return model_path
        
        # Check environment variable
        env_path = os.environ.get("LYRA_MODEL_PATH")
        if env_path and "phi-4" in env_path.lower() and os.path.exists(env_path):
            return env_path
        
        # Check default locations
        default_paths = [
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "BigModes", "Phi-4-multimodal-instruct-abliterated"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "Phi-4-multimodal-instruct-abliterated"),
            "G:\\AI\\Lyra\\BigModes\\Phi-4-multimodal-instruct-abliterated",
            "C:\\AI\\models\\Phi-4-multimodal-instruct-abliterated",
            "D:\\AI\\models\\Phi-4-multimodal-instruct-abliterated"
        ]
        
        for path in default_paths:
            if os.path.exists(path):
                return path
        
        # If no valid path is found, return the first default path (it will be checked for existence later)
        return default_paths[0]
        
    def initialize(self):
        """
        Initialize the processor by loading the actual AutoProcessor
        """
        try:
            from transformers import AutoProcessor
            logger.info(f"Loading Phi-4 multimodal processor from {self.model_path}")
            self.processor = AutoProcessor.from_pretrained(
                self.model_path,
                trust_remote_code=True
            )
            self.tokenizer = self.processor.tokenizer
            self.initialized = True
            logger.info("Phi-4 multimodal processor initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error initializing Phi-4 multimodal processor: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def __call__(self, text, images=None, audio=None, return_tensors=None):
        """
        Process inputs for the Phi-4 multimodal model
        
        Args:
            text: The text input
            images: Optional image input(s)
            audio: Optional audio input(s)
            return_tensors: The tensor format to return ('pt' for PyTorch)
            
        Returns:
            Processed inputs
        """
        if not self.initialized:
            self.initialize()
            
        if not self.processor:
            raise ValueError("Processor is not initialized")
            
        return self.processor(
            text=text,
            images=images,
            audio=audio,
            return_tensors=return_tensors
        )
    
    def batch_decode(self, *args, **kwargs):
        """
        Decode token ids to text
        
        Args:
            *args: Arguments to pass to the tokenizer's batch_decode method
            **kwargs: Keyword arguments to pass to the tokenizer's batch_decode method
            
        Returns:
            Decoded text
        """
        if not self.initialized:
            self.initialize()
            
        if not self.tokenizer:
            raise ValueError("Tokenizer is not initialized")
            
        return self.tokenizer.batch_decode(*args, **kwargs)
        
    @classmethod
    def from_pretrained(cls, model_path):
        """
        Create a processor from a pretrained model
        
        Args:
            model_path: Path to the model
            
        Returns:
            Processor instance
        """
        processor = cls(model_path)
        processor.initialize()
        return processor