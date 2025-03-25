"""
Main entry point for Lyra UI
"""
import sys
import os
import argparse
import importlib.metadata
from pathlib import Path
import traceback
import warnings
import signal
import time
import subprocess
import logging
import struct

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("lyra.log")
    ]
)
logger = logging.getLogger("lyra_launcher")

# Add the project directory to the Python path
sys.path.append(str(Path(__file__).parent))

# Filter NumPy-related warnings which don't affect functionality
warnings.filterwarnings("ignore", message="A module that was compiled using NumPy")
warnings.filterwarnings("ignore", message="Failed to initialize NumPy")

# Global variable to control the main loop
keep_running = True

def signal_handler(sig, frame):
    """Handle interrupt signals"""
    global keep_running
    print("Received shutdown signal. Press Ctrl+C again to force exit.")
    keep_running = False

def check_compatibility():
    """Check for potential compatibility issues and warn the user"""
    try:
        # Check for necessary packages and compatibility issues
        check_llama_cpp_compatibility()
        
        # Initialize fallback LLM in background if available
        try:
            from modules.fallback_llm import get_instance as get_fallback_llm
            fallback_llm = get_fallback_llm()
            logger.info("Core LLM initialization started in background")
        except ImportError:
            logger.info("Core LLM module not available")
    except Exception as e:
        logger.warning(f"Error during compatibility check: {e}")

def check_llama_cpp_compatibility():
    """Check if llama-cpp-python is installed and compatible"""
    try:
        import llama_cpp
        logger.info(f"Found llama_cpp version: {llama_cpp.__version__}")
    except ImportError:
        logger.warning("llama-cpp-python not installed. Some models may not be available.")
    except Exception as e:
        logger.warning(f"Error checking llama-cpp compatibility: {e}")

def test_models_local():
    """Test if models can be loaded correctly"""
    try:
        from model_config import get_manager
        
        # Get the model manager
        model_manager = get_manager()
        
        # Get lists of available models and configurations
        models = model_manager.models
        
        # Try to access configurations with different possible attribute names
        # or use an empty list if not available
        configs = getattr(model_manager, 'configurations', 
                  getattr(model_manager, 'model_configs', []))
        
        logger.info(f"Found {len(models)} models and {len(configs)} configurations")
        
        # Log the available models
        logger.info("Available models:")
        for model in models:
            model_type = getattr(model, 'model_type', 'unknown')
            logger.info(f"  - {model.name} ({model_type})")
        
        # Test Phi model if available (core model)
        phi_models = [m for m in models if "phi" in m.name.lower()]
        if phi_models:
            phi_model = phi_models[0]
            logger.info(f"Testing core model: {phi_model.name}")
            
            # Try loading the model
            loaded = model_manager.load_model(phi_model.name)
            if loaded and phi_model.name in model_manager.loaded_models:
                logger.info(f"Successfully loaded {phi_model.name}")
                
                # Try generating a short text
                response = model_manager.loaded_models[phi_model.name].generate_text("Hello, can you introduce yourself?")
                logger.info(f"Generated response: {response[:100]}...")
            else:
                logger.warning(f"Failed to load or access model: {phi_model.name}")
        
        # Also test fallback LLM if available
        try:
            from modules.fallback_llm import get_instance as get_fallback_llm
            fallback_llm = get_fallback_llm()
            
            if fallback_llm and fallback_llm.wait_for_initialization(timeout=10):
                logger.info("Testing core LLM")
                response = fallback_llm.generate_text("Hello, are you working?")
                logger.info(f"Core LLM response: {response[:100]}...")
        except ImportError:
            logger.info("Core LLM not available for testing")
        
    except ImportError as e:
        logger.error(f"Error importing required modules: {e}")
    except Exception as e:
        logger.error(f"Error testing models: {e}")

def detect_model_type(model_path):
    """
    Attempt to detect the model type based on file inspection
    """
    try:
        if not os.path.exists(model_path):
            return None
            
        # Check file extension
        if model_path.endswith((".bin", ".gguf", ".ggml")):
            return "llama.cpp"
        elif model_path.endswith(".pt") or model_path.endswith(".pth"):
            return "pytorch"
        elif os.path.isdir(model_path) and any(f.endswith(".bin") for f in os.listdir(model_path)):
            return "huggingface"
        else:
            # Default to huggingface if unsure
            return "huggingface"
    except Exception as e:
        logger.error(f"Error detecting model type: {e}")
        return None

