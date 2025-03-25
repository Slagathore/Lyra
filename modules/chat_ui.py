##g:\AI\Lyra\modules\chat_ui.py
import gradio as gr
import logging
import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from modules.model_manager import ModelManager
from modules.chat_interface import ChatInterface

# Configure logging
logger = logging.getLogger(__name__)

class LyraInterface:
    """Main interface for the Lyra AI system."""
    
    def __init__(self, model_manager=None, media_integrator=None):
        """Initialize the Lyra interface with model manager and optional media integrator."""
        self.model_manager = model_manager if model_manager else ModelManager()
        self.media_integrator = media_integrator
        self.chat_interface = ChatInterface()
        
        # Load settings
        self.settings = self._load_settings()
        self.history = []
        self.session_id = f"lyra_{int(time.time())}"
        
        # Interface components
        self.chatbot = None
        self.input_box = None
        self.model_selector = None
        
        logger.info("Lyra interface initialized")
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load interface settings from configuration."""
        settings_path = Path("configs/interface_settings.json")
        default_settings = {
            "theme": "Default",
            "max_history": 50,
            "system_prompt": "You are Lyra, a helpful AI assistant. Answer the user's questions accurately and concisely.",
            "temperature": 0.7,
            "max_tokens": 512
        }
        
        if not settings_path.exists():
            return default_settings
        
        try:
            with open(settings_path, 'r') as f:
                settings = json.load(f)
            # Fill in any missing settings with defaults
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return default_settings
    
    def submit_message(self, message, history, model_name, temperature, max_tokens):
        """Submit a message and get a response from the selected model."""
        if not message:
            return "", history
            
        # Load the model if not already loaded
        if not self.model_manager.active_model or self.model_manager.active_model != model_name:
            logger.info(f"Loading model: {model_name}")
            self.model_manager.load_model(model_name)
        
        # Format the chat history for the model
        formatted_prompt = self._format_prompt(history, message)
        
        # Generate response
        try:
            response = self.model_manager.generate(
                formatted_prompt,
                temperature=float(temperature),
                max_tokens=int(max_tokens)
            )
            
            # Handle potential errors in response
            if response.startswith("Error:"):
                logger.error(f"Error generating response: {response}")
                response = f"I encountered an error while processing your request. {response}"
            
            # Add to history
            history = history + [(message, response)]
            
            return "", history
        except Exception as e:
            logger.error(f"Error in submit_message: {e}", exc_info=True)
            error_msg = f"I encountered an error while processing your request: {str(e)}"
            history = history + [(message, error_msg)]
            return "", history
    
    def _format_prompt(self, history, new_message) -> str:
        """Format the chat history and new message into a prompt for the model."""
        # Get the model's format preference from configuration
        model_format = "default"
        if self.model_manager.active_model:
            config = self.model_manager.model_configs.get(self.model_manager.active_model)
            if config:
                model_format = config.parameters.get("format", "default")
        
        # Format based on model type
        if model_format == "llama3":
            system_prompt = self.settings.get("system_prompt", "")
            formatted = f"<|system|>\n{system_prompt}</s>\n"
            
            # Add history
            for user_msg, assistant_msg in history:
                formatted += f"<|user|>\n{user_msg}</s>\n"
                formatted += f"<|assistant|>\n{assistant_msg}</s>\n"
            
            # Add new message
            formatted += f"<|user|>\n{new_message}</s>\n"
            formatted += "<|assistant|>\n"
            
        elif model_format == "chatml":
            system_prompt = self.settings.get("system_prompt", "")
            formatted = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
            
            # Add history
            for user_msg, assistant_msg in history:
                formatted += f"<|im_start|>user\n{user_msg}<|im_end|>\n"
                formatted += f"<|im_start|>assistant\n{assistant_msg}<|im_end|>\n"
            
            # Add new message
            formatted += f"<|im_start|>user\n{new_message}<|im_end|>\n"
            formatted += "<|im_start|>assistant\n"
            
        elif model_format == "wizard":
            system_prompt = self.settings.get("system_prompt", "")
            formatted = f"{system_prompt}\n\n"
            
            # Add history
            for user_msg, assistant_msg in history:
                formatted += f"USER: {user_msg}\nASSISTANT: {assistant_msg}\n\n"
            
            # Add new message
            formatted += f"USER: {new_message}\nASSISTANT:"
            
        else:
            # Default format
            system_prompt = self.settings.get("system_prompt", "")
            formatted = f"{system_prompt}\n\n"
            
            # Add history
            for user_msg, assistant_msg in history:
                formatted += f"User: {user_msg}\nAssistant: {assistant_msg}\n\n"
            
            # Add new message
            formatted += f"User: {new_message}\nAssistant:"
        
        return formatted
    
    def clear_conversation(self):
        """Clear the conversation history."""
        return [], []
    
    def save_conversation(self, history):
        """Save the conversation history to disk."""
        if not history:
            return "No conversation to save"
        
        try:
            save_dir = Path("chat_history")
            save_dir.mkdir(exist_ok=True, parents=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            file_path = save_dir / f"conversation_{timestamp}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            return f"Conversation saved to {file_path}"
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            return f"Error saving conversation: {str(e)}"
    
    def create_ui(self):
        """Create the Gradio interface for Lyra."""
        with gr.Blocks(title="Lyra AI", theme=gr.themes.Soft()) as interface:
            # Header
            with gr.Row():
                with gr.Column(scale=9):
                    gr.Markdown("# 🔮 Lyra AI")
                with gr.Column(scale=1):
                    refresh_models_btn = gr.Button("🔄 Refresh Models")
            
            with gr.Row():
                # Chat interface
                with gr.Column(scale=4):
                    self.chatbot = gr.Chatbot(
                        [],
                        elem_id="chatbot",
                        height=600,
                        avatar_images=("🧑", "🔮")
                    )
                    
                    with gr.Row():
                        self.input_box = gr.Textbox(
                            placeholder="Type your message here...",
                            elem_id="input-box",
                            show_label=False,
                            lines=3
                        )
                        submit_btn = gr.Button("Send", variant="primary")
                    
                    with gr.Row():
                        clear_btn = gr.Button("Clear Conversation")
                        save_btn = gr.Button("Save Conversation")
                        save_status = gr.Textbox(label="Status", visible=False)
                
                # Settings and control panel
                with gr.Column(scale=1):
                    gr.Markdown("### Model Settings")
                    
                    self.model_selector = gr.Dropdown(
                        choices=list(self.model_manager.model_configs.keys()),
                        label="Select Model",
                        value=next(iter(self.model_manager.model_configs.keys()), None),
                        interactive=True
                    )
                    
                    temperature = gr.Slider(
                        minimum=0.1, maximum=1.5, value=0.7, step=0.1,
                        label="Temperature"
                    )
                    
                    max_tokens = gr.Slider(
                        minimum=64, maximum=4096, value=512, step=64,
                        label="Max Tokens"
                    )
                    
                    # Media generation (if available)
                    if self.media_integrator:
                        gr.Markdown("### Media Generation")
                        
                        with gr.Accordion("Generate Image", open=False):
                            image_prompt = gr.Textbox(
                                placeholder="Describe the image you want to generate...",
                                label="Image Description"
                            )
                            generate_img_btn = gr.Button("Generate Image")
                            image_output = gr.Image(type="filepath", label="Generated Image")
            
            # Button event handlers
            submit_btn.click(
                fn=self.submit_message,
                inputs=[self.input_box, self.chatbot, self.model_selector, temperature, max_tokens],
                outputs=[self.input_box, self.chatbot]
            )
            
            # Also submit on Enter key (submit only, not newline)
            self.input_box.submit(
                fn=self.submit_message,
                inputs=[self.input_box, self.chatbot, self.model_selector, temperature, max_tokens],
                outputs=[self.input_box, self.chatbot]
            )
            
            clear_btn.click(
                fn=self.clear_conversation,
                inputs=[],
                outputs=[self.chatbot, self.input_box]
            )
            
            save_btn.click(
                fn=self.save_conversation,
                inputs=[self.chatbot],
                outputs=[save_status]
            ).then(
                fn=lambda: gr.update(visible=True),
                inputs=[],
                outputs=[save_status]
            )
            
            refresh_models_btn.click(
                fn=self.chat_interface.refresh_models,
                inputs=[],
                outputs=[self.model_selector]
            )
            
            # Media generation functionality
            if self.media_integrator and hasattr(self.media_integrator, 'generate_image'):
                generate_img_btn.click(
                    fn=self.media_integrator.generate_image,
                    inputs=[image_prompt],
                    outputs=[image_output]
                )
        
        return interface


def create_chat_ui(disable_media=False, selected_models=None):
    """Create and return a Lyra interface instance with Gradio UI.
    
    Args:
        disable_media (bool): If True, disable media generation capabilities
        selected_models (list): List of model names to make available
        
    Returns:
        gr.Blocks: The Gradio interface
    """
    # Initialize model manager
    model_manager = ModelManager()
    
    # Filter available models if a selection was provided
    if selected_models and len(selected_models) > 0:
        logger.info(f"Filtering models to selection: {selected_models}")
        filtered_models = {}
        for name, config in model_manager.model_configs.items():
            if name in selected_models:
                filtered_models[name] = config
        
        # Replace the model configs with filtered list if not empty
        if filtered_models:
            model_manager.model_configs = filtered_models
    
    # Initialize media integrator if media is enabled
    media_integrator = None
    if not disable_media:
        try:
            from modules.media_integration import MediaIntegrator
            media_integrator = MediaIntegrator()
            logger.info("Media generation capabilities enabled")
        except ImportError:
            logger.warning("Media integration module not available, media features disabled")
        except Exception as e:
            logger.error(f"Error initializing media integrator: {e}")
    
    # Create and return the interface
    chat_ui = LyraInterface(model_manager, media_integrator)
    return chat_ui.create_ui()
