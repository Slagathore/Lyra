"""
Lyra UI - A Gradio interface for managing and interacting with LLM models
"""
import os
import json
import time
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
import argparse

from model_config import ModelConfig, get_manager
from lyra_bot import LyraBot

# Check Gradio version to handle compatibility
GRADIO_VERSION = getattr(gr, "__version__", "0.0.0")
IS_GRADIO_4_40_PLUS = tuple(map(int, GRADIO_VERSION.split("."))) >= (4, 40, 0)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Lyra AI Interface")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the interface on")
    parser.add_argument("--share", action="store_true", help="Create a shareable link")
    parser.add_argument("--model", type=str, help="Specify the model to use")
    parser.add_argument("--no-media", action="store_true", help="Disable media generation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--use-core-model", action="store_true", help="Use core LLM for text generation")
    parser.add_argument("--extended-thinking", action="store_true", help="Enable extended thinking capabilities")
    parser.add_argument("--telegram", action="store_true", help="Enable Telegram bot integration")
    parser.add_argument("--init-status", type=str, default="0", help="Initialization status from airlock")
    return parser.parse_args()

class LyraUI:
    """Main UI class for Lyra"""
    
    def __init__(self, args=None):
        # Process args
        self.args = args or parse_args()
        
        # Initialize bot
        self.bot = LyraBot()
        
        # Set up model if specified
        if self.args.model:
            self.bot.select_model(self.args.model)
        
        # Flag for whether media generation is enabled
        self.media_enabled = not self.args.no_media
        
        # Get initialization status from airlock if provided
        try:
            self.init_status = float(self.args.init_status) / 100
        except ValueError:
            self.init_status = 0
            
        # Initialize Telegram bot if enabled
        self.telegram_bot = None
        if self.args.telegram:
            self.init_telegram_bot()
        
        # Set up UI components
        self.setup_ui()
        
        # UI state
        self.current_model = None
        self.current_memory = "default"
        self.chat_history = []
        self.available_models = []
        self.available_memories = []
        self.settings = {}
        self.personality_presets = []
        
        # Load available models from the model manager
        if hasattr(self.bot, 'model_manager'):
            self.available_models = [model.name for model in self.bot.model_manager.models]
            
        # Get active model
        active_model = self.bot.model_manager.get_active_model()
        if active_model:
            self.current_model = active_model.name
            
        # Load available memories
        if hasattr(self.bot, 'memory_manager'):
            self.available_memories = self.bot.memory_manager.get_memory_names()
            
        # Ensure "default" is in available memories to prevent dropdown warning
        if "default" not in self.available_memories:
            self.available_memories.append("default")
    
    def init_telegram_bot(self):
        """Initialize the Telegram bot"""
        try:
            from telegram_bot import create_bot
            self.telegram_bot = create_bot(lyra_interface=self.bot)
            if self.telegram_bot:
                logger.info("Telegram bot initialized and started")
            else:
                logger.warning("Failed to initialize Telegram bot")
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
    
    def setup_ui(self):
        """Set up the UI components"""
        # Create the Gradio interface
        self.ui = gr.Blocks(title="Lyra AI", theme=gr.themes.Soft())
        
        with self.ui:
            gr.Markdown("# Lyra AI")
            
            # Add a progress bar that continues from airlock status
            startup_progress = gr.Progress(visible=True)
            
            # Add information bar at the top
            with gr.Row():
                with gr.Column():
                    status_bar = gr.Markdown("Initializing systems...")
            
            # Continue with the rest of the UI setup (chat interface, etc.)
            # ...
    
    def build_ui(self):
        """Build and return the Gradio interface"""
        # Define CSS for styling the UI
        css = """
            /* Custom styling for Lyra UI */
            .top-header {
                background-color: #283d5f;
                color: white;
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 12px;
            }
            .model-info {
                font-size: 0.9em;
                margin-bottom: 8px;
            }
        """
        
        # Create the main interface with tabs
        with gr.Blocks(css=css) as interface:
            # Header
            with gr.Row(elem_classes="top-header"):
                gr.Markdown("# Lyra AI Assistant")
            
            # Main tabs
            with gr.Tabs() as tabs:
                # Chat tab
                with gr.TabItem("Chat", id="chat_tab") as chat_tab:
                    self._build_chat_tab()
                
                # Models tab
                with gr.TabItem("Models"):
                    self._build_models_tab()
                
                # Personality tab
                with gr.TabItem("Personality"):
                    self._build_personality_tab()
                
                # Tools tab
                with gr.TabItem("Tools"):
                    self._build_tools_tab()
                
                # Settings tab
                with gr.TabItem("Settings"):
                    self._build_settings_tab()
            
            # Footer
            with gr.Row():
                gr.Markdown("Lyra AI Assistant")
        
        return interface
    
    def _build_chat_tab(self):
        """Build the chat interface tab"""
        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    [],
                    elem_id="chatbot",
                    height=600
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        show_label=False,
                        placeholder="Type your message here...",
                        elem_id="chat-input"
                    )
                    send_btn = gr.Button("Send", variant="primary")
                    
                    # Connect the send button to the handler
                    send_btn.click(
                        self._handle_send_message,
                        inputs=[msg, chatbot],
                        outputs=[chatbot]
                    ).then(lambda: "", None, [msg])
                    
                    # Also allow pressing Enter to send message
                    msg.submit(
                        self._handle_send_message,
                        inputs=[msg, chatbot],
                        outputs=[chatbot]
                    ).then(lambda: "", None, [msg])
                
                with gr.Row():
                    # Make sure we're using a valid value for memory_dropdown
                    memory_value = self.current_memory if self.current_memory in self.available_memories else self.available_memories[0]
                    memory_dropdown = gr.Dropdown(
                        self.available_memories,
                        value=memory_value,
                        label="Memory",
                        interactive=True,
                        info="Select chat memory or create a new one."
                    )
                    
                    # Add refresh button for memories
                    refresh_btn = gr.Button("🔄 Refresh", size="sm")
                    
                    # Add event handlers for these buttons
                    new_chat_btn = gr.Button("New Chat")
                    clear_history_btn = gr.Button("Clear History")
                    
                    # Connect the buttons to their handler functions
                    refresh_btn.click(
                        self._refresh_memories,
                        outputs=[memory_dropdown]
                    )
                    
                    new_chat_btn.click(
                        self._handle_new_chat, 
                        outputs=[chatbot, memory_dropdown]
                    )
                    
                    clear_history_btn.click(
                        self._handle_clear_history, 
                        outputs=[chatbot]
                    )
                    
                    # Memory selection changes active memory
                    memory_dropdown.change(
                        self._handle_memory_change,
                        inputs=[memory_dropdown],
                        outputs=[chatbot]
                    )
    
    def _build_models_tab(self):
        """Build the models management tab"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Available Models")
                
                model_dropdown = gr.Dropdown(
                    self.available_models,
                    value=self.current_model,
                    interactive=True,
                    info="Choose the AI model to load"
                )
                
                refresh_models_btn = gr.Button("🔄 Refresh Models")
                
                load_btn = gr.Button("Load Model", variant="primary")
                model_status = gr.Markdown("No model loaded" if not self.current_model else f"Active model: {self.current_model}")
                
                # Connect the buttons to their handler functions
                refresh_models_btn.click(
                    self._refresh_models,
                    outputs=[model_dropdown]
                )
                
                load_btn.click(
                    self._handle_load_model,
                    inputs=[model_dropdown],
                    outputs=[model_status]
                )
                
                # Add advanced model settings panel
                with gr.Accordion("Advanced Model Settings", open=False):
                    temperature = gr.Slider(0.1, 2.0, value=0.7, label="Temperature", info="Higher values make output more random, lower values more deterministic")
                    max_tokens = gr.Slider(64, 4096, value=1024, step=64, label="Max Tokens", info="Maximum length of the generated text")
                    top_p = gr.Slider(0.0, 1.0, value=0.9, label="Top P", info="Nucleus sampling parameter")
                    
                    save_model_settings_btn = gr.Button("Save Model Settings")
                    save_model_settings_btn.click(
                        self._handle_save_model_settings,
                        inputs=[model_dropdown, temperature, max_tokens, top_p],
                        outputs=[model_status]
                    )
    
    def _build_personality_tab(self):
        """Build the personality configuration tab"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Personality Settings")
                
                with gr.Group():
                    # Load current personality settings from the bot
                    current_personality = self.bot.personality.get_settings() if hasattr(self.bot, 'personality') else {}
                    
                    # Core personality traits
                    creativity = gr.Slider(0.0, 1.0, 
                        value=current_personality.get("creativity", 0.7), 
                        label="Creativity", 
                        info="Higher values make responses more creative and varied",
                        interactive=True
                    )
                    formality = gr.Slider(0.0, 1.0, 
                        value=current_personality.get("formality", 0.5), 
                        label="Formality", 
                        info="Higher values make responses more formal and professional",
                        interactive=True
                    )
                    verbosity = gr.Slider(0.0, 1.0, 
                        value=current_personality.get("verbosity", 0.6), 
                        label="Verbosity", 
                        info="Higher values make responses longer and more detailed",
                        interactive=True
                    )
                    empathy = gr.Slider(0.0, 1.0, 
                        value=current_personality.get("empathy", 0.8), 
                        label="Empathy", 
                        info="Higher values make responses more empathetic and understanding",
                        interactive=True
                    )
                    humor = gr.Slider(0.0, 1.0, 
                        value=current_personality.get("humor", 0.6), 
                        label="Humor", 
                        info="Higher values increase wit and humor in responses",
                        interactive=True
                    )
                
                # Personality presets
                with gr.Row():
                    gr.Markdown("### Personality Presets")
                    preset_dropdown = gr.Dropdown(
                        ["Default"] + self.bot.personality.get_preset_names() if hasattr(self.bot, 'personality') else ["Default"],
                        value="Default",
                        label="Select Preset",
                        interactive=True
                    )
                    
                    preset_description = gr.Textbox(
                        label="Preset Description",
                        placeholder="Enter a description for your preset...",
                        lines=2,
                        interactive=True
                    )
                
                with gr.Row():
                    load_preset_btn = gr.Button("Load Preset")
                    save_preset_btn = gr.Button("Save Current as Preset")
                    preset_name = gr.Textbox(
                        label="Preset Name", 
                        placeholder="Name for your new preset",
                        interactive=True
                    )
                
                # Connect buttons to handlers
                save_personality_btn = gr.Button("Save Personality Settings", variant="primary")
                save_personality_btn.click(
                    self._handle_save_personality,
                    inputs=[creativity, formality, verbosity, empathy, humor],
                    outputs=[gr.Markdown(value="")]
                ).then(
                    lambda: "Settings saved successfully!",
                    None,
                    [gr.Markdown(value="")]
                )
                
                load_preset_btn.click(
                    self._handle_load_preset,
                    inputs=[preset_dropdown],
                    outputs=[creativity, formality, verbosity, empathy, humor, preset_description]
                )
                
                save_preset_btn.click(
                    self._handle_save_preset,
                    inputs=[preset_name, preset_description, creativity, formality, verbosity, empathy, humor],
                    outputs=[preset_dropdown, gr.Markdown(value="")]
                ).then(
                    lambda: "Preset saved successfully!",
                    None,
                    [gr.Markdown(value="")]
                )
    
    def _build_tools_tab(self):
        """Build the tools interface tab"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Tools")
                
                # Image Generation
                with gr.Accordion("Image Generation", open=True):
                    image_prompt = gr.Textbox(
                        label="Prompt", 
                        placeholder="Describe the image you want to generate...",
                        lines=3,
                        interactive=True
                    )
                    
                    with gr.Row():
                        image_width = gr.Slider(256, 1024, value=512, step=64, label="Width", interactive=True)
                        image_height = gr.Slider(256, 1024, value=512, step=64, label="Height", interactive=True)
                    
                    generate_image_btn = gr.Button("Generate Image", variant="primary")
                    image_output = gr.Image(label="Generated Image", type="filepath")
                    
                    # Connect button to handler
                    generate_image_btn.click(
                        self._handle_generate_image,
                        inputs=[image_prompt, image_width, image_height],
                        outputs=[image_output]
                    )
                
                # Text to Speech
                with gr.Accordion("Text to Speech", open=False):
                    tts_text = gr.Textbox(
                        label="Text", 
                        placeholder="Enter text to convert to speech...",
                        lines=3,
                        interactive=True
                    )
                    
                    voice_options = ["Default", "Female", "Male", "Neural"]
                    tts_voice = gr.Dropdown(
                        voice_options, 
                        value="Default", 
                        label="Voice",
                        interactive=True
                    )
                    
                    tts_btn = gr.Button("Convert to Speech")
                    audio_output = gr.Audio(label="Generated Audio", type="filepath")
                    
                    # Connect button to handler
                    tts_btn.click(
                        self._handle_text_to_speech,
                        inputs=[tts_text, tts_voice],
                        outputs=[audio_output]
                    )
                
                # Code Generation
                with gr.Accordion("Code Generation", open=False):
                    code_description = gr.Textbox(
                        label="Description", 
                        placeholder="Describe the code you want to generate...",
                        lines=3,
                        interactive=True
                    )
                    
                    language_options = ["Python", "JavaScript", "HTML", "CSS", "Java", "C++"]
                    code_language = gr.Dropdown(
                        language_options, 
                        value="Python", 
                        label="Language",
                        interactive=True
                    )
                    
                    generate_code_btn = gr.Button("Generate Code")
                    code_output = gr.Code(label="Generated Code", language="python")
                    
                    # Connect button to handler
                    generate_code_btn.click(
                        self._handle_generate_code,
                        inputs=[code_description, code_language],
                        outputs=[code_output]
                    )
    
    def _build_settings_tab(self):
        """Build the settings interface tab"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Settings")
                
                with gr.Group():
                    system_prompt = gr.Textbox(
                        label="System Prompt", 
                        lines=5,
                        value=self.bot.get_system_instructions() if hasattr(self.bot, "get_system_instructions") else "",
                        info="Instructions that guide how the AI assistant behaves",
                        interactive=True
                    )
                    
                    context_extras = gr.Textbox(
                        label="Additional Context", 
                        lines=3,
                        value=self.bot.get_context_extras() if hasattr(self.bot, "get_context_extras") else "",
                        info="Extra information to provide to the AI in each conversation",
                        interactive=True
                    )
                    
                    save_btn = gr.Button("Save Settings", variant="primary")
                    settings_status = gr.Markdown("")
                    
                    # Connect button to handler
                    save_btn.click(
                        self._handle_save_settings,
                        inputs=[system_prompt, context_extras],
                        outputs=[settings_status]
                    )
                
                # Add UI sharing toggle section
                with gr.Group():
                    gr.Markdown("## Sharing")
                    
                    sharing_info = gr.Markdown("""
                        Create a public link to share your Lyra instance with others. 
                        The public link will remain active as long as Lyra is running.
                        
                        **Note:** Anyone with the link can access your Lyra instance and use it to chat.
                    """)
                    
                    with gr.Row():
                        # Display the current share URL if it exists
                        self.share_url_text = gr.Textbox(
                            label="Public URL", 
                            value="", 
                            interactive=False,
                            visible=False
                        )
                    
                    with gr.Row():
                        self.share_toggle = gr.Checkbox(
                            label="Enable public sharing", 
                            value=False,
                            interactive=True,
                            info="Toggle to create a public link (requires Lyra to be launched with --share)"
                        )
                        copy_btn = gr.Button("Copy URL", visible=False)
                    
                    # Update sharing status
                    sharing_status = gr.Markdown("")
                    
                    # Add event handlers
                    self.share_toggle.change(
                        self._handle_share_toggle,
                        inputs=[self.share_toggle],
                        outputs=[self.share_url_text, copy_btn, sharing_status]
                    )
                    
                    # Use JavaScript for clipboard functionality in a compatible way
                    if IS_GRADIO_4_40_PLUS:
                        copy_btn.click(
                            lambda x: gr.update(), 
                            inputs=[self.share_url_text], 
                            outputs=[],
                            _js="(url) => { navigator.clipboard.writeText(url); alert('Public URL copied to clipboard!'); }"
                        )
                    else:
                        copy_js = """
                        function(url) {
                            navigator.clipboard.writeText(url);
                            alert('Public URL copied to clipboard!');
                            return [];
                        }            
                        """
                        copy_btn.click(
                            lambda x: x, 
                            inputs=[self.share_url_text], 
                            outputs=[],
                            js=copy_js
                        )
                
                # Add Help & Documentation section
                with gr.Accordion("Help & Documentation", open=False):
                    gr.Markdown("""
                    ### Lyra UI Guide
                    
                    1. **Chat**: Send messages to Lyra or press Enter
                    2. **Models**: Choose and load different AI models
                    3. **Personality**: Adjust how Lyra responds to you
                    4. **Tools**: Generate images, speech, and code
                    5. **Settings**: Configure system instructions and context
                    
                    ### Chat Commands
                    - `/help` - Show this help
                    - `/models` - List available models
                    - `/presets` - List personality presets
                    - `/clear` - Clear chat history
                    
                    For more help, visit [Lyra Documentation](https://github.com/yourusername/lyra)
                    """)
                    
                    # Help buttons
                    with gr.Row():
                        help_btns = [
                            gr.Button("Chat Help"),
                            gr.Button("Models Help"),
                            gr.Button("Tools Help")
                        ]
                    
                    help_output = gr.Markdown("")
                    
                    # Connect help buttons to display specific help content
                    help_btns[0].click(lambda: "### Chat Help\n- Type messages and press Send\n- Create new conversations with 'New Chat'\n- Clear history with 'Clear History'\n- Switch between different conversations using the Memory dropdown", None, help_output)
                    help_btns[1].click(lambda: "### Models Help\n- Select a model from the dropdown\n- Click 'Load Model' to activate it\n- Adjust temperature and other parameters in Advanced Settings\n- Higher temperature means more creative, but potentially less accurate responses", None, help_output)
                    help_btns[2].click(lambda: "### Tools Help\n- **Image Generation**: Enter a description and generate images\n- **Text to Speech**: Convert text to spoken audio\n- **Code Generation**: Create code snippets in various languages", None, help_output)
    
    # Helper methods
    def _refresh_memories(self):
        """Refresh the available memories"""
        if hasattr(self.bot, 'memory_manager'):
            self.available_memories = self.bot.memory_manager.get_memory_names()
            if "default" not in self.available_memories:
                self.available_memories.append("default")
            return gr.update(choices=self.available_memories, value=self.current_memory)
        return gr.update()
    
    def _refresh_models(self):
        """Refresh the available models"""
        if hasattr(self.bot, 'model_manager'):
            self.available_models = [model.name for model in self.bot.model_manager.models]
            return gr.update(choices=self.available_models, value=self.current_model)
        return gr.update()
    
    def _handle_memory_change(self, memory_name):
        """Handle changing the active memory"""
        if hasattr(self.bot, 'memory_manager') and memory_name:
            self.bot.memory_manager.set_active_memory(memory_name)
            self.current_memory = memory_name
            
            # Load chat history from the selected memory
            if memory_name in self.bot.memory_manager.memories:
                memory_messages = self.bot.memory_manager.memories[memory_name]
                chat_history = []
                
                for msg in memory_messages:
                    if msg["role"] == "user":
                        # Start a new message pair
                        chat_history.append([msg["content"], ""])
                    elif msg["role"] == "assistant" and chat_history:
                        # Complete the last message pair
                        chat_history[-1][1] = msg["content"]
                
                return chat_history
        
        return []  # Return empty chat history
    
    def _handle_new_chat(self):
        """Handle new chat button click"""
        # Create a new memory in the memory manager
        if hasattr(self.bot, 'memory_manager'):
            timestamp = int(time.time())
            new_memory_name = f"chat_{timestamp}"
            self.bot.memory_manager.create_memory(new_memory_name)
            self.bot.memory_manager.set_active_memory(new_memory_name)
            self.current_memory = new_memory_name
            
            # Refresh available memories and select the new one
            self.available_memories = self.bot.memory_manager.get_memory_names()
            if "default" not in self.available_memories:
                self.available_memories.append("default")
                
            return [], gr.update(choices=self.available_memories, value=new_memory_name)
        
        return [], gr.update()  # Return empty chat history and no update
    
    def _handle_clear_history(self):
        """Handle clear history button click"""
        # Clear the current memory
        if hasattr(self.bot, 'memory_manager') and self.bot.memory_manager.active_memory:
            self.bot.memory_manager.memories[self.bot.memory_manager.active_memory] = []
            self.bot.memory_manager._save_memory(self.bot.memory_manager.active_memory)
        return []  # Return empty chat history
    
    def _handle_send_message(self, message, history):
        """Handle send message button click"""
        if not message.strip():
            return history  # Don't process empty message
        
        # Add user message to history
        history.append([message, None])
        
        # Process with the bot and get a response
        try:
            if hasattr(self.bot, 'chat'):
                response = self.bot.chat(message, memory_name=self.current_memory)
                history[-1][1] = response
            else:
                history[-1][1] = "Bot not initialized properly."
        except Exception as e:
            history[-1][1] = f"Error: {str(e)}"
            
        return history
    
    def _handle_load_model(self, model_name):
        """Handle loading a model"""
        try:
            if not model_name:
                return "No model selected"
                
            if hasattr(self.bot, 'load_model'):
                success = self.bot.load_model(model_name)
                if success:
                    self.current_model = model_name
                    return f"Model '{model_name}' loaded successfully!"
                else:
                    return f"Failed to load model '{model_name}'"
            else:
                return "Bot doesn't have load_model method"
        except Exception as e:
            return f"Error loading model: {str(e)}"
    
    def _handle_save_model_settings(self, model_name, temperature, max_tokens, top_p):
        """Handle saving model settings"""
        try:
            if not model_name:
                return "No model selected"
            
            # Find the model by name
            if hasattr(self.bot, 'model_manager'):
                for model in self.bot.model_manager.models:
                    if model.name == model_name:
                        # Update model parameters
                        model.params.update({
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                            "top_p": top_p
                        })
                        self.bot.model_manager.save_models()
                        return f"Settings for model '{model_name}' saved successfully!"
                
                return "Model manager not available or model not found"
        except Exception as e:
            return f"Error saving model settings: {str(e)}"
    
    def _handle_save_personality(self, creativity, formality, verbosity, empathy, humor):
        """Handle saving personality settings"""
        try:
            if hasattr(self.bot, 'personality'):
                self.bot.personality.update_settings(
                    creativity=creativity,
                    formality=formality,
                    verbosity=verbosity,
                    empathy=empathy,
                    humor=humor
                )
                return "Personality settings saved successfully!"
            
            return "Personality component not available"
        except Exception as e:
            return f"Error saving personality settings: {str(e)}"
    
    def _handle_load_preset(self, preset_name):
        """Handle loading a personality preset"""
        try:
            if not preset_name or preset_name == "Default":
                # Load default settings
                if hasattr(self.bot, 'personality'):
                    settings = self.bot.personality.get_settings()
                    description = "Default personality settings"
                    return [
                        settings.get("creativity", 0.7),
                        settings.get("formality", 0.5),
                        settings.get("verbosity", 0.6),
                        settings.get("empathy", 0.8),
                        settings.get("humor", 0.6),
                        description
                    ]
                
                return [0.7, 0.5, 0.6, 0.8, 0.6, "Default settings"]
            
            # Load the selected preset
            if hasattr(self.bot, 'personality'):
                success = self.bot.personality.load_preset(preset_name)
                if success:
                    settings = self.bot.personality.get_settings()
                    description = self.bot.personality.get_preset_description(preset_name)
                    return [
                        settings.get("creativity", 0.7),
                        settings.get("formality", 0.5),
                        settings.get("verbosity", 0.6),
                        settings.get("empathy", 0.8),
                        settings.get("humor", 0.6),
                        description
                    ]
            
            return [0.7, 0.5, 0.6, 0.8, 0.6, "Failed to load preset"]
        except Exception as e:
            return [0.7, 0.5, 0.6, 0.8, 0.6, f"Error: {str(e)}"]
    
    def _handle_save_preset(self, preset_name, description, creativity, formality, verbosity, empathy, humor):
        """Handle saving a personality preset"""
        try:
            if not preset_name:
                return gr.update(), "No preset name provided"
                
            if hasattr(self.bot, 'personality'):
                # First update current settings
                self.bot.personality.update_settings(
                    creativity=creativity,
                    formality=formality,
                    verbosity=verbosity,
                    empathy=empathy,
                    humor=humor
                )
                
                # Then save as preset
                success = self.bot.personality.save_preset(preset_name, description)
                if success:
                    # Get updated preset list
                    presets = ["Default"] + self.bot.personality.get_preset_names()
                    return gr.update(choices=presets, value=preset_name), f"Preset '{preset_name}' saved successfully!"
                else:
                    return gr.update(), f"Failed to save preset '{preset_name}'"
            
            return gr.update(), "Personality component not available"
        except Exception as e:
            return gr.update(), f"Error: {str(e)}"
    
    def _handle_generate_image(self, prompt, width, height):
        """Handle image generation"""
        try:
            if not prompt:
                return None
                
            if hasattr(self.bot, 'generate_image'):
                image_path = self.bot.generate_image(prompt, width=width, height=height)
                if image_path:
                    return image_path
            
            return None
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None
    
    def _handle_text_to_speech(self, text, voice):
        """Handle text-to-speech conversion"""
        try:
            if not text:
                return None
                
            if hasattr(self.bot, 'text_to_speech'):
                audio_path = self.bot.text_to_speech(text, voice=voice.lower())
                if audio_path:
                    return audio_path
            
            return None
        except Exception as e:
            print(f"Error converting text to speech: {str(e)}")
            return None
    
    def _handle_generate_code(self, description, language):
        """Handle code generation"""
        try:
            if not description:
                return "# Please provide a description"
                
            if hasattr(self.bot, 'generate_code'):
                code = self.bot.generate_code(description, language=language.lower())
                if code:
                    return code
            
            return "# Code generation not available"
        except Exception as e:
            return f"# Error: {str(e)}"
    
    def _handle_save_settings(self, system_prompt, context_extras):
        """Handle saving settings"""
        try:
            success = True
            messages = []
            
            # Update system instructions
            if hasattr(self.bot, 'set_system_instructions'):
                if self.bot.set_system_instructions(system_prompt):
                    messages.append("System instructions saved")
                else:
                    success = False
                    messages.append("Failed to save system instructions")
            
            # Update context extras
            if hasattr(self.bot, 'set_context_extras'):
                if self.bot.set_context_extras(context_extras):
                    messages.append("Additional context saved")
                else:
                    success = False
                    messages.append("Failed to save additional context")
            
            if success:
                return "Settings saved successfully!"
            else:
                return "Warning: " + ", ".join(messages)
        except Exception as e:
            return f"Error saving settings: {str(e)}"
    
    def _handle_share_toggle(self, enabled):
        """Handle toggling public sharing on/off"""
        if enabled:
            # Create a share URL if it doesn't exist
            if not hasattr(self, '_share_url') or not self._share_url:
                try:
                    # We need to update the launch parameters to enable sharing
                    # Note: Gradio doesn't officially support toggling sharing after launch
                    # This is a workaround that tries to create a new share tunnel
                    from gradio.networking import setup_tunnel
                    
                    # Check if we have interface with server properties
                    if hasattr(self, '_interface') and hasattr(self._interface, 'server_name') and hasattr(self._interface, 'server_port'):
                        self._share_url = setup_tunnel(self._interface.server_name, self._interface.server_port)
                        print(f"Created public share URL: {self._share_url}")
                        
                        # Return the URL and make the copy button visible
                        return gr.update(value=self._share_url, visible=True), gr.update(visible=True), "Share link created successfully!"
                    else:
                        return gr.update(value="Cannot create share link - server info not available", visible=True), gr.update(visible=False), "Error: Server information not available"
                except Exception as e:
                    print(f"Error creating share URL: {e}")
                    self._share_url = "Error creating share link. Try restarting with --share flag."
                    return gr.update(value=self._share_url, visible=True), gr.update(visible=False), f"Error: {str(e)}"
            else:
                # Use existing share URL
                return gr.update(value=self._share_url, visible=True), gr.update(visible=True), "Using existing share link"
        else:
            # Hide the URL when sharing is disabled
            # Note: We can't actually close an existing tunnel easily once created
            return gr.update(visible=False), gr.update(visible=False), "Sharing disabled (link may still be active)"
    
    def launch(self, **kwargs):
        """Launch the UI"""
        # Add loading hook to show continuing initialization
        def continue_initialization(progress=gr.Progress()):
            # Start from where the airlock left off
            initial_progress = self.init_status
            progress(initial_progress, desc="Continuing initialization...")
            
            # Track modules that need initializing
            modules_to_check = {
                "core_llm": "Core LLM",
                "extended_thinking": "Extended Thinking",
                "emotional_core": "Emotional Core",
                "metacognition": "Metacognition",
                "deep_memory": "Deep Memory"
            }
            
            # Track completed modules
            completed_modules = set()
            current_progress = initial_progress
            
            # Continue until all modules are initialized or timeout
            max_iterations = 30
            for i in range(max_iterations):
                # Check each module
                for module_key, module_name in list(modules_to_check.items()):
                    # Skip already completed modules
                    if module_key in completed_modules:
                        continue
                    
                    # Check if module is initialized
                    is_ready = False
                    
                    # Core LLM check
                    if module_key == "core_llm" and hasattr(self.bot, "fallback_llm"):
                        is_ready = getattr(self.bot.fallback_llm, "initialized", False)
                    
                    # Extended thinking check
                    elif module_key == "extended_thinking":
                        try:
                            from modules.extended_thinking import get_instance
                            ext_thinking = get_instance()
                            is_ready = getattr(ext_thinking, "enabled", False)
                        except ImportError:
                            is_ready = True  # Skip if not available
                    
                    # Other module checks would go here
                    # ...
                    
                    if is_ready:
                        completed_modules.add(module_key)
                        logger.info(f"Module initialized: {module_name}")
                
                # Update progress
                modules_count = len(modules_to_check)
                if modules_count > 0:
                    completed_count = len(completed_modules)
                    # Calculate progress: initial progress + remaining progress portion
                    current_progress = initial_progress + ((1.0 - initial_progress) * (completed_count / modules_count))
                    progress(current_progress, desc=f"Initializing: {completed_count}/{modules_count} modules ready")
                
                # Check if all modules are initialized
                if len(completed_modules) == len(modules_to_check):
                    break
                    
                # Wait before checking again
                time.sleep(1)
            
            # Final progress update
            progress(1.0, desc="Initialization complete!")
            return "System initialization complete. Lyra is ready!"
            
        self.ui.load(
            continue_initialization,
            outputs=[status_bar]
        )
        
        # Launch the UI
        self.ui.launch(**kwargs)

