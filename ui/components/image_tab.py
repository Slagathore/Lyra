"""
Image tab UI component with 3D object generation
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class ImageTab(TabComponent):
    """Image tab UI component"""
    
    def build(self):
        """Build the image generation tab"""
        with gr.Tabs():
            with gr.TabItem("2D Images"):
                self._build_image_generation()
            
            with gr.TabItem("3D Objects"):
                self._build_3d_generation()
            
            with gr.TabItem("Image Analysis"):
                self._build_image_analysis()
        
        # Add a section for sharing with other tabs
        with gr.Row():
            gr.Markdown("### Share with Video Tab")
            
            generated_assets = gr.Dropdown(
                choices=self._get_generated_assets(),
                label="Select Generated Asset",
                info="Choose an image or 3D object to send to the Video tab"
            )
            
            share_btn = gr.Button("Send to Video Tab", variant="primary")
            share_status = gr.Markdown("")
        
        # Store elements for asset sharing
        self.elements.update({
            "generated_assets": generated_assets,
            "share_btn": share_btn,
            "share_status": share_status
        })
        
        # Set up handler for sharing
        share_btn.click(
            fn=self._on_share_asset,
            inputs=[generated_assets],
            outputs=[share_status]
        )
    
    def _build_image_generation(self):
        """Build the 2D image generation section"""
        with gr.Row():
            with gr.Column(scale=3):
                prompt = gr.Textbox(
                    placeholder="Describe the image you want to generate...",
                    label="Image Description",
                    lines=3
                )
                
                with gr.Row():
                    width = gr.Slider(128, 1024, value=512, step=8, label="Width")
                    height = gr.Slider(128, 1024, value=512, step=8, label="Height")
                
                with gr.Row():
                    model = gr.Dropdown(
                        choices=list(self.bot.image_handler.models.keys()),
                        value=self.bot.image_handler.active_model,
                        label="Image Model"
                    )
                    
                    generate_btn = gr.Button("Generate Image", variant="primary")
                
                image_output = gr.Image(label="Generated Image", type="filepath")
                
                image_status = gr.Markdown("")
        
        # Store elements for later access
        self.elements.update({
            "prompt": prompt,
            "width": width,
            "height": height,
            "model": model,
            "generate_btn": generate_btn,
            "image_output": image_output,
            "image_status": image_status
        })
        
        # Set up event handler
        generate_btn.click(
            fn=self._on_image_generate,
            inputs=[prompt, width, height, model],
            outputs=[image_output, image_status, self.elements["generated_assets"]]
        )
    
    def _build_3d_generation(self):
        """Build the 3D object generation section"""
        with gr.Row():
            with gr.Column(scale=3):
                obj_prompt = gr.Textbox(
                    placeholder="Describe the 3D object you want to generate...",
                    label="3D Object Description",
                    lines=3
                )
                
                with gr.Row():
                    complexity = gr.Slider(1, 10, value=5, step=1, label="Complexity", 
                                         info="Higher values create more detailed objects but take longer")
                    
                    obj_format = gr.Dropdown(
                        choices=["glb", "obj", "fbx", "usdz"],
                        value="glb",
                        label="3D Format"
                    )
                
                with gr.Row():
                    style = gr.Dropdown(
                        choices=["realistic", "stylized", "lowpoly", "abstract"],
                        value="realistic",
                        label="Style"
                    )
                    
                    obj_generate_btn = gr.Button("Generate 3D Object", variant="primary")
                
                # 3D object viewer
                obj_output = gr.Model3D(label="Generated 3D Object")
                obj_preview = gr.Image(label="3D Preview Image", type="filepath")
                
                obj_status = gr.Markdown("")
                
                download_obj_btn = gr.Button("Download 3D Object")
        
        # Store elements for later access
        self.elements.update({
            "obj_prompt": obj_prompt,
            "complexity": complexity,
            "obj_format": obj_format,
            "style": style,
            "obj_generate_btn": obj_generate_btn,
            "obj_output": obj_output,
            "obj_preview": obj_preview,
            "obj_status": obj_status,
            "download_obj_btn": download_obj_btn
        })
        
        # Set up event handlers
        obj_generate_btn.click(
            fn=self._on_3d_generate,
            inputs=[obj_prompt, complexity, obj_format, style],
            outputs=[obj_output, obj_preview, obj_status, self.elements["generated_assets"]]
        )
        
        download_obj_btn.click(
            fn=self._on_download_3d,
            inputs=[obj_output],
            outputs=[obj_status]
        )
    
    def _build_image_analysis(self):
        """Build the image analysis section"""
        with gr.Row():
            with gr.Column():
                upload_image = gr.Image(label="Upload Image for Analysis", type="filepath")
                analyze_btn = gr.Button("Analyze Image")
                analysis_output = gr.Textbox(label="Image Analysis", lines=8)
        
        # Store elements for later access
        self.elements.update({
            "upload_image": upload_image,
            "analyze_btn": analyze_btn,
            "analysis_output": analysis_output
        })
        
        # Set up event handler
        analyze_btn.click(
            fn=self._on_image_analyze,
            inputs=[upload_image],
            outputs=[analysis_output]
        )
    
    def _on_image_generate(self, prompt, width, height, model):
        """Handle image generation"""
        if not prompt:
            return None, "Please provide a description of the image you want to generate.", self._get_generated_assets()
        
        image_path = self.bot.generate_image(prompt, width, height, model)
        
        if not image_path:
            return None, "Failed to generate image. Please try again.", self._get_generated_assets()
        
        # Add to assets manager
        self.bot.asset_manager.add_asset("image", image_path, prompt)
        
        return image_path, f"Image generated successfully from prompt: '{prompt[:50]}...'", self._get_generated_assets()
    
    def _on_3d_generate(self, prompt, complexity, format, style):
        """Handle 3D object generation"""
        if not prompt:
            return None, None, "Please provide a description of the 3D object you want to generate.", self._get_generated_assets()
        
        # Call to the 3D generation function (yet to be implemented in the bot)
        result = self.bot.generate_3d_object(prompt, complexity, format, style)
        
        if not result or "model_path" not in result:
            return None, None, "Failed to generate 3D object. Please try again.", self._get_generated_assets()
        
        # Add to assets manager
        self.bot.asset_manager.add_asset("3d_object", result["model_path"], prompt)
        
        return result["model_path"], result.get("preview_path"), f"3D object generated successfully: '{prompt[:50]}...'", self._get_generated_assets()
    
    def _on_download_3d(self, model_path):
        """Handle 3D object download"""
        if not model_path:
            return "No 3D model generated yet."
        
        # In a real implementation, this would trigger a download
        return f"Download started for {Path(model_path).name}"
    
    def _on_image_analyze(self, image_path):
        """Handle image analysis"""
        if not image_path:
            return "Please upload an image to analyze."
        
        analysis = self.bot.image_handler.analyze_image(image_path)
        return analysis
    
    def _get_generated_assets(self):
        """Get list of generated assets for sharing"""
        return self.bot.asset_manager.get_assets_by_types(["image", "3d_object"])
    
    def _on_share_asset(self, asset_id):
        """Share asset with the video tab"""
        if not asset_id:
            return "Please select an asset to share."
        
        success = self.bot.asset_manager.share_with_video_tab(asset_id)
        
        if success:
            return f"Asset successfully shared with the Video tab."
        else:
            return "Failed to share asset. Please try again."
