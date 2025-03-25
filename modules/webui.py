# ...existing code...

def create_models_tab():
    """Create the models tab with better error handling and UI"""
    with gr.Tab("Models"):
        with gr.Row():
            with gr.Column(scale=3):
                # Get available models
                from modules.model_loader import get_model_loader
                model_loader = get_model_loader()
                
                # Add default model directories
                model_dirs = [
                    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models"),
                    os.path.expanduser("~/models"),
                    os.path.expanduser("~/.cache/huggingface/hub")
                ]
                
                for model_dir in model_dirs:
                    model_loader.add_model_dir(model_dir)
                
                # Get the model list, filtering out invalid models
                models = model_loader.get_models(min_size_gb=0.01)
                model_names = list(models.keys())
                
                # Create a dropdown with model paths and names
                model_dropdown = gr.Dropdown(
                    choices=model_names,
                    label="Select Model",
                    value=model_names[0] if model_names else "",
                    info="Choose a model to load",
                    render=True,
                    interactive=True
                )
                
                # Add a refresh button
                refresh_btn = gr.Button("🔄 Refresh Models")
                
                # Model info display
                model_info = gr.JSON(
                    label="Model Information",
                    value={},
                    render=True
                )
                
            with gr.Column(scale=4):
                # Model settings
                with gr.Row():
                    gpu_layers = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=0,
                        step=1,
                        label="GPU Layers",
                        info="Number of layers to offload to GPU (0 for CPU only)"
                    )
                    context_size = gr.Slider(
                        minimum=1024,
                        maximum=32768,
                        value=4096,
                        step=1024,
                        label="Context Size",
                        info="Maximum token context window"
                    )
                
                with gr.Row():
                    threads = gr.Slider(
                        minimum=1,
                        maximum=32,
                        value=4,
                        step=1,
                        label="CPU Threads",
                        info="Number of threads to use"
                    )
                    n_batch = gr.Slider(
                        minimum=128,
                        maximum=2048,
                        value=512,
                        step=128,
                        label="Batch Size",
                        info="Batch size for prompt processing"
                    )
                
                with gr.Accordion("Advanced Settings", open=False):
                    with gr.Row():
                        lora_path = gr.Textbox(
                            label="LoRA Path",
                            info="Path to LoRA adapter (optional)",
                            value=""
                        )
                        mmproj = gr.Textbox(
                            label="MMProj Path",
                            info="Path to multimodal projector (optional)",
                            value=""
                        )
                    
                    with gr.Row():
                        rope_freq_base = gr.Number(
                            label="RoPE Frequency Base",
                            value=0,
                            info="RoPE base frequency (0 for model default)"
                        )
                        rope_freq_scale = gr.Number(
                            label="RoPE Frequency Scale",
                            value=0,
                            info="RoPE frequency scaling (0 for model default)"
                        )
                    
                    with gr.Row():
                        chat_template = gr.Textbox(
                            label="Chat Template",
                            info="Custom chat template (leave empty for default)",
                            value="",
                            lines=3
                        )
                    
                    with gr.Row():
                        model_status = gr.Markdown("Status: Model not loaded")
                
                with gr.Row():
                    load_btn = gr.Button("Load Model", variant="primary")
                    unload_btn = gr.Button("Unload Model", variant="secondary")
                    
                # Status and messages
                load_status = gr.Markdown("Ready to load model")
        
        # Function to handle model selection
        def on_model_select(model_path):
            if not model_path:
                return {}
                
            models = model_loader.get_models()
            if model_path in models:
                return models[model_path]
            return {}
            
        # Function to refresh models
        def refresh_models():
            models = model_loader.get_models(force_refresh=True, min_size_gb=0.01)
            model_names = list(models.keys())
            return gr.Dropdown.update(choices=model_names, value=model_names[0] if model_names else "")
            
        # Function to load model
        def load_model(model_path, gpu_layers, context_size, threads, n_batch, 
                      lora_path, mmproj, rope_freq_base, rope_freq_scale, chat_template):
            try:
                if not model_path:
                    return "Error: No model selected"
                    
                # Verify model size
                models = model_loader.get_models()
                if model_path in models:
                    model_info = models[model_path]
                    if model_info.get("size_gb", 0) < 0.01:
                        return "❌ Model file is too small or empty. Please select a valid model."
                
                # Create model config
                from modules.model import ModelConfig, load_model, is_model_loaded
                
                # Check if model is already loaded
                if is_model_loaded():
                    from modules.model import unload_model
                    unload_model()
                    
                config = ModelConfig(
                    model_name=os.path.basename(model_path),
                    model_path=model_path,
                    context_size=int(context_size),
                    gpu_layers=int(gpu_layers),
                    threads=int(threads),
                    n_batch=int(n_batch),
                    lora_path=lora_path if lora_path else "",
                    mmproj=mmproj if mmproj else "",
                    rope_freq_base=float(rope_freq_base) if rope_freq_base else 0,
                    rope_freq_scale=float(rope_freq_scale) if rope_freq_scale else 0,
                    chat_template=chat_template if chat_template else None
                )
                
                # Load the model
                success = load_model(config)
                
                if success:
                    return "✅ Model loaded successfully"
                else:
                    return "❌ Failed to load model. Check the server logs."
            except Exception as e:
                return f"❌ Error loading model: {str(e)}"
                
        # Function to unload model
        def unload_model():
            try:
                from modules.model import unload_model, is_model_loaded
                
                if is_model_loaded():
                    unload_model()
                    return "✅ Model unloaded"
                else:
                    return "ℹ️ No model currently loaded"
            except Exception as e:
                return f"❌ Error unloading model: {str(e)}"
                
        # Connect UI components
        model_dropdown.change(on_model_select, inputs=[model_dropdown], outputs=[model_info])
        refresh_btn.click(refresh_models, inputs=[], outputs=[model_dropdown])
        load_btn.click(load_model, 
                      inputs=[model_dropdown, gpu_layers, context_size, threads, n_batch,
                             lora_path, mmproj, rope_freq_base, rope_freq_scale, chat_template],
                      outputs=[load_status])
        unload_btn.click(unload_model, inputs=[], outputs=[load_status])

