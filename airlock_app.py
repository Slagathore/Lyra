"""
Airlock App for Lyra - Entry point interface that verifies system setup before launching the main UI
"""
import os
import sys
import time
import signal
import logging
import argparse
import subprocess
import threading
from pathlib import Path

# Add the project directory to the Python path
file_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(file_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger("airlock_app")

# Import modules
import gradio as gr
from model_config import ModelConfig, get_manager

# Initialization status tracking
init_status = {
    "core_llm": "Starting...",
    "extended_thinking": "Starting...",
    "boredom_system": "Starting...",
    "metacognition": "Starting...",
    "emotional_core": "Starting...",
    "deep_memory": "Starting...",
    "overall_progress": 0
}

# Initialize core LLM in background if available
core_llm = None
try:
    from modules.fallback_llm import get_instance as get_fallback_llm
    core_llm = get_fallback_llm()
    logger.info("Core LLM initialization started in background")
    init_status["core_llm"] = "Initializing..."
except ImportError:
    logger.info("Core LLM module not available")
    init_status["core_llm"] = "Not available"

# Always initialize extended thinking
try:
    from modules.extended_thinking import get_instance as get_extended_thinking
    extended_thinking = get_extended_thinking()
    logger.info("Extended thinking initialized")
    init_status["extended_thinking"] = "Initializing..."
except ImportError:
    logger.warning("Extended thinking module not available")
    init_status["extended_thinking"] = "Not available"

def update_initialization_status():
    """Update the initialization status of modules"""
    global init_status
    
    # Check core LLM status
    if core_llm and hasattr(core_llm, 'initialized'):
        init_status["core_llm"] = "Ready" if core_llm.initialized else "Initializing..."
    
    # Check extended thinking status
    if 'extended_thinking' in sys.modules:
        from modules.extended_thinking import get_instance
        ext_thinking = get_instance()
        init_status["extended_thinking"] = "Ready" if ext_thinking.enabled else "Initializing..."
    
    # Check boredom system
    try:
        from modules.boredom import get_instance
        boredom = get_instance()
        init_status["boredom_system"] = "Ready" if boredom.enabled else "Initializing..."
    except ImportError:
        init_status["boredom_system"] = "Not available"
    
    # Check metacognition
    try:
        from modules.metacognition import get_instance
        metacog = get_instance()
        init_status["metacognition"] = "Ready" if metacog.enabled else "Initializing..."
    except (ImportError, AttributeError):
        init_status["metacognition"] = "Not available"
    
    # Check emotional core
    try:
        from modules.emotional_core import get_instance
        emotional = get_instance()
        init_status["emotional_core"] = "Ready" if hasattr(emotional, 'initialized') and emotional.initialized else "Initializing..."
    except ImportError:
        init_status["emotional_core"] = "Not available"
    
    # Check deep memory
    try:
        from modules.deep_memory import get_instance
        memory = get_instance()
        init_status["deep_memory"] = "Ready" if hasattr(memory, 'initialized') and memory.initialized else "Initializing..."
    except ImportError:
        init_status["deep_memory"] = "Not available"
    
    # Calculate overall progress
    ready_count = sum(1 for status in init_status.values() if status == "Ready")
    total_modules = len(init_status) - 1  # Subtract 1 for the overall_progress key
    init_status["overall_progress"] = int((ready_count / total_modules) * 100) if total_modules > 0 else 0
    
    return init_status

def initialize_cognitive_modules():
    """Initialize cognitive modules in the background"""
    try:
        global init_status
        
        # Initialize metacognition
        try:
            from modules.metacognition import get_instance as get_metacognition
            metacognition = get_metacognition()
            logger.info("Metacognition module initialized")
            init_status["metacognition"] = "Ready"
        except ImportError:
            logger.info("Metacognition module not available")
            init_status["metacognition"] = "Not available"
        
        # Initialize emotional core
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            emotional_core = get_emotional_core()
            logger.info("Emotional core module initialized")
            init_status["emotional_core"] = "Ready"
        except ImportError:
            logger.info("Emotional core module not available")
            init_status["emotional_core"] = "Not available"
        
        # Initialize deep memory
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            deep_memory = get_deep_memory()
            logger.info("Deep memory module initialized")
            init_status["deep_memory"] = "Ready"
        except ImportError:
            logger.info("Deep memory module not available")
            init_status["deep_memory"] = "Not available"
        
        # Initialize cognitive integration
        try:
            from modules.cognitive_integration import get_instance as get_cognitive_architecture
            cognitive_architecture = get_cognitive_architecture()
            logger.info("Cognitive architecture initialized")
            
            # Connect with model manager
            model_manager = get_manager()
            cognitive_architecture.connect_with_model_manager(model_manager)
            logger.info("Connected cognitive architecture with model manager")
        except ImportError:
            logger.info("Cognitive integration module not available")
            
        # Initialize thinking integration - always initialize
        try:
            from modules.thinking_integration import get_instance as get_thinking_capabilities
            thinking_capabilities = get_thinking_capabilities()
            logger.info("Thinking capabilities module initialized")
            
            # Connect with model manager for advanced thinking
            model_manager = get_manager()
            thinking_capabilities.connect_model_manager(model_manager)
            init_status["extended_thinking"] = "Ready"
        except ImportError:
            logger.info("Thinking integration module not available")
            
        # Initialize boredom system and integration
        try:
            from modules.boredom import get_instance as get_boredom
            boredom = get_boredom()
            logger.info("Boredom system initialized")
            init_status["boredom_system"] = "Ready"
            
            from modules.boredom_integration import get_instance as get_boredom_integration
            boredom_integration = get_boredom_integration()
            logger.info("Boredom integration initialized")
        except ImportError:
            logger.info("Boredom system or integration not available")
            
        # Initialize code auditing if available
        try:
            from modules.code_auditing import get_instance as get_code_auditor
            auditor = get_code_auditor()
            logger.info("Code auditing module initialized")
        except ImportError:
            logger.info("Code auditing module not available")
        
        logger.info("All cognitive modules initialized")
        
        # Update the status one final time
        update_initialization_status()
    except Exception as e:
        logger.error(f"Error initializing cognitive modules: {e}")

# Start cognitive module initialization in background
init_thread = threading.Thread(target=initialize_cognitive_modules, daemon=True)
init_thread.start()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Lyra Airlock Interface")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the interface on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--use-core-model", action="store_true", help="Use core LLM for text generation")
    parser.add_argument("--extended-thinking", action="store_true", help="Enable extended thinking capabilities")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram bot integration")
    return parser.parse_args()