def main():
    """Main entry point"""
    args = parse_args()
    
    # Set logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create the UI
    ui = LyraUI(args)
    
    # Launch the interface
    try:
        logger.info(f"Starting Lyra interface on port {args.port}")
        ui.launch(
            server_name="0.0.0.0",  # Bind to all addresses
            server_port=args.port,
            share=args.share,
            prevent_thread_lock=True
        )
        logger.info(f"Lyra interface running at http://127.0.0.1:{args.port}")
        
        # Keep the main thread running
        while True:
            time.sleep(1)
    except OSError as e:
        if "Address already in use" in str(e):
            # Port conflict - try to use a different port
            logger.error(f"Port {args.port} is already in use. Trying alternate port.")
            try:
                alternate_port = args.port + 1
                logger.info(f"Trying alternate port {alternate_port}")
                ui.launch(
                    server_name="0.0.0.0",
                    server_port=alternate_port,
                    share=args.share,
                    prevent_thread_lock=True
                )
                logger.info(f"Lyra interface running at http://127.0.0.1:{alternate_port}")
                
                # Keep the main thread running
                while True:
                    time.sleep(1)
            except Exception as alt_e:
                logger.error(f"Error with alternate port: {alt_e}")
                sys.exit(1)
        else:
            logger.error(f"Error starting interface: {e}")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    ui = LyraUI()
    # When run directly, don't create a public share link by default
    ui.launch(share=False)
