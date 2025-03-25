# ...existing code...

class ModelConfig:
    def __init__(self, model_name="", model_path="", model_config_path="", context_size=2048, 
                 gpu_layers=None, threads=None, n_batch=512, lora_path="", mmproj="",
                 rope_scaling=None, rope_freq_base=0, rope_freq_scale=0, 
                 chat_template=None, prompt_template=None, params=None):
        self.model_name = model_name
        self.model_path = model_path
        self.model_config_path = model_config_path
        self.context_size = context_size
        self.gpu_layers = gpu_layers if gpu_layers is not None else 0
        self.threads = threads if threads is not None else 4
        self.n_batch = n_batch
        self.lora_path = lora_path
        self.mmproj = mmproj
        self.rope_scaling = rope_scaling
        self.rope_freq_base = rope_freq_base
        self.rope_freq_scale = rope_freq_scale
        self.chat_template = chat_template
        self.prompt_template = prompt_template
        self.params = params if params is not None else {}

# ...existing code...

def save_model_settings(model_config):
    try:
        settings = {
            "model_name": model_config.model_name,
            "model_path": model_config.model_path,
            "model_config_path": model_config.model_config_path,
            "context_size": model_config.context_size,
            "gpu_layers": model_config.gpu_layers,
            "threads": model_config.threads,
            "n_batch": model_config.n_batch,
            "lora_path": model_config.lora_path,
            "mmproj": model_config.mmproj,
            "rope_scaling": model_config.rope_scaling,
            "rope_freq_base": model_config.rope_freq_base,
            "rope_freq_scale": model_config.rope_freq_scale,
            "chat_template": model_config.chat_template,
            "prompt_template": model_config.prompt_template,
            "params": model_config.params if hasattr(model_config, 'params') else {}
        }
        # ...existing code...
    except Exception as e:
        logger.error(f"Error saving model settings: {str(e)}")
        return False

# ...existing code...

def load_model(model_config):
    """Load a model with the given configuration"""
    try:
        # Validate model file
        if not os.path.exists(model_config.model_path):
            logger.error(f"Model file not found: {model_config.model_path}")
            return False
            
        # Check file size
        file_size_gb = os.path.getsize(model_config.model_path) / (1024 * 1024 * 1024)
        if file_size_gb < 0.01:  # Less than 10MB
            logger.error(f"Model file is too small (likely invalid): {model_config.model_path} ({file_size_gb:.2f} GB)")
            return False
            
        # Proceed with model loading
        # ...existing code...
        
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        return False

# ...existing code...
