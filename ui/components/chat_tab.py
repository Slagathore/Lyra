"""
Chat tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Tuple, Any

from .base import TabComponent

# Check Gradio version to handle compatibility
GRADIO_VERSION = getattr(gr, "__version__", "0.0.0")
IS_GRADIO_4_40_PLUS = tuple(map(int, GRADIO_VERSION.split("."))) >= (4, 40, 0)

class ChatTab(TabComponent):
    """Chat tab UI component"""
    
    def __init__(self, bot):
        super().__init__(bot)
        self.active_attachments = []
    
    def build(self):
        """Build the chat tab UI"""
        with gr.Row():
            with gr.Column(scale=3):
                # Create Chatbot with version-compatible parameters
                if IS_GRADIO_4_40_PLUS:
                    chatbot = gr.Chatbot(
                        height=600, 
                        label="Conversation",
                        info="Your conversation with the AI assistant appears here"
                    )
                else:
                    chatbot = gr.Chatbot(
                        height=600,
                        label="Conversation"
                    )
                    gr.Markdown("*Your conversation with the AI assistant appears here*")
                
                with gr.Row():
                    with gr.Column(scale=8):
                        # Apply same pattern to textbox
                        if IS_GRADIO_4_40_PLUS:
                            msg = gr.Textbox(
                                placeholder="Type your message here...", 
                                show_label=False,
                                lines=2,
                                info="Enter your message to the AI assistant here"
                            )
                        else:
                            msg = gr.Textbox(
                                placeholder="Type your message here...", 
                                show_label=False,
                                lines=2
                            )
                    
                    with gr.Column(scale=1):
                        with gr.Row():
                            send_btn = gr.Button("Send", variant="primary")
                            upload_btn = gr.UploadButton("📎", file_types=["text", ".txt", ".md"])
                
                attachments_list = gr.Dataframe(
                    headers=["Label", "ID", "Active"],
                    datatype=["str", "str", "bool"],
                    col_count=(3, "fixed"),
                    label="Active Attachments",
                    visible=False,
                    interactive=True
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### Chat Settings")
                
                model_dropdown = gr.Dropdown(
                    choices=[m.name for m in self.bot.model_manager.models], 
                    label="Model",
                    value=self._get_active_model_name(),
                )
                gr.Markdown("*Select which AI model to use for generating responses*")
                
                memory_dropdown = gr.Dropdown(
                    choices=self.bot.memory_manager.get_memory_names(), 
                    label="Memory",
                    value=self.bot.memory_manager.active_memory,
                )
                gr.Markdown("*Select a conversation history to continue or start a new one*")
                
                new_memory_name = gr.Textbox(
                    placeholder="New memory name", 
                    label="Create Memory",
                )
                gr.Markdown("*Enter a name for a new conversation history*")
                
                create_memory_btn = gr.Button("Create")
                
                include_profile = gr.Checkbox(label="Include User Profile", value=True)
                include_system = gr.Checkbox(label="Include System Instructions", value=True)
                include_extras = gr.Checkbox(label="Include Context Extras", value=True)
                
                with gr.Accordion("Generation Settings", open=False):
                    temperature = gr.Slider(0.0, 2.0, value=0.8, label="Temperature")
                    top_p = gr.Slider(0.0, 1.0, value=0.95, label="Top P")
                    top_k = gr.Slider(0, 100, value=40, step=1, label="Top K")
                    repetition_penalty = gr.Slider(1.0, 2.0, value=1.06, label="Repetition Penalty")
                    max_tokens = gr.Slider(32, 4096, value=512, step=32, label="Max Tokens")
                    
                    if self.bot.model_manager.get_active_model() and self.bot.model_manager.get_active_model().num_experts:
                        num_experts = gr.Slider(1, 8, value=self.bot.model_manager.get_active_model().num_experts, 
                                              step=1, label="Number of Experts (MOE models)")
                    
                    with gr.Row():
                        clear_btn = gr.Button("Clear Chat")
                        regen_btn = gr.Button("Regenerate")
                
                with gr.Accordion("Voice Input/Output", open=False):
                    voice_input_btn = gr.Button("Voice Input")
                    voice_output_toggle = gr.Checkbox(label="Enable Voice Output", value=False)
        
        # Store elements for later access
        self.elements.update({
            "chatbot": chatbot,
            "msg": msg,
            "send_btn": send_btn,
            "upload_btn": upload_btn,
            "attachments_list": attachments_list,
            "model_dropdown": model_dropdown,
            "memory_dropdown": memory_dropdown,
            "new_memory_name": new_memory_name,
            "create_memory_btn": create_memory_btn,
            "include_profile": include_profile,
            "include_system": include_system,
            "include_extras": include_extras,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty,
            "max_tokens": max_tokens,
            "clear_btn": clear_btn,
            "regen_btn": regen_btn,
            "voice_input_btn": voice_input_btn,
            "voice_output_toggle": voice_output_toggle
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Upload button handler
        e["upload_btn"].upload(
            fn=self._on_attachment_upload,
            inputs=[e["upload_btn"]],
            outputs=[e["attachments_list"]]
        ).then(
            fn=lambda: True,
            outputs=[e["attachments_list"]],
            js="(x) => {document.getElementById(x.id).style.display = 'block'; return true}"
        )
        
        # Send button handler
        e["send_btn"].click(
            fn=self._on_chat_send,
            inputs=[
                e["msg"], e["chatbot"], e["temperature"], e["top_p"], e["top_k"], 
                e["repetition_penalty"], e["max_tokens"], e["include_profile"],
                e["include_system"], e["include_extras"], e["attachments_list"]
            ],
            outputs=[e["msg"], e["chatbot"]]
        )
        
        # Model dropdown handler
        e["model_dropdown"].change(
            fn=self._on_model_change,
            inputs=[e["model_dropdown"]],
            outputs=[e["chatbot"]]
        )
        
        # Memory dropdown handler
        e["memory_dropdown"].change(
            fn=self._on_memory_change,
            inputs=[e["memory_dropdown"]],
            outputs=[e["chatbot"]]
        )
        
        # Create memory button handler
        e["create_memory_btn"].click(
            fn=self._on_create_memory,
            inputs=[e["new_memory_name"]],
            outputs=[e["memory_dropdown"], e["new_memory_name"]]
        )
        
        # Clear button handler
        e["clear_btn"].click(
            fn=self._on_clear_chat,
            inputs=[],
            outputs=[e["chatbot"], e["attachments_list"]]
        ).then(
            fn=lambda: False,
            outputs=[e["attachments_list"]],
            js="(x) => {document.getElementById(x.id).style.display = 'none'; return false}"
        )
        
        # Voice input button handler
        e["voice_input_btn"].click(
            fn=self._on_voice_input,
            inputs=[],
            outputs=[e["msg"]]
        )
    
    def _get_active_model_name(self):
        """Get the name of the currently active model"""
        active_model = self.bot.model_manager.get_active_model()
        return active_model.name if active_model else "No model loaded"
    
    def _on_attachment_upload(self, file):
        """Handle uploading an attachment during chat"""
        if not file:
            return self._get_attachments_data()
            
        attachment_id = self.bot.context_manager.add_attachment(file.name, Path(file.name).name)
        
        if attachment_id:
            self.active_attachments.append({
                "id": attachment_id,
                "label": Path(file.name).name,
                "active": True
            })
        return self._get_attachments_data()
    
    def _get_attachments_data(self):
        """Get data for the attachments list"""
        data = []
        for attachment in self.active_attachments:
            data.append([
                attachment["label"],
                attachment["id"],
                attachment.get("active", True)
            ])
        return data
    
    def _on_chat_send(self, message, history, temp, top_p, top_k, rep_pen, 
                     max_tokens, include_profile, include_system, include_extras,
                     attachments_data):
        """Handle sending a message with all context options"""
        if not message.strip():
            return "", history
        
        # Add user message to history
        history.append((message, ""))
        
        # Get active model
        model = self.bot.model_manager.get_active_model()
        if not model:
            return "", history + [(None, "No active model selected")]
        
        # Prepare generation config
        gen_config = {
            "temperature": temp,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": rep_pen,
            "max_tokens": max_tokens
        }
        
        # Get active attachment IDs
        active_attachment_ids = []
        if isinstance(attachments_data, list) and attachments_data:
            for row in attachments_data:
                if row and len(row) >= 3 and row[2]:  # If the "Active" column is True
                    active_attachment_ids.append(row[1])  # Add the ID
        
        # Get response from bot
        response = self.bot.chat(
            message=message,
            gen_config=gen_config,
            include_profile=include_profile,
            include_system_instructions=include_system,
            include_extras=include_extras,
            active_attachments=active_attachment_ids
        )
        
        # Update history with response
        history[-1] = (message, response)
        return "", history
    
    def _on_model_change(self, model_name):
        """Handle model change from dropdown"""
        # Unload previous model
        self.bot.unload_model()
        
        # Load new model
        success = self.bot.load_model(model_name)
        
        # Create empty chat history to return
        empty_history = []
        
        if not success:
            return empty_history + [(None, f"Failed to load model: {model_name}")]
        
        return empty_history
    
    def _on_memory_change(self, memory_name):
        """Handle changing the active memory"""
        if not memory_name:
            return []
        
        # Set active memory
        success = self.bot.memory_manager.set_active_memory(memory_name)
        
        if not success:
            return []
        
        # Get messages from the selected memory
        messages = self.bot.memory_manager.get_active_memory_messages()
        
        # Format messages for chatbot display
        chat_history = []
        for msg in messages:
            if msg["role"] == "user":
                # Start a new pair with the user's message
                chat_history.append([msg["content"], ""])
            elif msg["role"] == "assistant" and chat_history:
                # Complete the last pair with the assistant's response
                chat_history[-1][1] = msg["content"]
        
        return chat_history
    
    def _on_create_memory(self, memory_name):
        """Handle creating a new memory"""
        if not memory_name:
            return self.bot.memory_manager.get_memory_names(), ""
        
        # Create the new memory
        success = self.bot.memory_manager.create_memory(memory_name)
        
        if not success:
            # Memory name might already exist
            return self.bot.memory_manager.get_memory_names(), memory_name
        
        # Return updated memory list and clear the input
        return self.bot.memory_manager.get_memory_names(), ""
    
    def _on_clear_chat(self):
        """Handle clearing the chat"""
        self.active_attachments = []
        # Clear chat history
        if self.bot.memory_manager.active_memory:
            self.bot.memory_manager.memories[self.bot.memory_manager.active_memory] = []
            self.bot.memory_manager._save_memory(self.bot.memory_manager.active_memory)
        return [], []
    
    def _on_voice_input(self):
        """Handle voice input button press"""
        # This is a placeholder for voice input functionality
        # In a real implementation, this would record audio and convert to text
        return "Voice input is not yet implemented"
