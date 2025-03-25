"""
Base component class for UI tabs
"""
import gradio as gr
from typing import Dict, List, Optional, Tuple, Any

class TabComponent:
    """Base class for tab components"""
    
    def __init__(self, bot):
        self.bot = bot
        self.elements = {}  # Dictionary to store UI elements
    
    def build(self):
        """Build the tab UI components"""
        # Implement in derived classes
        raise NotImplementedError("Derived classes must implement build()")