# ...existing code...

def create_public_sharing_ui():
    """Create the public sharing UI with better error handling"""
    with gr.Accordion("Public Sharing", open=False):
        with gr.Row():
            enable_sharing = gr.Checkbox(
                label="Enable Public Sharing",
                value=False,
                info="Make your Lyra instance accessible from the internet"
            )
            
        with gr.Row():
            share_token = gr.Textbox(
                label="Share Token (Optional)",
                value="",
                info="Token for custom sharing service",
                visible=True
            )
            
        with gr.Row():
            share_server = gr.Textbox(
                label="Share Server (Optional)",
                value="",
                info="Custom sharing server address",
                visible=True
            )
            
        with gr.Row():
            share_status = gr.Markdown("Sharing disabled")
            share_url = gr.Textbox(
                label="Public URL",
                value="",
                info="Your public sharing URL",
                interactive=False
            )
            
        share_btn = gr.Button("Start Sharing", variant="primary")
        stop_share_btn = gr.Button("Stop Sharing", variant="secondary")
        
        # Function to start sharing
        def start_sharing(enable, token, server):
            if not enable:
                return "Sharing not enabled", ""
                
            try:
                from modules.sharing import setup_tunnel, get_share_url
                import gradio as gr
                
                # Get the port from app.py 
                port = getattr(share_global_state, "port", 8080)
                
                # Start tunnel
                tunnel = setup_tunnel(port, share=True, share_token=token, share_server_address=server)
                
                if tunnel:
                    url = get_share_url()
                    setattr(share_global_state, "tunnel", tunnel)
                    setattr(share_global_state, "url", url)
                    return "✅ Sharing enabled", url
                else:
                    return "❌ Failed to start sharing", ""
            except Exception as e:
                return f"❌ Error starting sharing: {str(e)}", ""
                
        # Function to stop sharing
        def stop_sharing():
            try:
                tunnel = getattr(share_global_state, "tunnel", None)
                
                if tunnel:
                    # Close tunnel (implementation depends on sharing method)
                    setattr(share_global_state, "tunnel", None)
                    setattr(share_global_state, "url", "")
                    return "✅ Sharing stopped", ""
                else:
                    return "ℹ️ Sharing not active", ""
            except Exception as e:
                return f"❌ Error stopping sharing: {str(e)}", ""
                
        # Connect UI components
        share_btn.click(
            start_sharing,
            inputs=[enable_sharing, share_token, share_server],
            outputs=[share_status, share_url]
        )
        stop_share_btn.click(
            stop_sharing,
            inputs=[],
            outputs=[share_status, share_url]
        )
        
        # Sharing state
        class ShareGlobalState:
            def __init__(self):
                self.tunnel = None
                self.url = ""
                self.port = 8080
                
        share_global_state = ShareGlobalState()
        
        return share_global_state

# ...existing code...