def verify_models():
    """Verify model availability and filter to only include models from TT Models folder"""
    model_manager = get_manager()
    models = model_manager.models
    
    # Only include models from the TT Models folder
    tt_models_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "TT Models")
    
    # Filter out models not in TT Models folder
    filtered_models = []
    for model in models:
        # Check if model path is in TT Models folder
        if hasattr(model, 'model_path') and model.model_path:
            model_path = model.model_path
            if os.path.exists(model_path) and tt_models_path in model_path:
                filtered_models.append(model)
        # For fallback or other models without explicit paths
        elif "tt_models" in getattr(model, 'name', '').lower():
            filtered_models.append(model)
    
    return len(filtered_models) > 0, [model.name for model in filtered_models]

def verify_system_requirements():
    """Verify that the system meets requirements"""
    # Check for GPU availability
    try:
        import torch
        has_gpu = torch.cuda.is_available()
        gpu_info = torch.cuda.get_device_name(0) if has_gpu else "No GPU detected"
    except (ImportError, Exception):
        has_gpu = False
        gpu_info = "Could not detect GPU (torch not available)"
    
    # Check for memory
    import psutil
    mem = psutil.virtual_memory()
    total_ram = mem.total / (1024 ** 3)  # Convert to GB
    
    # Check for disk space
    disk = psutil.disk_usage('/')
    total_disk = disk.total / (1024 ** 3)  # Convert to GB
    free_disk = disk.free / (1024 ** 3)  # Convert to GB
    
    return {
        "has_gpu": has_gpu,
        "gpu_info": gpu_info,
        "total_ram_gb": round(total_ram, 2),
        "free_disk_gb": round(free_disk, 2),
        "python_version": sys.version.split()[0]
    }

