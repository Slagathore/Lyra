"""
OCR tab UI component
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from .base import TabComponent

class OCRTab(TabComponent):
    """OCR tab UI component"""
    
    def build(self):
        """Build the OCR tab"""
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Optical Character Recognition")
                gr.Markdown("Upload an image containing text to extract its content")
                
                image_input = gr.Image(label="Upload Image", type="filepath")
                ocr_btn = gr.Button("Extract Text", variant="primary")
                
                text_output = gr.Textbox(label="Extracted Text", lines=10)
                ocr_status = gr.Markdown("")
        
        # Store elements for later access
        self.elements.update({
            "image_input": image_input,
            "ocr_btn": ocr_btn,
            "text_output": text_output,
            "ocr_status": ocr_status
        })
        
        # Set up event handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up event handlers for this tab"""
        e = self.elements
        
        # OCR button handler
        e["ocr_btn"].click(
            fn=self._on_ocr_extract,
            inputs=[e["image_input"]],
            outputs=[e["text_output"], e["ocr_status"]]
        )
    
    def _on_ocr_extract(self, image_path):
        """Handle OCR text extraction"""
        if not image_path:
            return "Please upload an image containing text.", ""
        
        extracted_text = self.bot.ocr_extract(image_path)
        return extracted_text, "Text successfully extracted from image."
