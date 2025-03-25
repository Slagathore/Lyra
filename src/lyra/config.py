"""
Configuration module for Lyra
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "llm": {
        "model_dir": os.path.join(os.path.expanduser("~"), "lyra_models"),
        "text_model": "DavidAU/Qwen2.5-QwQ-37B-Eureka-Triple-Cubed-GGUF/q6_K.gguf",
        "use_local_llm": True,
        "temperature": 0.7,
        "max_tokens": 1024,
        "context_window": 4096
    },
    "video": {
        "model": "Wan-AI/Wan2.1-I2V-14B-480P",
        "output_dir": os.path.join(os.getcwd(), "output", "videos"),
        "height": 480,
        "width": 864,
        "num_frames": 24,
        "inference_steps": 25
    },
    "memory": {
        "use_faiss": True,
        "use_json": True,
        "use_sql": True,
        "embedding_model": "all-MiniLM-L6-v2"
    },
    "system": {
        "log_level": "INFO",
        "reflection_frequency": 5
    }
}

# Configuration file path
CONFIG_FILE = os.path.join(os.getcwd(), "lyra_config.json")

class LyraConfig:
    """Configuration manager for Lyra"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or CONFIG_FILE
        self.config = DEFAULT_CONFIG.copy()
        self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values
                    for section, values in loaded_config.items():
                        if section in self.config:
                            self.config[section].update(values)
                        else:
                            self.config[section] = values
                logger.info(f"Configuration loaded from {self.config_file}")
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        else:
            logger.info(f"No configuration file found at {self.config_file}, using defaults")
            
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value"""
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        return default
        
    def set(self, section: str, key: str, value: Any) -> None:
        """Set a configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        
    def get_llm_model_path(self) -> str:
        """Get the path to the LLM model"""
        model_dir = self.get("llm", "model_dir")
        text_model = self.get("llm", "text_model")
        # Handle both repository ID and file path formats
        if os.path.exists(text_model):
            return text_model
        return os.path.join(model_dir, text_model.replace("/", "_"))
        
    def get_video_model_path(self) -> str:
        """Get the path to the video model"""
        model_dir = self.get("llm", "model_dir")
        video_model = self.get("video", "model")
        # Handle both repository ID and file path formats
        if os.path.exists(video_model):
            return video_model
        return os.path.join(model_dir, video_model.replace("/", "_"))

# Global config instance
_config_instance = None

def get_config() -> LyraConfig:
    """Get the global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = LyraConfig()
    return _config_instance

if __name__ == "__main__":
    # Test the configuration
    config = get_config()
    print("LLM Model Path:", config.get_llm_model_path())
    print("Video Model Path:", config.get_video_model_path())
    
    # Change a value and save
    config.set("system", "log_level", "DEBUG")
    config.save_config()
