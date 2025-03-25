import logging
import importlib
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("register_improvement")

def register_collaborative_improvement():
    """
    Register the collaborative improvement module with the main Lyra system.
    This makes the module available to be called from other parts of the system.
    """
    try:
        # Import necessary modules
        logger.info("Importing collaborative improvement modules")
        from modules.improvement_interface import create_collaborative_improvement_interface
        from modules.collaborative_improvement import CollaborativeImprovement
        from modules.media_integration import MediaIntegrator
        
        # Register the module in Lyra's extension system
        # This is a placeholder for the actual registration code
        # that would depend on Lyra's extension mechanism
        logger.info("Registering collaborative improvement module")
        
        # Create the UI component
        improvement_ui = create_collaborative_improvement_interface()
        
        # Create the improvement processor
        improvement_processor = CollaborativeImprovement()
        
        # Create the media integrator
        media_integrator = MediaIntegrator()
        
        # Return the components that other parts of the system might need
        return {
            "ui": improvement_ui,
            "processor": improvement_processor,
            "media_integrator": media_integrator,
            "name": "Collaborative Improvement",
            "version": "0.1.0",
            "description": "A module that facilitates AI self-improvement through human interaction"
        }
    except Exception as e:
        logger.error(f"Failed to register collaborative improvement module: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def is_available():
    """Check if all requirements for the module are available."""
    try:
        # Check for required packages
        import numpy
        import re
        import json
        import gradio
        
        # Check for required files
        required_files = [
            Path("modules/collaborative_improvement.py"),
            Path("modules/improvement_interface.py"),
            Path("modules/media_integration.py")
        ]
        
        for file in required_files:
            if not file.exists():
                logger.warning(f"Required file {file} not found")
                return False
        
        return True
    except ImportError as e:
        logger.warning(f"Missing dependency: {e}")
        return False

# This allows the module to be run directly to test availability
if __name__ == "__main__":
    if is_available():
        print("Collaborative improvement module is available for registration")
    else:
        print("Collaborative improvement module is missing dependencies")
