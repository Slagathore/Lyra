"""
Video tab UI component with media integration
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class VideoTab(TabComponent):
    """Video tab UI component"""
    
    def build(self):
        """Build the video generation tab"""
        with gr.Tabs():
            with gr.TabItem("Text-to-Video"):
                self._build_text_to_video()
            
            with gr.TabItem("Media Composer"):
                self._build_media_composer()
    
    def _build_text_to_video(self):
        """Build the basic text-to-video generation section"""
        with gr.Row():
            with gr.Column():
                prompt = gr.Textbox(
                    placeholder="Describe the video you want to generate...",
                    label="Video Description",
                    lines=3
                )
                
                with gr.Row():
                    duration = gr.Slider(1, 30, value=5, step=1, label="Duration (seconds)")
                    model = gr.Dropdown(
                        choices=list(self.bot.video_handler.models.keys()),
                        value=self.bot.video_handler.active_model,
                        label="Video Model"
                    )
                
                generate_btn = gr.Button("Generate Video", variant="primary")
                
                video_output = gr.Video(label="Generated Video")
                video_status = gr.Markdown("")
        
        # Store elements for later access
        self.elements.update({
            "prompt": prompt,
            "duration": duration,
            "model": model,
            "generate_btn": generate_btn,
            "video_output": video_output,
            "video_status": video_status
        })
        
        # Set up event handlers
        generate_btn.click(
            fn=self._on_video_generate,
            inputs=[prompt, duration, model],
            outputs=[video_output, video_status]
        )
    
    def _build_media_composer(self):
        """Build the media composition section for combining assets"""
        with gr.Row():
            with gr.Column(scale=3):
                gr.Markdown("### Available Media Assets")
                
                # Assets selection area
                shared_assets = gr.Dataframe(
                    headers=["Name", "Type", "ID"],
                    label="Shared Assets",
                    interactive=True,
                    col_count=(3, "fixed")
                )
                
                refresh_assets_btn = gr.Button("Refresh Asset List")
                
                # Timeline and arrangement
                gr.Markdown("### Composition Timeline")
                
                with gr.Row():
                    timeline = gr.Dataframe(
                        headers=["Asset ID", "Start Time (s)", "Duration (s)", "Order"],
                        label="Timeline",
                        interactive=True,
                        col_count=(4, "fixed")
                    )
                
                with gr.Row():
                    add_to_timeline_btn = gr.Button("Add Selected to Timeline")
                    clear_timeline_btn = gr.Button("Clear Timeline")
                
                # Basic composition parameters
                with gr.Row():
                    transition = gr.Dropdown(
                        choices=["cut", "fade", "dissolve", "wipe"],
                        value="fade",
                        label="Transition Effect"
                    )
                    
                    background_audio = gr.Dropdown(
                        choices=self._get_audio_assets(),
                        label="Background Audio",
                        info="Optional audio to play throughout the composition"
                    )
                
                # Caption or description
                caption = gr.Textbox(
                    placeholder="Add a description or caption for the composed video...",
                    label="Video Caption/Description",
                    lines=2
                )
                
                compose_btn = gr.Button("Compose Video", variant="primary")
            
            with gr.Column(scale=2):
                composed_video = gr.Video(label="Composed Video")
                composition_status = gr.Markdown("")
                
                download_btn = gr.Button("Download Composed Video", interactive=False)
        
        # Store elements for later access
        self.elements.update({
            "shared_assets": shared_assets,
            "refresh_assets_btn": refresh_assets_btn,
            "timeline": timeline,
            "add_to_timeline_btn": add_to_timeline_btn,
            "clear_timeline_btn": clear_timeline_btn,
            "transition": transition,
            "background_audio": background_audio,
            "caption": caption,
            "compose_btn": compose_btn,
            "composed_video": composed_video,
            "composition_status": composition_status,
            "download_btn": download_btn
        })
        
        # Set up event handlers
        refresh_assets_btn.click(
            fn=self._on_refresh_assets,
            outputs=[shared_assets, background_audio]
        )
        
        add_to_timeline_btn.click(
            fn=self._on_add_to_timeline,
            inputs=[shared_assets, timeline],
            outputs=[timeline]
        )
        
        clear_timeline_btn.click(
            fn=lambda: [],
            outputs=[timeline]
        )
        
        compose_btn.click(
            fn=self._on_compose_video,
            inputs=[timeline, transition, background_audio, caption],
            outputs=[composed_video, composition_status, download_btn]
        )
        
        # Initialize with current assets
        self._on_refresh_assets()
    
    def _on_video_generate(self, prompt, duration, model):
        """Handle video generation"""
        if not prompt:
            return None, "Please provide a description of the video you want to generate."
        
        video_path = self.bot.generate_video(prompt, duration, model)
        
        if not video_path:
            return None, "Failed to generate video. Please try again."
        
        # Add to assets manager
        self.bot.asset_manager.add_asset("video", video_path, prompt)
        
        return video_path, f"Video generated successfully from prompt: '{prompt[:50]}...'"
    
    def _on_refresh_assets(self):
        """Refresh the list of available assets"""
        # Get all shared assets
        assets = self.bot.asset_manager.get_shared_assets()
        
        # Format for dataframe
        assets_data = []
        for asset in assets:
            assets_data.append([
                asset["name"],
                asset["type"],
                asset["id"]
            ])
        
        # Get audio assets for background dropdown
        audio_assets = self._get_audio_assets()
        
        return assets_data, audio_assets
    
    def _get_audio_assets(self):
        """Get list of audio assets for background selection"""
        # Get audio-only assets
        audio_assets = self.bot.asset_manager.get_assets_by_types(["audio"])
        return audio_assets
    
    def _on_add_to_timeline(self, assets_df, current_timeline):
        """Add selected assets to the timeline"""
        if not isinstance(assets_df, list) or not assets_df:
            return current_timeline
        
        # Process selected rows from assets dataframe
        new_timeline = current_timeline.copy() if isinstance(current_timeline, list) else []
        
        # Create a default order based on current timeline length
        next_order = len(new_timeline) + 1
        
        # For each selected asset in the UI
        for row in assets_df:
            if row and len(row) >= 3:  # If the row has the expected format
                asset_id = row[2]  # The ID is in the third column
                
                # Determine reasonable defaults based on asset type
                asset_info = self.bot.asset_manager.get_asset_info(asset_id)
                if asset_info:
                    asset_type = asset_info["type"]
                    
                    # Default duration based on type
                    if asset_type == "image":
                        duration = 5.0  # 5 seconds for images
                    elif asset_type == "audio":
                        duration = asset_info.get("duration", 10.0)  # Audio duration or default
                    elif asset_type == "video":
                        duration = asset_info.get("duration", 10.0)  # Video duration or default
                    elif asset_type == "3d_object":
                        duration = 8.0  # 8 seconds for 3D objects
                    else:
                        duration = 5.0  # Default for unknown types
                    
                    # Add to timeline with next sequential start time
                    start_time = 0.0
                    if new_timeline:
                        # Find the end of the last clip
                        last_start = 0.0
                        last_duration = 0.0
                        for item in new_timeline:
                            if len(item) >= 3:
                                item_start = float(item[1])
                                item_duration = float(item[2])
                                if item_start + item_duration > last_start + last_duration:
                                    last_start = item_start
                                    last_duration = item_duration
                        
                        start_time = last_start + last_duration
                    
                    new_timeline.append([asset_id, start_time, duration, next_order])
                    next_order += 1
        
        return new_timeline
    
    def _on_compose_video(self, timeline, transition, background_audio, caption):
        """Handle video composition from timeline assets"""
        if not timeline or not isinstance(timeline, list) or len(timeline) == 0:
            return None, "Please add assets to the timeline first.", False
        
        # Prepare timeline data for the composition engine
        composition_data = {
            "timeline": timeline,
            "transition": transition,
            "background_audio": background_audio,
            "caption": caption
        }
        
        # Call the composition engine
        result = self.bot.compose_video(composition_data)
        
        if not result or "video_path" not in result:
            return None, "Failed to compose video. Please check your timeline and try again.", False
        
        # Add to assets manager
        self.bot.asset_manager.add_asset("video", result["video_path"], caption or "Composed video")
        
        return result["video_path"], "Video composition completed successfully!", True
