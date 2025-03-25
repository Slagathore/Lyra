import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("base_provider")

class BaseModel:
    """Base class for language model providers."""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        
        # Initialize the model
        self._initialize()
    
    def _initialize(self):
        """Initialize the model. Override in subclasses."""
        logger.info(f"Base model initialized with config: {self.config.model_name}")
    
    def generate(self, prompt: str, **kwargs):
        """
        Generate a response to the given prompt.
        This method should be overridden by subclasses.
        """
        logger.warning("Base model generate() called - this should be overridden")
        return f"BaseModel response (not implemented) to: {prompt}"
    
    def cleanup(self):
        """Clean up resources. Override in subclasses if needed."""
        logger.info("Base model cleanup")
        self.model = None