def validate_model_with_initializer(model_path, init_type):
    """
    Validate a model with a specific initializer
    Returns True if validation was successful
    """
    # This is a simplified validation that doesn't actually load models
    # In a real implementation, you'd perform actual validation tests
    
    try:
        if not os.path.exists(model_path):
            logger.warning(f"Model path does not exist: {model_path}")
            return False
            
        if init_type == "llama.cpp":
            return model_path.endswith((".bin", ".gguf", ".ggml"))
        elif init_type == "huggingface":
            return os.path.isdir(model_path) or not model_path.endswith((".bin", ".gguf", ".ggml"))
        else:
            return True
    except Exception as e:
        logger.error(f"Error validating model: {e}")
        return False

def initialize_cognitive_modules():
    """Initialize core cognitive modules including extended thinking"""
    try:
        logger.info("Initializing cognitive modules...")
        
        # Use the cognitive initializer to set up all modules
        try:
            from utils.cognitive_initializer import initialize_cognitive_modules as init_cognitive
            
            # Get model manager first
            try:
                from modules.model_config import get_manager
                model_manager = get_manager()
            except ImportError:
                logger.warning("Model manager not available for cognitive initialization")
                model_manager = None
            
            # Initialize all cognitive modules
            results = init_cognitive(model_manager)
            
            # Log results
            successful = sum(1 for r in results.values() if r)
            total = len(results)
            logger.info(f"Initialized {successful}/{total} cognitive modules")
            
            # Log detailed results at debug level
            for module, success in results.items():
                if success:
                    logger.debug(f"Successfully initialized {module}")
                else:
                    logger.warning(f"Failed to initialize {module}")
            
        except ImportError:
            logger.warning("Cognitive initializer not available, falling back to manual initialization")
            # Fall back to manual initialization
            _initialize_cognitive_modules_fallback()
    except Exception as e:
        logger.error(f"Error initializing cognitive modules: {e}")

def _initialize_cognitive_modules_fallback():
    """Fallback method for initializing cognitive modules individually"""
    # Initialize metacognition
    try:
        from modules.metacognition import get_instance as get_metacognition
        metacognition = get_metacognition()
        logger.info("Metacognition module initialized")
    except ImportError:
        logger.warning("Metacognition module not available")
    
    # Initialize emotional core
    try:
        from modules.emotional_core import get_instance as get_emotional_core
        emotional_core = get_emotional_core()
        logger.info("Emotional core module initialized")
    except ImportError:
        logger.warning("Emotional core module not available")
    
    # Initialize deep memory
    try:
        from modules.deep_memory import get_instance as get_deep_memory
        deep_memory = get_deep_memory()
        logger.info("Deep memory module initialized")
    except ImportError:
        logger.warning("Deep memory module not available")
        
    # Initialize boredom integration
    try:
        from modules.boredom_integration import get_instance as get_boredom_integration
        boredom_integration = get_boredom_integration()
        logger.info("Boredom integration initialization started")
    except ImportError:
        logger.warning("Boredom integration module not available")
    
    # Initialize thinking integration
    try:
        from modules.thinking_integration import get_instance as get_thinking_capabilities
        thinking_capabilities = get_thinking_capabilities()
        logger.info("Thinking integration module initialized")
    except ImportError:
        logger.warning("Thinking integration module not available")
    
    # Initialize cognitive integration
    try:
        from modules.cognitive_integration import get_instance as get_cognitive_architecture
        cognitive_architecture = get_cognitive_architecture()
        logger.info("Cognitive architecture initialized")
        
        # Connect modules to model manager
        model_manager = None
        try:
            from modules.model_config import get_manager
            model_manager = get_manager()
            cognitive_architecture.connect_with_model_manager(model_manager)
            logger.info("Connected cognitive architecture with model manager")
        except ImportError:
            logger.warning("Model manager not available for cognitive integration")
            
    except ImportError:
        logger.warning("Cognitive integration module not available")
        
    # Initialize cognitive model integration
    try:
        from modules.cognitive_model_integration import get_instance as get_model_integration
        model_manager_arg = model_manager if 'model_manager' in locals() and model_manager is not None else None
        model_integration = get_model_integration(model_manager_arg)
        logger.info("Cognitive model integration initialized")
    except ImportError:
        logger.warning("Cognitive model integration module not available")
    except Exception as e:
        logger.warning(f"Error initializing cognitive model integration: {e}")

