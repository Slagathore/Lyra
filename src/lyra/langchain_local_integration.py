"""
LangChain integration with local LLMs for Lyra
"""
from typing import Optional, List, Dict, Any, Union
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import logging
import glob

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Try to import LangChain dependencies
try:
    # Updated imports for newer LangChain versions
    try:
        from langchain_community.llms import LlamaCpp
        LLAMACPP_AVAILABLE = True
    except ImportError:
        try:
            from langchain.llms import LlamaCpp
            LLAMACPP_AVAILABLE = True
        except ImportError:
            LLAMACPP_AVAILABLE = False
            logger.warning("LlamaCpp not available for LangChain")
    
    try:
        from langchain_community.llms import HuggingFacePipeline
    except ImportError:
        try:
            from langchain.llms import HuggingFacePipeline
        except ImportError:
            HuggingFacePipeline = None
    
    try:
        from langchain.chains import ConversationChain
        from langchain.memory import ConversationBufferMemory
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline, StoppingCriteria, StoppingCriteriaList
        HUGGINGFACE_PIPELINE_AVAILABLE = HuggingFacePipeline is not None
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        HUGGINGFACE_PIPELINE_AVAILABLE = False
        LANGCHAIN_AVAILABLE = False
        logger.warning("Required LangChain or transformers components not available")
    
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LLAMACPP_AVAILABLE = False
    HUGGINGFACE_PIPELINE_AVAILABLE = False
    logger.warning("LangChain not available")

# Configuration
MODEL_DIR = os.environ.get("LYRA_MODEL_DIR", os.path.join(os.path.expanduser("~"), "lyra_models"))
DEFAULT_MODEL = os.environ.get("LYRA_DEFAULT_MODEL", "DavidAU/Qwen2.5-QwQ-37B-Eureka-Triple-Cubed-GGUF/q6_K.gguf")
DEFAULT_MODEL_PATH = os.path.join(MODEL_DIR, DEFAULT_MODEL.replace("/", "_"))

class StopOnTokens(StoppingCriteria):
    """Stopping criteria for text generation when specific tokens are encountered"""
    def __init__(self, stop_token_ids):
        self.stop_token_ids = stop_token_ids
    
    def __call__(self, input_ids, scores, **kwargs):
        for stop_id in self.stop_token_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False

def get_available_models() -> List[Dict[str, Any]]:
    """
    Get a list of available local models
    
    Returns:
        List of model info dictionaries with 'name', 'path', 'type', and 'size'
    """
    models = []
    
    # Check if model directory exists
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR, exist_ok=True)
        logger.info(f"Created model directory at {MODEL_DIR}")
        return models
    
    # Check for GGUF models
    for path in glob.glob(os.path.join(MODEL_DIR, "**/*.gguf"), recursive=True):
        model_size = os.path.getsize(path) / (1024 * 1024 * 1024)  # Size in GB
        models.append({
            "name": os.path.basename(path),
            "path": path,
            "type": "GGUF",
            "size": f"{model_size:.2f} GB"
        })
    
    # Check for Hugging Face models (look for config.json)
    for config_path in glob.glob(os.path.join(MODEL_DIR, "**/config.json"), recursive=True):
        model_dir = os.path.dirname(config_path)
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            name = config.get('_name_or_path', os.path.basename(model_dir))
            
            # Calculate total model size
            model_size = sum(
                os.path.getsize(os.path.join(dirpath, filename)) 
                for dirpath, _, filenames in os.walk(model_dir)
                for filename in filenames
            ) / (1024 * 1024 * 1024)  # Size in GB
            
            models.append({
                "name": name,
                "path": model_dir,
                "type": "Hugging Face",
                "size": f"{model_size:.2f} GB"
            })
        except Exception as e:
            logger.warning(f"Error parsing model config at {config_path}: {e}")
    
    return models

