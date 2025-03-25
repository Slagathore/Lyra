"""
Model configuration and management for multiple LLM models
"""
import os
import json
import glob
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
import time

# Base directory for models
MODELS_BASE_DIR = Path('G:/AI/Lyra/BigModes')
CONFIG_FILE = Path('G:/AI/Lyra/model_config.json')

@dataclass
class ModelConfig:
    """Configuration for a single model"""
    name: str                   # Display name for the model
    path: str                   # Full path to the model file
    type: str = "llama-cpp"     # Model type (llama-cpp, oobabooga, etc.)
    chat_format: str = "chatml" # Default chat format
    n_gpu_layers: int = 35      # Number of GPU layers to use
    n_ctx: int = 4096           # Context size
    n_batch: int = 512          # Batch size
    active: bool = False        # Whether this is the currently active model
    description: str = ""       # Optional description
    # Add MOE-specific configuration
    num_experts: int = None     # Number of experts to use (None = default)
    # Add performance tuning parameters
    temperature: float = 0.8
    repetition_penalty: float = 1.06
    top_k: int = 40
    min_p: float = 0.05
    top_p: float = 0.95
    repeat_last_n: int = 64
    smoothing_factor: float = None  # For Class 3-4 models or MOE models
    # Add usage statistics
    last_used: float = None     # Timestamp when the model was last used
    usage_count: int = 0        # Number of times the model has been used

    def __post_init__(self):
        """Validate and fix path format"""
        # Convert path strings to Path objects for consistency
        if isinstance(self.path, str):
            self.path = str(Path(self.path))  # Ensure paths are stored as strings
        elif isinstance(self.path, Path):
            self.path = str(self.path)  # Convert Path objects to strings
        
        # Auto-detect MOE models and set experts
        if "MOE" in self.name or "moe" in self.name.lower():
            if self.num_experts is None:
                if "Dark-Champion" in self.name:
                    self.num_experts = 8
                elif "DeepSeek-DeepHermes" in self.name:
                    self.num_experts = 2
            
            # Set smoothing factor for MOE models
            if self.smoothing_factor is None:
                self.smoothing_factor = 1.5
        
    @property
    def file_exists(self) -> bool:
        """Check if the model file exists"""
        return os.path.exists(self.path)
    
    @property
    def file_size_gb(self) -> float:
        """Get model file size in GB"""
        if not self.file_exists:
            return 0.0
        return os.path.getsize(self.path) / (1024 * 1024 * 1024)

class PathEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts Path objects to strings"""
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)

class ModelManager:
    """Manages multiple model configurations"""
    def __init__(self):
        self.models: List[ModelConfig] = []
        self.load_config()
        
    def load_config(self):
        """Load configuration from file or create default if not exists"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    self.models = [ModelConfig(**model) for model in data['models']]
            except json.JSONDecodeError as e:
                print(f"Error loading config: {e}")
                # If the config file is corrupted, try to repair it
                if self._repair_config_file():
                    # Try loading again after repair
                    try:
                        with open(CONFIG_FILE, 'r') as f:
                            data = json.load(f)
                            self.models = [ModelConfig(**model) for model in data['models']]
                            print("Successfully loaded repaired config file")
                    except Exception:
                        # If repair and reload fails, create default config
                        print("Config repair failed, creating default configuration")
                        self._create_default_config()
                else:
                    # If repair fails, create default config
                    print("Could not repair config file, creating default configuration")
                    self._create_default_config()
            except Exception as e:
                print(f"Error loading config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
    
    def _repair_config_file(self) -> bool:
        """Attempt to repair a corrupted config file"""
        try:
            # Create a backup of the corrupted file
            backup_path = str(CONFIG_FILE) + ".bak"
            if os.path.exists(CONFIG_FILE):
                import shutil
                shutil.copy2(CONFIG_FILE, backup_path)
                print(f"Created backup of corrupted config at {backup_path}")
            
            # If we can't parse the file at all, just start over
            try:
                with open(CONFIG_FILE, 'r') as f:
                    content = f.read()
                
                # Try some basic repairs on common JSON errors
                # Remove trailing commas
                content = content.replace(",\n}", "\n}")
                content = content.replace(",\n]", "\n]")
                
                # Ensure proper encoding
                content = content.encode('utf-8', errors='ignore').decode('utf-8')
                
                # Try to parse the repaired content
                json.loads(content)
                
                # If we get here, the repair worked, so save it
                with open(CONFIG_FILE, 'w') as f:
                    f.write(content)
                
                return True
            except:
                # If basic repair fails, delete the corrupted file
                # so we can create a fresh one
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
                return False
        except Exception as e:
            print(f"Error attempting to repair config: {e}")
            return False
    
    def save_config(self):
        """Save current configuration to file"""
        # Ensure all models have string paths, not Path objects
        for model in self.models:
            if isinstance(model.path, Path):
                model.path = str(model.path)
                
        data = {
            'models': [asdict(model) for model in self.models]
        }
        
        # First write to a temporary file to avoid corrupting the main file
        temp_path = str(CONFIG_FILE) + ".tmp"
        try:
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2, cls=PathEncoder)
            
            # Verify the file is valid JSON
            with open(temp_path, 'r') as f:
                json.load(f)
            
            # If successful, replace the real file
            import os
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)
            os.rename(temp_path, CONFIG_FILE)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
    
    def _create_default_config(self):
        """Create default configuration by scanning the models directory"""
        self.models = []
        
        # Find all .gguf files in the models directory and subdirectories
        gguf_files = []
        for path in MODELS_BASE_DIR.glob('**/*.gguf'):
            gguf_files.append(path)
        
        # Create a configuration for each model file
        for i, path in enumerate(gguf_files):
            active = i == 0  # First model is active by default
            name = path.stem
            
            # Check for common model types
            chat_format = "chatml"  # Default
            if "qwen" in name.lower():
                chat_format = "chatml"
            elif "llama-2" in name.lower() or "llama2" in name.lower():
                chat_format = "llama-2"
            elif "mistral" in name.lower():
                chat_format = "mistral"
            
            self.models.append(ModelConfig(
                name=name,
                path=str(path),  # Convert Path to string
                active=active,
                chat_format=chat_format
            ))
        
        self.save_config()
    
    def get_active_model(self) -> Optional[ModelConfig]:
        """Get the currently active model"""
        for model in self.models:
            if model.active:
                return model
        return None if not self.models else self.models[0]
    
    def set_active_model(self, model_name: str) -> bool:
        """Set the active model by name"""
        # First deactivate all models
        for model in self.models:
            model.active = False
            
        # Find and activate the requested model
        for model in self.models:
            if model.name.lower() == model_name.lower():
                model.active = True
                model.last_used = time.time()
                model.usage_count += 1
                self.save_config()
                return True
                
        return False
    
    def add_model(self, model: ModelConfig) -> bool:
        """Add a new model to the configuration"""
        # Check if model already exists
        if any(m.path == model.path for m in self.models):
            return False
            
        self.models.append(model)
        self.save_config()
        return True
    
    def remove_model(self, model_name: str) -> bool:
        """Remove a model from the configuration"""
        initial_count = len(self.models)
        self.models = [m for m in self.models if m.name.lower() != model_name.lower()]
        
        if len(self.models) < initial_count:
            self.save_config()
            return True
        return False
    
    def scan_for_new_models(self) -> List[ModelConfig]:
        """Scan for new models not in the current configuration"""
        new_models = []
        
        # Get paths of existing models
        existing_paths = {str(model.path) for model in self.models}  # Convert to strings for comparison
        
        # Find all .gguf files
        for path in MODELS_BASE_DIR.glob('**/*.gguf'):
            path_str = str(path).replace('\\', '/')
            if path_str not in existing_paths:
                name = path.stem
                
                # Guess the format based on filename
                chat_format = "chatml"  # Default
                if "qwen" in name.lower():
                    chat_format = "chatml"
                elif "llama-2" in name.lower() or "llama2" in name.lower():
                    chat_format = "llama-2"
                elif "mistral" in name.lower():
                    chat_format = "mistral"
                
                new_model = ModelConfig(
                    name=name,
                    path=path_str,  # Already a string
                    chat_format=chat_format
                )
                new_models.append(new_model)
                self.models.append(new_model)
        
        if new_models:
            self.save_config()
            
        return new_models
    
    def increment_usage(self, model_name: str):
        """Increment usage statistics for a model"""
        for model in self.models:
            if model.name.lower() == model_name.lower():
                model.usage_count += 1
                model.last_used = time.time()
                self.save_config()
                return True
        return False
    
    def get_frequent_models(self, count: int = 3) -> List[ModelConfig]:
        """Get the most frequently used models"""
        # Create a copy of the models sorted by usage count (descending)
        sorted_models = sorted(
            self.models, 
            key=lambda m: (m.usage_count if m.usage_count else 0), 
            reverse=True
        )
        return sorted_models[:count]
    
    def get_recent_models(self, count: int = 3) -> List[ModelConfig]:
        """Get the most recently used models"""
        # Create a copy of the models sorted by last used timestamp (descending)
        sorted_models = sorted(
            [m for m in self.models if m.last_used is not None],
            key=lambda m: m.last_used,
            reverse=True
        )
        return sorted_models[:count]

# Create a singleton instance
model_manager = ModelManager()

def get_manager() -> ModelManager:
    """Get the singleton ModelManager instance"""
    return model_manager

if __name__ == "__main__":
    # Simple test and demonstration
    manager = get_manager()
    active_model = manager.get_active_model()
    
    print(f"Found {len(manager.models)} models.")
    print(f"Active model: {active_model.name if active_model else 'None'}")
    
    for model in manager.models:
        exists = "✓" if model.file_exists else "✗"
        print(f"{model.name} ({model.file_size_gb:.1f} GB) [{exists}]")
