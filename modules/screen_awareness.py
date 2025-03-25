"""
Screen Awareness module for Lyra
Allows Lyra to see and interact with content on the user's screen
"""

import os
import time
import json
import base64
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Set up logging
logger = logging.getLogger("screen_awareness")

class ScreenCapture:
    """Handles capturing and analyzing screen content"""
    
    def __init__(self, screenshot_dir: str = None):
        """Initialize screen capture module"""
        self.screenshot_dir = screenshot_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                           "data", "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        self.last_capture_time = 0
        self.last_screenshot_path = None
        self.active = False
        self.capture_frequency = 5  # seconds between captures in active mode
        
    def capture_screenshot(self) -> Optional[str]:
        """Capture a screenshot of the current screen"""
        try:
            # Try different screenshot methods depending on platform
            import platform
            system = platform.system()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"screen_{timestamp}.png")
            
            if system == "Windows":
                self._capture_windows(screenshot_path)
            elif system == "Darwin":  # macOS
                self._capture_macos(screenshot_path)
            elif system == "Linux":
                self._capture_linux(screenshot_path)
            else:
                logger.warning(f"Unsupported platform: {system}")
                return None
                
            self.last_screenshot_path = screenshot_path
            self.last_capture_time = time.time()
            
            logger.info(f"Screenshot captured: {screenshot_path}")
            return screenshot_path
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
    
    def _capture_windows(self, output_path: str) -> bool:
        """Capture screenshot on Windows"""
        try:
            # Try using PIL first
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(output_path)
            return True
        except ImportError:
            try:
                # Fallback to pyautogui
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(output_path)
                return True
            except ImportError:
                # Last resort - use native Windows API through subprocess
                import subprocess
                script = """
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $screen = [System.Windows.Forms.SystemInformation]::VirtualScreen
                $bitmap = New-Object System.Drawing.Bitmap $screen.Width, $screen.Height
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($screen.Left, $screen.Top, 0, 0, $bitmap.Size)
                $bitmap.Save('%s')
                """ % output_path
                subprocess.run(["powershell", "-Command", script], check=True)
                return True
    
    def _capture_macos(self, output_path: str) -> bool:
        """Capture screenshot on macOS"""
        import subprocess
        subprocess.run(["screencapture", "-x", output_path], check=True)
        return True
    
    def _capture_linux(self, output_path: str) -> bool:
        """Capture screenshot on Linux"""
        try:
            # Try using PIL first
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            screenshot.save(output_path)
            return True
        except ImportError:
            try:
                # Fallback to pyautogui
                import pyautogui
                screenshot = pyautogui.screenshot()
                screenshot.save(output_path)
                return True
            except ImportError:
                # Last resort - use scrot
                import subprocess
                subprocess.run(["scrot", output_path], check=True)
                return True
    
    def analyze_screen_content(self, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze screen content and return structured data
        Uses OCR and basic image analysis
        """
        path_to_analyze = screenshot_path or self.last_screenshot_path
        
        if not path_to_analyze or not os.path.exists(path_to_analyze):
            return {"error": "No screenshot available to analyze"}
        
        try:
            results = {
                "timestamp": time.time(),
                "screenshot_path": path_to_analyze,
                "text": self.extract_text_from_image(path_to_analyze),
                "ui_elements": self.detect_ui_elements(path_to_analyze),
                "windows": self.detect_application_windows(path_to_analyze)
            }
            
            return results
        except Exception as e:
            logger.error(f"Error analyzing screen content: {e}")
            return {"error": str(e), "screenshot_path": path_to_analyze}
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Try Tesseract OCR through pytesseract
            try:
                import pytesseract
                from PIL import Image
                
                img = Image.open(image_path)
                text = pytesseract.image_to_string(img)
                return text
            except ImportError:
                logger.warning("pytesseract not installed. Using placeholder OCR.")
                return "[OCR requires pytesseract package]"
        except Exception as e:
            logger.error(f"Error in OCR: {e}")
            return f"[OCR Error: {str(e)}]"
    
    def detect_ui_elements(self, image_path: str) -> List[Dict]:
        """Detect UI elements in the screenshot"""
        # This would use computer vision techniques to detect buttons, text fields, etc.
        # For now, return a placeholder
        return [{"type": "placeholder", "message": "UI element detection requires CV capabilities"}]
    
    def detect_application_windows(self, image_path: str) -> List[Dict]:
        """Detect application windows in the screenshot"""
        # In a real implementation, we would use platform-specific APIs to get window info
        try:
            import platform
            system = platform.system()
            
            if system == "Windows":
                return self._get_windows_app_info()
            elif system == "Darwin":
                return self._get_macos_app_info()
            elif system == "Linux":
                return self._get_linux_app_info()
            else:
                return [{"app": "unknown", "title": "Unsupported platform"}]
        except Exception as e:
            logger.error(f"Error detecting windows: {e}")
            return [{"error": str(e)}]
    
    def _get_windows_app_info(self) -> List[Dict]:
        """Get application window info on Windows"""
        try:
            import win32gui
            
            def callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    rect = win32gui.GetWindowRect(hwnd)
                    if rect[2] - rect[0] > 200 and rect[3] - rect[1] > 200:  # Only significant windows
                        window_text = win32gui.GetWindowText(hwnd)
                        if window_text:
                            windows.append({
                                "title": window_text,
                                "position": rect
                            })
                return True
            
            windows = []
            win32gui.EnumWindows(callback, windows)
            return windows
        except ImportError:
            return [{"title": "Win32GUI not available", "info": "Install pywin32 for window detection"}]
    
    def _get_macos_app_info(self) -> List[Dict]:
        """Get application window info on macOS"""
        try:
            import subprocess
            result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of every process whose visible is true'], 
                                   capture_output=True, text=True, check=True)
            apps = result.stdout.strip().split(', ')
            return [{"app": app} for app in apps]
        except Exception:
            return [{"app": "macOS app detection requires AppleScript permissions"}]
    
    def _get_linux_app_info(self) -> List[Dict]:
        """Get application window info on Linux"""
        try:
            import subprocess
            result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, check=True)
            windows = []
            for line in result.stdout.splitlines():
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    windows.append({"id": parts[0], "title": parts[3]})
            return windows
        except Exception:
            return [{"title": "Linux window detection requires wmctrl"}]
    
    def start_monitoring(self) -> bool:
        """Start continuous screen monitoring"""
        self.active = True
        return True
    
    def stop_monitoring(self) -> bool:
        """Stop continuous screen monitoring"""
        self.active = False
        return True
    
    def get_active_status(self) -> Dict[str, Any]:
        """Get current status of the screen monitor"""
        return {
            "active": self.active,
            "last_capture_time": self.last_capture_time,
            "capture_frequency": self.capture_frequency,
            "last_screenshot": self.last_screenshot_path
        }

class ScreenInteraction:
    """Allows Lyra to interact with elements on screen"""
    
    def __init__(self):
        self.can_interact = self._check_interaction_capability()
    
    def _check_interaction_capability(self) -> bool:
        """Check if screen interaction is possible"""
        try:
            import pyautogui
            return True
        except ImportError:
            logger.warning("PyAutoGUI not installed. Screen interaction disabled.")
            return False
    
    def click_position(self, x: int, y: int) -> bool:
        """Click at a specific screen position"""
        if not self.can_interact:
            return False
            
        try:
            import pyautogui
            pyautogui.click(x, y)
            return True
        except Exception as e:
            logger.error(f"Error clicking at position ({x}, {y}): {e}")
            return False
    
    def click_element(self, element_description: str, screenshot_path: str = None) -> bool:
        """
        Find and click a UI element based on description
        This would require sophisticated image recognition in a full implementation
        """
        # Placeholder implementation
        logger.warning("Element detection and clicking not implemented")
        return False
    
    def type_text(self, text: str) -> bool:
        """Type text at the current cursor position"""
        if not self.can_interact:
            return False
            
        try:
            import pyautogui
            pyautogui.write(text)
            return True
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False
    
    def press_key(self, key: str) -> bool:
        """Press a specific keyboard key"""
        if not self.can_interact:
            return False
            
        try:
            import pyautogui
            pyautogui.press(key)
            return True
        except Exception as e:
            logger.error(f"Error pressing key {key}: {e}")
            return False

class ScreenAwarenessModule:
    """Main module for screen awareness capabilities"""
    
    def __init__(self):
        self.capture = ScreenCapture()
        self.interaction = ScreenInteraction()
        self.enabled = False
        self.permission_granted = False
        self.last_analysis = None
        self.screen_history = []  # Keep track of recent screen states
        self.max_history = 10     # Maximum number of screen states to remember
    
    def request_permission(self) -> Dict[str, Any]:
        """Request permission to access the screen"""
        self.permission_granted = True  # In a real app, this would show a permission dialog
        return {
            "granted": self.permission_granted,
            "timestamp": time.time(),
            "message": "Permission granted for screen access"
        }
    
    def enable(self) -> bool:
        """Enable screen awareness"""
        if not self.permission_granted:
            self.request_permission()
            
        self.enabled = self.permission_granted
        if self.enabled:
            self.capture.start_monitoring()
        return self.enabled
    
    def disable(self) -> bool:
        """Disable screen awareness"""
        self.enabled = False
        self.capture.stop_monitoring()
        return True
    
    def get_current_screen_state(self, capture_new: bool = True) -> Dict[str, Any]:
        """Get the current state of the screen with analysis"""
        if not self.enabled:
            return {"error": "Screen awareness is not enabled"}
            
        try:
            screenshot_path = None
            if capture_new:
                screenshot_path = self.capture.capture_screenshot()
                
            analysis = self.capture.analyze_screen_content(screenshot_path)
            self.last_analysis = analysis
            
            # Add to history and trim if needed
            self.screen_history.append({
                "timestamp": time.time(),
                "analysis": analysis
            })
            
            if len(self.screen_history) > self.max_history:
                self.screen_history = self.screen_history[-self.max_history:]
                
            return analysis
        except Exception as e:
            logger.error(f"Error getting screen state: {e}")
            return {"error": str(e)}
    
    def describe_screen(self, detailed: bool = False) -> str:
        """Generate a natural language description of what's on screen"""
        if not self.enabled:
            return "I don't currently have permission to see your screen."
            
        try:
            screen_state = self.get_current_screen_state()
            
            if "error" in screen_state:
                return f"I couldn't analyze your screen: {screen_state['error']}"
                
            # Basic description
            description = "I can see your screen. "
            
            # Add text found on screen
            if screen_state.get("text"):
                text = screen_state["text"].strip()
                if len(text) > 500 and not detailed:
                    text_preview = text[:500] + "..."
                    description += f"I can see some text, including: \"{text_preview}\". "
                elif text:
                    description += f"I can see the following text: \"{text}\". "
                else:
                    description += "I don't see any text on your screen. "
            
            # Add info about application windows if available
            if screen_state.get("windows") and isinstance(screen_state["windows"], list):
                if len(screen_state["windows"]) > 0:
                    window_names = [w.get("title", w.get("app", "")) for w in screen_state["windows"] if w.get("title") or w.get("app")]
                    if window_names:
                        if len(window_names) <= 3 or detailed:
                            description += f"I can see the following windows: {', '.join(window_names)}. "
                        else:
                            description += f"I can see {len(window_names)} windows, including {', '.join(window_names[:3])}... "
            
            if detailed:
                description += "\n\nDetailed analysis is available but not fully implemented in this version."
                
            return description
        except Exception as e:
            logger.error(f"Error describing screen: {e}")
            return f"I encountered an error trying to describe your screen: {str(e)}"
    
    def look_for(self, target: str) -> Dict[str, Any]:
        """
        Look for specific content on screen
        This is a more focused search based on user request
        """
        if not self.enabled:
            return {"found": False, "error": "Screen awareness is not enabled"}
            
        try:
            # Capture fresh screenshot
            screen_state = self.get_current_screen_state()
            
            if "error" in screen_state:
                return {"found": False, "error": screen_state["error"]}
            
            results = {"found": False, "target": target, "matches": []}
            
            # Check text content
            if screen_state.get("text"):
                text = screen_state["text"].lower()
                target_lower = target.lower()
                
                if target_lower in text:
                    results["found"] = True
                    
                    # Try to get some context around the match
                    lines = text.split('\n')
                    matching_lines = [line for line in lines if target_lower in line.lower()]
                    if matching_lines:
                        results["text_context"] = matching_lines[:5]  # Limit to 5 matches
            
            # Check window titles
            if screen_state.get("windows") and isinstance(screen_state["windows"], list):
                matching_windows = []
                for window in screen_state["windows"]:
                    title = window.get("title", "").lower()
                    app = window.get("app", "").lower()
                    
                    if target_lower in title or target_lower in app:
                        matching_windows.append(window)
                
                if matching_windows:
                    results["found"] = True
                    results["matching_windows"] = matching_windows
            
            return results
        except Exception as e:
            logger.error(f"Error looking for {target}: {e}")
            return {"found": False, "error": str(e), "target": target}
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of screen awareness module"""
        return {
            "enabled": self.enabled,
            "permission_granted": self.permission_granted,
            "can_interact": self.interaction.can_interact,
            "capture_active": self.capture.active,
            "history_size": len(self.screen_history)
        }

# Singleton instance
_instance = None

def get_instance():
    """Get the singleton instance of ScreenAwarenessModule"""
    global _instance
    if _instance is None:
        _instance = ScreenAwarenessModule()
    return _instance
