"""
Utility functions to suppress common warnings that might clutter the console
but aren't critical to the application's functionality.
"""
import warnings
import logging
import os
import sys

logger = logging.getLogger(__name__)

def suppress_common_warnings():
    """
    Suppress common warnings that might clutter the console but aren't
    critical to the application's functionality.
    """
    # NumPy related warnings
    warnings.filterwarnings("ignore", message=".*NumPy.*")
    warnings.filterwarnings("ignore", message=".*numpy.*")
    
    # Gradio related warnings (often related to component deprecation)
    warnings.filterwarnings("ignore", message=".*gradio.*")
    
    # Torch related warnings (common for model loading)
    warnings.filterwarnings("ignore", message=".*torch.*cuda.*")
    warnings.filterwarnings("ignore", message=".*source code of class.*")
    
    # Hugging Face related warnings
    warnings.filterwarnings("ignore", message=".*huggingface.*")
    warnings.filterwarnings("ignore", message=".*tokenizers.*")
    
    # Common ResourceWarning
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    logger.debug("Common warnings suppressed")

def enable_debugging_warnings():
    """
    Re-enable warnings for debugging purposes.
    Call this when you need to see all warnings for debugging.
    """
    warnings.resetwarnings()
    # Show all warnings
    warnings.simplefilter("default")
    logger.info("All warnings enabled for debugging")

def configure_environment_for_warnings():
    """
    Configure environment variables to control warnings from
    various libraries.
    """
    # Suppress TensorFlow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # 0=all, 1=info, 2=warning, 3=error
    
    # Suppress PyTorch warnings
    if 'PYTORCH_DISABLE_WARNINGS' not in os.environ:
        os.environ['PYTORCH_DISABLE_WARNINGS'] = '1'
    
    # Configure Python warnings globally
    if not sys.warnoptions:
        # If no Python warning options are set, configure them
        warnings.simplefilter("ignore")
        # But still show deprecation warnings for our own code
        warnings.filterwarnings("default", category=DeprecationWarning, 
                               module=r"modules\.")
        
    logger.debug("Environment configured for warning suppression")