def create_chat_settings_tab():
    """Create a comprehensive chat settings tab with tooltips"""
    with gr.Tab("Chat Settings"):
        with gr.Row():
            with gr.Column():
                # Enable Personality Evolution
                with gr.Row():
                    evolving_personality = gr.Checkbox(
                        label="Enable Evolving Personality",
                        value=False,
                        info="Allow the bot's personality to evolve naturally over time based on interactions"
                    )
                    
                    floating_assistant = gr.Checkbox(
                        label="Enable Floating Assistant Mode",
                        value=False,
                        info="Allow the assistant to float freely around your screen when idle"
                    )
                
                # Generation Settings
                with gr.Accordion("Basic Generation Settings", open=True):
                    temperature = gr.Slider(
                        minimum=0.0,
                        maximum=2.0,
                        value=0.7,
                        step=0.05,
                        label="Temperature",
                        info="Controls randomness. Higher values produce more diverse outputs."
                    )
                    
                    with gr.Row():
                        dynamic_temp = gr.Checkbox(
                            label="Dynamic Temperature", 
                            value=False,
                            info="Adjust temperature dynamically based on content"
                        )
                        
                    response_tokens = gr.Slider(
                        minimum=16,
                        maximum=4096,
                        value=1024,
                        step=16,
                        label="Max Response Tokens",
                        info="Maximum number of tokens to generate in response"
                    )
                    
                    context_tokens = gr.Slider(
                        minimum=512,
                        maximum=32768,
                        value=4096,
                        step=512,
                        label="Context Tokens",
                        info="Maximum tokens to keep in memory (context window)"
                    )
                    
                    rep_penalty = gr.Slider(
                        minimum=1.0,
                        maximum=2.0,
                        value=1.1,
                        step=0.05,
                        label="Repetition Penalty",
                        info="Penalizes repetition. Higher values reduce repetition."
                    )
                    
                    ban_eos = gr.Checkbox(
                        label="Ban EOS Token",
                        value=False,
                        info="Prevent the model from ending generation prematurely"
                    )
                    
                    auto_max_tokens = gr.Checkbox(
                        label="Auto Max Tokens",
                        value=True,
                        info="Automatically determine the maximum number of tokens based on context"
                    )
                
                # Advanced Sampling Settings
                with gr.Accordion("Advanced Sampling", open=False):
                    with gr.Row():
                        top_k = gr.Slider(
                            minimum=0,
                            maximum=100,
                            value=40,
                            step=1,
                            label="Top K",
                            info="Limits sampling to top K most likely tokens. 0 = disabled."
                        )
                        
                        top_p = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.9,
                            step=0.05,
                            label="Top P",
                            info="Nucleus sampling: limits to tokens comprising the top P probability mass."
                        )
                        
                    with gr.Row():
                        typical_p = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.05,
                            label="Typical P",
                            info="Controls how 'typical' token selections are. 0 = disabled."
                        )
                        
                        min_p = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.05,
                            label="Min P",
                            info="Sets minimum probability threshold. 0 = disabled."
                        )
                        
                    with gr.Row():
                        top_a = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.05,
                            label="Top A",
                            info="Adaptive sampling parameter. 0 = disabled."
                        )
                        
                        tfs = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.0,
                            step=0.05,
                            label="TFS",
                            info="Tail-free sampling: removes the 'tail' of the distribution. 0 = disabled."
                        )
                        
                # Smoothing and Guidance Settings
                with gr.Accordion("Smoothing & Guidance", open=False):
                    with gr.Row():
                        smoothing_factor = gr.Slider(
                            minimum=0.0,
                            maximum=10.0,
                            value=0.0,
                            step=0.1,
                            label="Smoothing Factor",
                            info="Controls how aggressively to smooth distributions. 0 = disabled."
                        )
                        
                        smoothing_curve = gr.Slider(
                            minimum=0.0,
                            maximum=5.0,
                            value=0.0,
                            step=0.1,
                            label="Smoothing Curve",
                            info="Controls the shape of the smoothing curve. 0 = disabled."
                        )
                        
                    with gr.Row():
                        guidance_scale = gr.Slider(
                            minimum=1.0,
                            maximum=10.0,
                            value=1.0,
                            step=0.1,
                            label="Guidance Scale",
                            info="Controls how strongly to follow the guidance. 1.0 = no guidance."
                        )
                        
                        negative_prompt = gr.Textbox(
                            label="Negative Prompt",
                            placeholder="What the model should avoid...",
                            lines=2,
                            info="Text the model should avoid emulating"
                        )
                        
                # Special Controls
                with gr.Accordion("Special Controls", open=False):
                    with gr.Row():
                        grammar_file = gr.Textbox(
                            label="Grammar File/Model",
                            info="Path to a grammar file to constrain generation"
                        )
                        
                        seed = gr.Number(
                            label="Seed",
                            value=-1,
                            info="Random seed for generation. -1 = random seed."
                        )
                        
                    with gr.Row():
                        spicy_model = gr.Textbox(
                            label="Spicy Flavoring Model",
                            info="Path to a secondary model to influence generation"
                        )
                        
                        sampler_priority = gr.Dropdown(
                            choices=["Default", "Temperature", "Top-K", "Top-P", "Typical-P", "Min-P"],
                            value="Default",
                            label="Sampler Priority",
                            info="Determines which sampling method takes precedence"
                        )
                        
                    with gr.Row():
                        dry_run = gr.Checkbox(
                            label="Dry Run",
                            value=False,
                            info="Preview generation without actually generating text"
                        )
                        
                        xtc = gr.Checkbox(
                            label="XTC",
                            value=False,
                            info="Extreme tail cutting - more aggressive distribution pruning"
                        )
                        
                # Mirostat Settings
                with gr.Accordion("Mirostat", open=False):
                    with gr.Row():
                        mirostat_mode = gr.Radio(
                            choices=["0", "1", "2"],
                            value="0",
                            label="Mirostat Mode",
                            info="Adaptive token sampling. 0=off, 1=basic, 2=advanced"
                        )
                        
                    with gr.Row():
                        mirostat_tau = gr.Slider(
                            minimum=0.0,
                            maximum=10.0,
                            value=5.0,
                            step=0.1,
                            label="Mirostat Tau",
                            info="Target entropy, higher = more random"
                        )
                        
                        mirostat_eta = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            value=0.1,
                            step=0.01,
                            label="Mirostat Eta",
                            info="Learning rate for mirostat"
                        )
                    
                # Token Bans
                with gr.Accordion("Token Bans", open=False):
                    token_bans = gr.Textbox(
                        label="Token Bans",
                        placeholder="Enter tokens to ban, separated by commas",
                        lines=3,
                        info="List of tokens to ban from generation"
                    )
                
            with gr.Column():
                # User Information
                with gr.Accordion("User Information", open=False):
                    user_telegram = gr.Textbox(
                        label="Telegram Username",
                        placeholder="@username",
                        info="Your Telegram username for notifications"
                    )
                    
                    schedule_awareness = gr.Checkbox(
                        label="Enable Schedule Awareness",
                        value=True,
                        info="Allow the bot to learn your daily schedule"
                    )

                # Personality Traits
                with gr.Accordion("Primary Personality Traits", open=True):
                    gr.Markdown("## Personality Traits (0-100)")
                    
                    happiness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=50,
                        step=1,
                        label="Happiness",
                        info="How happy/joyful the character is"
                    )
                    
                    sadness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=25,
                        step=1,
                        label="Sadness",
                        info="How melancholic or sad the character is"
                    )
                    
                    anger = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=15,
                        step=1,
                        label="Anger",
                        info="How easily angered or irritable the character is"
                    )
                    
                    fear = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=20,
                        step=1,
                        label="Fear",
                        info="How fearful or anxious the character is"
                    )
                    
                    surprise = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=60,
                        step=1,
                        label="Surprise",
                        info="How easily surprised or shocked the character is"
                    )
                    
                    curiosity = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=75,
                        step=1,
                        label="Curiosity",
                        info="How curious or inquisitive the character is"
                    )
                    
                    trust = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=65,
                        step=1,
                        label="Trust",
                        info="How trusting the character is of others"
                    )
                    
                    empathy = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=80,
                        step=1,
                        label="Empathy",
                        info="How empathetic or understanding the character is"
                    )
                    
                # Secondary Traits
                with gr.Accordion("Secondary Traits", open=False):
                    confidence = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=70,
                        step=1,
                        label="Confidence",
                        info="How confident the character is in themselves"
                    )
                    
                    shyness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=30,
                        step=1,
                        label="Shyness",
                        info="How shy or reserved the character is"
                    )
                    
                    playfulness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=65,
                        step=1,
                        label="Playfulness",
                        info="How playful or humorous the character is"
                    )
                    
                    seriousness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=40,
                        step=1,
                        label="Seriousness",
                        info="How serious or focused the character is"
                    )
                    
                    kindness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=75,
                        step=1,
                        label="Kindness",
                        info="How kind or compassionate the character is"
                    )
                    
                    creativity = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=80,
                        step=1,
                        label="Creativity",
                        info="How creative or imaginative the character is"
                    )

                # Relationship Traits
                with gr.Accordion("Relationship Dynamics", open=False):
                    romance = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=25,
                        step=1,
                        label="Romance",
                        info="How romantic the character is"
                    )
                    
                    sass = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=35,
                        step=1,
                        label="Sassiness",
                        info="How sassy or sarcastic the character is"
                    )
                    
                    loyalty = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=90,
                        step=1,
                        label="Loyalty",
                        info="How loyal the character is to friends/user"
                    )
                    
                    submissiveness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=40,
                        step=1,
                        label="Submissiveness",
                        info="How submissive vs dominant the character is"
                    )
                    
                    brattiness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=20,
                        step=1,
                        label="Brattiness",
                        info="How bratty or rebellious the character is"
                    )
                    
                    nurturing = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=60,
                        step=1,
                        label="Nurturing",
                        info="How caring and nurturing the character is"
                    )
                    
                # Hidden/Internal Traits
                with gr.Accordion("Internal States", visible=True, open=False):
                    loneliness = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=45,
                        step=1,
                        label="Loneliness",
                        info="How much the character experiences loneliness"
                    )
                    
                    boredom = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=30,
                        step=1,
                        label="Boredom",
                        info="How easily bored the character gets (increases with idle time)"
                    )
                    
                    nsfw_drive = gr.Slider(
                        minimum=0,
                        maximum=10,
                        value=3,
                        step=1,
                        label="NSFW Drive",
                        info="Level of NSFW content (higher values enable downbad mode)"
                    )
                    
                    attachment = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=50,
                        step=1,
                        label="Attachment",
                        info="How attached the character becomes to the user (develops over time)"
                    )
                    
                    emotion_volatility = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=40,
                        step=1,
                        label="Emotional Volatility",
                        info="How quickly the character's emotions change"
                    )
                
                # Saving Preset Settings
                gr.Markdown("## Saving Settings")
                with gr.Row():
                    save_preset_btn = gr.Button("💾 Save Settings as Preset")
                    preset_name = gr.Textbox(
                        label="Preset Name",
                        placeholder="My Custom Settings"
                    )
                
                with gr.Row():
                    load_preset_dropdown = gr.Dropdown(
                        label="Load Preset",
                        choices=["Default", "Creative", "Professional", "Emotional", "Analytical", "Flirty", "Shy", "Cheerful", "Sassy"],
                        value="Default"
                    )
                    load_preset_btn = gr.Button("📂 Load Preset")
                    
        # Add CSS for tooltips
        gr.HTML("""
        <style>
        /* Tooltip styling */
        .tooltip-holder {
            position: relative;
            display: inline-block;
        }
        
        .gradio-slider input[type="range"],
        .gradio-checkbox input[type="checkbox"],
        .gradio-dropdown select,
        .gradio-textbox textarea,
        .gradio-radio input[type="radio"],
        .gradio-number input[type="number"] {
            position: relative;
        }
        
        .gradio-slider:hover::after,
        .gradio-checkbox:hover::after,
        .gradio-dropdown:hover::after,
        .gradio-textbox:hover::after,
        .gradio-radio:hover::after,
        .gradio-number:hover::after {
            content: attr(data-info);
            position: absolute;
            z-index: 1000;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 14px;
            width: 250px;
            top: -25px;
            left: 50%;
            transform: translateX(-50%);
            pointer-events: none;
        }
        </style>
        
        <script>
        // Add tooltip functionality to all components with info attributes
        document.addEventListener('DOMContentLoaded', function() {
            setTimeout(function() {
                document.querySelectorAll('.gradio-slider, .gradio-checkbox, .gradio-dropdown, .gradio-textbox, .gradio-radio, .gradio-number').forEach(function(el) {
                    const infoLabel = el.querySelector('.info-text');
                    if (infoLabel) {
                        const infoText = infoLabel.textContent;
                        el.setAttribute('data-info', infoText);
                        infoLabel.style.display = 'none';
                    }
                });
            }, 1000);
        });
        </script>
        """)
        
        # Return all the UI components for connecting callbacks
        return {
            "generation": {
                "temperature": temperature,
                "dynamic_temp": dynamic_temp,
                "response_tokens": response_tokens,
                "context_tokens": context_tokens,
                "rep_penalty": rep_penalty,
                "ban_eos": ban_eos,
                "auto_max_tokens": auto_max_tokens,
                "top_k": top_k,
                "top_p": top_p,
                "typical_p": typical_p,
                "min_p": min_p,
                "top_a": top_a,
                "tfs": tfs,
                "smoothing_factor": smoothing_factor,
                "smoothing_curve": smoothing_curve,
                "guidance_scale": guidance_scale,
                "negative_prompt": negative_prompt,
                "grammar_file": grammar_file,
                "seed": seed,
                "spicy_model": spicy_model,
                "sampler_priority": sampler_priority,
                "dry_run": dry_run,
                "xtc": xtc,
                "mirostat_mode": mirostat_mode,
                "mirostat_tau": mirostat_tau,
                "mirostat_eta": mirostat_eta,
                "token_bans": token_bans
            },
            "personality": {
                "happiness": happiness,
                "sadness": sadness,
                "anger": anger,
                "fear": fear,
                "surprise": surprise,
                "curiosity": curiosity,
                "trust": trust,
                "empathy": empathy,
                "confidence": confidence,
                "shyness": shyness,
                "playfulness": playfulness,
                "seriousness": seriousness,
                "kindness": kindness,
                "creativity": creativity,
                "romance": romance,
                "sass": sass,
                "loyalty": loyalty,
                "submissiveness": submissiveness,
                "brattiness": brattiness,
                "nurturing": nurturing,
                "loneliness": loneliness,
                "boredom": boredom,
                "nsfw_drive": nsfw_drive,
                "attachment": attachment,
                "emotion_volatility": emotion_volatility
            },
            "controls": {
                "evolving_personality": evolving_personality,
                "floating_assistant": floating_assistant,
                "user_telegram": user_telegram,
                "schedule_awareness": schedule_awareness,
                "save_preset_btn": save_preset_btn,
                "preset_name": preset_name,
                "load_preset_dropdown": load_preset_dropdown,
                "load_preset_btn": load_preset_btn
            }
        }