def main():
    """
    Main launcher for Lyra - starts the airlock interface by default
    but allows command-line options for flexibility
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Lyra AI System")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the interface on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--direct", action="store_true", help="Skip airlock, launch main interface directly")
    parser.add_argument("--no-media", action="store_true", help="Disable media generation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--test-models", action="store_true", help="Test model initialization and exit")
    parser.add_argument("--use-core-model", action="store_true", help="Use core LLM for text generation")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram bot integration")
    parser.add_argument("--disable-boredom", action="store_true", help="Disable boredom checker")
    args = parser.parse_args()

    # Get the directory this script is in
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure we're in the correct directory
    os.chdir(BASE_DIR)
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Run model tests if requested
    if args.test_models:
        test_models_local()
        return

    # Initialize cognitive modules - ALWAYS initialize extended thinking
    initialize_cognitive_modules()
    
    # Check compatibility
    check_compatibility()

    # Choose which app to run
    if args.direct:
        target_script = "lyra_ui.py"
        logger.info("Launching main interface directly")
    else:
        target_script = "airlock_app.py"
        logger.info("Launching airlock interface")
    
    # Build command to run the appropriate script
    cmd = [sys.executable, os.path.join(BASE_DIR, target_script)]
    
    # Add command line arguments
    if args.port != 7860:
        cmd.extend(["--port", str(args.port)])
    if args.share:
        cmd.append("--share")
    if args.debug:
        cmd.append("--debug")
    if args.no_media and args.direct:
        cmd.append("--no-media")
    if args.use_core_model:
        cmd.append("--use-core-model")
    if args.telegram:
        cmd.append("--telegram")
    if args.disable_boredom:
        cmd.append("--disable-boredom")
    
    # Always pass extended thinking flag
    cmd.append("--extended-thinking")
    cmd.append("--extended-thinking")
    
    try:
        # Run the target script
        logger.info(f"Running command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        
        # Wait for a short time to check if the process crashes immediately
        time.sleep(2)
        returncode = process.poll()
        
        if returncode is not None and returncode != 0:
            logger.error(f"Error running {target_script}: Process exited with code {returncode}")
            
            # If there was an error with the airlock, try launching the main interface directly
            if target_script == "airlock_app.py":
                logger.info("Attempting to launch main interface directly")
                main_with_boredom_disabled()
            else:
                logger.error("Main interface also failed to start")
                print("Error starting Lyra. Check the logs for details.")
        else:
            # Process is still running, wait for it to complete
            process.wait()
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running {target_script}: {e}")
        
        # If there was an error with the airlock, try launching the main interface directly
        if target_script == "airlock_app.py":
            logger.info("Attempting to launch main interface directly")
            main_with_boredom_disabled()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        handle_error(e, args.debug)

def main_with_boredom_disabled():
    """Retry main with boredom checker disabled"""
    # Create a modified args list with --disable-boredom added
    modified_args = sys.argv[1:] if len(sys.argv) > 1 else []
    if '--disable-boredom' not in modified_args:
        modified_args.append('--disable-boredom')
    
    # Add --direct flag to bypass airlock
    if '--direct' not in modified_args:
        modified_args.append('--direct')
    
    sys.argv[1:] = modified_args
    main()  # Retry with boredom checker disabled

def handle_error(e, debug_mode):
    """Handle error with appropriate messaging"""
    print(f"Error starting Lyra: {e}")
    if debug_mode:
        import traceback
        traceback.print_exc()
    else:
        print("Run with --debug flag for more information")

if __name__ == "__main__":
    # Register signal handler
    import signal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    main()
