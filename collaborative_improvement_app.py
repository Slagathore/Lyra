import argparse
import logging
import os
import sys
from pathlib import Path
import gradio as gr

# Add modules directory to path
sys.path.append(os.path.abspath("."))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("collaborative_improvement.log")
    ]
)
logger = logging.getLogger("collaborative_improvement_app")

def main():
    """Main entry point for the collaborative improvement application."""
    parser = argparse.ArgumentParser(description="Collaborative Improvement Module")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the Gradio interface on")
    parser.add_argument("--no-media", action="store_true", help="Disable media generation")
    parser.add_argument("--auto-improve", action="store_true", help="Enable automatic code improvements")
    parser.add_argument("--check-improvements", action="store_true", help="Check for pending code improvements")
    args = parser.parse_args()
    
    logger.info("Starting Collaborative Improvement Module")
    
    # Import here to avoid circular imports
    from modules.register_improvement import register_collaborative_improvement, is_available
    
    # Check if all requirements are available
    if not is_available():
        logger.error("Not all requirements for the collaborative improvement module are available")
        print("Error: Missing dependencies. See log for details.")
        return 1
    
    # Register the module
    components = register_collaborative_improvement()
    if not components:
        logger.error("Failed to register collaborative improvement module")
        print("Error: Failed to initialize module. See log for details.")
        return 1
    
    # Get the UI
    ui = components["ui"]
    
    # Set up code updater if auto-improve is enabled
    if args.auto_improve or args.check_improvements:
        try:
            from modules.code_updater import CodeUpdater
            code_updater = CodeUpdater()
            
            # If auto-improve, apply all pending suggestions with high impact
            if args.auto_improve:
                logger.info("Auto-improvement enabled, checking for pending suggestions")
                pending = code_updater.get_pending_suggestions()
                
                if pending:
                    logger.info(f"Found {len(pending)} pending code improvement suggestions")
                    for suggestion_id, suggestion in pending.items():
                        logger.info(f"Auto-implementing suggestion: {suggestion_id}")
                        implementation_id = code_updater.apply_suggestion(suggestion_id, auto_mode=True)
                        if implementation_id:
                            logger.info(f"Successfully applied suggestion {suggestion_id} as {implementation_id}")
                        else:
                            logger.warning(f"Failed to apply suggestion {suggestion_id}")
                else:
                    logger.info("No pending code improvement suggestions found")
            
            # If just checking, print out pending suggestions
            elif args.check_improvements:
                pending = code_updater.get_pending_suggestions()
                if pending:
                    print(f"Found {len(pending)} pending code improvement suggestions:")
                    for suggestion_id, suggestion in pending.items():
                        print(f"- {suggestion_id}: {suggestion.get('description')} (Impact: {suggestion.get('estimated_impact', 'unknown')})")
                else:
                    print("No pending code improvement suggestions found")
        except Exception as e:
            logger.error(f"Error setting up code updater: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Launch the interface
    logger.info(f"Launching Gradio interface on port {args.port}")
    gr.close_all()
    
    # Launch the interface
    ui.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=False,
        inbrowser=True
    )
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