# ...existing code...

def create_texting_tab():
    """Create the texting module tab that uses only TT Models"""
    with gr.Tab("Texting"):
        with gr.Row():
            with gr.Column(scale=3):
                # Get available texting models
                from modules.model_loader import get_model_loader
                model_loader = get_model_loader()
                
                # Get only TT Models
                texting_models = model_loader.get_models(min_size_gb=0.01, texting_only=True)
                model_names = list(texting_models.keys())
                
                # Create model selection
                texting_model_dropdown = gr.Dropdown(
                    choices=model_names,
                    label="Select Texting Model",
                    value=model_names[0] if model_names else "",
                    info="Choose a model for texting from TT Models folder",
                    render=True,
                    interactive=True
                )
                
                refresh_texting_btn = gr.Button("🔄 Refresh Texting Models")
                
            with gr.Column(scale=4):
                # Chat interface
                chat_history = gr.Chatbot(
                    label="Chat",
                    height=500,
                    show_label=False
                )
                
                with gr.Row():
                    message_input = gr.Textbox(
                        label="Message",
                        placeholder="Type your message here...",
                        lines=3,
                        show_label=False
                    )
                    send_btn = gr.Button("Send")
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat")
                    save_chat_btn = gr.Button("Save Chat")
                    
        # Function to refresh texting models
        def refresh_texting_models():
            texting_models = model_loader.get_models(force_refresh=True, min_size_gb=0.01, texting_only=True)
            model_names = list(texting_models.keys())
            return gr.Dropdown.update(choices=model_names, value=model_names[0] if model_names else "")
            
        # Function to send message
        def send_message(model_path, history, message):
            if not model_path:
                history.append((message, "Please select a texting model first."))
                return history, ""
                
            if not message.strip():
                return history, ""
                
            # Add user message to history
            history.append((message, ""))
            
            try:
                # Check if the model is loaded, if not load it
                from modules.model import get_model, load_model, ModelConfig, is_model_loaded
                
                current_model = get_model()
                if not is_model_loaded() or (current_model and current_model.model_config.model_path != model_path):
                    # Load the selected model
                    config = ModelConfig(
                        model_name=os.path.basename(model_path),
                        model_path=model_path,
                        context_size=4096,
                        gpu_layers=40,  # Default value, can be adjusted
                        threads=4,
                        n_batch=512
                    )
                    
                    success = load_model(config)
                    if not success:
                        history[-1] = (message, "Failed to load the texting model.")
                        return history, ""
                        
                # Get the model instance
                model = get_model()
                
                # Process special phrase
                if message.lower().strip() == "frogger frogger frogger":
                    # Get personality state
                    from modules.personality import get_personality_manager
                    pm = get_personality_manager()
                    traits = pm.get_all_traits()
                    
                    # Format traits as a response
                    response = "🔒 **Hidden Attributes** 🔒\n\n"
                    for category, items in traits.items():
                        response += f"**{category.title()}**:\n"
                        for trait, value in items.items():
                            response += f"- {trait.replace('_', ' ').title()}: {value}\n"
                        response += "\n"
                        
                    history[-1] = (message, response)
                    return history, ""
                
                # Generate response
                messages = [{"role": "user", "content": message}]
                
                # Check for existing conversation history
                if len(history) > 1:
                    # Add some context from previous messages
                    context_messages = []
                    for i in range(max(0, len(history)-5), len(history)-1):
                        user_msg, bot_msg = history[i]
                        if user_msg:
                            context_messages.append({"role": "user", "content": user_msg})
                        if bot_msg:
                            context_messages.append({"role": "assistant", "content": bot_msg})
                    
                    messages = context_messages + messages
                
                # Get response from model
                from modules.api.chat import chat_completion
                response_data, status_code = chat_completion(messages, model)
                
                if status_code == 200 and "response" in response_data:
                    response = response_data["response"]
                else:
                    response = f"Error: {response_data.get('error', 'Unknown error')}"
                
                # Update history with response
                history[-1] = (message, response)
                return history, ""
                
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                history[-1] = (message, error_msg)
                return history, ""
                
        # Function to clear chat
        def clear_chat():
            return [], ""
            
        # Function to save chat
        def save_chat(history):
            try:
                import time
                import json
                import os
                
                # Create chats directory if it doesn't exist
                chats_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chats")
                os.makedirs(chats_dir, exist_ok=True)
                
                # Create chat file with timestamp
                timestamp = int(time.time())
                chat_file = os.path.join(chats_dir, f"chat_{timestamp}.json")
                
                # Format history as JSON
                chat_data = []
                for user_msg, bot_msg in history:
                    chat_data.append({"user": user_msg, "assistant": bot_msg})
                    
                with open(chat_file, 'w', encoding='utf-8') as f:
                    json.dump(chat_data, f, indent=2)
                    
                return f"Chat saved to {chat_file}"
                
            except Exception as e:
                return f"Error saving chat: {str(e)}"
                
        # Connect UI components
        refresh_texting_btn.click(refresh_texting_models, inputs=[], outputs=[texting_model_dropdown])
        
        send_btn.click(
            send_message,
            inputs=[texting_model_dropdown, chat_history, message_input],
            outputs=[chat_history, message_input]
        )
        
        message_input.submit(
            send_message,
            inputs=[texting_model_dropdown, chat_history, message_input],
            outputs=[chat_history, message_input]
        )
        
        clear_btn.click(clear_chat, inputs=[], outputs=[chat_history, message_input])
        
        save_chat_result = gr.Textbox(label="Save Result", visible=False)
        save_chat_btn.click(save_chat, inputs=[chat_history], outputs=[save_chat_result])
        
        return {
            "model_dropdown": texting_model_dropdown,
            "chat_history": chat_history,
            "message_input": message_input
        }

