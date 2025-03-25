"""
Notes tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class NotesTab(TabComponent):
    """Notes tab UI component"""
    
    def build(self):
        """Build the notes management tab"""
        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("### Personal Notes")
                
                note_list = gr.Dropdown(
                    choices=self.bot.user_notes.get_note_names(),
                    label="Your Notes"
                )
                
                note_content = gr.Textbox(
                    placeholder="Note content will appear here...",
                    label="Note Content",
                    lines=15
                )
                
                with gr.Row():
                    refresh_notes_btn = gr.Button("Refresh List")
                    delete_note_btn = gr.Button("Delete Note")
                
                with gr.Row():
                    new_note_title = gr.Textbox(
                        placeholder="Title for new note",
                        label="New Note Title"
                    )
                    
                    new_note_btn = gr.Button("Create New Note")
            
            with gr.Column(scale=2):
                gr.Markdown("### Bot's Notes")
                gr.Markdown("Notes that the bot has saved for reference")
                
                bot_note_list = gr.Dropdown(
                    choices=self.bot.bot_notes.get_note_names(),
                    label="Bot's Notes"
                )
                
                bot_note_content = gr.Textbox(
                    placeholder="Bot note content will appear here...",
                    label="Bot Note Content",
                    lines=15,
                    interactive=False
                )
                
                refresh_bot_notes_btn = gr.Button("Refresh Bot Notes")
        
        # Store elements for later access
        self.elements.update({
            "note_list": note_list,
            "note_content": note_content,
            "refresh_notes_btn": refresh_notes_btn,
            "delete_note_btn": delete_note_btn,
            "new_note_title": new_note_title,
            "new_note_btn": new_note_btn,
            "bot_note_list": bot_note_list,
            "bot_note_content": bot_note_content,
            "refresh_bot_notes_btn": refresh_bot_notes_btn
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Load note content when a note is selected
        e["note_list"].change(
            fn=self._on_note_select,
            inputs=[e["note_list"]],
            outputs=[e["note_content"]]
        )
        
        # Load bot note content when a note is selected
        e["bot_note_list"].change(
            fn=self._on_bot_note_select,
            inputs=[e["bot_note_list"]],
            outputs=[e["bot_note_content"]]
        )
        
        # Refresh notes button handler
        e["refresh_notes_btn"].click(
            fn=self._on_refresh_notes,
            outputs=[e["note_list"]]
        )
        
        # Delete note button handler
        e["delete_note_btn"].click(
            fn=self._on_delete_note,
            inputs=[e["note_list"]],
            outputs=[e["note_list"], e["note_content"]]
        )
        
        # Create new note button handler
        e["new_note_btn"].click(
            fn=self._on_create_note,
            inputs=[e["new_note_title"], e["note_content"]],
            outputs=[e["note_list"], e["new_note_title"], e["note_content"]]
        )
        
        # Refresh bot notes button handler
        e["refresh_bot_notes_btn"].click(
            fn=self._on_refresh_bot_notes,
            outputs=[e["bot_note_list"]]
        )
    
    def _on_note_select(self, note_name):
        """Handle note selection"""
        if not note_name:
            return ""
        
        note_content = self.bot.user_notes.get_note(note_name)
        return note_content or ""
    
    def _on_bot_note_select(self, note_name):
        """Handle bot note selection"""
        if not note_name:
            return ""
        
        note_content = self.bot.bot_notes.get_note(note_name)
        return note_content or ""
    
    def _on_refresh_notes(self):
        """Refresh the list of user notes"""
        return self.bot.user_notes.get_note_names()
    
    def _on_refresh_bot_notes(self):
        """Refresh the list of bot notes"""
        return self.bot.bot_notes.get_note_names()
    
    def _on_delete_note(self, note_name):
        """Handle note deletion"""
        if not note_name:
            return self.bot.user_notes.get_note_names(), ""
        
        success = self.bot.user_notes.delete_note(note_name)
        
        if success:
            return self.bot.user_notes.get_note_names(), ""
        else:
            return self.bot.user_notes.get_note_names(), "Failed to delete note."
    
    def _on_create_note(self, title, content):
        """Handle note creation"""
        if not title or not content:
            return self.bot.user_notes.get_note_names(), title, content
        
        success = self.bot.save_user_note(title, content)
        
        if success:
            return self.bot.user_notes.get_note_names(), "", ""
        else:
            return self.bot.user_notes.get_note_names(), title, content
