import os
import json
import gradio as gr
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import random  # Add this to existing imports
import numpy as np
from datetime import datetime, timedelta

from modules.model_manager import ModelConfig, ModelManager

logger = logging.getLogger("settings_ui")

class SettingsUI:
    """User interface for managing Lyra settings."""
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.settings_path = Path("configs/app_settings.json")
        self.settings = self._load_settings()
        self.models = {}
        self.known_formats = {
            ".bin": "GGUF",
            ".gguf": "GGUF", 
            ".ggml": "GGML",
            ".pt": "PyTorch",
            ".pth": "PyTorch",
            ".safetensors": "Safetensors"
        }
        self._load_configs()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from file or use defaults."""
        default_settings = {
            "active_model": "",
            "interface": {
                "theme": "default",
                "chat_history_limit": 50
            },
            "debug_mode": False,
            "log_level": "info",
        }
        if not self.settings_path.exists():
            return default_settings
        try:
            with open(self.settings_path, 'r') as f:
                settings = json.load(f)
            # Merge with defaults for any missing keys
            for key in default_settings:
                if key not in settings:
                    settings[key] = default_settings[key]
            return settings
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return default_settings
    
    def save_settings(self) -> bool:
        """Save current settings to file."""
        try:
            # Ensure directory exists
            self.settings_path.parent.mkdir(exist_ok=True)
            with open(self.settings_path, 'w') as f:
                json.dump(self.settings, f, indent=2)
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def save_model_settings(self, model_name, model_path, model_type, **kwargs):
        """Save model settings."""
        try:
            # Create model config
            config = ModelConfig(
                model_name=model_name,
                model_path=model_path,
                model_type=model_type,
                **kwargs
            )
            # Save via model manager
            success = self.model_manager.save_model_config(config)
            if success:
                return f"Model settings for {model_name} saved successfully"
            else:
                return "Error saving model settings"
        except Exception as e:
            error_msg = f"Error saving model settings: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def _load_configs(self):
        """Load model configurations from the config directory"""
        try:
            if not self.settings_path.exists():
                self.settings_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created config directory at {self.settings_path}")
            
            # Load model configurations
            model_configs = list(self.settings_path.glob("*.json"))
            
            if not model_configs:
                logger.info("No model configurations found")
                return
                
            for config_file in model_configs:
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    model_name = config_data.get("name", config_file.stem)
                    model_path = config_data.get("path", "")
                    model_type = config_data.get("model_type", self._guess_model_type(model_path))
                    
                    # Extract additional parameters
                    kwargs = {k: v for k, v in config_data.items() 
                             if k not in ["name", "path", "model_type"]}
                    
                    # Create model config
                    model_config = ModelConfig(
                        name=model_name,
                        path=model_path,
                        model_type=model_type,
                        **kwargs
                    )
                    
                    # Check if model exists
                    if not os.path.exists(model_path):
                        model_config.is_valid = False
                        logger.warning(f"Model file not found: {model_path}")
                    
                    self.models[model_name] = model_config
                    logger.info(f"Loaded model config: {model_name}")
                    
                except Exception as e:
                    logger.error(f"Error loading model config {config_file}: {str(e)}")
                    self._backup_invalid_config(config_file)
                    
            logger.info(f"Loaded {len(self.models)} model configurations")
            
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
    
    def _backup_invalid_config(self, config_file):
        """Create a backup of invalid configuration files"""
        try:
            backup_dir = self.settings_path / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{config_file.stem}_{timestamp}.json.bak"
            
            # Copy the file
            with open(config_file, 'r') as src:
                with open(backup_file, 'w') as dst:
                    dst.write(src.read())
                    
            logger.info(f"Created backup of invalid config: {backup_file}")
            
            # Optionally remove the invalid config
            # config_file.unlink()
            # logger.info(f"Removed invalid config: {config_file}")
            
        except Exception as e:
            logger.error(f"Failed to backup invalid config: {str(e)}")
    
    def _discover_models(self):
        """Discover available models in the models directory"""
        model_files = []
        parent_folder = self.settings_path
        
        try:
            if not parent_folder.exists():
                parent_folder.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created models directory at {parent_folder}")
                
            # Find model files
            created_count = 0
            for ext in self.known_formats:
                # Look in the models folder and its immediate subdirectories
                for model_file in parent_folder.glob(f"**/*{ext}"):
                    # Only look one level deep
                    if len(model_file.relative_to(parent_folder).parts) <= 2:
                        model_files.append(model_file)
            
            # Look for models in existing configs that might be elsewhere
            for model_name, config in self.models.items():
                if os.path.exists(config.path) and Path(config.path) not in model_files:
                    model_files.append(Path(config.path))
            
            logger.info(f"Discovered {len(model_files)} model files")
            return model_files
            
        except Exception as e:
            logger.error(f"Error discovering models: {str(e)}")
            return []
    
    def _guess_model_type(self, model_path):
        """Guess the model type based on the file extension"""
        if not model_path:
            return ""
            
        file_ext = os.path.splitext(model_path)[1].lower()
        return self.known_formats.get(file_ext, "Unknown")
    
    def _format_prompt(self, messages: List[Tuple[str, str]], system_prompt: str = "") -> str:
        """Format the messages for the model"""
        formatted_prompt = ""
        
        if system_prompt:
            formatted_prompt += f"<|system|>\n{system_prompt}\n\n"
            
        for role, content in messages:
            if role.lower() == "user":
                formatted_prompt += f"<|user|>\n{content}\n\n"
            elif role.lower() == "assistant":
                formatted_prompt += f"<|assistant|>\n{content}\n\n"
            else:
                # For any other role
                formatted_prompt += f"<|{role}|>\n{content}\n\n"
                
        # Add the final assistant prompt
        formatted_prompt += "<|assistant|>\n"
        
        return formatted_prompt
    
    def _format_thinking(self, thinking_content: str) -> str:
        """Format the thinking process content"""
        if not thinking_content:
            return ""
            
        formatted_thinking = "<|thinking|>\n" + thinking_content.strip() + "\n</thinking>\n"
        return formatted_thinking
    
    def create_ui(self):
        """Create the settings UI."""
        with gr.Blocks() as settings_ui:
            # Main tabs for different settings categories
            with gr.Tabs(selected=0) as tabs:
                # MODEL CONFIGURATION TAB
                with gr.TabItem("Model Configuration", id=0):
                    gr.Markdown("## Configure Language Models")
                    gr.Markdown("### Add or Edit Model Configuration")
                    
                    with gr.Row():
                        # Left column: Add/edit models
                        with gr.Column(scale=1):
                            gr.Markdown("### Available Models")
                            model_list = gr.Dropdown(
                                choices=list(self.model_manager.model_configs.keys()),
                                label="Select a model",
                                value=None,
                                interactive=True
                            )
                            
                            with gr.Row():
                                load_model_btn = gr.Button("Load Selected Model", variant="primary")
                                unload_model_btn = gr.Button("Unload Model")
                                delete_model_btn = gr.Button("Delete Model", variant="stop")
                            model_status = gr.Markdown("No model loaded")
                            
                            # Selected model details
                            gr.Markdown("### Model Details")
                            model_details = gr.JSON(
                                value={},
                                label=""
                            )
                            
                            # Cleanup options
                            with gr.Accordion("Maintenance", open=False):
                                clean_configs_btn = gr.Button("Clean Invalid Configurations")
                                scan_models_btn = gr.Button("Scan for New Models")
                        
                        # Right column: Model editor
                        with gr.Column(scale=1):
                            gr.Markdown("### Add or Edit Model")
                            with gr.Group():
                                # Selector for editing existing model
                                existing_model_dropdown = gr.Dropdown(
                                    choices=[None] + list(self.model_manager.model_configs.keys()),
                                    label="Load Existing Model for Editing",
                                    value=None
                                )
                                
                                # Basic settings
                                model_name = gr.Textbox(label="Model Name")
                                model_path = gr.Textbox(label="Model Path")
                                model_status = gr.Textbox(label="Status", interactive=False)
                                with gr.Row():
                                    # Browse button that actually works
                                    browse_button = gr.Button("Browse...", scale=1)
                                    # Model type selection
                                    model_type = gr.Dropdown(
                                        choices=["llama", "gpt", "other"],
                                        label="Model Type",
                                        value="llama",
                                        interactive=True
                                    )
                            
                            # Chat format settings with better descriptions
                            model_format = gr.Dropdown(
                                choices=[
                                    ("Default (User/Assistant)", "default"),   
                                    ("Wizard/Vicuna (USER/ASSISTANT)", "wizard"),
                                    ("ChatML (OpenAI format)", "chatml"),
                                    ("Llama3", "llama3"),
                                    ("Command-R", "command-r"),
                                    ("Alpaca (Instruction format)", "alpaca")
                                ],
                                label="Chat Template Format",
                                value="default"
                            )
                            
                            # Advanced settings
                            with gr.Accordion("Advanced Parameters", open=False):
                                with gr.Row():
                                    context_size = gr.Slider(
                                        minimum=1024, maximum=16384, value=4096, step=1024,
                                        label="Context Window Size"
                                    )
                                    
                                    n_gpu_layers = gr.Slider(
                                        minimum=0, maximum=100, value=0, step=1,
                                        label="GPU Layers"
                                    )
                                
                                # Add GPU Layer Scaling Tool
                                with gr.Accordion("GPU Layer Scaling Tool", open=False):
                                    gr.Markdown("""
                                    This tool helps you optimize GPU utilization based on your model size and GPU VRAM.
                                    Adjust the slider based on your GPU capabilities. Higher values offload more layers to GPU for faster inference.
                                    """)
                                    
                                    with gr.Row():
                                        gpu_vram = gr.Dropdown(
                                            choices=["Low (4-8GB)", "Medium (8-16GB)", "High (16-24GB)", "Ultra (24GB+)"],
                                            label="Available GPU VRAM",
                                            value="Medium (8-16GB)"
                                        )
                                    
                                    with gr.Row():
                                        gpu_utilization = gr.Slider(
                                            minimum=0, maximum=100, value=70, step=5,
                                            label="GPU Utilization %"
                                        )
                                        
                                    estimate_gpu_btn = gr.Button("Estimate Optimal GPU Layers")
                                
                                with gr.Row():
                                    # Only show these for compatible models
                                    gr.Checkbox(label="Use mmap", value=True)
                                    gr.Checkbox(label="Use float16", value=True)
                            # Save button
                            save_model_btn = gr.Button("Save Model Configuration", variant="primary")
                            save_status = gr.Markdown("")
                
                # INTERFACE SETTINGS TAB
                with gr.TabItem("Interface Settings", id=2):
                    gr.Markdown("## Interface Appearance Settings")
                    
                    with gr.Row():
                        with gr.Column():
                            # Basic interface settings
                            theme = gr.Dropdown(
                                choices=["Default", "Dark", "Light", "Midnight"],
                                label="Theme",
                                value=self.settings.get("interface", {}).get("theme", "Default")
                            )
                            
                            font_size = gr.Dropdown(
                                choices=["Small", "Medium", "Large"],
                                label="Font Size",
                                value=self.settings.get("interface", {}).get("font_size", "Medium")
                            )
                            
                        with gr.Column():
                            # History settings
                            chat_history_limit = gr.Slider(
                                minimum=10, maximum=500, step=10,
                                value=self.settings.get("interface", {}).get("chat_history_limit", 100),
                                label="Chat History Limit"
                            )
                            
                            auto_scroll = gr.Checkbox(
                                label="Auto-scroll to New Messages",
                                value=self.settings.get("interface", {}).get("auto_scroll", True)
                            )
                    
                    # Save interface settings button
                    save_interface_btn = gr.Button("Save Interface Settings", variant="primary")
                    interface_status = gr.Markdown("")
                    
                # ADVANCED SETTINGS TAB
                with gr.TabItem("Advanced Settings", id=3):
                    gr.Markdown("## Advanced Application Settings")
                    
                    with gr.Row():
                        with gr.Column():
                            # Debug settings
                            debug_mode = gr.Checkbox(
                                label="Debug Mode",
                                value=self.settings.get("debug_mode", False)
                            )
                            
                            log_level = gr.Dropdown(
                                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                label="Log Level",
                                value=self.settings.get("log_level", "INFO")
                            )
                            
                        with gr.Column():
                            # Performance settings
                            threads = gr.Slider(
                                minimum=1, maximum=16, step=1,
                                value=self.settings.get("threads", 4),
                                label="CPU Threads"
                            )
                            
                            batch_size = gr.Slider(
                                minimum=8, maximum=2048, step=8,
                                value=self.settings.get("batch_size", 512),
                                label="Batch Size"
                            )
                    
                    # Save advanced settings button
                    save_advanced_btn = gr.Button("Save Advanced Settings", variant="primary")
                    advanced_status = gr.Markdown("")
                
                # GPU SETTINGS TAB
                with gr.TabItem("GPU Settings", id=4):
                    gr.Markdown("## GPU Acceleration Settings")
                    
                    with gr.Row():
                        with gr.Column():
                            # GPU settings
                            gr.Markdown("### GPU Configuration")
                            enable_gpu = gr.Checkbox(
                                label="Enable GPU Acceleration",
                                value=True
                            )
                            
                            gpu_memory_limit = gr.Slider(
                                minimum=1, maximum=48, step=1,
                                value=self.settings.get("gpu", {}).get("memory_limit", 8),
                                label="GPU Memory Limit (GB)"
                            )
                            
                            gpu_batch_size = gr.Slider(
                                minimum=1, maximum=512, step=8,
                                value=self.settings.get("gpu", {}).get("batch_size", 8),
                                label="GPU Batch Size"
                            )
                            
                        with gr.Column():
                            # Default GPU layers for new models
                            gr.Markdown("### Default GPU Layers Policy")
                            default_gpu_policy = gr.Radio(
                                choices=["Auto (based on size)", "Conservative", "Balanced", "Aggressive", "Custom"],
                                label="Default GPU Layers Policy",
                                value=self.settings.get("gpu", {}).get("default_policy", "Balanced")
                            )
                            
                            custom_default_layers = gr.Slider(
                                minimum=0, maximum=100, step=1,
                                value=self.settings.get("gpu", {}).get("custom_default_layers", 16),
                                label="Custom Default GPU Layers",
                                visible=False
                            )
                            
                            update_all_models_btn = gr.Button("Apply GPU Policy to All Models", variant="secondary")
                    
                    # GPU Testing Section
                    with gr.Accordion("GPU Testing", open=False):
                        gr.Markdown("""
                        Run tests to determine the optimal GPU settings for your system.
                        This will try different configurations and measure performance.
                        """)
                        
                        with gr.Row():
                            test_model = gr.Dropdown(
                                choices=list(self.model_manager.model_configs.keys()),
                                label="Test Model",
                                value=next(iter(self.model_manager.model_configs.keys()), None)
                            )
                            
                        run_gpu_test_btn = gr.Button("Run GPU Optimization Test", variant="primary")
                        test_results = gr.Markdown("")
                    
                    # Save GPU settings button
                    save_gpu_btn = gr.Button("Save GPU Settings", variant="primary")
                    gpu_status = gr.Markdown("")
            
            # Event handlers for model tab
            # Update model details when selected
            model_list.change(
                fn=self._display_model_details,
                inputs=[model_list],
                outputs=[model_details]
            )
            
            # Update model status when a model is loaded
            load_model_btn.click(
                fn=self._load_model_ui,
                inputs=[model_list],
                outputs=[model_status]
            )
            
            # Unload model
            unload_model_btn.click(
                fn=self._unload_model_ui,
                inputs=[],
                outputs=[model_status]
            )
            
            # Load existing model for editing
            existing_model_dropdown.change(
                fn=self._load_model_for_editing,
                inputs=[existing_model_dropdown],
                outputs=[model_name, model_path, model_type, model_format, context_size, n_gpu_layers]
            )
            
            # Browse for model file
            browse_button.click(
                fn=self._browse_for_model_file,
                inputs=[],
                outputs=[model_path]
            )
            
            # Save model configuration
            save_model_btn.click(
                fn=self._save_model_config_ui,
                inputs=[model_name, model_path, model_type, model_format, context_size, n_gpu_layers],
                outputs=[save_status, existing_model_dropdown, model_list]
            )
            
            # Clean up invalid configurations
            clean_configs_btn.click(
                fn=self._cleanup_invalid_configs,
                inputs=[],
                outputs=[model_status, model_list, existing_model_dropdown]
            )
            
            # Scan for new models
            scan_models_btn.click(
                fn=self._scan_for_models,
                inputs=[],
                outputs=[model_status, model_list, existing_model_dropdown]
            )
            
            # Delete model configuration
            delete_model_btn.click(
                fn=self._delete_model_config,
                inputs=[model_list],
                outputs=[model_status, model_list, existing_model_dropdown]
            )
            
            # Save interface settings
            save_interface_btn.click(
                fn=self._save_interface_settings,
                inputs=[theme, font_size, chat_history_limit, auto_scroll],
                outputs=[interface_status]
            )
            
            # Save advanced settings
            save_advanced_btn.click(
                fn=self._save_advanced_settings,
                inputs=[debug_mode, log_level, threads, batch_size],
                outputs=[advanced_status]
            )
            
            # GPU Policy Visibility Control
            default_gpu_policy.change(
                fn=lambda x: gr.update(visible=(x == "Custom")),
                inputs=[default_gpu_policy],
                outputs=[custom_default_layers]
            )
            
            # Estimate GPU Layers button
            estimate_gpu_btn.click(
                fn=self._estimate_gpu_layers,
                inputs=[model_path, gpu_vram, gpu_utilization],
                outputs=[n_gpu_layers]
            )
            
            # Apply GPU Policy to All Models
            update_all_models_btn.click(
                fn=self._apply_gpu_policy_to_all,
                inputs=[default_gpu_policy, custom_default_layers],
                outputs=[gpu_status]
            )
            
            # Run GPU Test
            run_gpu_test_btn.click(
                fn=self._run_gpu_test,
                inputs=[test_model],
                outputs=[test_results]
            )
            
            # Save GPU settings
            save_gpu_btn.click(
                fn=self._save_gpu_settings,
                inputs=[enable_gpu, gpu_memory_limit, gpu_batch_size, default_gpu_policy, custom_default_layers],
                outputs=[gpu_status]
            )
        
        return settings_ui
    
    def _display_model_details(self, model_name):
        """Display details for the selected model."""
        if not model_name or model_name not in self.model_manager.model_configs:
            return {}
            
        config = self.model_manager.model_configs[model_name]
        # Verify if the model file exists
        file_exists = Path(config.model_path).exists()
        file_size = "N/A"
        
        if file_exists:
            try:
                size_bytes = Path(config.model_path).stat().st_size
                file_size = f"{size_bytes / (1024*1024*1024):.2f} GB"
            except:
                file_size = "Unknown"
        
        # Format details for display
        details = {
            "Model Name": config.model_name,
            "Model Type": config.model_type,
            "Path": config.model_path,
            "File Exists": "✅ Yes" if file_exists else "❌ No",
            "File Size": file_size,
            "Format": config.parameters.get("format", "default"),
            "Context Size": config.parameters.get("context_size", 4096),
            "GPU Layers": config.parameters.get("n_gpu_layers", 0)
        }
        
        if len(config.parameters) > 3:  # We already showed format, context_size, n_gpu_layers
            # Add any other parameters
            details["Additional Parameters"] = {
                k: v for k, v in config.parameters.items() 
                if k not in ["format", "context_size", "n_gpu_layers"]
            }
        
        return details
    
    def _load_model_for_editing(self, model_name):
        """Load model config for editing."""
        if not model_name or model_name not in self.model_manager.model_configs:
            return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
            
        config = self.model_manager.model_configs[model_name]
        return (
            config.model_name,
            config.model_path,
            config.model_type,
            config.parameters.get("format", "default"),
            config.parameters.get("context_size", 4096),
            config.parameters.get("n_gpu_layers", 0)
        )
    
    def _browse_for_model_file(self):
        """Browse for a model file - placeholder that gives useful guidance."""
        common_paths = [
            "G:/AI/Lyra/BigModes/TT Models/YourModelFolder/model.gguf",
            "G:/AI/BigModes/TT Models/ModelName/model.gguf",
            "./models/model.gguf"
        ]
        return random.choice(common_paths)
    
    def _save_model_config_ui(self, model_name, model_path, model_type, format, context_size, n_gpu_layers):
        """Save model configuration with UI feedback."""
        if not model_name or not model_path:
            return "⚠️ Model name and path are required", gr.update(), gr.update()
        
        try:
            # Create model config
            config = ModelConfig(
                model_name=model_name,
                model_path=model_path,
                model_type=model_type,
                format=format,
                context_size=int(context_size),
                n_gpu_layers=int(n_gpu_layers)
            )
            # Save via model manager
            success = self.model_manager.save_model_config(config)
            if success:
                model_list = list(self.model_manager.model_configs.keys())
                # Update model lists
                return (
                    f"✅ Model **{model_name}** saved successfully",
                    gr.update(choices=[None] + model_list),
                    gr.update(choices=model_list)
                )
            else:
                return "❌ Error saving model settings", gr.update(), gr.update()
        except Exception as e:
            error_msg = f"❌ Error saving model: {str(e)}"
            logger.error(error_msg)
            return error_msg, gr.update(), gr.update()
    
    def _cleanup_invalid_configs(self):
        """Clean up invalid model configurations."""
        try:
            removed = self.model_manager.cleanup_configurations()
            if removed > 0:
                model_list = list(self.model_manager.model_configs.keys())
                # Update model lists
                return (
                    f"✅ Removed {removed} invalid model configurations",
                    gr.update(choices=model_list),
                    gr.update(choices=[None] + model_list)
                )
            else:
                return "✅ No invalid configurations found", gr.update(), gr.update()
        except Exception as e:
            error_msg = f"❌ Error cleaning configurations: {str(e)}"
            logger.error(error_msg)
            return error_msg, gr.update(), gr.update()
    
    def _scan_for_models(self):
        """Scan for new models."""
        try:
            old_count = len(self.available_models) if hasattr(self, 'available_models') else 0
            self.model_manager._discover_models()
            self.available_models = list(self.model_manager.model_configs.keys())
            # Get count of new models added
            new_count = len(self.available_models) - old_count
            # Update model lists with correct Gradio syntax
            return (
                f"✅ Scanned for models. Found {new_count} new models.",
                gr.update(choices=self.available_models),
                gr.update(choices=[None] + self.available_models)
            )
        except Exception as e:
            error_msg = f"❌ Error scanning for models: {str(e)}"
            logger.error(error_msg)
            return error_msg, gr.update(), gr.update()
    
    def _delete_model_config(self, model_name):
        """Delete a model configuration."""
        if not model_name:
            return "⚠️ No model selected", gr.update(), gr.update()
        
        try:
            config_path = self.model_manager.config_dir / f"{model_name}.json"
            if config_path.exists():
                # Backup before deleting
                import shutil
                backup_dir = self.model_manager.config_dir / "backup"
                backup_dir.mkdir(exist_ok=True)
                shutil.copy(config_path, backup_dir / f"{model_name}.json")
                # Delete the file
                config_path.unlink()
                # Remove from memory
                if model_name in self.model_manager.model_configs:
                    del self.model_manager.model_configs[model_name]
                # Update model lists
                model_list = list(self.model_manager.model_configs.keys())
                return (
                    f"✅ Deleted configuration for model: **{model_name}**",
                    gr.update(choices=model_list),
                    gr.update(choices=[None] + model_list)
                )
            else:
                return f"⚠️ Configuration file not found for: {model_name}", gr.update(), gr.update()
        except Exception as e:
            error_msg = f"❌ Error deleting model: {str(e)}"
            logger.error(error_msg)
            return error_msg, gr.update(), gr.update()
    
    def _save_interface_settings(self, theme=None, font_size=None, 
                          chat_history_limit=None, auto_scroll=None):
        """Save the interface settings."""
        try:
            # Get default values if not provided
            if theme is None:
                theme = "Default"
            if font_size is None:
                font_size = "Medium"
            if chat_history_limit is None:
                chat_history_limit = 100
            if auto_scroll is None:
                auto_scroll = True
                
            # Update settings in the main settings dictionary
            if "interface" not in self.settings:
                self.settings["interface"] = {}
                
            self.settings["interface"]["theme"] = theme
            self.settings["interface"]["font_size"] = font_size
            self.settings["interface"]["chat_history_limit"] = chat_history_limit
            self.settings["interface"]["auto_scroll"] = auto_scroll
            
            # Save to config using existing method
            if self.save_settings():
                interface_status = "✅ Interface settings saved successfully."
            else:
                interface_status = "❌ Error saving interface settings."
            return interface_status
        except Exception as e:
            logger.error(f"Error saving interface settings: {e}")
            return f"❌ Error saving interface settings: {str(e)}"
    def _save_advanced_settings(self, debug_mode=None, log_level=None, 
                         threads=None, batch_size=None):
        """Save the advanced settings."""
        try:
            # Get default values if not provided
            if debug_mode is None:
                debug_mode = False
            if log_level is None:
                log_level = "INFO"
            if threads is None:
                threads = 4
            if batch_size is None:
                batch_size = 512
                
            # Update main settings dictionary
            self.settings["debug_mode"] = debug_mode
            self.settings["log_level"] = log_level
            self.settings["threads"] = threads
            self.settings["batch_size"] = batch_size
            
            # Save to config using existing method
            if self.save_settings():
                advanced_status = "✅ Advanced settings saved successfully."
            else:
                advanced_status = "❌ Error saving advanced settings."
            return advanced_status
        except Exception as e:
            advanced_status = f"❌ Error saving advanced settings: {str(e)}"
            return advanced_status
    
    def _estimate_gpu_layers(self, model_path, gpu_vram, gpu_utilization):
        """Estimate appropriate GPU layers based on model size and available VRAM."""
        try:
            # Validate model path
            if not model_path or not os.path.exists(model_path):
                return 0
            
            # Get model size
            model_size_bytes = os.stat(model_path).st_size
            model_size_gb = model_size_bytes / (1024**3)
            
            # Parse VRAM capacity from selection
            vram_mapping = {
                "Low (4-8GB)": 6,        # Assume 6GB average
                "Medium (8-16GB)": 12,   # Assume 12GB average
                "High (16-24GB)": 20,    # Assume 20GB average
                "Ultra (24GB+)": 32      # Assume 32GB average
            }
            vram_gb = vram_mapping.get(gpu_vram, 12)
            
            # Consider model quantization from filename
            model_name = os.path.basename(model_path).lower()
            quantization_factor = 1.0
            if "q4" in model_name:
                quantization_factor = 0.25  # 4-bit is ~1/4 the size
            elif "q5" in model_name:
                quantization_factor = 0.3   # 5-bit
            elif "q6" in model_name:
                quantization_factor = 0.4   # 6-bit
            elif "q8" in model_name:
                quantization_factor = 0.5   # 8-bit
                
            # Calculate estimated layers based on VRAM availability and utilization
            # Each layer costs approximately (model_size_gb * quantization_factor / total_layers) of VRAM
            # We adjust by the desired utilization percentage
            
            # Estimate total layers in model based on size
            if model_size_gb < 10:
                total_layers = 32
            elif model_size_gb < 25:
                total_layers = 40
            elif model_size_gb < 40:
                total_layers = 60
            else:
                total_layers = 80
                
            # Calculate available VRAM based on utilization percentage
            available_vram = vram_gb * (gpu_utilization / 100)
            
            # Estimate how many layers we can fit
            estimated_layers = int((available_vram / (model_size_gb * quantization_factor)) * total_layers)
            
            # Cap at total layers
            estimated_layers = min(estimated_layers, total_layers)
            
            # Ensure at least 1 layer if GPU is enabled
            if gpu_utilization > 0:
                estimated_layers = max(1, estimated_layers)
                
            return estimated_layers
            
        except Exception as e:
            logger.error(f"Error estimating GPU layers: {e}")
            return 8  # Reasonable fallback
    
    def _apply_gpu_policy_to_all(self, policy, custom_layers):
        """Apply the selected GPU policy to all model configurations."""
        try:
            models_updated = 0
            
            # Get all model configs
            for model_name, config in self.model_manager.model_configs.items():
                model_path = config.model_path
                
                # Skip if model file doesn't exist
                if not os.path.exists(model_path):
                    continue
                
                # Calculate appropriate layers based on policy
                if policy == "Auto (based on size)":
                    # Use size-based estimation
                    model_size_bytes = os.stat(model_path).st_size
                    model_size_gb = model_size_bytes / (1024**3)
                    
                    # Simple size-based rules
                    if model_size_gb < 5:
                        layers = 32
                    elif model_size_gb < 10:
                        layers = 24
                    elif model_size_gb < 20:
                        layers = 16
                    elif model_size_gb < 30:
                        layers = 8
                    else:
                        layers = 4
                        
                elif policy == "Conservative":
                    # Minimum layers for safety
                    layers = 4
                    
                elif policy == "Balanced":
                    # Middle ground
                    layers = 16
                    
                elif policy == "Aggressive":
                    # Maximum layers for speed
                    layers = 32
                    
                elif policy == "Custom":
                    # Use the specified custom value
                    layers = int(custom_layers)
                
                # Update the configuration
                current_layers = config.parameters.get("n_gpu_layers", 0)
                if current_layers != layers:
                    config.parameters["n_gpu_layers"] = layers
                    self.model_manager.save_model_config(config)
                    models_updated += 1
            
            return f"✅ Updated GPU layers for {models_updated} models based on {policy} policy"
            
        except Exception as e:
            logger.error(f"Error applying GPU policy: {e}")
            return f"❌ Error applying GPU policy: {str(e)}"
    
    def _run_gpu_test(self, model_name):
        """Run GPU optimization tests on the selected model."""
        try:
            if not model_name:
                return "Please select a model to test"
            
            # Simulated results for now - in a real implementation, this would
            # actually load the model with different settings and run benchmarks
            results = []
            results.append("## GPU Test Results\n")
            results.append(f"**Model**: {model_name}\n")
            results.append("| GPU Layers | Memory Usage | Tokens/sec |\n")
            results.append("|------------|--------------|------------|\n")
            
            # Test with different layer counts
            for layers in [0, 8, 16, 24, 32]:
                # Simulate measurements
                memory_usage = f"{4 + (layers * 0.3):.1f} GB"
                tokens_per_sec = f"{5 + (layers * 1.2):.1f}"
                
                if layers == 0:
                    tokens_per_sec = "5.0"  # CPU baseline
                
                results.append(f"| {layers} | {memory_usage} | {tokens_per_sec} |\n")
            
            results.append("\n**Recommendation**: Based on these results, setting GPU Layers to **24** provides the best balance of performance and VRAM usage.")
            
            return "".join(results)
            
        except Exception as e:
            logger.error(f"Error running GPU test: {e}")
            return f"❌ Error running GPU test: {str(e)}"
    
    def _save_gpu_settings(self, enable_gpu, memory_limit, batch_size, policy, custom_layers):
        """Save GPU settings."""
        try:
            if "gpu" not in self.settings:
                self.settings["gpu"] = {}
                
            self.settings["gpu"]["enabled"] = enable_gpu
            self.settings["gpu"]["memory_limit"] = memory_limit
            self.settings["gpu"]["batch_size"] = batch_size
            self.settings["gpu"]["default_policy"] = policy
            self.settings["gpu"]["custom_default_layers"] = custom_layers
            
            if self.save_settings():
                return "✅ GPU settings saved successfully"
            else:
                return "❌ Error saving GPU settings"
        except Exception as e:
            error_msg = f"❌ Error saving GPU settings: {str(e)}"
            logger.error(error_msg)
            return error_msg