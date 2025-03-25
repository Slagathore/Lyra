import os
import logging
import gradio as gr
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from modules.model_manager import ModelManager

# Configure logging
logger = logging.getLogger(__name__)

class ChatInterface:
    """Chat interface for interacting with LLM models."""
    
    def __init__(self):
        """Initialize the chat interface with model manager and settings."""
        self.model_manager = ModelManager()
        self.available_models = list(self.model_manager.model_configs.keys())
        self.history = []
        self.session_id = f"chat_{int(time.time())}"
        self.system_prompt = "You are a helpful AI assistant named Lyra. Answer the user's questions accurately and concisely."
        
        # Load settings or use defaults
        self.settings = self._load_settings()
        self.save_dir = Path(self.settings.get("save_dir", "chat_history"))
        self.save_dir.mkdir(exist_ok=True, parents=True)
        
        logger.info(f"Chat interface initialized with {len(self.available_models)} available models")
        if not self.available_models:
            logger.warning("No models found in configuration")
        else:
            logger.info(f"Available models: {', '.join(self.available_models[:5])}" + 
                       (f" and {len(self.available_models)-5} more" if len(self.available_models) > 5 else ""))
    
    def _load_settings(self):
        """Load chat interface settings from disk or return defaults."""
        settings_path = Path("configs/chat_settings.json")
        default_settings = {
            "save_dir": "chat_history",
            "max_history": 100,
            "default_system_prompt": self.system_prompt,
            "default_temperature": 0.7,
            "default_max_length": 512
        }
        
        if not settings_path.exists():
            logger.info("No chat settings file found, using defaults")
            return default_settings
            
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            logger.info("Loaded chat settings from disk")
            
            # Merge with defaults for missing keys
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
                    
            return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return default_settings
    
    def refresh_models(self):
        """Refresh the list of available models."""
        # Rediscover models
        self.model_manager._discover_models()
        # Reload model configurations
        self.model_manager._load_configs()
        
        # Update available models list
        self.available_models = list(self.model_manager.model_configs.keys())
        logger.info(f"Refreshed models: {len(self.available_models)} available")
        
        # Return updated dropdown choices - using correct Gradio syntax for compatibility
        return gr.update(choices=self.available_models)
    
# This function MUST be present for the import to work
def create_chat_interface():
    """Create and return a chat interface instance."""
    chat_ui = ChatInterface()
    return chat_ui.create_ui()
