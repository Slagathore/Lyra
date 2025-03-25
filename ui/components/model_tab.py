"""
Model tab UI component
"""
import gradio as gr
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class ModelTab(TabComponent):
    """Model tab UI component"""
    
    def build(self):
        """Build the model management tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Available Models")
                
                model_list = gr.Dataframe(
                    headers=["Name", "Size", "Type", "Active"],
                    label="Models"
                )
                
                with gr.Row():
                    scan_btn = gr.Button("Scan for New Models")
                    refresh_btn = gr.Button("Refresh List")
                
                gr.Markdown("### Set Active Model")
                
                model_dropdown = gr.Dropdown(
                    choices=[m.name for m in self.bot.model_manager.models],
                    value=self._get_active_model_name(),
                    label="Select Model"
                )
                
                set_active_btn = gr.Button("Set as Active Model")
                
                model_status = gr.Markdown("")
            
            with gr.Column(scale=1):
                gr.Markdown("### Model Details")
                
                model_info = gr.JSON(label="Model Configuration")
                
                with gr.Row():
                    n_gpu_layers = gr.Slider(0, 100, value=35, step=1, label="GPU Layers")
                    n_ctx = gr.Slider(512, 8192, value=4096, step=512, label="Context Size")
                
                with gr.Row():
                    chat_format = gr.Dropdown(
                        choices=["llama-2", "chatml", "mistral", "custom"],
                        label="Chat Format"
                    )
                    
                    update_model_btn = gr.Button("Update Settings")
                
                with gr.Row():
                    remove_model_btn = gr.Button("Remove Model", variant="stop")
        
        # Store elements for later access
        self.elements.update({
            "model_list": model_list,
            "scan_btn": scan_btn,
            "refresh_btn": refresh_btn,
            "model_dropdown": model_dropdown,
            "set_active_btn": set_active_btn,
            "model_status": model_status,
            "model_info": model_info,
            "n_gpu_layers": n_gpu_layers,
            "n_ctx": n_ctx,
            "chat_format": chat_format,
            "update_model_btn": update_model_btn,
            "remove_model_btn": remove_model_btn
        })
        
        # Set up event handlers
        self._setup_handlers()
        
        # Initialize with model list
        self._on_refresh_models()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Scan button handler
        e["scan_btn"].click(
            fn=self._on_scan_models,
            outputs=[e["model_list"], e["model_dropdown"], e["model_status"]]
        )
        
        # Refresh button handler
        e["refresh_btn"].click(
            fn=self._on_refresh_models,
            outputs=[e["model_list"]]
        )
        
        # Model dropdown change handler
        e["model_dropdown"].change(
            fn=self._on_model_tab_select,
            inputs=[e["model_dropdown"]],
            outputs=[e["model_info"], e["n_gpu_layers"], e["n_ctx"], e["chat_format"]]
        )
        
        # Set active model button handler
        e["set_active_btn"].click(
            fn=self._on_set_active_model,
            inputs=[e["model_dropdown"]],
            outputs=[e["model_list"], e["model_status"]]
        )
        
        # Update model settings button handler
        e["update_model_btn"].click(
            fn=self._on_update_model_settings,
            inputs=[e["model_dropdown"], e["n_gpu_layers"], e["n_ctx"], e["chat_format"]],
            outputs=[e["model_info"], e["model_status"]]
        )
        
        # Remove model button handler
        e["remove_model_btn"].click(
            fn=self._on_remove_model,
            inputs=[e["model_dropdown"]],
            outputs=[e["model_list"], e["model_dropdown"], e["model_status"]]
        )
    
    def _get_active_model_name(self):
        """Get the name of the currently active model"""
        active_model = self.bot.model_manager.get_active_model()
        return active_model.name if active_model else "No model loaded"
    
    def _on_scan_models(self):
        """Scan for new models"""
        new_models = self.bot.model_manager.scan_for_new_models()
        model_list_data = self._get_model_list_data()
        models = [m.name for m in self.bot.model_manager.models]
        
        if new_models:
            return model_list_data, models, f"Found {len(new_models)} new models."
        else:
            return model_list_data, models, "No new models found."
    
    def _on_refresh_models(self):
        """Refresh the model list"""
        return self._get_model_list_data()
    
    def _get_model_list_data(self):
        """Get data for model list display"""
        data = []
        for model in self.bot.model_manager.models:
            data.append([
                model.name,
                f"{model.file_size_gb:.1f} GB" if model.file_exists else "Not found",
                model.type,
                "✓" if model.active else ""
            ])
        return data
    
    def _on_model_tab_select(self, model_name):
        """Handle selecting a model in the model tab"""
        model = None
        for m in self.bot.model_manager.models:
            if m.name == model_name:
                model = m
                break
        
        if not model:
            return {}, 35, 4096, "chatml"
        
        return asdict(model), model.n_gpu_layers, model.n_ctx, model.chat_format
    
    def _on_set_active_model(self, model_name):
        """Set the active model"""
        if not model_name:
            return self._get_model_list_data(), "Please select a model to activate."
        
        success = self.bot.model_manager.set_active_model(model_name)
        
        if success:
            return self._get_model_list_data(), f"Model '{model_name}' set as active."
        else:
            return self._get_model_list_data(), f"Failed to set model '{model_name}' as active."
    
    def _on_update_model_settings(self, model_name, n_gpu_layers, n_ctx, chat_format):
        """Update model settings"""
        if not model_name:
            return {}, "Please select a model to update."
        
        # Find the model
        model = None
        for m in self.bot.model_manager.models:
            if m.name == model_name:
                model = m
                break
        
        if not model:
            return {}, "Model not found."
        
        # Update model settings
        model.n_gpu_layers = n_gpu_layers
        model.n_ctx = n_ctx
        model.chat_format = chat_format
        
        # Save changes
        self.bot.model_manager.save_config()
        
        return asdict(model), f"Settings for model '{model_name}' updated successfully."
    
    def _on_remove_model(self, model_name):
        """Remove a model from the configuration"""
        if not model_name:
            return self._get_model_list_data(), [m.name for m in self.bot.model_manager.models], "Please select a model to remove."
        
        success = self.bot.model_manager.remove_model(model_name)
        
        if success:
            return self._get_model_list_data(), [m.name for m in self.bot.model_manager.models], f"Model '{model_name}' removed from configuration."
        else:
            return self._get_model_list_data(), [m.name for m in self.bot.model_manager.models], f"Failed to remove model '{model_name}'."
