import gradio as gr
import logging
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from modules.model_manager import ModelManager
import time

logger = logging.getLogger(__name__)

class AirlockInterface:
    """
    Airlock interface for selecting models and features before starting chat.
    Acts as a staging area before entering the main chat interface.
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.selected_models = []
        self.active_features = {
            "vision": False,
            "speech": False,
            "image_gen": False,
            "video_gen": False,
            "3d_gen": False,
            "code_gen": False,
            "reasoning": False,
            "multimodal": False,
        }
        
        # Load models and categorize them
        self.available_models = self._categorize_models()
        self.feature_providers = self._load_feature_providers()
        
        logger.info(f"Airlock interface initialized with {len(self.available_models)} models")
    
    def _categorize_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize available models by size and capability."""
        models = {}
        
        # Common categories
        categories = {
            "small": {"name": "Small (7B-14B)", "models": []},
            "medium": {"name": "Medium (14B-35B)", "models": []},
            "large": {"name": "Large (35B+)", "models": []},
            "specialized": {"name": "Specialized Models", "models": []},
            "multimodal": {"name": "Multimodal Models", "models": []}
        }
        
        models_by_category = {}
        
        # Categorize models based on name, size and capabilities
        for model_name, config in self.model_manager.model_configs.items():
            model_path = config.model_path
            
            # Check if model file exists
            model_exists = Path(model_path).exists()
            
            # Get model size if possible
            model_size_gb = 0
            try:
                if model_exists:
                    model_size_bytes = Path(model_path).stat().st_size
                    model_size_gb = model_size_bytes / (1024**3)
            except:
                pass
            
            # Create model entry
            model_entry = {
                "name": model_name,
                "path": model_path,
                "exists": model_exists,
                "size_gb": model_size_gb,
                "config": config,
                "gpu_layers": config.parameters.get("n_gpu_layers", 0),
                "format": config.parameters.get("format", "default")
            }
            
            # Categorize based on name and size
            category = None
            model_name_lower = model_name.lower()
            
            # Check for multimodal models
            if "multimodal" in model_name_lower or "phi-4" in model_name_lower:
                category = "multimodal"
            # Specialized models
            elif any(term in model_name_lower for term in ["coder", "code", "sql", "math"]):
                category = "specialized"
            # Categorize by size
            elif model_size_gb > 35 or "70b" in model_name_lower or "65b" in model_name_lower:
                category = "large"
            elif model_size_gb > 14 or "30b" in model_name_lower or "33b" in model_name_lower:
                category = "medium"
            else:
                category = "small"
            
            # Add to appropriate category
            if category in categories:
                categories[category]["models"].append(model_entry)
        
        # Sort models in each category by size
        for category in categories.values():
            category["models"].sort(key=lambda x: (not x["exists"], -x["size_gb"]))
        
        # Add a monitor flag to indicate we should refresh model list later
        self.models_changed = False
        
        # Add directory timestamps to detect changes
        self.last_scan_time = time.time()
        self.model_dir_timestamps = {}
        
        # Record timestamps of model directories for change detection
        for category in categories.values():
            for model in category["models"]:
                model_dir = Path(model["path"]).parent
                try:
                    if model_dir.exists():
                        self.model_dir_timestamps[str(model_dir)] = model_dir.stat().st_mtime
                except:
                    pass
        
        return categories

    def check_for_model_changes(self) -> bool:
        """Check if models have been added or removed since last scan.
        
        Returns:
            True if changes detected, False otherwise
        """
        # Don't check too frequently (max once every 30 seconds)
        current_time = time.time()
        if current_time - self.last_scan_time < 30:
            return self.models_changed
        
        self.last_scan_time = current_time
        
        # Check if model directories have changed
        for dir_path, last_mtime in self.model_dir_timestamps.items():
            dir_path = Path(dir_path)
            if not dir_path.exists():
                # Directory was removed
                self.models_changed = True
                logger.info(f"Model directory removed: {dir_path}")
                return True
            
            try:
                current_mtime = dir_path.stat().st_mtime
                if current_mtime > last_mtime:
                    # Directory was modified
                    self.models_changed = True
                    logger.info(f"Model directory modified: {dir_path}")
                    return True
            except:
                pass
        
        # Check for new model directories
        try:
            # Quick check for any new files in main model directory
            model_dirs = set()
            tt_models_dir = Path("G:/AI/Lyra/BigModes/TT Models")
            
            if tt_models_dir.exists():
                for item in tt_models_dir.glob("*"):
                    if item.is_dir():
                        model_dirs.add(str(item))
                    elif item.suffix.lower() in ('.gguf', '.bin', '.safetensors'):
                        model_dirs.add(str(item.parent))
            
            for dir_path in model_dirs:
                if dir_path not in self.model_dir_timestamps:
                    # New model directory
                    self.models_changed = True
                    logger.info(f"New model directory found: {dir_path}")
                    return True
        except Exception as e:
            logger.warning(f"Error checking for new models: {e}")
        
        return self.models_changed

    def refresh_models(self):
        """Refresh the model listing from disk."""
        self.model_manager = ModelManager()
        self.model_manager._discover_models()  # Force rediscovery
        self.available_models = self._categorize_models()
        self.models_changed = False
        logger.info("Model list refreshed from disk")
        return self.available_models
    
    def _load_feature_providers(self) -> Dict[str, Dict[str, Any]]:
        """Load information about feature providers."""
        providers = {
            "vision": {
                "name": "Vision & OCR",
                "icon": "🔍",
                "model": "phi-4",
                "available": self._check_phi4_available(),
                "description": "Extract text from images and analyze visual content"
            },
            "speech": {
                "name": "Speech Recognition & TTS",
                "icon": "🔊",
                "model": "phi-4",
                "available": self._check_phi4_available(),
                "description": "Convert speech to text and text to speech"
            },
            "image_gen": {
                "name": "Image Generation",
                "icon": "🖼️",
                "model": "FLUX.1",
                "available": self._check_flux_available(),
                "description": "Generate images from text descriptions"
            },
            "video_gen": {
                "name": "Video Generation",
                "icon": "🎬",
                "model": "ComfyUI",
                "available": self._check_comfyui_available(),
                "description": "Create short videos from prompts"
            },
            "3d_gen": {
                "name": "3D Model Generation",
                "icon": "🧊",
                "model": "Cube",
                "available": self._check_cube_available(),
                "description": "Generate 3D models from text descriptions"
            }
        }
        
        return providers
    
    def _check_phi4_available(self) -> bool:
        """Check if Phi-4 multimodal model is available."""
        phi4_path = Path("G:/AI/Lyra/BigModes/Phi-4-multimodal-instruct-abliterated")
        model_files_exist = all(
            [phi4_path.exists(),
             (phi4_path / "model-00001-of-00003.safetensors").exists()]
        )
        return model_files_exist
    
    def _check_flux_available(self) -> bool:
        """Check if FLUX image generation is available."""
        flux_path = Path("G:/AI/Full Models/FLUX.1-dev")
        return flux_path.exists() and (flux_path / "model_index.json").exists()
    
    def _check_comfyui_available(self) -> bool:
        """Check if ComfyUI is available for video generation."""
        # This is a simple placeholder. In a real implementation, 
        # you'd check if ComfyUI is installed and accessible
        return True
    
    def _check_cube_available(self) -> bool:
        """Check if the Cube 3D generator is available."""
        cube_path = Path("G:/AI/Lyra/BigModes/cube")
        return cube_path.exists()
    
    def get_model_cards(self, category):
        """Get HTML cards for models in the specified category."""
        if category not in self.available_models:
            return "<div class='error-message'>Category not found</div>"
        
        models = self.available_models[category]["models"]
        
        # Fixed: More reliable HTML structure with explicit onclick handlers
        cards_html = """
        <div class='model-card-container'>
            <div class='model-grid'>
        """
        
        for model in models:
            # Create a card for each model
            status = "✅" if model["exists"] else "❌"
            size = f"{model['size_gb']:.1f} GB" if model["exists"] else "N/A"
            
            # Fix: Use direct onclick handler with explicit model name
            card_html = f"""
            <div class='model-card' data-model-name="{model['name']}" onclick="selectModelCard('{model['name']}')">
                <div class='model-header'>
                    <span class='model-status'>{status}</span>
                    <span class='model-name'>{model["name"]}</span>
                </div>
                <div class='model-details'>
                    <div>Size: {size}</div>
                    <div>Format: {model["format"]}</div>
                    <div>GPU Layers: {model["gpu_layers"]}</div>
                </div>
                <div class='model-select'>
                    <button class="select-model-btn" onclick="event.stopPropagation(); selectModelCard('{model['name']}')">Select</button>
                </div>
            </div>
            """
            cards_html += card_html
        
        cards_html += """
            </div>
        </div>
        """
        
        return cards_html
    
    def select_model(self, model_name):
        """Select a model for use in the chat."""
        if model_name not in self.selected_models:
            self.selected_models.append(model_name)
            logger.info(f"Selected model: {model_name}")
            return f"Selected model: {model_name}", self.selected_models
        return f"Model already selected: {model_name}", self.selected_models
    
    def deselect_model(self, model_name):
        """Remove a model from the selected list."""
        if model_name in self.selected_models:
            self.selected_models.remove(model_name)
            logger.info(f"Removed model: {model_name}")
            return f"Removed model: {model_name}", self.selected_models
        return f"Model not in selection: {model_name}", self.selected_models
    
    def toggle_feature(self, feature_name, enabled):
        """Toggle a feature on or off."""
        if feature_name in self.active_features:
            self.active_features[feature_name] = enabled
            status = "enabled" if enabled else "disabled"
            logger.info(f"Feature {feature_name} {status}")
            return f"Feature {feature_name} {status}"
        return f"Unknown feature: {feature_name}"
    
    def create_ui(self):
        """Create the Gradio interface for the airlock."""
        with gr.Blocks(title="Lyra AI - Model Selection", 
                     theme=gr.themes.Soft(),
                     css=self._get_custom_css()) as interface:
            
            # Header
            with gr.Row():
                gr.Markdown("# Lyra AI Model Selection")
                with gr.Column(scale=1):
                    gr.Markdown("Choose models and features before starting your chat")
                    # Add refresh models button at the top level
                    refresh_models_btn = gr.Button("🔄 Refresh Model List", scale=1)
            
            with gr.Tabs():
                # Model Selection Tab
                with gr.TabItem("Select Models"):
                    with gr.Row():
                        # Left column: Model categories
                        with gr.Column(scale=1):
                            gr.Markdown("### Model Categories")
                            
                            # Create category buttons - FIXED
                            category_buttons = []
                            for category_id, category_info in self.available_models.items():
                                btn = gr.Button(
                                    f"{category_info['name']} ({len(category_info['models'])})", 
                                    elem_id=f"cat-{category_id}"
                                )
                                category_buttons.append((category_id, btn))
                            
                            # Selected models display
                            gr.Markdown("### Selected Models")
                            selected_models_display = gr.TextArea(
                                value="No models selected",
                                label="Selected Models",
                                interactive=False,
                                elem_id="selected-models-display"
                            )
                            
                            # Store selected models in a State
                            selected_models_state = gr.State([])
                            
                            # Clear selection button
                            clear_selection_btn = gr.Button("Clear Model Selection")
                        
                        # Right column: Model display
                        with gr.Column(scale=2):
                            gr.Markdown("### Available Models")
                            model_display = gr.HTML(
                                value="<div class='loading-message'>Select a category to see available models</div>",
                                elem_id="model-display"
                            )
                            
                            # Hidden components for selection
                            model_selection_input = gr.Textbox(visible=False, elem_id="model-selection-input")
                            selection_status = gr.Textbox(visible=False)
                    
                    # Connect category buttons to display models - FIXED
                    for category_id, btn in category_buttons:
                        btn.click(
                            fn=lambda c=category_id: self.get_model_cards(c),
                            inputs=[],
                            outputs=[model_display]
                        )
                    
                    # FIXED: Simplified model selection function - this is critical
                    def select_model_and_update(model_name, current_models):
                        if not model_name:
                            return "", current_models, self._format_selected_models(current_models)
                        
                        # Make sure current_models is a list
                        if current_models is None:
                            current_models = []
                        
                        # Create a new list to avoid modifying the input
                        updated_models = current_models.copy() if current_models else []
                        
                        # Remove or add the model
                        if model_name in updated_models:
                            updated_models.remove(model_name)
                            status = f"Removed: {model_name}"
                        else:
                            updated_models.append(model_name)
                            status = f"Added: {model_name}"
                        
                        # Return status, updated list, and formatted text
                        return status, updated_models, self._format_selected_models(updated_models)
                    
                    # Function to format selected models for display
                    def _format_selected_models(self, model_list):
                        if not model_list:
                            return "No models selected"
                        return "\n".join([f"• {m}" for m in model_list])
                    
                    # FIXED: Attach model selection function with more reliable method
                    model_selection_input.change(
                        fn=select_model_and_update,
                        inputs=[model_selection_input, selected_models_state],
                        outputs=[selection_status, selected_models_state, selected_models_display]
                    )
                    
                    # FIXED: Clear selection function
                    def clear_selection():
                        return [], "Models cleared"
                    
                    clear_selection_btn.click(
                        fn=clear_selection,
                        inputs=[],
                        outputs=[selected_models_state, selection_status]
                    ).then(
                        fn=lambda: "No models selected",
                        inputs=[],
                        outputs=[selected_models_display]
                    )
                    
                    # FIXED: More robust JavaScript for model selection
                    js_script = """
                    <script>
                    // Function to select a model and update the hidden input
                    function selectModelCard(modelName) {
                        // Find the hidden input field
                        const inputElement = document.querySelector('#model-selection-input input');
                        if (!inputElement) {
                            console.error("Could not find model selection input");
                            return;
                        }
                        
                        // Set the value
                        inputElement.value = modelName;
                        
                        // Create and dispatch change event
                        const event = new Event('change', { bubbles: true });
                        inputElement.dispatchEvent(event);
                        
                        // Toggle visual selection - find the card with this model name
                        const cards = document.querySelectorAll('.model-card');
                        cards.forEach(card => {
                            if (card.getAttribute('data-model-name') === modelName) {
                                card.classList.toggle('selected');
                            }
                        });
                    }
                    
                    // Initialize when the DOM is loaded
                    document.addEventListener('DOMContentLoaded', function() {
                        console.log("DOM loaded, setting up model selection");
                        
                        // Add click handlers to any existing cards
                        document.querySelectorAll('.model-card').forEach(card => {
                            const modelName = card.getAttribute('data-model-name');
                            if (modelName) {
                                console.log("Found card for model:", modelName);
                            }
                        });
                    });
                    
                    // Use MutationObserver to handle dynamically added cards
                    const observer = new MutationObserver(mutations => {
                        for (const mutation of mutations) {
                            if (mutation.type === 'childList') {
                                mutation.addedNodes.forEach(node => {
                                    if (node.nodeType === 1) { // Element node
                                        // Handle cards that are direct children of added node
                                        if (node.classList && node.classList.contains('model-card')) {
                                            console.log("New card added to DOM");
                                        }
                                        
                                        // Handle cards inside the added node
                                        node.querySelectorAll && node.querySelectorAll('.model-card').forEach(card => {
                                            console.log("Card found inside new node");
                                        });
                                    }
                                });
                            }
                        }
                    });
                    
                    // Start observing the document
                    observer.observe(document.body, { childList: true, subtree: true });
                    </script>
                    """
                    gr.HTML(js_script)
                
                # Features Tab - Preserve settings state between tabs
                with gr.TabItem("Select Features"):
                    # FIXED: Create state for feature settings
                    vision_state = gr.State(False)
                    speech_state = gr.State(False)
                    image_gen_state = gr.State(False)
                    video_gen_state = gr.State(False)
                    model_gen_state = gr.State(False)
                    
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown("### Multimodal Capabilities")
                            
                            # Vision capabilities
                            with gr.Group():
                                gr.Markdown("#### 🔍 Vision & OCR")
                                vision_toggle = gr.Checkbox(
                                    label="Enable Vision & OCR",
                                    value=False,
                                    interactive=self.feature_providers["vision"]["available"]
                                )
                                if not self.feature_providers["vision"]["available"]:
                                    gr.Markdown("⚠️ Phi-4 model not available")
                            
                            # Speech capabilities
                            with gr.Group():
                                gr.Markdown("#### 🔊 Speech Recognition & TTS")
                                speech_toggle = gr.Checkbox(
                                    label="Enable Speech Features",
                                    value=False,
                                    interactive=self.feature_providers["speech"]["available"]
                                )
                                if not self.feature_providers["speech"]["available"]:
                                    gr.Markdown("⚠️ Phi-4 model not available")
                        
                        with gr.Column(scale=1):
                            gr.Markdown("### Media Generation")
                            
                            # Image generation
                            with gr.Group():
                                gr.Markdown("#### 🖼️ Image Generation")
                                image_gen_toggle = gr.Checkbox(
                                    label="Enable Image Generation",
                                    value=False,
                                    interactive=self.feature_providers["image_gen"]["available"]
                                )
                                if not self.feature_providers["image_gen"]["available"]:
                                    gr.Markdown("⚠️ FLUX model not available")
                                    
                            # Video generation
                            with gr.Group():
                                gr.Markdown("#### 🎬 Video Generation")
                                video_gen_toggle = gr.Checkbox(
                                    label="Enable Video Generation",
                                    value=False,
                                    interactive=self.feature_providers["video_gen"]["available"]
                                )
                                
                            # 3D model generation
                            with gr.Group():
                                gr.Markdown("#### 🧊 3D Model Generation")
                                model_gen_toggle = gr.Checkbox(
                                    label="Enable 3D Generation",
                                    value=False,
                                    interactive=self.feature_providers["3d_gen"]["available"]
                                )
                                if not self.feature_providers["3d_gen"]["available"]:
                                    gr.Markdown("⚠️ Cube model not available")
                    
                    # Connect toggles to states for persistence
                    vision_toggle.change(lambda x: x, inputs=[vision_toggle], outputs=[vision_state])
                    speech_toggle.change(lambda x: x, inputs=[speech_toggle], outputs=[speech_state])
                    image_gen_toggle.change(lambda x: x, inputs=[image_gen_toggle], outputs=[image_gen_state])
                    video_gen_toggle.change(lambda x: x, inputs=[video_gen_toggle], outputs=[video_gen_state])
                    model_gen_toggle.change(lambda x: x, inputs=[model_gen_toggle], outputs=[model_gen_state])

                # Advanced Settings Tab
                with gr.TabItem("Advanced Settings"):
                    # CHANGED: Set GPU layers default to 50
                    gpu_layers_state = gr.State(50)
                    context_size_state = gr.State(4096)
                    parallel_state = gr.State(1)
                    server_mode_state = gr.State(True)
                    
                    with gr.Row():
                        with gr.Column():
                            gr.Markdown("### Performance Settings")
                            
                            with gr.Row():
                                # GPU settings - Changed default to 50
                                gpu_layers = gr.Slider(
                                    minimum=0, maximum=100, value=50, step=1,
                                    label="Default GPU Layers"
                                )
                                gpu_vram = gr.Dropdown(
                                    choices=["Low (4-8GB)", "Medium (8-16GB)", "High (16-24GB)", "Ultra (24GB+)"],
                                    label="Available GPU VRAM",
                                    value="Medium (8-16GB)"
                                )
                            
                            with gr.Row():
                                # Memory settings
                                context_size = gr.Slider(
                                    minimum=2048, maximum=16384, value=4096, step=1024,
                                    label="Context Size"
                                )
                                n_parallel = gr.Slider(
                                    minimum=1, maximum=8, value=1, step=1,
                                    label="Parallel Requests"
                                )
                                
                            with gr.Row():
                                # Server mode
                                server_mode = gr.Checkbox(
                                    label="Use llama-server (recommended)",
                                    value=True
                                )
                                server_port = gr.Number(
                                    value=8080,
                                    label="Server Port",
                                    interactive=True
                                )
                        
                        with gr.Column():
                            gr.Markdown("### Interface Settings")
                            
                            with gr.Row():
                                # Theme selector
                                theme = gr.Dropdown(
                                    choices=["Light", "Dark", "Soft", "Glass"],
                                    label="UI Theme",
                                    value="Soft"
                                )
                                # Font size
                                font_size = gr.Dropdown(
                                    choices=["Small", "Medium", "Large"],
                                    label="Font Size",
                                    value="Medium"
                                )
                            
                            with gr.Row():
                                # Chat settings
                                max_history = gr.Slider(
                                    minimum=10, maximum=100, value=50, step=5,
                                    label="Chat History Length"
                                )
                                auto_save = gr.Checkbox(
                                    label="Auto-save Chat History",
                                    value=True
                                )
                            
                            with gr.Row():
                                # Debug options
                                debug_mode = gr.Checkbox(
                                    label="Debug Mode",
                                    value=False
                                )
                                log_level = gr.Dropdown(
                                    choices=["INFO", "DEBUG", "WARNING", "ERROR"],
                                    label="Log Level",
                                    value="INFO"
                                )
                    
                    # Connect settings to states
                    gpu_layers.change(lambda x: x, inputs=[gpu_layers], outputs=[gpu_layers_state])
                    context_size.change(lambda x: x, inputs=[context_size], outputs=[context_size_state])
                    n_parallel.change(lambda x: x, inputs=[n_parallel], outputs=[parallel_state])
                    server_mode.change(lambda x: x, inputs=[server_mode], outputs=[server_mode_state])
            
            # Launch button at bottom of interface
            with gr.Row():
                launch_btn = gr.Button("Launch Lyra Chat", variant="primary", scale=2)
            
            # Function to collect all settings and return them
            def collect_settings(selected_models, 
                              vision, speech, image_gen, video_gen, model_gen,
                              gpu_layers, context_size, n_parallel, server_mode):
                
                # Format selected models
                if not selected_models:
                    selected_models = []
                
                # Collect feature settings
                features = {
                    "vision": vision,
                    "speech": speech,
                    "image_gen": image_gen,
                    "video_gen": video_gen,
                    "3d_gen": model_gen
                }
                
                # Collect advanced settings
                advanced = {
                    "gpu_layers": gpu_layers,
                    "context_size": context_size,
                    "n_parallel": n_parallel,
                    "server_mode": server_mode
                }
                
                # Return values directly, not wrapped in State objects or dicts
                return selected_models, features, advanced
            
            # Connect launch button to the collect_settings function
            # Critical fix: Use actual State objects in outputs, not dictionaries
            launch_btn.click(
                fn=collect_settings,
                inputs=[
                    selected_models_state,
                    vision_state, speech_state, image_gen_state, video_gen_state, model_gen_state,
                    gpu_layers_state, context_size_state, parallel_state, server_mode_state
                ],
                outputs=[selected_models_state, gr.State(), gr.State()]  # Create new State objects
            )
        
        # Add event handler for refresh button
        refresh_models_btn.click(
            fn=self.refresh_models,
            inputs=[],
            outputs=[]
        ).then(
            # After refreshing, update the current category view
            fn=lambda: self.get_model_cards("small"),  # Default to small models
            inputs=[],
            outputs=[model_display]
        )
        
        return interface, launch_btn, selected_models_state, self.active_features
    
    def _get_custom_css(self):
        """Get custom CSS for the airlock interface."""
        return """
        .model-card-container {
            max-height: 75vh;
            overflow-y: auto;
            padding-right: 10px;
        }
        
        .model-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .model-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            background-color: #f9f9f9;
            cursor: pointer;
        }
        
        .model-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            background-color: #f0f7ff;
        }
        
        /* Make selected state very obvious */
        .model-card.selected {
            border: 3px solid #4CAF50 !important;
            background-color: #e1f5e1 !important;
            box-shadow: 0 0 15px rgba(76, 175, 80, 0.7) !important;
        }
        
        .model-card.selected .model-select button {
            background-color: #1b5e20 !important;
            color: white !important;
            font-weight: bold !important;
        }
        
        .model-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            border-bottom: 1px solid #eee;
            padding-bottom: 8px;
        }
        
        .model-name {
            font-weight: bold;
            font-size: 1.1em;
            color: #333;
            word-break: break-word;
        }
        
        .model-details {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 15px;
        }
        
        .model-select {
            display: flex;
            justify-content: center;
        }
        
        .model-select button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .model-select button:hover {
            background-color: #45a049;
        }
        
        /* Improved status indicators */
        .model-status {
            font-weight: bold;
        }
        
        /* Added loading and error message styling */
        .loading-message, .error-message {
            padding: 20px;
            text-align: center;
            background-color: #f5f5f5;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .error-message {
            color: #d32f2f;
            background-color: #ffebee;
        }
        
        /* Custom scrollbar for model list */
        .model-card-container::-webkit-scrollbar {
            width: 8px;
        }
        
        .model-card-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .model-card-container::-webkit-scrollbar-thumb {
            background: #888;
            border-radius: 10px;
        }
        
        .model-card-container::-webkit-scrollbar-thumb:hover {
            background: #555;
        }
        """


def create_airlock_interface():
    """Create and return an airlock interface instance."""
    airlock_ui = AirlockInterface()
    return airlock_ui.create_ui()
