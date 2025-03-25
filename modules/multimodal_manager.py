import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class MultimodalManager:
    """Manages models for different multimodal tasks"""
    
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        self.config_path = os.path.join(self.data_dir, "multimodal_config.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Default task models
        self.task_models = {
            "chat": "",          # Primary chat model
            "text_generation": "",  # Text completion
            "image_generation": "",  # Image generation model
            "text_to_image": "",  # Text-to-image model
            "text_to_speech": "",  # TTS model
            "code_generation": "",  # Code generation
            "embedding": "",     # Embedding model
            "vision": ""         # Vision model for image understanding
        }
        
        # Additional settings for each task
        self.task_settings = {
            "chat": {},
            "text_generation": {},
            "image_generation": {},
            "text_to_image": {},
            "text_to_speech": {},
            "code_generation": {},
            "embedding": {},
            "vision": {}
        }
        
        # Load config if it exists
        self.load()
    
    def load(self) -> bool:
        """Load multimodal configuration from disk"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Update task models with loaded data
                if "task_models" in config:
                    for task, model in config["task_models"].items():
                        if task in self.task_models:
                            self.task_models[task] = model
                
                # Update task settings
                if "task_settings" in config:
                    for task, settings in config["task_settings"].items():
                        if task in self.task_settings:
                            self.task_settings[task] = settings
                
                logger.info(f"Loaded multimodal configuration from {self.config_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading multimodal configuration: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save multimodal configuration to disk"""
        try:
            config = {
                "task_models": self.task_models,
                "task_settings": self.task_settings
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved multimodal configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving multimodal configuration: {str(e)}")
            return False
    
    def set_model_for_task(self, task: str, model_path: str) -> bool:
        """Set the model to use for a specific task"""
        if task not in self.task_models:
            logger.warning(f"Invalid task: {task}")
            return False
        
        self.task_models[task] = model_path
        self.save()
        return True
    
    def get_model_for_task(self, task: str) -> str:
        """Get the model path for a specific task"""
        if task not in self.task_models:
            logger.warning(f"Invalid task: {task}")
            return ""
        
        return self.task_models[task]
    
    def set_task_setting(self, task: str, setting_name: str, setting_value: Any) -> bool:
        """Set a specific setting for a task"""
        if task not in self.task_settings:
            logger.warning(f"Invalid task: {task}")
            return False
        
        self.task_settings[task][setting_name] = setting_value
        self.save()
        return True
    
    def get_task_setting(self, task: str, setting_name: str, default: Any = None) -> Any:
        """Get a specific setting for a task"""
        if task not in self.task_settings:
            logger.warning(f"Invalid task: {task}")
            return default
        
        return self.task_settings[task].get(setting_name, default)
    
    def get_task_settings(self, task: str) -> Dict[str, Any]:
        """Get all settings for a task"""
        if task not in self.task_settings:
            logger.warning(f"Invalid task: {task}")
            return {}
        
        return self.task_settings[task]
    
    def get_all_tasks(self) -> List[str]:
        """Get a list of all available tasks"""
        return list(self.task_models.keys())
    
    def has_model_for_task(self, task: str) -> bool:
        """Check if a model is set for a specific task"""
        if task not in self.task_models:
            return False
        
        return bool(self.task_models[task])

# Global instance
_multimodal_manager = None

def get_multimodal_manager():
    """Get the global multimodal manager instance"""
    global _multimodal_manager
    if _multimodal_manager is None:
        _multimodal_manager = MultimodalManager()
    return _multimodal_manager
