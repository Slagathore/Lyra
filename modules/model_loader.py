import os
import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class ModelLoader:
    def __init__(self):
        self.model_dirs = []
        self.models_cache = {}
        self.last_refresh = 0
        self.refresh_interval = 300  # 5 minutes
        self.texting_models_dir = os.path.join(os.path.expanduser("~"), "TT Models")
        
    def add_model_dir(self, model_dir):
        """Add a directory to search for models"""
        if os.path.exists(model_dir) and os.path.isdir(model_dir):
            if model_dir not in self.model_dirs:
                self.model_dirs.append(model_dir)
                logger.info(f"Added model directory: {model_dir}")
            return True
        else:
            logger.warning(f"Model directory not found or not a directory: {model_dir}")
            return False
            
    def get_models(self, force_refresh=False, min_size_gb=0.01, texting_only=False):
        """Get a list of available models with metadata, filtering by minimum size"""
        current_time = time.time()
        
        # Refresh cache if needed
        if force_refresh or (current_time - self.last_refresh) > self.refresh_interval:
            self._refresh_models_cache()
            self.last_refresh = current_time
            
        # Filter out models that are too small (likely corrupt or empty)
        filtered_models = {k: v for k, v in self.models_cache.items() 
                          if v.get("size_gb", 0) >= min_size_gb}
        
        # If texting_only is True, only include models from the TT Models directory
        if texting_only:
            texting_models = {k: v for k, v in filtered_models.items() 
                             if self.texting_models_dir in k}
            return texting_models
        
        return filtered_models
    
    def _refresh_models_cache(self):
        """Scan model directories and refresh the models cache"""
        self.models_cache = {}
        
        # Always add the TT Models directory if it exists
        if os.path.exists(self.texting_models_dir) and os.path.isdir(self.texting_models_dir):
            if self.texting_models_dir not in self.model_dirs:
                self.model_dirs.append(self.texting_models_dir)
                logger.info(f"Added TT Models directory: {self.texting_models_dir}")
        
        for model_dir in self.model_dirs:
            self._scan_directory(model_dir)
            
        logger.info(f"Refreshed models cache, found {len(self.models_cache)} models")
    
    def _scan_directory(self, directory):
        """Scan a directory for model files"""
        try:
            # Supported model extensions
            model_extensions = ['.bin', '.gguf', '.ggml', '.pt', '.pth', '.safetensors']
            
            # Scan directory
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_ext = os.path.splitext(file)[1].lower()
                    
                    if file_ext in model_extensions:
                        # Try to extract model info
                        model_info = self._extract_model_info(file_path)
                        self.models_cache[file_path] = model_info
                        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {str(e)}")
    
    def _extract_model_info(self, model_path):
        """Extract model information from filename and metadata files"""
        try:
            file_size = os.path.getsize(model_path) / (1024 * 1024 * 1024)  # Convert to GB
            
            # Skip files smaller than 1MB (likely not real models)
            if file_size < 0.001:
                logger.debug(f"Skipping very small file (likely not a model): {model_path}")
                return {
                    "name": os.path.basename(model_path),
                    "path": model_path,
                    "size_gb": 0,
                    "parameters": "Invalid",
                    "type": "Unknown",
                    "config": None,
                    "valid": False,
                    "is_texting_model": self.texting_models_dir in model_path
                }
                
            file_name = os.path.basename(model_path)
            model_name = os.path.splitext(file_name)[0]
            
            # Check for metadata files
            model_dir = os.path.dirname(model_path)
            config_extensions = ['.json', '.yaml', '.yml']
            
            model_config = None
            for ext in config_extensions:
                config_path = os.path.join(model_dir, f"{model_name}{ext}")
                if os.path.exists(config_path):
                    try:
                        if ext == '.json':
                            with open(config_path, 'r', encoding='utf-8') as f:
                                model_config = json.load(f)
                        # Add YAML support if needed
                        break
                    except:
                        pass
            
            # Estimate model parameters based on file size
            # This is a rough estimate, different quantization methods impact this
            param_estimate = self._estimate_parameters(file_size, model_path)
            
            # Extract model type from name
            model_type = "Unknown"
            if "llama" in model_name.lower():
                model_type = "LLaMA"
            elif "mistral" in model_name.lower():
                model_type = "Mistral"
            elif "gpt" in model_name.lower():
                model_type = "GPT"
            elif "phi" in model_name.lower():
                model_type = "Phi"
            elif "qwen" in model_name.lower():
                model_type = "Qwen"
            
            return {
                "name": model_name,
                "path": model_path,
                "size_gb": round(file_size, 2),
                "parameters": param_estimate,
                "type": model_type,
                "config": model_config,
                "valid": True,
                "is_texting_model": self.texting_models_dir in model_path
            }
        except Exception as e:
            logger.error(f"Error extracting model info for {model_path}: {str(e)}")
            return {
                "name": os.path.basename(model_path),
                "path": model_path,
                "size_gb": 0,
                "parameters": "Unknown",
                "type": "Unknown",
                "config": None,
                "valid": False,
                "is_texting_model": self.texting_models_dir in model_path
            }
    
    def _estimate_parameters(self, size_gb, model_path):
        """Estimate model parameters based on file size and extension"""
        try:
            ext = os.path.splitext(model_path)[1].lower()
            
            # For GGUF models, try to extract from the name
            if ext == '.gguf':
                filename = os.path.basename(model_path).lower()
                
                # Look for common parameter indicators like 7b, 13b, etc.
                import re
                param_match = re.search(r'(\d+)b', filename)
                if param_match:
                    return f"{param_match.group(1)}B"
                    
            # Rough estimates based on file size for different quantization levels
            if size_gb < 1:
                return "< 1B"
            elif size_gb < 2:
                return "1-2B"
            elif size_gb < 5:
                return "3-7B"
            elif size_gb < 10:
                return "7-13B"
            elif size_gb < 20:
                return "13-20B"
            elif size_gb < 40:
                return "20-40B"
            else:
                return "40B+"
                
        except:
            return "Unknown"

# Create a global instance
_model_loader = None

def get_model_loader():
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
    return _model_loader
