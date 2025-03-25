import gradio as gr
import argparse
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("lyra.log")
    ]
)
logger = logging.getLogger("lyra_app")

def main():
    """Main entry point for the Lyra application."""
    parser = argparse.ArgumentParser(description="Lyra AI System")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the interface on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--no-media", action="store_true", help="Disable media generation")
    parser.add_argument("--mode", choices=["default", "collaborative", "direct"], default="default", 
                       help="Operation mode: default=full system, collaborative=improvement mode, direct=direct model chat")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    logger.info("Starting Lyra AI System")
    
    # Initialize model manager to ensure models are available
    from modules.model_manager import ModelManager
    model_manager = ModelManager()
    models = list(model_manager.model_configs.keys())
    if not models:
        logger.warning("No models configured. Please add models in the settings.")
    else:
        logger.info(f"Found {len(models)} configured models: {', '.join(models)}")
    
    # Create appropriate interface based on mode
    if args.mode == "direct":
        # Direct chat with models
        from modules.chat_interface import create_chat_interface
        interface = create_chat_interface()
        logger.info("Starting in direct chat mode")
        
    elif args.mode == "collaborative":
        # Collaborative improvement mode
        from modules.register_improvement import register_collaborative_improvement, is_available
        if not is_available():
            logger.error("Collaborative improvement requirements not available")
            print("Error: Missing dependencies for collaborative improvement mode")
            return 1
            
        components = register_collaborative_improvement()
        if not components:
            logger.error("Failed to register collaborative improvement module")
            print("Error: Failed to initialize collaborative improvement module")
            return 1
            
        interface = components["ui"]
        logger.info("Starting in collaborative improvement mode")
        
    else:
        # Default integrated mode
        from modules.chat_ui import create_chat_ui
        interface = create_chat_ui(disable_media=args.no_media)
        logger.info("Starting in integrated mode (default)")
    
    # Launch interface
    interface.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        inbrowser=True
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
