import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("model_manager")

class ModelConfig:
    """Configuration for language models."""
    
    def __init__(self, model_name: str, model_path: str, model_type: str, **kwargs):
        self.model_name = model_name
        self.model_path = model_path
        self.model_type = model_type
        
        # Store parameters in a dictionary to avoid attribute errors
        self.parameters = kwargs
    
    @property
    def as_dict(self) -> Dict[str, Any]:
        """Return configuration as a dictionary."""
        config_dict = {
            "model_name": self.model_name,
            "model_path": self.model_path,
            "model_type": self.model_type,
            **self.parameters
        }
        return config_dict
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'ModelConfig':
        """Create a ModelConfig from a dictionary."""
        model_name = config_dict.pop("model_name", "unknown")
        model_path = config_dict.pop("model_path", "")
        model_type = config_dict.pop("model_type", "unknown")
        
        return cls(
            model_name=model_name,
            model_path=model_path,
            model_type=model_type,
            **config_dict
        )


class ModelManager:
    """Manages the loading, unloading, and configuration of language models."""
    
    def __init__(self, config_dir: str = "configs", models_dir: str = "TT Models"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        # Try multiple possible paths for BigModes directory
        possible_paths = [
            Path("G:/AI/Lyra/BigModes"),
            Path("G:/AI/BigModes"),
            Path("G:/BigModes"),
            Path("../BigModes"),
            Path("BigModes"),
            Path(".")  # Current directory as fallback
        ]
        
        self.models_dir = None
        for base_path in possible_paths:
            test_path = base_path / models_dir
            if test_path.exists():
                self.models_dir = test_path
                logger.info(f"Found models directory at: {self.models_dir}")
                break
        
        if not self.models_dir:
            # If not found, use the first path but log a warning
            self.models_dir = possible_paths[0] / models_dir
            logger.warning(f"Models directory not found, will use: {self.models_dir}")
        
        self.active_model = None
        self.active_model_instance = None
        self.model_configs = {}
        self.model_instances = {}
        
        # Load existing configurations
        self._load_configs()
        
        # Auto-discover models if none are configured
        if not self.model_configs:
            self._discover_models()
    
    def _load_configs(self):
        """Load model configurations from disk."""
        try:
            valid_configs = 0
            invalid_configs = 0
            
            for config_file in self.config_dir.glob("*.json"):
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    model_config = ModelConfig.from_dict(config_data)
                    
                    # Validate model file exists before adding to configs
                    model_path = Path(model_config.model_path)
                    if not model_path.exists():
                        logger.warning(f"Model file not found, skipping config: {model_config.model_name} (path: {model_path})")
                        invalid_configs += 1
                        # Optionally move invalid configs to backup
                        self._backup_invalid_config(config_file)
                        continue
                    
                    self.model_configs[model_config.model_name] = model_config
                    logger.info(f"Loaded configuration for model: {model_config.model_name}")
                    valid_configs += 1
                except Exception as e:
                    logger.error(f"Error loading config from {config_file}: {e}")
                    invalid_configs += 1
            
            logger.info(f"Loaded {valid_configs} valid model configurations, skipped {invalid_configs} invalid configurations")
        except Exception as e:
            logger.error(f"Error loading model configurations: {e}")
    
    def _backup_invalid_config(self, config_file):
        """Move invalid config to a backup directory."""
        try:
            backup_dir = self.config_dir / "invalid_configs"
            backup_dir.mkdir(exist_ok=True)
            
            backup_path = backup_dir / config_file.name
            import shutil
            shutil.move(str(config_file), str(backup_path))
            logger.info(f"Moved invalid config to: {backup_path}")
        except Exception as e:
            logger.error(f"Error backing up invalid config: {e}")
    
    def save_model_config(self, model_config: ModelConfig):
        """Save a model configuration to disk."""
        try:
            config_path = self.config_dir / f"{model_config.model_name}.json"
            with open(config_path, 'w') as f:
                json.dump(model_config.as_dict, f, indent=2)
            
            # Update in-memory configs
            self.model_configs[model_config.model_name] = model_config
            logger.info(f"Saved configuration for model: {model_config.model_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving model configuration: {e}")
            return False
    
    def load_model(self, model_name: str):
        """Load a model based on its configuration name."""
        if (model_name not in self.model_configs):
            logger.error(f"No configuration found for model: {model_name}")
            return None
        
        # Unload current model if any
        if self.active_model_instance:
            self.unload_model()
        
        try:
            config = self.model_configs[model_name]
            
            # Verify model file exists before attempting to load
            model_path = Path(config.model_path)
            if not model_path.exists():
                error_msg = f"Model file not found: {model_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
                
            # Log the model loading attempt with full path for debugging
            logger.info(f"Loading model: {model_name}")
            logger.info(f"Model path: {config.model_path}")
            logger.info(f"Model type: {config.model_type}")
            logger.info(f"Model format: {config.parameters.get('format', 'default')}")
            
            # Import the appropriate module based on model type
            try:
                if config.model_type == "llama":
                    # Check if we should use the server provider
                    if config.parameters.get("use_server", False):
                        from modules.llm_providers.llama_server_provider import LlamaServerModel
                        model_instance = LlamaServerModel(config)
                    else:
                        from modules.llm_providers.llama_provider import LlamaModel
                        model_instance = LlamaModel(config)
                elif config.model_type == "gpt":
                    from modules.llm_providers.gpt_provider import GPTModel
                    model_instance = GPTModel(config)
                else:
                    # Default or fallback
                    from modules.llm_providers.base_provider import BaseModel
                    model_instance = BaseModel(config)
            except Exception as e:
                logger.error(f"Error loading model provider for {model_name}: {e}")
                # Try fallback to server provider if direct loading fails
                if config.model_type == "llama" and not config.parameters.get("use_server", False):
                    logger.info(f"Attempting to fall back to server provider for {model_name}")
                    try:
                        from modules.llm_providers.llama_server_provider import LlamaServerModel
                        # Update config to use server
                        config.parameters["use_server"] = True
                        config.parameters["host"] = "127.0.0.1"
                        config.parameters["port"] = 8080
                        model_instance = LlamaServerModel(config)
                        # Save the updated config
                        self.save_model_config(config)
                    except Exception as server_e:
                        logger.error(f"Fallback to server provider also failed: {server_e}")
                        raise e  # Re-raise the original error
                else:
                    raise
            
            logger.info(f"Successfully loaded model: {model_name}")
            self.active_model = model_name
            self.active_model_instance = model_instance
            self.model_instances[model_name] = model_instance
            
            return model_instance
            
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def unload_model(self):
        """Unload the currently active model."""
        if self.active_model_instance:
            try:
                # Call cleanup method if available
                if hasattr(self.active_model_instance, 'cleanup'):
                    self.active_model_instance.cleanup()
                
                logger.info(f"Unloaded model: {self.active_model}")
                self.active_model = None
                self.active_model_instance = None
                return True
            except Exception as e:
                logger.error(f"Error unloading model: {e}")
                return False
        return True
    
    def generate(self, prompt: str, **kwargs):
        """Generate a response using the active model."""
        if not self.active_model_instance:
            logger.error("No active model to generate response")
            return "Error: No model loaded. Please load a model first from the dropdown menu."
        
        try:
            # Log the request to help with debugging
            logger.debug(f"Generating with model: {self.active_model}")
            logger.debug(f"Generation parameters: {kwargs}")
            logger.debug(f"Prompt first 100 chars: {prompt[:100]}...")
            
            # Convert between parameter naming conventions if needed
            adjusted_kwargs = self._adjust_generation_params(kwargs)
            
            # Log the adjusted parameters
            logger.debug(f"Adjusted parameters for model type: {adjusted_kwargs}")
            
            # Call generate
            response = self.active_model_instance.generate(prompt, **adjusted_kwargs)
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return f"Error generating response: {str(e)}\n\nCheck the logs for more details."
    
    def _adjust_generation_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust generation parameters for different model types.
        This handles parameter name differences between APIs.
        """
        if not self.active_model or not self.active_model_instance:
            return params
        
        config = self.model_configs.get(self.active_model)
        if not config:
            return params
        
        # Deep copy of params to avoid modifying the original
        adjusted = params.copy()
        
        # Handle different naming conventions
        if config.model_type == "llama":
            # LLaMA can use either max_tokens or max_new_tokens depending on version
            # Keep both for compatibility
            if 'max_tokens' in adjusted and 'max_new_tokens' not in adjusted:
                adjusted['max_new_tokens'] = adjusted['max_tokens']
            elif 'max_new_tokens' in adjusted and 'max_tokens' not in adjusted:
                adjusted['max_tokens'] = adjusted['max_new_tokens']
            
            # Remove parameters that might cause errors in some implementations
            for param in ['presence_penalty', 'frequency_penalty']:
                if param in adjusted:
                    adjusted.pop(param)
            
        elif config.model_type == "gpt":
            # GPT uses 'max_tokens' instead of 'max_new_tokens'
            if 'max_new_tokens' in adjusted and 'max_tokens' not in adjusted:
                adjusted['max_tokens'] = adjusted.pop('max_new_tokens')
        
        return adjusted
    
    def _discover_models(self):
        """Auto-discover models in the models directory."""
        if self.models_dir is None or not self.models_dir.exists():
            logger.warning(f"Models directory not found: {self.models_dir}")
            return
        
        logger.info(f"Scanning for models in {self.models_dir} and its subdirectories")
        
        # Look for model files with common extensions
        model_extensions = [".gguf", ".bin", ".ggml", ".pt", ".pth", ".safetensors"]
        model_files = []
        
        # Recursive glob to find models in subdirectories with detailed logging
        for ext in model_extensions:
            try:
                found_files = list(self.models_dir.glob(f"**/*{ext}"))
                if found_files:
                    logger.info(f"Found {len(found_files)} files with extension {ext}:")
                    for f in found_files[:5]:  # Log first 5 for debugging
                        logger.info(f"  - {f}")
                    if len(found_files) > 5:
                        logger.info(f"  - ... and {len(found_files) - 5} more")
                model_files.extend(found_files)
            except Exception as e:
                logger.error(f"Error searching for {ext} files: {e}")
        
        logger.info(f"Found {len(model_files)} potential model files")
        
        if len(model_files) == 0:
            # Try direct file listing as fallback
            try:
                for root, dirs, files in os.walk(self.models_dir):
                    for file in files:
                        if any(file.endswith(ext) for ext in model_extensions):
                            full_path = Path(root) / file
                            logger.info(f"Found model via walk: {full_path}")
                            model_files.append(full_path)
            except Exception as e:
                logger.error(f"Error walking directory: {e}")
            
            logger.info(f"Found {len(model_files)} models after directory walk")
        
        # Create configurations for discovered models
        created_count = 0
        for model_file in model_files:
            # Create a model name that includes parent folder for better identification
            parent_folder = model_file.parent.name
            base_name = model_file.stem
            
            if parent_folder and parent_folder != "TT Models":
                model_name = f"{parent_folder} - {base_name}"
            else:
                model_name = base_name
            
            # Determine model type and format based on naming
            model_type = "llama"  # Default
            
            # Detect model format from filename or folder
            model_format = "default"
            if "wizard" in str(model_file).lower() or "wizard" in parent_folder.lower():
                model_format = "wizard"
            elif "chatML" in str(model_file) or "chatml" in str(model_file).lower():
                model_format = "chatml"
            elif "llama3" in str(model_file).lower() or "llama-3" in str(model_file).lower():
                model_format = "llama3"
            elif "dark-champion" in str(model_file).lower() or "darkchampion" in str(model_file).lower():
                model_format = "llama3"  # Default Dark Champion to Llama3 format
            elif "command-r" in str(model_file).lower() or "commandr" in str(model_file).lower():
                model_format = "command-r"
            elif "vicuna" in str(model_file).lower() or "vicuna" in parent_folder.lower():
                model_format = "vicuna"
            elif "mistral" in str(model_file).lower() or "mistral" in parent_folder.lower():
                model_format = "default"  # Mistral typically uses default format
            
            # Calculate appropriate GPU layers based on model size and name
            n_gpu_layers = self._estimate_gpu_layers(model_file, model_name)
            
            logger.info(f"Discovered model: {model_name} at {model_file} (format: {model_format}, gpu_layers: {n_gpu_layers})")
            
            # Create model config with appropriate format
            model_config = ModelConfig(
                model_name=model_name,
                model_path=str(model_file),
                model_type=model_type,
                format=model_format,
                context_size=4096,
                n_gpu_layers=n_gpu_layers
            )
            
            # Save the configuration
            if self.save_model_config(model_config):
                created_count += 1
            
        logger.info(f"Auto-discovered and configured {created_count} models")

    def _estimate_gpu_layers(self, model_file: Path, model_name: str) -> int:
        """
        Estimate appropriate number of GPU layers based on model size and available VRAM.
        """
        try:
            # Get model size in bytes - FIX: use st_size instead of size
            model_size_bytes = model_file.stat().st_size  # <-- FIXED: Changed from .size to .st_size
            model_size_gb = model_size_bytes / (1024**3)
            
            # Default to 0 (CPU only) for extremely large models
            gpu_layers = 0
            
            # Base estimation on model size
            if model_size_gb < 5:
                # Small models (<5GB) can usually be fully loaded to GPU
                gpu_layers = 32  # Full model or close to it
            elif model_size_gb < 10:
                # Medium models (5-10GB)
                gpu_layers = 24
            elif model_size_gb < 20:
                # Large models (10-20GB)
                gpu_layers = 20
            elif model_size_gb < 30:
                # XL models (20-30GB)
                gpu_layers = 16
            elif model_size_gb < 40:
                # XXL models (30-40GB)
                gpu_layers = 8
            else:
                # Extremely large models (>40GB)
                gpu_layers = 4  # Just a few layers for attention
                
            # Adjust based on model name indicators
            model_name_lower = model_name.lower()
            
            # Increase for models known to perform well with GPU acceleration
            if "moe" in model_name_lower or "mixture" in model_name_lower:
                # MOE models generally need more GPU layers
                gpu_layers = min(gpu_layers + 8, 40)
            
            # Q4/Q5 quantized models can fit more layers on GPU
            if any(q in model_name_lower for q in ["q4", "q5", "q8"]):
                gpu_layers = min(gpu_layers + 4, 45)
                
            # Small bit models can fit even more
            if any(q in model_name_lower for q in ["q2", "q3"]):
                gpu_layers = min(gpu_layers + 8, 50)
                
            logger.info(f"Estimated {gpu_layers} GPU layers for {model_name} ({model_size_gb:.2f} GB)")
            return gpu_layers
            
        except Exception as e:
            logger.error(f"Error estimating GPU layers: {e}")
            # Default fallback: 0 (CPU only)
            return 0
    
    def cleanup_configurations(self):
        """Remove configurations for models that no longer exist."""
        to_remove = []
        
        # Check each configuration
        for model_name, config in self.model_configs.items():
            model_path = Path(config.model_path)
            if not model_path.exists():
                to_remove.append(model_name)
                logger.info(f"Marking for removal: {model_name} (file not found: {model_path})")
        
        # Remove invalid configurations
        for model_name in to_remove:
            config_path = self.config_dir / f"{model_name}.json"
            try:
                # Backup the config first
                self._backup_invalid_config(config_path)
                # Remove from memory
                del self.model_configs[model_name]
                logger.info(f"Removed invalid configuration: {model_name}")
            except Exception as e:
                logger.error(f"Error removing configuration for {model_name}: {e}")
        
        return len(to_remove)  # Return number of removed configurations