def launch_main_interface(model_name=None, enable_telegram=False):
    """Launch the main Lyra interface on a different port"""
    args = parse_args()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct command to launch main interface
    cmd = [sys.executable, os.path.join(base_dir, "lyra_ui.py")]
    
    # Set main UI to use a different port (7861 instead of airlock's 7860)
    main_ui_port = args.port + 1  # Use next port after airlock
    cmd.extend(["--port", str(main_ui_port)])
    
    # Add other command line arguments
    if args.share:
        cmd.append("--share")
    if args.debug:
        cmd.append("--debug")
    if args.use_core_model:
        cmd.append("--use-core-model")
    
    # Always add extended thinking flag
    cmd.append("--extended-thinking")
    
    # Add model if specified and not "None"
    if model_name and model_name.lower() != "none" and model_name != "None - Use Default":
        cmd.extend(["--model", model_name])
    
    # Add telegram flag if requested
    if enable_telegram or args.telegram:
        cmd.append("--telegram")
        
    # Add initialization progress status
    init_status_arg = f"--init-status={init_status['overall_progress']}"
    cmd.append(init_status_arg)
    
    logger.info(f"Launching main interface with command: {' '.join(cmd)}")
    
    # Show a message indicating successful launch with correct port
    success_message = f"Launching Lyra main interface. This tab can be closed. Lyra will be available at http://127.0.0.1:{main_ui_port}"
    
    # First start the main UI process BEFORE shutting down the airlock
    # This approach allows the process to start loading before we shut down
    try:
        # Start the main UI process
        process = subprocess.Popen(cmd)
        logger.info(f"Started main UI process with PID: {process.pid}")
        
        # Wait for the UI to start (no need to kill airlock since it uses a different port)
        success_message += "\n\nThe Airlock interface will remain open while Lyra loads."
    except Exception as e:
        logger.error(f"Error during launch: {e}")
        return f"Error launching main interface: {str(e)}"
    
    # Return success message
    return success_message

def check_modules_status():
    """Check status of cognitive modules"""
    status = update_initialization_status()
    
    status_lines = []
    for module, state in status.items():
        if module != "overall_progress":  # Skip the progress value
            status_lines.append(f"- {module.replace('_', ' ').title()}: {state}")
    
    return "\n".join(status_lines)

