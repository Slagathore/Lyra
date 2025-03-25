import os
import sys
import time
import logging
import threading
import random
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class Window3DRenderer:
    """Implements 3D window visualization for the floating assistant"""
    
    def __init__(self):
        self.enabled = False
        self.windows_info = []
        self.update_thread = None
        self.should_run = False
        self.last_update = 0
        self.update_interval = 0.5  # Update every 500ms
        
        # Position tracking
        self.assistant_position = (100, 100)
        self.assistant_target = (100, 100)
        self.motion_speed = 2.0  # Speed multiplier
        
        # Z-ordering of windows
        self.windows_z_order = []
        
        # UI properties
        self.perspective_angle = 15  # Degrees
        self.shadow_opacity = 0.5
        self.layer_spacing = 10  # Pixels between z layers
        self.transition_time = 0.3  # Seconds
        
        # Load settings
        self.load_settings()
    
    def load_settings(self):
        """Load 3D renderer settings"""
        try:
            settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            settings_file = os.path.join(settings_dir, "3d_renderer_settings.json")
            
            if os.path.exists(settings_file):
                import json
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                self.enabled = settings.get("enabled", False)
                self.perspective_angle = settings.get("perspective_angle", 15)
                self.shadow_opacity = settings.get("shadow_opacity", 0.5)
                self.layer_spacing = settings.get("layer_spacing", 10)
                self.motion_speed = settings.get("motion_speed", 2.0)
                
                logger.info("Loaded 3D renderer settings")
                
        except Exception as e:
            logger.error(f"Error loading 3D renderer settings: {str(e)}")
    
    def save_settings(self):
        """Save 3D renderer settings"""
        try:
            settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
            os.makedirs(settings_dir, exist_ok=True)
            settings_file = os.path.join(settings_dir, "3d_renderer_settings.json")
            
            settings = {
                "enabled": self.enabled,
                "perspective_angle": self.perspective_angle,
                "shadow_opacity": self.shadow_opacity,
                "layer_spacing": self.layer_spacing,
                "motion_speed": self.motion_speed
            }
            
            import json
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
            logger.info("Saved 3D renderer settings")
            
        except Exception as e:
            logger.error(f"Error saving 3D renderer settings: {str(e)}")
    
    def enable(self, state=True):
        """Enable or disable 3D window rendering"""
        self.enabled = state
        
        if state and not self.is_running():
            self.start()
        elif not state and self.is_running():
            self.stop()
            
        self.save_settings()
        return self.enabled
    
    def is_running(self):
        """Check if the 3D renderer is running"""
        return self.update_thread is not None and self.update_thread.is_alive()
    
    def start(self):
        """Start the 3D renderer"""
        if self.is_running():
            logger.warning("3D renderer is already running")
            return False
            
        try:
            self.should_run = True
            self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
            self.update_thread.start()
            logger.info("Started 3D renderer")
            return True
        except Exception as e:
            logger.error(f"Error starting 3D renderer: {str(e)}")
            return False
    
    def stop(self):
        """Stop the 3D renderer"""
        if not self.is_running():
            logger.warning("3D renderer is not running")
            return False
            
        try:
            self.should_run = False
            
            # Wait for thread to end
            if self.update_thread:
                self.update_thread.join(timeout=1.0)
                self.update_thread = None
                
            logger.info("Stopped 3D renderer")
            return True
        except Exception as e:
            logger.error(f"Error stopping 3D renderer: {str(e)}")
            return False
    
    def _update_loop(self):
        """Main update loop for 3D rendering"""
        try:
            while self.should_run:
                current_time = time.time()
                delta_time = current_time - self.last_update
                
                if delta_time >= self.update_interval:
                    # Update window information
                    self._update_windows_info()
                    
                    # Update assistant position (smooth movement)
                    self._update_assistant_position(delta_time)
                    
                    # Apply 3D transformation to windows
                    self._apply_3d_transforms()
                    
                    self.last_update = current_time
                
                # Small sleep to avoid excessive CPU usage
                time.sleep(0.01)
                
        except Exception as e:
            logger.error(f"Error in 3D renderer update loop: {str(e)}")
    
    def _update_windows_info(self):
        """Update information about open windows"""
        try:
            if sys.platform == 'win32':
                self._update_windows_info_win32()
            elif sys.platform == 'darwin':
                self._update_windows_info_darwin()
            else:  # Linux
                self._update_windows_info_linux()
        except Exception as e:
            logger.error(f"Error updating windows info: {str(e)}")
    
    def _update_windows_info_win32(self):
        """Update window information on Windows"""
        try:
            import win32gui
            import win32con
            
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                    rect = win32gui.GetWindowRect(hwnd)
                    title = win32gui.GetWindowText(hwnd)
                    
                    # Only include windows with a non-empty title and reasonable size
                    if title and rect[2] - rect[0] > 50 and rect[3] - rect[1] > 50:
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "rect": rect,
                            "active": hwnd == win32gui.GetForegroundWindow(),
                            "z_order": len(windows)  # Initial z-order based on enumeration
                        })
                return True
                
            windows = []
            win32gui.EnumWindows(enum_windows_callback, windows)
            
            # Update z-order based on window stacking
            foreground_window = win32gui.GetForegroundWindow()
            if foreground_window:
                # Move the active window to the front of the z-order
                for window in windows:
                    if window["hwnd"] == foreground_window:
                        window["z_order"] = 0
                    else:
                        window["z_order"] += 1
            
            # Update our window list
            self.windows_info = windows
            
        except Exception as e:
            logger.error(f"Error updating Windows window info: {str(e)}")
    
    def _update_windows_info_darwin(self):
        """Update window information on macOS"""
        # This would require pyobjc or another macOS-specific library
        logger.warning("macOS window detection not implemented yet")
        self.windows_info = []  # Empty for now
    
    def _update_windows_info_linux(self):
        """Update window information on Linux"""
        # This would require Python bindings for X11 or Wayland
        logger.warning("Linux window detection not implemented yet")
        self.windows_info = []  # Empty for now
    
    def _update_assistant_position(self, delta_time):
        """Update the assistant's position with smooth movement"""
        # Calculate direction and distance to target
        dx = self.assistant_target[0] - self.assistant_position[0]
        dy = self.assistant_target[1] - self.assistant_position[1]
        
        # Move towards target
        speed = self.motion_speed * delta_time * 100  # Scale by delta time and a factor
        distance = (dx**2 + dy**2)**0.5
        
        if distance > 1.0:  # Only move if we're not already very close
            move_x = dx * min(speed / distance, 1.0)
            move_y = dy * min(speed / distance, 1.0)
            
            self.assistant_position = (
                self.assistant_position[0] + move_x,
                self.assistant_position[1] + move_y
            )
    
    def _apply_3d_transforms(self):
        """Apply 3D transformations to windows based on assistant position"""
        if not self.windows_info:
            return
            
        # Sort windows by z-order (lower z_order = closer to camera)
        self.windows_info.sort(key=lambda w: w["z_order"])
        
        # Reset z-transformed positions
        for window in self.windows_info:
            window["transform"] = {
                "translate_x": 0,
                "translate_y": 0,
                "scale": 1.0,
                "rotation": 0,
                "opacity": 1.0
            }
            
        # Apply perspective and assistant influence
        for i, window in enumerate(self.windows_info):
            # Calculate distance from assistant to window center
            window_center_x = (window["rect"][0] + window["rect"][2]) / 2
            window_center_y = (window["rect"][1] + window["rect"][3]) / 2
            
            dx = self.assistant_position[0] - window_center_x
            dy = self.assistant_position[1] - window_center_y
            distance = (dx**2 + dy**2)**0.5
            
            # Normalize distance for effect calculation
            normalized_distance = min(1.0, distance / 1000)  # 1000px = max effect distance
            
            # Z-order based effects
            z_effect = i / max(1, len(self.windows_info) - 1)
            
            # Calculate transformations
            z_translate = self.layer_spacing * i  # Deeper z-layers get more offset
            perspective_scale = 1.0 - (z_effect * 0.1)  # Deeper layers appear smaller
            
            # Calculate x, y translation based on perspective and assistant position
            perspective_x = dx * z_effect * 0.01 * self.perspective_angle
            perspective_y = dy * z_effect * 0.01 * self.perspective_angle
            
            # Apply transformation
            window["transform"] = {
                "translate_x": perspective_x,
                "translate_y": perspective_y,
                "z_translate": z_translate,
                "scale": perspective_scale,
                "opacity": 1.0 - (z_effect * 0.2)  # Deeper layers more transparent
            }
    
    def set_assistant_target(self, x, y):
        """Set target position for assistant"""
        self.assistant_target = (x, y)
    
    def get_current_assistant_position(self):
        """Get current assistant position"""
        return self.assistant_position
    
    def get_window_transforms(self):
        """Get current window transformation data"""
        return [
            {
                "title": w["title"],
                "rect": w["rect"],
                "transform": w["transform"],
                "active": w["active"],
                "z_order": w["z_order"]
            }
            for w in self.windows_info
        ]
    
    def bring_window_to_front(self, window_title):
        """Bring a window with the given title to the front"""
        try:
            if sys.platform == 'win32':
                import win32gui
                
                # Find window by title
                for window in self.windows_info:
                    if window_title.lower() in window["title"].lower():
                        # Set foreground window
                        win32gui.SetForegroundWindow(window["hwnd"])
                        return True
                        
            # Other platforms would have their own implementations here
            
            return False
        except Exception as e:
            logger.error(f"Error bringing window to front: {str(e)}")
            return False
    
    def apply_transform_to_window(self, window_hwnd):
        """Apply stored transform data to a specific window (platform specific)"""
        if not self.enabled:
            return False
            
        try:
            if sys.platform == 'win32':
                # Find the window in our list
                transform_data = None
                for window in self.windows_info:
                    if window["hwnd"] == window_hwnd:
                        transform_data = window["transform"]
                        break
                
                if not transform_data:
                    return False
                
                # This would need actual Win32 API calls to modify window appearance
                # For now, we just log what we would do
                logger.debug(f"Would apply transform to window {window_hwnd}: {transform_data}")
                
            # Other platforms would have their own implementations
            
            return True
        except Exception as e:
            logger.error(f"Error applying window transform: {str(e)}")
            return False

# Global instance
_window_3d_renderer = None

def get_window_3d_renderer():
    """Get the global 3D window renderer instance"""
    global _window_3d_renderer
    if _window_3d_renderer is None:
        _window_3d_renderer = Window3DRenderer()
    return _window_3d_renderer