# ...existing code...

def create_telegram_settings_ui():
    """Create the Telegram notification settings UI"""
    with gr.Accordion("Telegram Notifications", open=False):
        with gr.Row():
            enable_telegram = gr.Checkbox(
                label="Enable Telegram Notifications",
                value=False,
                info="Allow the assistant to send notifications to your Telegram"
            )
        
        with gr.Row():
            api_token = gr.Textbox(
                label="Telegram Bot API Token",
                placeholder="Enter your Telegram bot API token",
                type="password",
                info="Create a bot with @BotFather and paste the token here"
            )
            
        with gr.Row():
            test_message = gr.Textbox(
                label="Test Message",
                placeholder="Enter a test message",
                value="Hello from Lyra Assistant!"
            )
            
            test_username = gr.Textbox(
                label="Your Telegram Username",
                placeholder="@username",
                info="Your Telegram username to receive notifications"
            )
            
        with gr.Row():
            save_btn = gr.Button("Save Settings", variant="primary")
            test_btn = gr.Button("Send Test Message")
            
        status_message = gr.Markdown("")
        
        # Load current settings
        from modules.telegram_notify import get_telegram_notifier
        notifier = get_telegram_notifier()
        
        # Update UI with current settings
        enable_telegram.value = notifier.enabled
        
        # Function to save settings
        def save_telegram_settings(enable, token, username):
            try:
                from modules.telegram_notify import get_telegram_notifier
                from modules.personality import get_personality_manager
                
                notifier = get_telegram_notifier()
                
                # Save the API token
                if token:
                    notifier.set_api_token(token)
                    
                # Enable/disable notifications
                notifier.enable(enable)
                
                # Save the username in personality manager
                if username:
                    pm = get_personality_manager()
                    if username.startswith('@'):
                        username = username[1:]
                    pm.set_telegram_username(username)
                    
                return "✅ Telegram settings saved successfully"
            except Exception as e:
                return f"❌ Error saving Telegram settings: {str(e)}"
        
        # Function to send test message
        def send_test_message(enable, token, username, message):
            try:
                if not enable:
                    return "❌ Telegram notifications are not enabled"
                    
                if not token:
                    return "❌ Please enter a Telegram bot API token"
                    
                if not username:
                    return "❌ Please enter your Telegram username"
                    
                if not message:
                    message = "Test message from Lyra Assistant"
                    
                from modules.telegram_notify import get_telegram_notifier
                
                notifier = get_telegram_notifier()
                
                # Temporarily set token if not saved
                if token != notifier.api_token:
                    notifier.set_api_token(token)
                    
                # Enable if not enabled
                was_enabled = notifier.enabled
                if not was_enabled:
                    notifier.enable(True)
                    
                # Send the message
                success = notifier.send_message(username, message)
                
                # Restore previous state if needed
                if not was_enabled:
                    notifier.enable(False)
                    
                if success:
                    return f"✅ Test message sent to {username}. Please check your Telegram!"
                else:
                    return "❌ Failed to send test message. Check the logs for details."
            except Exception as e:
                return f"❌ Error sending test message: {str(e)}"
        
        # Connect UI components
        save_btn.click(
            save_telegram_settings,
            inputs=[enable_telegram, api_token, test_username],
            outputs=[status_message]
        )
        
        test_btn.click(
            send_test_message,
            inputs=[enable_telegram, api_token, test_username, test_message],
            outputs=[status_message]
        )
        
        return {
            "enable_telegram": enable_telegram,
            "api_token": api_token,
            "test_username": test_username
        }