def create_airlock_ui():
    """Create the airlock UI"""
    with gr.Blocks(title="Lyra AI - Airlock", theme=gr.themes.Soft()) as airlock_ui:
        gr.Markdown("# Lyra AI - System Verification")
        
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("## System Requirements")
                system_info = verify_system_requirements()
                
                with gr.Group():
                    gr.Markdown(f"- **Python Version**: {system_info['python_version']}")
                    gr.Markdown(f"- **GPU**: {'Available - ' + system_info['gpu_info'] if system_info['has_gpu'] else 'Not Available'}")
                    gr.Markdown(f"- **Memory**: {system_info['total_ram_gb']} GB")
                    gr.Markdown(f"- **Free Disk Space**: {system_info['free_disk_gb']} GB")
                
                has_models, model_list = verify_models()
                
                gr.Markdown("## Model Selection")
                
                # Add "None" option at the top of the list
                model_choices = ["None - Use Default"]
                if has_models:
                    model_choices.extend(model_list)
                
                models_dropdown = gr.Dropdown(
                    choices=model_choices,
                    value="None - Use Default",
                    label="Select Model to Launch With (Optional)"
                )
                
                telegram_checkbox = gr.Checkbox(label="Enable Telegram Bot", value=False)
                
                launch_btn = gr.Button("Launch Lyra", variant="primary")
                status_text = gr.Textbox(label="Status", interactive=False)
                
                # Event handlers
                def handle_launch(model, telegram):
                    # If "None - Use Default" is selected, pass None to launch_main_interface
                    if model == "None - Use Default":
                        return launch_main_interface(None, telegram)
                    return launch_main_interface(model, telegram)
                
                launch_btn.click(
                    fn=handle_launch,
                    inputs=[models_dropdown, telegram_checkbox],
                    outputs=[status_text]
                )
            
            with gr.Column(scale=2):
                gr.Markdown("## Lyra Cognitive System")
                gr.Markdown("Initializing cognitive modules... This may take a few minutes.")
                
                # Fix the Progress component - remove problematic arguments
                progress_bar = gr.Progress(elem_id="startup_progress")
                
                # Display detailed status of module loading
                status_modules = gr.Markdown("*Loading modules...*")
                
                # Add a real-time console log display
                log_display = gr.Textbox(
                    label="Initialization Log", 
                    placeholder="Loading modules...",
                    lines=12,
                    max_lines=12,
                    interactive=False
                )
                
                # Add a refresh button for module status
                refresh_button = gr.Button("Refresh Status")
                
                # Status info that shows where Lyra will be hosted
                gr.Markdown("## Connection Information")
                main_ui_port = parse_args().port + 1
                server_info = gr.Markdown(f"""
                Lyra will be hosted at: 
                - **Local URL**: http://127.0.0.1:{main_ui_port}
                - **Network URL**: http://your-ip-address:{main_ui_port} (if accessible on your network)
                
                The Airlock interface will continue running on port {parse_args().port} until closed.
                """)
                
                # Register the refresh button callback
                refresh_button.click(
                    fn=check_modules_status,
                    inputs=[],
                    outputs=[status_modules]
                )
                
                # Show initial status
                status_modules.value = check_modules_status()
        
        # Add a status bar at the bottom
        with gr.Row(variant="compact"):
            status_bar = gr.Markdown("Initializing system components...")
        
        # Set up the progress updater function
        def update_progress():
            """Update progress information"""
            status = update_initialization_status()
            progress_value = status["overall_progress"] / 100
            
            # Update the log with latest module status
            ready_modules = [k for k, v in status.items() if v == "Ready" and k != "overall_progress"]
            initializing_modules = [k for k, v in status.items() if v == "Initializing..." and k != "overall_progress"]
            
            log_text = "=== Initialization Status ===\n"
            if ready_modules:
                log_text += f"Ready: {', '.join(m.replace('_', ' ').title() for m in ready_modules)}\n"
            if initializing_modules:
                log_text += f"Initializing: {', '.join(m.replace('_', ' ').title() for m in initializing_modules)}\n"
            
            status_message = f"System initialization: {status['overall_progress']}% complete"
            
            if status["core_llm"] == "Ready":
                status_message += " | Core LLM: Ready"
            
            return progress_value, log_text, status_message
            
        # Function to periodically update the progress - fix the progress update syntax
        def progress_updater(progress=gr.Progress()):
            last_value = 0
            log_content = ""
            
            while True:
                progress_value, new_log, status_message = update_progress()
                
                # Update progress with proper syntax
                progress(progress_value)
                
                # If progress changed, update the progress bar
                if progress_value != last_value:
                    last_value = progress_value
                
                # Update the log if there are changes
                if new_log != log_content:
                    log_content = new_log
                    yield progress_value, new_log, status_message
                
                # If fully initialized, break the loop
                if progress_value >= 1.0:
                    break
                
                # Wait before checking again
                time.sleep(2)
            
            yield 1.0, log_content, "System initialization complete! Ready to launch."
        
        # Schedule the progress updater
        airlock_ui.load(
            progress_updater,
            outputs=[progress_bar, log_display, status_bar],
            _js="() => {document.getElementById('startup_progress').style.display = 'block';}"
        )
    
    return airlock_ui

