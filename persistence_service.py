"""
Persistence Service for Lyra
Runs Lyra as a background Windows service
"""

import os
import sys
import time
import json
import signal
import logging
import threading
import subprocess
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("persistence_service.log")
    ]
)
logger = logging.getLogger("persistence_service")

class LyraService:
    """Main service class for running Lyra in the background"""
    
    def __init__(self):
        self.running = False
        self.stopped = threading.Event()
        self.config = self._load_config()
        self.processes = {}
        
        # Initialize system tray if enabled
        self.tray_icon = None
        if self.config.get("system_tray_enabled", True):
            self._init_system_tray()
        
        # Configure logging level
        log_level = self.config.get("log_level", "INFO").upper()
        numeric_level = getattr(logging, log_level, logging.INFO)
        logging.getLogger().setLevel(numeric_level)
        
        # Core cognitive components
        self.core_model = None
        self.cognitive_modules = {}
        
        # Try to load core model and cognitive modules
        self._load_cognitive_components()
    
    def _load_config(self):
        """Load configuration from file"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "persistence_config.json")
        
        # Default configuration
        default_config = {
            "autostart": True,
            "startup_delay": 30,
            "telegram_enabled": True,
            "system_tray_enabled": True,
            "hotkeys_enabled": True,
            "api_enabled": True,
            "api_port": 5000,
            "log_level": "INFO",
            "python_path": sys.executable,
        }
        
        # Load existing config if available
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults for any missing keys
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return default_config
    
    def _init_system_tray(self):
        """Initialize system tray icon"""
        try:
            import pystray
            from PIL import Image, ImageDraw
            
            # Create a simple icon
            icon_size = (64, 64)
            icon_image = Image.new('RGB', icon_size, color=(0, 0, 0))
            draw = ImageDraw.Draw(icon_image)
            
            # Draw a simple "L" for Lyra
            draw.rectangle((10, 10, 54, 54), fill=(0, 120, 212))
            draw.text((24, 20), "L", fill=(255, 255, 255))
            
            # Create menu
            def on_quit(icon, item):
                icon.stop()
                self.stop()
            
            def on_open_ui(icon, item):
                self._open_ui()
            
            def on_restart(icon, item):
                self.restart_components()
            
            menu = pystray.Menu(
                pystray.MenuItem("Open Lyra UI", on_open_ui),
                pystray.MenuItem("Restart Components", on_restart),
                pystray.MenuItem("Quit", on_quit)
            )
            
            # Create the icon
            self.tray_icon = pystray.Icon("LyraAI", icon_image, "Lyra AI", menu)
            
            # Start in a separate thread
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            logger.info("System tray icon initialized")
            
        except ImportError:
            logger.warning("System tray functionality not available. Install pystray and Pillow packages.")
    
    def _open_ui(self):
        """Open the Lyra UI"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ui_script = os.path.join(script_dir, "lyra_ui.py")
            
            # Use subprocess.Popen to launch in background
            subprocess.Popen([
                self.config.get("python_path", sys.executable),
                ui_script,
                "--direct"  # Skip airlock
            ])
            
            logger.info("Launched Lyra UI")
        except Exception as e:
            logger.error(f"Error launching UI: {e}")
    
    def _load_cognitive_components(self):
        """Load core cognitive components including Phi-4 if available"""
        try:
            # Try to load the core model (Phi-4 or other models)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            sys.path.append(script_dir)
            
            # Load model loader for access to Phi-4 and other models
            try:
                from model_loader import get_instance as get_model_loader
                model_loader = get_model_loader()
                self.cognitive_modules["model_loader"] = model_loader
                
                # Try to specifically connect to Phi-4 if available
                phi_models = [m for m in model_loader.models if "phi" in m.name.lower()]
                if phi_models:
                    for model in phi_models:
                        if "phi-4" in model.name.lower() or "phi4" in model.name.lower():
                            logger.info(f"Found Phi-4 model: {model.name}")
                            self.core_model = model
                            break
                    
                    # If no Phi-4, use any Phi model
                    if not self.core_model and phi_models:
                        self.core_model = phi_models[0]
                        logger.info(f"Using Phi model: {self.core_model.name}")
                
                logger.info("Model loader connected, models accessible in headless mode")
            except ImportError as e:
                logger.warning(f"Could not load model_loader: {e}")
            
            # Load core cognitive modules
            try:
                from modules.module_registry import initialize_all_modules, get_registry
                status = initialize_all_modules()
                self.cognitive_modules["module_registry"] = get_registry()
                logger.info(f"Initialized cognitive modules: {status}")
                
                # Connect fallback LLM
                try:
                    from modules.fallback_llm import get_instance as get_fallback_llm
                    self.cognitive_modules["fallback_llm"] = get_fallback_llm()
                except ImportError:
                    pass
                
                # Load extended thinking
                try:
                    from modules.extended_thinking import get_instance as get_extended_thinking
                    self.cognitive_modules["extended_thinking"] = get_extended_thinking()
                except ImportError:
                    pass
                
                # Load emotional core
                try:
                    from modules.emotional_core import get_instance as get_emotional_core
                    self.cognitive_modules["emotional_core"] = get_emotional_core()
                except ImportError:
                    pass
                
                # Load deep memory
                try:
                    from modules.deep_memory import get_instance as get_deep_memory
                    self.cognitive_modules["deep_memory"] = get_deep_memory()
                except ImportError:
                    pass
                
                # Let's connect models with thinking if both are available
                if "model_loader" in self.cognitive_modules and "extended_thinking" in self.cognitive_modules:
                    thinking = self.cognitive_modules["extended_thinking"]
                    if hasattr(thinking, "connect_model_manager"):
                        thinking.connect_model_manager(self.cognitive_modules["model_loader"])
                        logger.info("Connected model manager to extended thinking")
                
            except ImportError as e:
                logger.warning(f"Could not initialize all modules: {e}")
            
        except Exception as e:
            logger.error(f"Error loading cognitive components: {e}")
    
    def start_telegram_bot(self):
        """Start the Telegram bot with LLM connection"""
        if not self.config.get("telegram_enabled", True):
            return
            
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            bot_script = os.path.join(script_dir, "telegram_bot.py")
            
            # Create a bot interface that Telegram can use
            bot_interface = None
            try:
                from lyra_bot import LyraBot
                bot_interface = LyraBot()
                
                # Connect with the core model if available
                if self.core_model and hasattr(bot_interface, "select_model"):
                    bot_interface.select_model(self.core_model.name)
                    logger.info(f"Connected Telegram bot with model: {self.core_model.name}")
            except ImportError:
                logger.warning("Could not create LyraBot for Telegram")
            
            # Import and create the Telegram bot directly
            try:
                import telegram_bot
                bot = telegram_bot.create_bot(lyra_interface=bot_interface)
                if bot:
                    logger.info("Created and started Telegram bot directly")
                    self.processes["telegram"] = "internal"  # Mark as internally managed
                    return
            except ImportError:
                pass  # Fall back to subprocess method
            
            # Start the bot as a subprocess if direct creation failed
            process = subprocess.Popen([
                self.config.get("python_path", sys.executable),
                bot_script
            ])
            
            # Store the process
            self.processes["telegram"] = process
            logger.info(f"Started Telegram bot subprocess (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"Error starting Telegram bot: {e}")
    
    def start_api_server(self):
        """Start the API server"""
        if not self.config.get("api_enabled", True):
            return
            
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            api_script = os.path.join(script_dir, "api_server.py")
            
            # Skip if API script doesn't exist yet
            if not os.path.exists(api_script):
                logger.warning(f"API server script not found at {api_script}")
                return
            
            # Get API port
            api_port = self.config.get("api_port", 5000)
            
            # Start the process
            process = subprocess.Popen([
                self.config.get("python_path", sys.executable),
                api_script,
                "--port", str(api_port)
            ])
            
            # Store the process
            self.processes["api"] = process
            logger.info(f"Started API server on port {api_port} (PID: {process.pid})")
            
        except Exception as e:
            logger.error(f"Error starting API server: {e}")
    
    def start_components(self):
        """Start all enabled components"""
        # First check if cognitive modules are loaded
        if not self.cognitive_modules:
            self._load_cognitive_components()
        
        # Start the Telegram bot with connected LLM
        self.start_telegram_bot()
        
        # Start the API server
        self.start_api_server()
        
        # Register hotkeys if enabled
        if self.config.get("hotkeys_enabled", True):
            self._register_hotkeys()
        
        logger.info(f"All components started. Active cognitive modules: {list(self.cognitive_modules.keys())}")
    
    def restart_components(self):
        """Restart all components"""
        self.stop_components()
        time.sleep(1)  # Give processes time to terminate
        self.start_components()
    
    def stop_components(self):
        """Stop all components"""
        for name, process in list(self.processes.items()):
            try:
                logger.info(f"Stopping {name} process (PID: {process.pid})")
                process.terminate()
                
                # Give it a moment to terminate gracefully
                for _ in range(5):  # Wait up to 5 seconds
                    if process.poll() is not None:
                        break
                    time.sleep(1)
                
                # Force kill if still running
                if process.poll() is None:
                    logger.info(f"Forcing termination of {name} process")
                    process.kill()
                
                del self.processes[name]
            except Exception as e:
                logger.error(f"Error stopping {name} process: {e}")
    
    def _register_hotkeys(self):
        """Register global hotkeys"""
        try:
            import keyboard
            
            # Define hotkey actions
            def on_open_ui():
                self._open_ui()
            
            # Register hotkeys
            keyboard.add_hotkey("alt+shift+l", on_open_ui)  # Open UI
            
            logger.info("Global hotkeys registered")
        except ImportError:
            logger.warning("Hotkeys functionality not available. Install keyboard package.")
    
    def run(self):
        """Run the service"""
        self.running = True
        
        # Apply startup delay if configured
        startup_delay = self.config.get("startup_delay", 30)
        if startup_delay > 0:
            logger.info(f"Applying startup delay of {startup_delay} seconds")
            time.sleep(startup_delay)
        
        # Start all components
        self.start_components()
        
        # Main loop
        try:
            while self.running and not self.stopped.is_set():
                # Monitor processes and restart if needed
                for name, process in list(self.processes.items()):
                    if process.poll() is not None:
                        logger.warning(f"{name} process exited unexpectedly, restarting")
                        if name == "telegram":
                            self.start_telegram_bot()
                        elif name == "api":
                            self.start_api_server()
                
                # Sleep to avoid high CPU usage
                time.sleep(5)
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the service"""
        if not self.running:
            return
            
        logger.info("Stopping Lyra service")
        self.running = False
        self.stopped.set()
        
        # Stop all components
        self.stop_components()
        
        # Stop system tray if active
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except:
                pass
        
        logger.info("Lyra service stopped")

def main():
    """Main entry point for the service"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a file handler for logs
    file_handler = logging.FileHandler(os.path.join(log_dir, "persistence_service.log"))
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    
    logger.info("Starting Lyra persistence service")
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}")
        service.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run the service
    service = LyraService()
    service.run()

if __name__ == "__main__":
    main()
