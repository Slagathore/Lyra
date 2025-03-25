import os
import sys
import logging

logger = logging.getLogger(__name__)

# ...existing code...

def initialize_directories():
    """Initialize required directories for Lyra"""
    # Create directories if they don't exist
    directories = [
        "models",
        "lora",
        "logs",
        "docs",
        "data",
        "cache",
        "outputs"
    ]
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    for directory in directories:
        dir_path = os.path.join(root_dir, directory)
        os.makedirs(dir_path, exist_ok=True)
        logger.info(f"Initialized directory: {dir_path}")
        
    return root_dir

# Add this near the start of the main function
def main():
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Lyra application")
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    args = parser.parse_args()
    
    # Initialize directories
    root_dir = initialize_directories()
    
    # Add model directories to the loader
    from modules.model_loader import get_model_loader
    import modules.webui as webui
    model_loader = get_model_loader()
    model_loader.add_model_dir(os.path.join(root_dir, "models"))
    
    # Check for potentially invalid models and warn users
    models = model_loader.get_models()
    invalid_models = [path for path, info in models.items() if info.get("size_gb", 0) < 0.01]
    if invalid_models:
        logger.warning(f"Found {len(invalid_models)} potentially invalid model files (size < 10MB)")
        for path in invalid_models[:5]:  # Show first 5 to avoid log spam
            logger.warning(f"  - {path}")
        if len(invalid_models) > 5:
            logger.warning(f"  - ... and {len(invalid_models) - 5} more")
    
    # Set up global error handling for better user feedback
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        # Log the error
        logger.error("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
        # Return False to allow normal exception handling to continue
        return False
        
    sys.excepthook = global_exception_handler
    
    # ...existing code...
    
    # When launching the server, pass the port to the sharing module
    port = args.port
    if hasattr(webui, "share_global_state"):
        webui.share_global_state.port = port
    
    # ...existing code...

# ...existing code...