def main():
    """Main entry point for airlock app"""
    args = parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        
    try:
        # Create the UI
        airlock_ui = create_airlock_ui()
        
        # Launch the UI
        logger.info("Starting airlock interface...")
        server = airlock_ui.launch(
            server_name="0.0.0.0",  # Bind to all addresses
            server_port=args.port,
            share=args.share,
            prevent_thread_lock=True
        )
        
        # Log server URLs
        local_url = f"http://127.0.0.1:{args.port}"
        logger.info(f"Airlock interface running at: {local_url}")
        
        # If server object has the urls attribute, log all URLs
        if hasattr(server, 'urls'):
            for url in server.urls:
                logger.info(f"Server URL: {url}")
        
        # Keep the main thread running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down airlock")
    except Exception as e:
        logger.error(f"Error starting airlock: {e}")
        # Try to launch with a simplified UI if there's an error with the progress bar
        try:
            logger.info("Attempting to launch with simplified UI")
            launch_simplified_ui(args)
        except Exception as nested_e:
            logger.error(f"Failed to launch simplified UI: {nested_e}")

def launch_simplified_ui(args):
    """Launch a simplified version of the airlock UI if the main one fails"""
    # Create a simpler UI without the progress elements that might be causing issues
    with gr.Blocks(title="Lyra AI - Airlock (Simple Mode)") as simple_ui:
        gr.Markdown("# Lyra AI - System Verification (Simple Mode)")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("## System Requirements")
                system_info = verify_system_requirements()
                
                with gr.Group():
                    gr.Markdown(f"- **Python Version**: {system_info['python_version']}")
                    gr.Markdown(f"- **GPU**: {'Available - ' + system_info['gpu_info'] if system_info['has_gpu'] else 'Not Available'}")
                    gr.Markdown(f"- **Memory**: {system_info['total_ram_gb']} GB")
                    gr.Markdown(f"- **Free Disk Space**: {system_info['free_disk_gb']} GB")
                
                has_models, model_list = verify_models()
                
                gr.Markdown("## Model Selection")
                if has_models:
                    # Add "None - Use Default" as first option
                    model_choices = ["None - Use Default"] + model_list
                    models_dropdown = gr.Dropdown(
                        choices=model_choices,
                        value="None - Use Default",
                        label="Select Model to Launch With (Optional)"
                    )
                else:
                    gr.Markdown("No models found. Default model will be used.")
                    models_dropdown = gr.Textbox(visible=False, value="None")
                
                telegram_checkbox = gr.Checkbox(label="Enable Telegram Bot", value=False)
                
                launch_btn = gr.Button("Launch Lyra", variant="primary")
                status_text = gr.Textbox(label="Status", interactive=False)
                
                # Event handlers
                def handle_launch(model, telegram):
                    # If "None - Use Default" is selected, pass None to launch_main_interface
                    if model == "None - Use Default" or not model:
                        return launch_main_interface(None, telegram)
                    return launch_main_interface(model, telegram)
                
                launch_btn.click(
                    fn=handle_launch,
                    inputs=[models_dropdown, telegram_checkbox],
                    outputs=[status_text]
                )
    
    # Launch the simplified UI
    logger.info("Starting simplified airlock interface...")
    server = simple_ui.launch(
        server_name="0.0.0.0",
        server_port=args.port,
        share=args.share,
        prevent_thread_lock=True
    )
    
    # Log server URLs
    local_url = f"http://127.0.0.1:{args.port}"
    logger.info(f"Simplified airlock interface running at: {local_url}")
    
    # Keep the main thread running
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
