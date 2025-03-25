"""
Memory tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class MemoryTab(TabComponent):
    """Memory tab UI component"""
    
    def build(self):
        """Build the memory management tab"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Memory Management")
                gr.Markdown("Create, rename, and delete conversation memories")
                
                memory_list = gr.Dropdown(
                    choices=self.bot.memory_manager.get_memory_names(),
                    value=self.bot.memory_manager.active_memory,
                    label="Available Memories"
                )
                
                with gr.Row():
                    new_memory_name = gr.Textbox(
                        placeholder="Name for new memory",
                        label="Create Memory"
                    )
                    
                    create_memory_btn = gr.Button("Create")
                
                with gr.Row():
                    set_active_btn = gr.Button("Set as Active")
                    delete_memory_btn = gr.Button("Delete Memory")
                
                memory_status = gr.Markdown("")
                
                gr.Markdown("### Memory Details")
                memory_content = gr.JSON(label="Memory Content")
                
                refresh_memory_btn = gr.Button("Refresh")
        
        # Store elements for later access
        self.elements.update({
            "memory_list": memory_list,
            "new_memory_name": new_memory_name,
            "create_memory_btn": create_memory_btn,
            "set_active_btn": set_active_btn,
            "delete_memory_btn": delete_memory_btn,
            "memory_status": memory_status,
            "memory_content": memory_content,
            "refresh_memory_btn": refresh_memory_btn
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Memory selection handler
        e["memory_list"].change(
            fn=self._on_memory_tab_select,
            inputs=[e["memory_list"]],
            outputs=[e["memory_content"]]
        )
        
        # Create memory button handler
        e["create_memory_btn"].click(
            fn=self._on_memory_tab_create,
            inputs=[e["new_memory_name"]],
            outputs=[e["memory_list"], e["new_memory_name"], e["memory_status"]]
        )
        
        # Set active memory button handler
        e["set_active_btn"].click(
            fn=self._on_memory_set_active,
            inputs=[e["memory_list"]],
            outputs=[e["memory_status"]]
        )
        
        # Delete memory button handler
        e["delete_memory_btn"].click(
            fn=self._on_memory_delete,
            inputs=[e["memory_list"]],
            outputs=[e["memory_list"], e["memory_content"], e["memory_status"]]
        )
        
        # Refresh button handler
        e["refresh_memory_btn"].click(
            fn=self._on_memory_refresh,
            outputs=[e["memory_list"], e["memory_content"]]
        )
    
    def _on_memory_tab_select(self, memory_name):
        """Handle memory selection in the memory tab"""
        if not memory_name:
            return []
        
        if memory_name not in self.bot.memory_manager.memories:
            return []
        
        return self.bot.memory_manager.memories[memory_name]
    
    def _on_memory_tab_create(self, memory_name):
        """Handle memory creation in the memory tab"""
        if not memory_name:
            return self.bot.memory_manager.get_memory_names(), "", "Please enter a name for the memory."
        
        success = self.bot.memory_manager.create_memory(memory_name)
        
        if success:
            return self.bot.memory_manager.get_memory_names(), "", f"Memory '{memory_name}' created successfully."
        else:
            return self.bot.memory_manager.get_memory_names(), memory_name, f"Memory '{memory_name}' already exists."
    
    def _on_memory_set_active(self, memory_name):
        """Set the active memory"""
        if not memory_name:
            return "Please select a memory to set as active."
        
        success = self.bot.memory_manager.set_active_memory(memory_name)
        
        if success:
            return f"Memory '{memory_name}' set as active."
        else:
            return f"Failed to set memory '{memory_name}' as active."
    
    def _on_memory_delete(self, memory_name):
        """Delete a memory"""
        if not memory_name:
            return self.bot.memory_manager.get_memory_names(), [], "Please select a memory to delete."
        
        success = self.bot.memory_manager.delete_memory(memory_name)
        
        if success:
            return self.bot.memory_manager.get_memory_names(), [], f"Memory '{memory_name}' deleted successfully."
        else:
            return self.bot.memory_manager.get_memory_names(), [], f"Failed to delete memory '{memory_name}'."
    
    def _on_memory_refresh(self):
        """Refresh memory list and active memory content"""
        memory_names = self.bot.memory_manager.get_memory_names()
        active_memory = self.bot.memory_manager.active_memory
        
        if active_memory and active_memory in self.bot.memory_manager.memories:
            memory_content = self.bot.memory_manager.memories[active_memory]
        else:
            memory_content = []
        
        return memory_names, memory_content