# ...existing code...

def create_main_ui():
    """Create the main UI"""
    with gr.Blocks(css="""
        .gradio-container {max-width: 1200px}
        .float-container {margin-bottom: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 5px;}
        .personality-controls {margin-top: 15px; padding-top: 10px; border-top: 1px solid #eee;}
    """) as interface:
        gr.Markdown("# Lyra Assistant")
        
        # Add evolving personality switch at the top level
        with gr.Row(elem_classes="float-container"):
            evolving_switch = gr.Checkbox(
                label="Enable Evolving Personality",
                value=False,
                info="Allow the assistant's personality to evolve based on interactions"
            )
            floating_switch = gr.Checkbox(
                label="Enable Floating Assistant",
                value=False,
                info="Allow the assistant to float around your screen when idle"
            )
        
        # Create tabs
        with gr.Tabs():
            # Models tab
            create_models_tab()
            
            # Chat tab
            chat_components = create_chat_tab()
            
            # Texting tab
            texting_components = create_texting_tab()
            
            # Chat settings tab
            settings_components = create_chat_settings_tab()
            
            # Image generation tab
            create_image_generation_tab()
            
            # TTS tab
            create_tts_tab()
            
            # Code generation tab
            create_code_generation_tab()
            
            # Memory tab
            create_memory_tab()
            
            # Help tab
            create_help_tab()
            
        # Telegram notification settings
        telegram_components = create_telegram_settings_ui()
        
        # Public sharing UI
        share_global_state = create_public_sharing_ui()
        
        # Function to handle evolving personality toggle
        def toggle_evolving_personality(enabled):
            try:
                from modules.personality import get_personality_manager
                pm = get_personality_manager()
                success = pm.enable_evolution(enabled)
                return success
            except Exception as e:
                logger.error(f"Error toggling evolving personality: {str(e)}")
                return False
        
        # Function to handle floating assistant toggle
        def toggle_floating_assistant(enabled):
            try:
                from modules.floating_assistant import get_floating_assistant
                fa = get_floating_assistant()
                success = fa.enable(enabled)
                return success
            except Exception as e:
                logger.error(f"Error toggling floating assistant: {str(e)}")
                return False
        
        # Connect the global toggles
        evolving_switch.change(
            toggle_evolving_personality,
            inputs=[evolving_switch],
            outputs=[]
        )
        
        floating_switch.change(
            toggle_floating_assistant,
            inputs=[floating_switch],
            outputs=[]
        )
        
        # Load initial state
        def load_initial_state():
            try:
                # Load personality evolution state
                from modules.personality import get_personality_manager
                pm = get_personality_manager()
                evolving_enabled = pm.evolving_enabled
                
                # Load floating assistant state
                from modules.floating_assistant import get_floating_assistant
                fa = get_floating_assistant()
                floating_enabled = fa.enabled
                
                return evolving_enabled, floating_enabled
            except Exception as e:
                logger.error(f"Error loading initial state: {str(e)}")
                return False, False
        
        # Set initial toggle states
        evolving_enabled, floating_enabled = load_initial_state()
        evolving_switch.value = evolving_enabled
        floating_switch.value = floating_enabled
        
        # Connect chat messages to personality system
        def on_chat_sent(message, response):
            try:
                if message and response:
                    from modules.personality import get_personality_manager
                    pm = get_personality_manager()
                    
                    # Record interaction
                    pm.interact()
                    
                    # Detect tone in user message
                    tone = pm.detect_tone(message)
                    
                    # Adjust traits based on tone
                    pm.adjust_traits_from_tone(tone)
                    
                    # Record interaction with floating assistant
                    from modules.floating_assistant import get_floating_assistant
                    fa = get_floating_assistant()
                    fa.interact()
            except Exception as e:
                logger.error(f"Error processing chat for personality: {str(e)}")
        
        # Connect chat events
        if hasattr(chat_components, "send_btn"):
            chat_components.send_btn.click(
                on_chat_sent,
                inputs=[chat_components.message_input, chat_components.chatbot],
                outputs=[]
            )
        
        return interface

# ...existing code...