import os
import sys
import time
import logging
import threading
import subprocess
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class FloatingAssistant:
    def __init__(self):
        self.enabled = False
        self.window = None
        self.process = None
        self.thread = None
        self.should_run = False
        self.position = (100, 100)
        self.size = (300, 400)
        self.opacity = 0.9
        self.can_float = True
        self.is_floating = False
        self.last_interaction_time = time.time()
        self.wait_time_before_float = 300  # 5 minutes of inactivity before floating
        
        # Load settings
        self.load_settings()
    
    def load_settings(self):
        """Load floating assistant settings"""
        try:
            settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            settings_file = os.path.join(settings_dir, "floating_settings.json")
            
            if os.path.exists(settings_file):
                import json
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                self.enabled = settings.get("enabled", False)
                self.position = tuple(settings.get("position", (100, 100)))
                self.size = tuple(settings.get("size", (300, 400)))
                self.opacity = settings.get("opacity", 0.9)
                self.can_float = settings.get("can_float", True)
                self.wait_time_before_float = settings.get("wait_time_before_float", 300)
                
                logger.info("Loaded floating assistant settings")
                
        except Exception as e:
            logger.error(f"Error loading floating assistant settings: {str(e)}")
    
    def save_settings(self):
        """Save floating assistant settings"""
        try:
            settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "floating_settings.json")
            
            settings = {
                "enabled": self.enabled,
                "position": self.position,
                "size": self.size,
                "opacity": self.opacity,
                "can_float": self.can_float,
                "wait_time_before_float": self.wait_time_before_float
            }
            
            import json
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            logger.info("Saved floating assistant settings")
            
        except Exception as e:
            logger.error(f"Error saving floating assistant settings: {str(e)}")
    
    def enable(self, state=True):
        """Enable or disable the floating assistant"""
        self.enabled = state
        
        if state and not self.is_running():
            self.start()
        elif not state and self.is_running():
            self.stop()
            
        self.save_settings()
        return self.enabled
    
    def is_running(self):
        """Check if the floating assistant is running"""
        return self.thread is not None and self.thread.is_alive()
    
    def start(self):
        """Start the floating assistant"""
        if self.is_running():
            logger.warning("Floating assistant is already running")
            return False
            
        try:
            self.should_run = True
            self.thread = threading.Thread(target=self._run_assistant, daemon=True)
            self.thread.start()
            logger.info("Started floating assistant")
            return True
        except Exception as e:
            logger.error(f"Error starting floating assistant: {str(e)}")
            return False
    
    def stop(self):
        """Stop the floating assistant"""
        if not self.is_running():
            logger.warning("Floating assistant is not running")
            return False
            
        try:
            self.should_run = False
            
            # Close the window if it exists
            if self.process and hasattr(self.process, 'terminate'):
                self.process.terminate()
                self.process = None
            
            # Wait for thread to end
            if self.thread:
                self.thread.join(timeout=1.0)
                self.thread = None
                
            logger.info("Stopped floating assistant")
            return True
        except Exception as e:
            logger.error(f"Error stopping floating assistant: {str(e)}")
            return False
    
    def _run_assistant(self):
        """Background thread function to run the floating assistant"""
        try:
            if sys.platform == 'win32':
                self._run_windows_assistant()
            elif sys.platform == 'darwin':
                self._run_macos_assistant()
            else:  # Linux and others
                self._run_linux_assistant()
        except Exception as e:
            logger.error(f"Error in floating assistant thread: {str(e)}")
    
    def _run_windows_assistant(self):
        """Run the floating assistant on Windows"""
        try:
            # Import Windows-specific modules
            import win32gui
            import win32con
            import win32api
            import pystray
            from PIL import Image, ImageDraw
            
            # Create a system tray icon for the assistant
            icon_image = self._create_tray_icon()
            icon = pystray.Icon("LyraAssistant", icon_image, "Lyra Assistant")
            
            # Define menu items
            def on_exit(icon, item):
                self.stop()
                icon.stop()
                
            def on_toggle_float(icon, item):
                self.can_float = not self.can_float
                self.save_settings()
                
            icon.menu = pystray.Menu(
                pystray.MenuItem("Toggle Floating", on_toggle_float, checked=lambda item: self.can_float),
                pystray.MenuItem("Exit", on_exit)
            )
            
            # Start the system tray icon in a separate thread
            icon_thread = threading.Thread(target=icon.run, daemon=True)
            icon_thread.start()
            
            # Main loop for floating window
            while self.should_run:
                current_time = time.time()
                if self.can_float and not self.is_floating and (current_time - self.last_interaction_time) > self.wait_time_before_float:
                    # Create floating window
                    self._create_floating_window()
                    self.is_floating = True
                    
                elif self.is_floating and ((current_time - self.last_interaction_time) <= self.wait_time_before_float or not self.can_float):
                    # Hide floating window
                    self._hide_floating_window()
                    self.is_floating = False
                    
                time.sleep(1)
                
            # Clean up
            if icon and icon_thread.is_alive():
                icon.stop()
                
        except Exception as e:
            logger.error(f"Error in Windows floating assistant: {str(e)}")
    
    def _run_macos_assistant(self):
        """Run the floating assistant on macOS"""
        logger.warning("macOS floating assistant not fully implemented")
        # Implementation would be similar to Windows but using macOS-specific APIs
        
        while self.should_run:
            time.sleep(1)
    
    def _run_linux_assistant(self):
        """Run the floating assistant on Linux"""
        logger.warning("Linux floating assistant not fully implemented")
        # Implementation would use GTK or other Linux UI toolkit
        
        while self.should_run:
            time.sleep(1)
    
    def _create_tray_icon(self):
        """Create an icon for the system tray"""
        try:
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw a circle
            draw.ellipse((4, 4, 60, 60), fill=(0, 120, 212))
            
            # Draw a simple face
            draw.ellipse((20, 20, 28, 28), fill=(255, 255, 255))  # Left eye
            draw.ellipse((36, 20, 44, 28), fill=(255, 255, 255))  # Right eye
            draw.arc((16, 32, 48, 48), 0, 180, fill=(255, 255, 255), width=2)  # Smile
            
            return image
            
        except Exception as e:
            logger.error(f"Error creating tray icon: {str(e)}")
            # Return a blank image if there's an error
            from PIL import Image
            return Image.new('RGBA', (64, 64), (0, 120, 212))
    
    def _create_floating_window(self):
        """Create the floating assistant window"""
        # This method would be platform-specific
        # For now, we'll use a placeholder implementation
        logger.info("Creating floating assistant window")
        
        try:
            if sys.platform == 'win32':
                # On Windows, we could use a transparent window with custom behavior
                script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                         "tools", "floating_window.py")
                
                if os.path.exists(script_path):
                    # Launch the floating window script as a separate process
                    self.process = subprocess.Popen([sys.executable, script_path, 
                                                  f"--x={self.position[0]}", 
                                                  f"--y={self.position[1]}",
                                                  f"--width={self.size[0]}",
                                                  f"--height={self.size[1]}",
                                                  f"--opacity={self.opacity}"])
                else:
                    logger.error(f"Floating window script not found: {script_path}")
            
        except Exception as e:
            logger.error(f"Error creating floating window: {str(e)}")
    
    def _hide_floating_window(self):
        """Hide the floating assistant window"""
        logger.info("Hiding floating assistant window")
        
        try:
            if self.process and hasattr(self.process, 'terminate'):
                self.process.terminate()
                self.process = None
                
        except Exception as e:
            logger.error(f"Error hiding floating window: {str(e)}")
    
    def interact(self):
        """Record user interaction"""
        self.last_interaction_time = time.time()
        
        # If currently floating, hide the window
        if self.is_floating:
            self._hide_floating_window()
            self.is_floating = False

# Global instance
_floating_assistant = None

def get_floating_assistant():
    """Get the global floating assistant instance"""
    global _floating_assistant
    if _floating_assistant is None:
        _floating_assistant = FloatingAssistant()
    return _floating_assistant
