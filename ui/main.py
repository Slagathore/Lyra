"""
Main UI Controller for Lyra
"""
import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from model_config import ModelConfig, get_manager
from lyra_bot import LyraBot

# Import UI components
from .components.chat_tab import ChatTab
from .components.image_tab import ImageTab
from .components.voice_tab import VoiceTab
from .components.video_tab import VideoTab
from .components.ocr_tab import OCRTab
from .components.code_tab import CodeTab
from .components.smart_home_tab import SmartHomeTab
from .components.notes_tab import NotesTab
from .components.memory_tab import MemoryTab
from .components.model_tab import ModelTab
from .components.personality_tab import PersonalityTab
from .components.context_tab import ContextTab

# Check Gradio version to handle compatibility
GRADIO_VERSION = getattr(gr, "__version__", "0.0.0")
IS_GRADIO_4_40_PLUS = tuple(map(int, GRADIO_VERSION.split("."))) >= (4, 40, 0)

class LyraUI:
    """Main UI class for Lyra"""
    
    def __init__(self):
        self.bot = LyraBot()
        self.interface = None
        
        # Initialize tab components
        self.chat_tab = ChatTab(self.bot)
        self.image_tab = ImageTab(self.bot)
        self.voice_tab = VoiceTab(self.bot)
        self.video_tab = VideoTab(self.bot)
        self.ocr_tab = OCRTab(self.bot)
        self.code_tab = CodeTab(self.bot)
        self.smart_home_tab = SmartHomeTab(self.bot)
        self.notes_tab = NotesTab(self.bot)
        self.memory_tab = MemoryTab(self.bot)
        self.model_tab = ModelTab(self.bot)
        self.personality_tab = PersonalityTab(self.bot)
        self.context_tab = ContextTab(self.bot)
    
    def build_ui(self):
        """Build the Gradio interface"""
        with gr.Blocks(title="Lyra - Advanced AI Assistant") as interface:
            with gr.Row():
                gr.Markdown("# Lyra AI Assistant")
                with gr.Column(scale=1):
                    docs_btn = gr.Button("📚 Documentation", scale=0)
            
            with gr.Tabs():
                with gr.Tab("Chat"):
                    self.chat_tab.build()
                
                with gr.Tab("Images"):
                    self.image_tab.build()
                
                with gr.Tab("Voice"):
                    self.voice_tab.build()
                
                with gr.Tab("Video"):
                    self.video_tab.build()
                
                with gr.Tab("OCR"):
                    self.ocr_tab.build()
                
                with gr.Tab("Code Sandbox"):
                    self.code_tab.build()
                
                with gr.Tab("Smart Home"):
                    self.smart_home_tab.build()
                
                with gr.Tab("Notes"):
                    self.notes_tab.build()
                
                with gr.Tab("Memory"):
                    self.memory_tab.build()
                
                with gr.Tab("Models"):
                    self.model_tab.build()
                
                with gr.Tab("Personality"):
                    self.personality_tab.build()
                    
                with gr.Tab("Context & Profile"):
                    self.context_tab.build()
        
            # Add version info at the bottom
            with gr.Row():
                gr.Markdown(f"Running on Gradio {GRADIO_VERSION}")
        
            # Add handler for documentation button
            docs_btn.click(
                fn=self._open_documentation,
                inputs=[],
                outputs=[]
            )
        
        self.interface = interface
        return interface
    
    def _open_documentation(self):
        """Open the documentation folder"""
        docs_path = Path('G:/AI/Lyra/docs')
        if docs_path.exists():
            try:
                import webbrowser
                webbrowser.open(str(docs_path))
            except:
                pass
        else:
            print(f"Documentation folder not found at {docs_path}, creating...")
            docs_path.mkdir(exist_ok=True, parents=True)
            print("Documentation available at G:/AI/Lyra/docs")