def validate_model_path(model_path: Optional[str] = None) -> str:
    """
    Validate and return a usable model path
    
    Args:
        model_path: Path to the model file or directory
        
    Returns:
        Validated model path
    """
    if not model_path:
        model_path = DEFAULT_MODEL_PATH
    
    # If the path doesn't exist, check if it's a model name in the models directory
    if not os.path.exists(model_path):
        potential_paths = [
            os.path.join(MODEL_DIR, model_path),
            os.path.join(MODEL_DIR, model_path.replace("/", "_")),
            # Check if it's just a model name without path
            *[model["path"] for model in get_available_models() if os.path.basename(model["path"]) == model_path]
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                model_path = path
                break
    
    if not os.path.exists(model_path):
        available_models = get_available_models()
        if available_models:
            # Use the first available model
            model_path = available_models[0]["path"]
            logger.warning(f"Model path not found. Using first available model: {model_path}")
        else:
            raise ValueError(f"Model path not found: {model_path} and no other models available")
    
    return model_path

def create_local_llm(model_path: Optional[str] = None, 
                    temperature: float = 0.7,
                    max_tokens: int = 1000,
                    verbose: bool = False):
    """
    Create a local LLM instance
    
    Args:
        model_path: Path to the model file or directory
        temperature: Sampling temperature
        max_tokens: Maximum number of tokens to generate
        verbose: Whether to enable verbose output
        
    Returns:
        LangChain LLM instance or None if not available
    """
    if not LANGCHAIN_AVAILABLE:
        logger.error("LangChain not available")
        return None
    
    try:
        # Validate model path
        model_path = validate_model_path(model_path)
        logger.info(f"Using model path: {model_path}")
    except Exception as e:
        logger.error(f"Failed to validate model path: {e}")
        return None
    
    # Try to create a LlamaCpp LLM if available and path ends with .gguf
    if LLAMACPP_AVAILABLE and model_path.lower().endswith('.gguf'):
        try:
            logger.info(f"Creating LlamaCpp LLM with model: {model_path}")
            
            # Check available memory for context size
            try:
                import psutil
                available_memory_gb = psutil.virtual_memory().available / (1024**3)
                n_ctx = min(8192, max(2048, int(available_memory_gb * 512)))  # Scale context with available memory
                logger.info(f"Setting context size to {n_ctx} based on {available_memory_gb:.2f}GB available RAM")
            except:
                n_ctx = 4096
                logger.info(f"Could not determine available memory. Using default context size: {n_ctx}")
            
            llm = LlamaCpp(
                model_path=model_path,
                temperature=temperature,
                max_tokens=max_tokens,
                n_ctx=n_ctx,
                verbose=verbose,
                n_gpu_layers=-1,  # Auto-detect GPU layers
                f16_kv=True       # Use half-precision for key/value cache
            )
            return llm
        except Exception as e:
            logger.error(f"Failed to create LlamaCpp LLM: {e}")
    
    # Try to create a HuggingFacePipeline LLM if available
    if HUGGINGFACE_PIPELINE_AVAILABLE:
        try:
            logger.info(f"Creating HuggingFacePipeline LLM with model: {model_path}")
            
            # Determine if we should use CUDA
            if torch.cuda.is_available():
                device = "cuda"
                device_map = "auto"
                torch_dtype = torch.float16
                logger.info(f"Using CUDA with {torch.cuda.device_count()} device(s)")
            else:
                device = "cpu"
                device_map = None
                torch_dtype = torch.float32
                logger.info("Using CPU for inference")
            
            # Load model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                model_path, 
                device_map=device_map,
                torch_dtype=torch_dtype,
                load_in_8bit=device == "cuda"
            )
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Configure stopping criteria
            stop_token_ids = []
            for token in ["<|im_end|>", "</s>", "<|endoftext|>"]:
                if token in tokenizer.vocab:
                    stop_token_ids.append(tokenizer.vocab[token])
            
            stopping_criteria = StoppingCriteriaList([StopOnTokens(stop_token_ids)]) if stop_token_ids else None
            
            # Create pipeline
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_length=max_tokens,
                temperature=temperature,
                device=device,
                stopping_criteria=stopping_criteria
            )
            
            # Create LangChain LLM
            llm = HuggingFacePipeline(pipeline=pipe)
            return llm
        except Exception as e:
            logger.error(f"Failed to create HuggingFacePipeline LLM: {e}")
    
    logger.error("No suitable LLM implementation available")
    return None

def create_conversation_chain(model_path: Optional[str] = None,
                             temperature: float = 0.7,
                             max_tokens: int = 1000):
    """
    Create a conversation chain with a local LLM
    
    Args:
        model_path: Path to the model file
        temperature: Sampling temperature
        max_tokens: Maximum number of tokens to generate
        
    Returns:
        ConversationChain instance or None if not available
    """
    if not LANGCHAIN_AVAILABLE:
        logger.error("LangChain not available")
        return None
    
    # Create LLM
    llm = create_local_llm(model_path, temperature, max_tokens)
    if llm is None:
        return None
    
    # Create conversation chain
    try:
        memory = ConversationBufferMemory(memory_key="history")
        conversation = ConversationChain(llm=llm, memory=memory)
        return conversation
    except Exception as e:
        logger.error(f"Failed to create conversation chain: {e}")
        return None

def get_model_info(model_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about a specific model
    
    Args:
        model_path: Path to the model
        
    Returns:
        Dictionary with model information
    """
    try:
        model_path = validate_model_path(model_path)
        model_size = sum(
            os.path.getsize(os.path.join(dirpath, filename)) 
            for dirpath, _, filenames in os.walk(model_path) if os.path.isdir(model_path)
            for filename in filenames
        ) / (1024 * 1024 * 1024) if os.path.isdir(model_path) else os.path.getsize(model_path) / (1024 * 1024 * 1024)
        
        model_type = "GGUF" if model_path.lower().endswith('.gguf') else "Hugging Face"
        
        # Try to get additional info for HF models
        additional_info = {}
        if model_type == "Hugging Face":
            config_path = os.path.join(model_path, "config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                additional_info = {
                    "architecture": config.get("architectures", ["Unknown"])[0],
                    "vocab_size": config.get("vocab_size", "Unknown"),
                    "hidden_size": config.get("hidden_size", "Unknown"),
                    "num_layers": config.get("num_hidden_layers", "Unknown"),
                }
        
        return {
            "path": model_path,
            "name": os.path.basename(model_path),
            "type": model_type,
            "size_gb": f"{model_size:.2f}",
            **additional_info
        }
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    # Test the local LangChain integration
    print("Available models:")
    models = get_available_models()
    for i, model in enumerate(models):
        print(f"{i+1}. {model['name']} ({model['type']}, {model['size']})")
    
    if models:
        model_path = models[0]["path"]
        print(f"\nUsing model: {model_path}")
        
        conversation = create_conversation_chain(model_path)
        if conversation:
            user_input = "Hello, how are you?"
            print(f"\nUser: {user_input}")
            response = conversation.predict(input=user_input)
            print(f"Bot: {response}")
            
            user_input = "Tell me a short story about a robot."
            print(f"\nUser: {user_input}")
            response = conversation.predict(input=user_input)
            print(f"Bot: {response}")
        else:
            print("Failed to create conversation chain")
    else:
        print("No models available. Please download a model to the models directory.")
