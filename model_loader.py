"""
Model loader for Lyra - handles loading and management of language models
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Any

# Set up logging
logger = logging.getLogger("model_loader")

class ModelInterface:
    """Interface for different LLM backends"""
    
    def __init__(self, model_name: str, model_type: str):
        self.model_name = model_name
        self.model_type = model_type
        self.model = None
        self.initialized = False
        
    def initialize(self) -> bool:
        """Initialize the model"""
        # Must be implemented by subclasses
        raise NotImplementedError
        
    def generate_text(self, prompt: str, max_tokens: int = 1024) -> str:
        """Generate text from prompt"""
        # Must be implemented by subclasses
        raise NotImplementedError
        
    def get_embeddings(self, text: str) -> Optional[List[float]]:
        """Get embeddings for text"""
        # Optional feature, not all models support this
        return None
        
    def tokenize(self, text: str) -> List[int]:
        """Tokenize text into token IDs"""
        # Optional feature, not all models support this
        return []
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model"""
        return {
            "name": self.model_name,
            "type": self.model_type,
            "initialized": self.initialized
        }

class ModelLoader:
    """Handles loading different types of models"""
    
    def __init__(self):
        self.fallback_llm = None
        
        # Try to initialize the fallback LLM if available
        try:
            from modules.fallback_llm import get_instance as get_fallback_llm
            self.fallback_llm = get_fallback_llm()
            logger.info("Fallback LLM initialized")
        except ImportError:
            logger.warning("Fallback LLM not available")
    
    def load_model(self, model_config) -> Optional[ModelInterface]:
        """
        Load a model based on its configuration
        
        Args:
            model_config: Configuration for the model
            
        Returns:
            Initialized ModelInterface or None if loading failed
        """
        try:
            model_type = model_config.get("type", "unknown").lower()
            model_name = model_config.get("name", "unknown")
            model_path = model_config.get("path")
            
            logger.info(f"Loading model '{model_name}' of type '{model_type}'")
            
            # Handle different model types
            if model_type == "llama.cpp":
                return self._load_llama_cpp_model(model_config)
            elif model_type == "openai":
                return self._load_openai_model(model_config)
            elif model_type == "huggingface":
                return self._load_huggingface_model(model_config)
            elif model_type == "api":
                return self._load_api_model(model_config)
            elif model_type == "ollama":
                return self._load_ollama_model(model_config)
            elif model_type == "phi":
                return self._load_phi_model(model_config)
            else:
                logger.error(f"Unsupported model type: {model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return None
    
    def _load_llama_cpp_model(self, config) -> Optional[ModelInterface]:
        """Load a model using llama.cpp"""
        try:
            # Import here to avoid dependency issues
            from model_backends.llama_cpp_backend import LlamaCppInterface
            
            interface = LlamaCppInterface(
                model_name=config.get("name", "llama_model"),
                model_path=config.get("path")
            )
            
            if interface.initialize():
                return interface
            else:
                return None
                
        except ImportError:
            logger.error("llama.cpp backend not available")
            return None
    
    def _load_openai_model(self, config) -> Optional[ModelInterface]:
        """Load a model using OpenAI API"""
        try:
            # Import here to avoid dependency issues
            from model_backends.openai_backend import OpenAIInterface
            
            interface = OpenAIInterface(
                model_name=config.get("name", "gpt-3.5-turbo"),
                api_key=config.get("api_key")
            )
            
            if interface.initialize():
                return interface
            else:
                return None
                
        except ImportError:
            logger.error("OpenAI backend not available")
            return None
    
    def _load_huggingface_model(self, config) -> Optional[ModelInterface]:
        """Load a model using Hugging Face Transformers"""
        try:
            # Import here to avoid dependency issues
            from model_backends.huggingface_backend import HuggingFaceInterface
            
            interface = HuggingFaceInterface(
                model_name=config.get("name", "unknown"),
                model_path=config.get("path")
            )
            
            if interface.initialize():
                return interface
            else:
                return None
                
        except ImportError:
            logger.error("Hugging Face backend not available")
            return None
    
    def _load_api_model(self, config) -> Optional[ModelInterface]:
        """Load a model using a generic API endpoint"""
        try:
            # Import here to avoid dependency issues
            from model_backends.api_backend import ApiInterface
            
            interface = ApiInterface(
                model_name=config.get("name", "api_model"),
                api_url=config.get("url"),
                api_key=config.get("api_key")
            )
            
            if interface.initialize():
                return interface
            else:
                return None
                
        except ImportError:
            logger.error("API backend not available")
            return None
    
    def _load_ollama_model(self, config) -> Optional[ModelInterface]:
        """Load a model using Ollama"""
        try:
            # Import here to avoid dependency issues
            from model_backends.ollama_backend import OllamaInterface
            
            interface = OllamaInterface(
                model_name=config.get("name", "llama2"),
                host=config.get("host", "localhost"),
                port=config.get("port", 11434)
            )
            
            if interface.initialize():
                return interface
            else:
                return None
                
        except ImportError:
            logger.error("Ollama backend not available")
            return None
    
    def _load_phi_model(self, config) -> Optional[ModelInterface]:
        """Load Microsoft Phi models"""
        try:
            # Import here to avoid dependency issues
            from model_backends.phi_backend import PhiInterface
            
            interface = PhiInterface(
                model_name=config.get("name", "phi-2"),
                model_path=config.get("path")
            )
            
            if interface.initialize():
                return interface
            else:
                # Try using fallback LLM if available
                if self.fallback_llm:
                    from model_backends.fallback_backend import FallbackInterface
                    fallback = FallbackInterface(
                        model_name=config.get("name", "phi-fallback"),
                        fallback_llm=self.fallback_llm
                    )
                    if fallback.initialize():
                        return fallback
                return None
                
        except ImportError:
            logger.error("Phi model backend not available")
            
            # Try using fallback LLM if available
            if self.fallback_llm:
                from model_backends.fallback_backend import FallbackInterface
                fallback = FallbackInterface(
                    model_name=config.get("name", "phi-fallback"),
                    fallback_llm=self.fallback_llm
                )
                if fallback.initialize():
                    return fallback
            return None
    
    def get_fallback_interface(self) -> Optional[ModelInterface]:
        """
        Get an interface using the fallback LLM
        Useful when primary model loading fails
        """
        if not self.fallback_llm:
            return None
            
        try:
            from model_backends.fallback_backend import FallbackInterface
            
            interface = FallbackInterface(
                model_name="fallback-model",
                fallback_llm=self.fallback_llm
            )
            
            if interface.initialize():
                return interface
            else:
                return None
        except Exception as e:
            logger.error(f"Error creating fallback interface: {e}")
            return None

# Add singleton instance support
_model_loader_instance = None

def get_instance():
    """Get the singleton instance of ModelLoader"""
    global _model_loader_instance
    if _model_loader_instance is None:
        _model_loader_instance = ModelLoader()
    return _model_loader_instance

# Add the get_instance method to the ModelLoader class itself for compatibility
ModelLoader.get_instance = get_instance
