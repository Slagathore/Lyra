"""
Context and Profile tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class ContextTab(TabComponent):
    """Context and Profile tab UI component"""
    
    def build(self):
        """Build the context and profile tab"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### System Instructions")
                gr.Markdown("These instructions guide Lyra's overall behavior")
                
                system_instructions = gr.Textbox(
                    value=self.bot.context_manager.get_system_instructions(),
                    lines=8,
                    label="System Instructions"
                )
                
                save_system_btn = gr.Button("Save System Instructions")
                system_status = gr.Markdown("")
                
                gr.Markdown("### User Profile")
                gr.Markdown("Tell Lyra about yourself for more personalized interactions")
                
                # Get current profile
                profile = self.bot.get_user_profile()
                
                user_name = gr.Textbox(
                    value=profile.get("name", ""),
                    label="Your Name"
                )
                
                # Convert interests list to string
                interests_str = ", ".join(profile.get("interests", []))
                
                user_interests = gr.Textbox(
                    value=interests_str,
                    label="Your Interests (comma separated)",
                    placeholder="AI, music, hiking, cooking..."
                )
                
                user_background = gr.Textbox(
                    value=profile.get("background", ""),
                    lines=4,
                    label="Your Background",
                    placeholder="Brief description of your background, occupation, etc."
                )
                
                communication_style = gr.Dropdown(
                    choices=["neutral", "casual", "formal", "technical", "friendly", "professional"],
                    value=profile.get("communication_style", "neutral"),
                    label="Preferred Communication Style"
                )
                
                save_profile_btn = gr.Button("Save User Profile")
                profile_status = gr.Markdown("")
            
            with gr.Column(scale=1):
                gr.Markdown("### Context Extras")
                gr.Markdown("Additional context used in conversations")
                
                context_extras = gr.Textbox(
                    value=self.bot.context_manager.get_context_extras(),
                    lines=8,
                    label="Additional Context",
                    placeholder="Domain-specific knowledge, preferences, or any other information you want Lyra to know..."
                )
                
                save_extras_btn = gr.Button("Save Context Extras")
                extras_status = gr.Markdown("")
                
                gr.Markdown("### Attachments")
                gr.Markdown("Reference files for Lyra to use")
                
                with gr.Row():
                    attachment_file = gr.File(
                        label="Upload Attachment",
                        file_types=["txt", "md", "pdf", "csv", "json"]
                    )
                    
                    attachment_label = gr.Textbox(
                        placeholder="Label for this attachment (optional)",
                        label="Attachment Label"
                    )
                
                add_attachment_btn = gr.Button("Add Attachment")
                attachment_status = gr.Markdown("")
                
                all_attachments = gr.Dataframe(
                    headers=["ID", "Label", "Path"],
                    label="Available Attachments",
                    interactive=False
                )
                
                refresh_attachments_btn = gr.Button("Refresh Attachments")
        
        # Store elements for later access
        self.elements.update({
            "system_instructions": system_instructions,
            "save_system_btn": save_system_btn,
            "system_status": system_status,
            "user_name": user_name,
            "user_interests": user_interests,
            "user_background": user_background,
            "communication_style": communication_style,
            "save_profile_btn": save_profile_btn,
            "profile_status": profile_status,
            "context_extras": context_extras,
            "save_extras_btn": save_extras_btn,
            "extras_status": extras_status,
            "attachment_file": attachment_file,
            "attachment_label": attachment_label,
            "add_attachment_btn": add_attachment_btn,
            "attachment_status": attachment_status,
            "all_attachments": all_attachments,
            "refresh_attachments_btn": refresh_attachments_btn
        })
        
        # Set up event handlers
        self._setup_handlers()
        
        # Initialize attachments list
        self._on_refresh_attachments()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # Save system instructions button handler
        e["save_system_btn"].click(
            fn=self._on_save_system_instructions,
            inputs=[e["system_instructions"]],
            outputs=[e["system_status"]]
        )
        
        # Save user profile button handler
        e["save_profile_btn"].click(
            fn=self._on_save_user_profile,
            inputs=[e["user_name"], e["user_interests"], e["user_background"], e["communication_style"]],
            outputs=[e["profile_status"]]
        )
        
        # Save context extras button handler
        e["save_extras_btn"].click(
            fn=self._on_save_context_extras,
            inputs=[e["context_extras"]],
            outputs=[e["extras_status"]]
        )
        
        # Add attachment button handler
        e["add_attachment_btn"].click(
            fn=self._on_add_attachment,
            inputs=[e["attachment_file"], e["attachment_label"]],
            outputs=[e["all_attachments"], e["attachment_status"], e["attachment_label"]]
        )
        
        # Refresh attachments button handler
        e["refresh_attachments_btn"].click(
            fn=self._on_refresh_attachments,
            outputs=[e["all_attachments"]]
        )
    
    def _on_save_system_instructions(self, instructions):
        """Save system instructions"""
        if not instructions:
            return "System instructions cannot be empty."
        
        success = self.bot.set_system_instructions(instructions)
        
        if success:
            return "System instructions saved successfully."
        else:
            return "Failed to save system instructions."
    
    def _on_save_user_profile(self, name, interests_str, background, communication_style):
        """Save user profile"""
        # Parse interests as a list
        interests = [i.strip() for i in interests_str.split(",") if i.strip()]
        
        # Create profile data
        profile = {
            "name": name,
            "interests": interests,
            "background": background,
            "communication_style": communication_style
        }
        
        success = self.bot.update_user_profile(**profile)
        
        if success:
            return "User profile saved successfully."
        else:
            return "Failed to save user profile."
    
    def _on_save_context_extras(self, extras):
        """Save context extras"""
        success = self.bot.set_context_extras(extras)
        
        if success:
            return "Context extras saved successfully."
        else:
            return "Failed to save context extras."
    
    def _on_add_attachment(self, file, label):
        """Add a new attachment"""
        if not file:
            return self._get_attachments_data(), "Please select a file to upload.", label
        
        file_path = file.name
        if not label:
            label = Path(file_path).name
        
        attachment_id = self.bot.context_manager.add_attachment(file_path, label)
        
        if attachment_id:
            return self._get_attachments_data(), f"Attachment '{label}' added successfully.", ""
        else:
            return self._get_attachments_data(), "Failed to add attachment.", label
    
    def _on_refresh_attachments(self):
        """Refresh the attachments list"""
        return self._get_attachments_data()
    
    def _get_attachments_data(self):
        """Get attachment data for display"""
        attachments = self.bot.context_manager.get_active_attachments()
        data = []
        
        for attachment in attachments:
            data.append([
                attachment.get("id", ""),
                attachment.get("label", ""),
                attachment.get("path", "")
            ])
        
        return data
