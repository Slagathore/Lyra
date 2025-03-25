#!/usr/bin/env python3
import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to sys.path to find modules
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("lyra.log")
    ]
)
logger = logging.getLogger("launcher")

def main():
    """Launch the Lyra AI application in the appropriate mode."""
    parser = argparse.ArgumentParser(description="Lyra AI Launcher")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the interface on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--mode", choices=["direct", "airlock"], default="direct", 
                      help="Launch mode: direct=main interface, airlock=model selection first")
    parser.add_argument("--no-media", action="store_true", help="Disable media generation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("Debug logging enabled")
    
    logger.info(f"Starting Lyra AI System in {args.mode} mode")
    
    try:
        if args.mode == "direct":
            # Launch in direct mode (main interface)
            from modules.chat_ui import create_chat_ui
            interface = create_chat_ui(disable_media=args.no_media)
            logger.info("Created main interface")
        else:
            # Launch in airlock mode
            from modules.airlock_interface import AirlockInterface
            from modules.chat_ui import create_chat_ui
            
            # Create airlock interface
            airlock = AirlockInterface()
            interface, launch_btn, selected_models, active_features = airlock.create_ui()
            logger.info("Created airlock interface")
            
            # Set up the transition to main app
            def switch_to_main_app(selected_models):
                if not selected_models:
                    return gr.update(visible=True), gr.update(visible=False), "Please select at least one model"
                
                logger.info(f"Launching main app with models: {selected_models}")
                
                # Create the main app interface
                main_interface = create_chat_ui(selected_models=selected_models)
                
                # Hide airlock, show main app
                return gr.update(visible=False), gr.update(visible=True, value=main_interface), ""
            
            # Set up the combined interface
            import gradio as gr
            with gr.Blocks(title="Lyra AI System") as app:
                error_msg = gr.Textbox(label="Status", visible=False)
                
                with gr.Row(visible=True) as airlock_container:
                    # Embed the airlock interface
                    interface.render()
                
                with gr.Row(visible=False) as main_app_container:
                    main_interface = gr.HTML("Loading main application...")
                
                # Connect launch button to transition function
                launch_btn.click(
                    fn=switch_to_main_app,
                    inputs=[selected_models],
                    outputs=[airlock_container, main_app_container, error_msg]
                )
            
            interface = app
        
        # Launch the interface
        interface.launch(
            server_name="0.0.0.0",
            server_port=args.port,
            share=args.share,
            inbrowser=True
        )
        
        return 0
    except Exception as e:
        logger.error(f"Error starting Lyra: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
