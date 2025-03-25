import gradio as gr
import logging
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from modules.model_manager import ModelManager
from modules.chat_ui import create_chat_ui  # Use chat_ui instead of deprecated lyra_interface
from modules.airlock_interface import AirlockInterface
from modules.media_integration import MediaIntegrator

# g:\AI\Lyra\modules\airlock_to_main.py
import torch
from PIL import Image

class AirlockAPI:
    """API for interacting with the Airlock service."""
    
    def __init__(self, api_url: str = "http://localhost:7860/api"):
        self.api_url = api_url
        
    def submit_task(self, task_type: str, content: str, parameters=None):
        """Submit a task to the airlock."""
        if parameters is None:
            parameters = {}
            
        task = {
            "type": task_type,
            "content": content,
            "parameters": parameters
        }
        
        # In a real implementation, this would make an API call
        print(f"Submitting task to airlock: {task_type}")
        
        # Mock response
        return {"task_id": "task_12345", "status": "submitted"}
    
    def check_task_status(self, task_id: str):
        """Check the status of a task in the airlock."""
        # In a real implementation, this would make an API call
        print(f"Checking status of task: {task_id}")
        
        # Mock response
        return {"task_id": task_id, "status": "completed", "result": "Task result"}
    
    def get_task_result(self, task_id: str):
        """Get the result of a completed task."""
        # In a real implementation, this would make an API call
        print(f"Getting result of task: {task_id}")
        
        # Mock response
        return {"task_id": task_id, "result": "This is the task result", "status": "completed"}

class AirlockToMainProcessor:
    """Process tasks between airlock and main system."""
    
    def __init__(self, api: AirlockAPI = None):
        self.api = api if api is not None else AirlockAPI()
    
    def process_text_task(self, content: str, parameters=None):
        """Process a text-based task."""
        if parameters is None:
            parameters = {}
            
        task_id = self.api.submit_task("text", content, parameters).get("task_id")
        
        # In a real implementation, we might poll for status
        # For now, we'll just get the result directly
        result = self.api.get_task_result(task_id)
        return result
    
    def process_image_task(self, prompt: str, parameters=None):
        """Process an image generation task."""
        if parameters is None:
            parameters = {}
            
        task_id = self.api.submit_task("image", prompt, parameters).get("task_id")
        
        # Get the result
        result = self.api.get_task_result(task_id)
        return result

# Configure logging
logger = logging.getLogger(__name__)

class AirlockConnector:
    """Manages the connection between the airlock and main interface."""
    
    def __init__(self):
        """Initialize the connector with models and media integrator."""
        self.model_manager = ModelManager()
        self.media_integrator = None
        try:
            self.media_integrator = MediaIntegrator()
            logger.info("Media integration initialized for airlock connector")
        except Exception as e:
            logger.warning(f"Could not initialize media integrator: {e}")
    
    def create_combined_interface(self):
        """Create the combined airlock and main app interface."""
        # Create the airlock interface
        airlock = AirlockInterface()
        airlock_interface, launch_btn, selected_models_list, active_features = airlock.create_ui()
        
        # Create the wrapper interface
        with gr.Blocks(title="Lyra AI System", theme=gr.themes.Soft()) as interface:
            status_msg = gr.Textbox(label="Status", visible=False)
            
            # Container for airlock (visible initially)
            with gr.Row(visible=True) as airlock_container:
                airlock_interface.render()
            
            # Container for main app (hidden initially)
            with gr.Row(visible=False) as main_container:
                main_placeholder = gr.HTML("Loading main application...")
            
            # Function to handle transition
            def transition_to_main(selected_model_list, active_features_dict=None, advanced_settings=None):
                # Ensure we handle the types correctly - selected_model_list may be a state wrapper
                if hasattr(selected_model_list, 'value'):
                    selected_model_list = selected_model_list.value
                    
                # Same for other parameters
                if hasattr(active_features_dict, 'value'):
                    active_features_dict = active_features_dict.value
                    
                if hasattr(advanced_settings, 'value'):
                    advanced_settings = advanced_settings.value
                
                # Handle empty or None model selections
                if not selected_model_list or not any(selected_model_list):
                    return (
                        gr.update(visible=True), 
                        gr.update(visible=False), 
                        "Please select at least one model"
                    )
                
                # Clean up empty selections
                if isinstance(selected_model_list, list):
                    selected_model_list = [m for m in selected_model_list if m]
                
                logger.info(f"Transitioning to main app with models: {selected_model_list}")
                
                # Configure media options based on selected features
                disable_media = True
                if active_features_dict and any(active_features_dict.values()):
                    disable_media = False
                    logger.info(f"Media features enabled: {active_features_dict}")
                
                # Create main interface with selected models and media settings
                media_options = {}
                if active_features_dict:
                    # Map airlock features to media integrator options
                    for feature_name, enabled in active_features_dict.items():
                        if enabled:
                            media_options[f"enable_{feature_name}"] = True
                
                # Apply advanced settings if provided
                if advanced_settings:
                    logger.info(f"Applying advanced settings: {advanced_settings}")
                    
                    try:
                        # Apply settings to model configs
                        for model_name in selected_model_list:
                            if model_name in self.model_manager.model_configs:
                                config = self.model_manager.model_configs[model_name]
                                
                                # Apply GPU layers if specified
                                if "gpu_layers" in advanced_settings:
                                    config.parameters["n_gpu_layers"] = advanced_settings["gpu_layers"]
                                
                                # Apply context size if specified
                                if "context_size" in advanced_settings:
                                    config.parameters["context_size"] = advanced_settings["context_size"]
                                
                                # Save updated config
                                self.model_manager.save_model_config(config)
                    except Exception as e:
                        logger.error(f"Error applying advanced settings: {e}")
                
                try:
                    # Create the main interface with options
                    main_interface = create_chat_ui(
                        disable_media=disable_media,
                        selected_models=selected_model_list,
                        media_options=media_options
                    )
                    
                    # Hide airlock, show main app
                    return (
                        gr.update(visible=False), 
                        gr.update(visible=True, value=main_interface), 
                        ""
                    )
                except Exception as e:
                    logger.error(f"Error creating main interface: {e}")
                    return (
                        gr.update(visible=True), 
                        gr.update(visible=False), 
                        f"Error: {str(e)}"
                    )
            
            # Collect advanced settings from airlock
            def collect_advanced_settings(gpu_layers, context_size, n_parallel, server_mode):
                return {
                    "gpu_layers": gpu_layers,
                    "context_size": context_size,
                    "n_parallel": n_parallel,
                    "server_mode": server_mode
                }
            
            # Advanced settings state
            advanced_settings_state = gr.State({})
            
            # Connect launch button to transition function with all settings
            launch_btn.click(
                fn=transition_to_main,
                inputs=[selected_models_list, gr.State(active_features), advanced_settings_state],
                outputs=[airlock_container, main_container, status_msg]
            )
        
        return interface

# Function to be called from main application
def initialize_airlock_to_main():
    """Initialize and return the combined interface."""
    connector = AirlockConnector()
    return connector.create_combined_interface()
