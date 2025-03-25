import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger("llama_provider")

class LlamaModel:
    """Provider for LLama models."""
    
    def __init__(self, config):
        self.config = config
        self.model = None
        self.tokenizer = None
        
        # Initialize the model
        self._initialize()
    
    def _initialize(self):
        """Initialize the Llama model."""
        try:
            # Dynamic import to avoid requiring llama-cpp-python if not used
            from llama_cpp import Llama
            
            # Get model path
            model_path = self.config.model_path
            
            # Check if the model file exists
            if not os.path.exists(model_path):
                logger.error(f"Model file not found: {model_path}")
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Extract parameters from config
            context_size = self.config.parameters.get("context_size", 4096)
            n_gpu_layers = self.config.parameters.get("n_gpu_layers", 0)
            
            # Get format-specific parameters
            model_format = self.config.parameters.get("format", "default")
            
            # Log all parameters for debugging
            logger.info(f"Initializing Llama with: path={model_path}, context={context_size}, gpu_layers={n_gpu_layers}, format={model_format}")
            
            # Improve format detection with more specific checks
            model_name_lower = self.config.model_name.lower()
            model_path_lower = self.config.model_path.lower()
            
            # FIXED: Initialize chat_format with a default value to avoid undefined variable warning
            chat_format = None
            
            # First try the format specified in config
            model_format = self.config.parameters.get("format", "default")
            
            # Override with more specific detection if needed
            if "llama-3" in model_name_lower or "llama3" in model_name_lower:
                chat_format = "llama-3"
                logger.info("Detected Llama-3 model format")
            elif "wizard" in model_name_lower or "wizardlm" in model_name_lower:
                chat_format = "vicuna"  # Wizard models use Vicuna format
                logger.info("Detected WizardLM model format (using vicuna template)")
            elif "chatml" in model_name_lower or "chat-ml" in model_name_lower or "command-r" in model_name_lower:
                chat_format = "chatml"
                logger.info("Detected ChatML format")
            elif "mistral" in model_name_lower:
                chat_format = "mistral"
                logger.info("Detected Mistral format")
            elif "deepseek" in model_name_lower or "hermes" in model_name_lower:
                # DeepSeek and Hermes models often use ChatML format
                chat_format = "chatml"
                logger.info("Detected DeepSeek/Hermes model (using chatml template)")
            elif "dolphin" in model_name_lower:
                # Dolphin uses chatml format
                chat_format = "chatml" 
                logger.info("Detected Dolphin model (using chatml template)")
            elif "alpaca" in model_name_lower:
                chat_format = "alpaca"
                logger.info("Detected Alpaca format")
            elif "vicuna" in model_name_lower:
                chat_format = "vicuna"
                logger.info("Detected Vicuna format")
            else:
                # Default to the requested format in config
                chat_format = self._map_format_to_library(model_format)
                logger.info(f"Using format from config: {chat_format}")
            
            # Initialize model with correct parameter names
            init_params = {
                "model_path": model_path,
                "n_ctx": context_size,
                "n_gpu_layers": n_gpu_layers,
            }
            
            # Add chat format if specified
            if chat_format:
                init_params["chat_format"] = chat_format
                logger.info(f"Using chat format: {chat_format}")
            
            # Add error handling for specific MOE models
            model_name = self.config.model_name.lower()
            if "moe" in model_name or "mixture" in model_name:
                logger.info("MOE model detected, adding specific parameters")
                # Some MOE models need specific settings
                init_params["logits_all"] = True
                # Use either n_gqa or set specific experts parameters based on model type
                if "2x" in model_name or "x2" in model_name:
                    init_params["n_gqa"] = 2
                elif "8x" in model_name or "x8" in model_name:
                    init_params["n_gqa"] = 8
            
            # Add CUDA-specific parameters
            if n_gpu_layers > 0:
                init_params["n_batch"] = 512  # Increase batch size for GPU
                if "offload_kqv" not in init_params:
                    init_params["offload_kqv"] = True  # Offload KQV operations to GPU
                logger.info(f"Enabling GPU acceleration with {n_gpu_layers} layers")
            
            # Enhanced error handling with specific fallbacks
            try:
                # Try initializing with the configured parameters
                self.model = Llama(**init_params)
            except AssertionError as e:
                # If assertion error, try common fallbacks
                logger.warning(f"Initial model loading failed: {e}")
                
                # Fallbacks that help with various models
                fallbacks = [
                    # Try with smaller context
                    {"n_ctx": 2048, "verbose": False},
                    # Try with different batch size
                    {"n_ctx": 4096, "n_batch": 256, "verbose": False},
                    # Try with no GPU acceleration
                    {"n_ctx": 4096, "n_gpu_layers": 0, "verbose": False},
                    # Try with minimal settings
                    {"n_ctx": 2048, "n_gpu_layers": 0, "n_batch": 128, "verbose": False}
                ]
                
                for i, fallback_params in enumerate(fallbacks, 1):
                    try:
                        logger.info(f"Attempt {i}: Trying with fallback settings: {fallback_params}")
                        # Update init_params with fallback values
                        for k, v in fallback_params.items():
                            init_params[k] = v
                        
                        # Try to initialize model with new parameters
                        self.model = Llama(**init_params)
                        logger.info(f"Model loaded successfully with fallback settings {i}")
                        break
                    except Exception as inner_e:
                        logger.warning(f"Fallback {i} failed: {inner_e}")
                        
                        if i == len(fallbacks):
                            # Final fallback failed
                            logger.error("All fallbacks failed, model cannot be loaded")
                            raise  # Re-raise last exception
            
            logger.info(f"Successfully loaded Llama model: {self.config.model_name}")
        except ImportError as e:
            logger.error(f"Failed to import llama_cpp. Error: {e}")
            logger.error("Make sure llama-cpp-python is installed. Try: pip install llama-cpp-python")
            raise
        except Exception as e:
            logger.error(f"Error initializing Llama model: {e}", exc_info=True)
            raise
    
    def _map_format_to_library(self, format_name: str) -> str:
        """Map our format names to the names used by the llama-cpp library."""
        format_map = {
            "llama3": "llama-3",
            "llama-3": "llama-3",
            "wizard": "vicuna",
            "wizardlm": "vicuna",
            "chatml": "chatml",
            "command-r": "chatml",
            "mistral": "mistral",
            "vicuna": "vicuna",
            "alpaca": "alpaca",
            "default": None,
        }
        
        # Normalize format name and look up
        normalized = format_name.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        for key, value in format_map.items():
            if normalized == key.lower().replace("-", "").replace("_", ""):
                return value
        
        # Return None for default/unknown formats
        return None
    
    def generate(self, prompt: str, **kwargs):
        """Generate a response using the Llama model."""
        if not self.model:
            logger.error("Model not initialized")
            return "Error: Model not initialized"
        
        try:
            # Extract parameters with correct Llama naming
            max_tokens = kwargs.get("max_tokens", 256)  # Use max_tokens directly
            temperature = kwargs.get("temperature", 0.7)
            top_p = kwargs.get("top_p", 0.95)
            top_k = kwargs.get("top_k", 40)
            
            # Log the parameters being used 
            logger.info(f"Generating with: max_tokens={max_tokens}, temp={temperature}, top_p={top_p}, top_k={top_k}")
            logger.info(f"Prompt begins with: {prompt[:50]}...")
            
            # Call the model correctly - for llama_cpp.Llama the correct method is just calling the object
            try:
                # First try with the modern API format
                output = self.model(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k
                )
                
                # Handle different response formats
                if isinstance(output, dict) and "choices" in output and len(output["choices"]) > 0:
                    text = output["choices"][0]["text"]
                    logger.info(f"Generated response using new API format")
                    return text
                    
                # For older API version (string response)
                elif isinstance(output, str):
                    logger.info(f"Generated response with older API (string format)")
                    return output
                    
                # If it's some other dictionary format
                elif isinstance(output, dict):
                    if "text" in output:
                        return output["text"]
                    # Other possible key names
                    for key in ["generation", "content", "response"]:
                        if key in output:
                            return output[key]
                
                # Last resort - convert whatever we got to string
                return str(output)
                
            except TypeError as e:
                # If we got a TypeError, try with the specific method
                logger.warning(f"Retrying with alternate API method: {e}")
                
                # Some versions of llama-cpp-python use the .generate() method instead
                if hasattr(self.model, "generate"):
                    # Try alternate API style
                    response = self.model.generate(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        top_p=top_p,
                        top_k=top_k
                    )
                    return response
                else:
                    raise
                
        except Exception as e:
            logger.error(f"Error generating response with Llama: {e}", exc_info=True)
            logger.error(f"Model type: {type(self.model)}")
            logger.error(f"Parameters that caused error: {kwargs}")
            return f"Error generating response: {str(e)}\n\nPlease check model configuration."
    
    def cleanup(self):
        """Clean up resources."""
        logger.info(f"Cleaning up Llama model: {self.config.model_name}")
        self.model = None
