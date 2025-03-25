"""
Persistent Module for Lyra
Provides a system tray icon and manages background operation
"""

import os
import sys
import time
import json
import logging
import threading
import queue
import socket
import signal
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
import subprocess
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/persistent_module.log", mode="a")
    ]
)
logger = logging.getLogger("persistent_module")

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Try to import pystray and PIL
try:
    import pystray
    from PIL import Image, ImageDraw, ImageFont
    TRAY_AVAILABLE = True
except ImportError as e:
    logger.error(f"Could not import pystray or PIL: {e}")
    logger.error("System tray functionality will be disabled")
    TRAY_AVAILABLE = False

# Try to import psutil for process management
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    logger.warning("psutil not available, some process management features will be limited")
    PSUTIL_AVAILABLE = False

# Import core connector to connect to Lyra core
try:
    from utils.core_connector import get_connector, get_core
except ImportError:
    logger.error("Could not import core_connector")
    
    # Try alternative import path
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from utils.core_connector import get_connector, get_core
    except ImportError:
        logger.error("Failed to import core_connector using alternative path")
        get_connector = get_core = None

class PersistentModule:
    """
    Module that runs in the background and provides a system tray icon
    Manages Lyra's background operation and provides quick access to functionality
    """
    
    def __init__(self, port=37849):
        """
        Initialize the persistent module
        
        Args:
            port: Port number to use for the socket communication
        """
        self.port = port
        self.icon = None
        self.running = False
        self.socket = None
        
        # Command queue for handling GUI commands
        self.command_queue = queue.Queue()
        
        # Event to signal worker thread to exit
        self.exit_event = threading.Event()
        
        # Status variables
        self.status = {
            "core_connected": False,
            "ui_running": False,
            "start_time": time.time(),
            "last_activity": time.time(),
            "memory_usage": 0,
            "cpu_usage": 0
        }
        
        # Configuration
        self.config = self._load_config()
        
        # Connect to the core
        self._connect_to_core()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        config_file = Path("config/persistent_config.json")
        default_config = {
            "autostart_ui": False,
            "minimize_to_tray": True,
            "check_for_updates": True,
            "ui_port": 7860,
            "dark_mode": True,
            "show_notifications": True,
            "start_minimized": False,
            "launch_browser": True
        }
        
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    return {**default_config, **user_config}
            except Exception as e:
                logger.error(f"Error loading persistent config: {e}")
        else:
            # Save default config if not exists
            try:
                config_file.parent.mkdir(exist_ok=True, parents=True)
                with open(config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default persistent config at {config_file}")
            except Exception as e:
                logger.error(f"Error saving default persistent config: {e}")
        
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    user_config = json.load(f)
                    # Merge user config with defaults
                    return {**default_config, **user_config}
            except Exception as e:
                logger.error(f"Error loading persistent config: {e}")
        else:
            # Save default config if not exists
            try:
                config_file.parent.mkdir(exist_ok=True, parents=True)
                with open(config_file, "w") as f:
                    json.dump(default_config, f, indent=2)
                logger.info(f"Created default persistent config at {config_file}")
            except Exception as e:
                logger.error(f"Error saving default persistent config: {e}")
        
        return default_config
    
    def _save_config(self) -> bool:
        """Save configuration to file"""
        config_file = Path("config/persistent_config.json")
        try:
            config_file.parent.mkdir(exist_ok=True, parents=True)
            with open(config_file, "w") as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved persistent config to {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error saving persistent config: {e}")
            return False
    
    def _connect_to_core(self) -> bool:
        """Connect to the Lyra core"""
        if get_connector is None:
            logger.error("Core connector not available")
            self.status["core_connected"] = False
            return False
        
        try:
            # Get connector and connect to core
            self.connector = get_connector()
            self.core = self.connector.get_core()
            
            if self.core:
                self.status["core_connected"] = True
                logger.info("Connected to Lyra core")
                
                # Register the persistent module as a client
                client_id = f"persistent_module_{os.getpid()}"
                self.connector.register_client(client_id)
                return True
            else:
                logger.error("Failed to connect to Lyra core")
                self.status["core_connected"] = False
                return False
        except Exception as e:
            logger.error(f"Error connecting to core: {e}")
            self.status["core_connected"] = False
            return False
    
    def _create_tray_icon(self):
        """Create and configure the system tray icon"""
        if not TRAY_AVAILABLE:
            logger.error("System tray functionality not available")
            return False
        
        try:
            # Try to load the icon from file
            icon_path = Path("assets/lyra_icon.png")
            if icon_path.exists():
                icon_image = Image.open(icon_path)
            else:
                # Create a simple icon if file doesn't exist
                icon_image = self._create_default_icon()
            
            # Create the tray icon
            self.icon = pystray.Icon(
                name="LyraTray",
                icon=icon_image,
                title="Lyra AI",
                menu=self._create_menu()
            )
            logger.info("System tray icon created")
            return True
        except Exception as e:
            logger.error(f"Error creating system tray icon: {e}")
            return False
    
    def _create_default_icon(self) -> Image.Image:
        """Create a default icon if no icon file is available"""
        # Create a simple gradient icon with "L" in the center
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        
        try:
            # Try to create a blue-purple gradient background
            for x in range(64):
                for y in range(64):
                    distance = ((x - 32) ** 2 + (y - 32) ** 2) ** 0.5 / 45.0
                    r = int(80 * (1.0 - distance))
                    g = int(100 * (1.0 - distance)) 
                    b = int(200 + (55 * (1.0 - distance)))
                    d.point((x, y), fill=(r, g, b, 255))
            
            # Find an available font
            font_paths = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",     # macOS
                "C:/Windows/Fonts/arialbd.ttf"                           # Windows
            ]
            
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    font = ImageFont.truetype(path, 36)
                    break
                    
            if not font:
                font = ImageFont.load_default()
                
            # Draw "L" in the center
            text_width, text_height = d.textsize("L", font=font) if hasattr(d, "textsize") else font.getsize("L")
            position = ((64 - text_width) // 2, (64 - text_height) // 2)
            d.text(position, "L", fill=(255, 255, 255, 230), font=font)
            
            # Round the corners slightly
            return img
        except Exception as e:
            logger.error(f"Error creating default icon: {e}")
            # Fallback to an even simpler icon
            img = Image.new('RGBA', (64, 64), color=(100, 100, 200, 255))
            return img

    def _create_menu(self) -> pystray.Menu:
        """Create the system tray menu"""
        return pystray.Menu(
            pystray.MenuItem(
                "Open Lyra Interface",
                self._on_open_ui,
                default=True  # Default action when clicking on the icon
            ),
            pystray.MenuItem(
                "Status",
                pystray.Menu(
                    lambda: pystray.MenuItem(
                        f"Core: {'Connected' if self.status['core_connected'] else 'Disconnected'}",
                        lambda: None,
                        enabled=False
                    ),
                    lambda: pystray.MenuItem(
                        f"UI: {'Running' if self.status['ui_running'] else 'Not running'}",
                        lambda: None,
                        enabled=False
                    ),
                    lambda: pystray.MenuItem(
                        f"Uptime: {self._format_uptime(time.time() - self.status['start_time'])}",
                        lambda: None,
                        enabled=False
                    ),
                    pystray.MenuItem(
                        "Refresh Status",
                        self._on_refresh_status
                    )
                )
            ),
            pystray.MenuItem(
                "Quick Actions",
                pystray.Menu(
                    pystray.MenuItem(
                        "Restart UI",
                        self._on_restart_ui
                    ),
                    pystray.MenuItem(
                        "Check for Updates",
                        self._on_check_updates
                    ),
                    pystray.MenuItem(
                        "Open Log Folder",
                        self._on_open_logs
                    )
                )
            ),
            pystray.MenuItem(
                "Settings",
                pystray.Menu(
                    lambda: pystray.MenuItem(
                        "Start UI Automatically",
                        self._on_toggle_autostart,
                        checked=lambda item: self.config.get("autostart_ui", False)
                    ),
                    lambda: pystray.MenuItem(
                        "Minimize to Tray",
                        self._on_toggle_minimize_to_tray,
                        checked=lambda item: self.config.get("minimize_to_tray", True)
                    ),
                    lambda: pystray.MenuItem(
                        "Dark Mode",
                        self._on_toggle_dark_mode,
                        checked=lambda item: self.config.get("dark_mode", True)
                    )
                )
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Exit",
                self._on_exit
            )
        )
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in seconds to a human-readable string"""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    
    def _on_open_ui(self, icon, item):
        """Open the Lyra UI"""
        self.command_queue.put(("open_ui", {}))
    
    def _on_open_logs(self, icon, item):
        """Open the logs folder"""
        self.command_queue.put(("open_logs", {}))
    
    def _on_toggle_autostart(self, icon, item):
        """Toggle autostart UI setting"""
        self.command_queue.put(("toggle_setting", {"setting": "autostart_ui"}))
    
    def _on_toggle_minimize_to_tray(self, icon, item):
        """Toggle minimize to tray setting"""
        self.command_queue.put(("toggle_setting", {"setting": "minimize_to_tray"}))
    
    def _on_toggle_dark_mode(self, icon, item):
        """Toggle dark mode setting"""
        self.command_queue.put(("toggle_setting", {"setting": "dark_mode"}))
    
    def _on_exit(self, icon, item):
        """Exit the application"""
        self.command_queue.put(("exit", {}))
    
    def _start_socket_server(self) -> bool:
        """Start the socket server for communication with the UI"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("localhost", self.port))
            self.socket.listen(5)
            self.socket.settimeout(1.0)  # 1 second timeout for accept()
            
            logger.info(f"Socket server started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Error starting socket server: {e}")
            return False
    
    def _socket_listener(self):
        """Thread function for listening to socket connections"""
        logger.info("Socket listener thread started")
        
        # Prevent CPU spinning on repeated errors
        consecutive_errors = 0
        
        while not self.exit_event.is_set():
            try:
                # Accept a connection with timeout
                try:
                    client, addr = self.socket.accept()
                    logger.info(f"Connection from {addr}")
                    
                    # Set a timeout for receiving data
                    client.settimeout(5.0)
                    
                    # Handle the connection
                    self._handle_client_connection(client)
                    
                    # Reset error counter on successful connection
                    consecutive_errors = 0
                    
                except socket.timeout:
                    # Just a timeout, continue the loop
                    continue
                    
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in socket listener: {e}")
                
                # Add delay if we're getting repeated errors
                if consecutive_errors > 3:
                    time.sleep(1.0)
                    continue
    
    def _handle_client_connection(self, client):
        """Handle a client connection"""
        try:
            data = client.recv(1024).decode('utf-8')
            command = json.loads(data)
            action = command.get("action")
            params = command.get("params", {})
            
            if not action:
                client.send(json.dumps({"success": False, "error": "No action specified"}).encode('utf-8'))
                return
            
            # Handle different actions
            if action == "status":
                response = self._get_status_info()
                client.send(json.dumps({"success": True, "data": response}).encode('utf-8'))
            
            elif action == "process_message":
                if self.status["core_connected"] and self.core:
                    message = params.get("message", "")
                    core_response = self.core.process_message(message)
                    client.send(json.dumps({"success": True, "data": core_response}).encode('utf-8'))
                else:
                    client.send(json.dumps({"success": False, "error": "Core not connected"}).encode('utf-8'))
            
            elif action == "update_config":
                new_config = params.get("config", {})
                if new_config:
                    self.config.update(new_config)
                    self._save_config()
                    client.send(json.dumps({"success": True}).encode('utf-8'))
                else:
                    client.send(json.dumps({"success": False, "error": "No config provided"}).encode('utf-8'))
            
            elif action == "ui_started":
                self.status["ui_running"] = True
                client.send(json.dumps({"success": True}).encode('utf-8'))
            
            elif action == "ui_stopping":
                self.status["ui_running"] = False
                client.send(json.dumps({"success": True}).encode('utf-8'))
            
            elif action == "get_config":
                client.send(json.dumps({"success": True, "data": self.config}).encode('utf-8'))
            
            else:
                client.send(json.dumps({"success": False, "error": f"Unknown action: {action}"}).encode('utf-8'))
        
        except Exception as e:
            logger.error(f"Error handling client connection: {e}")
            try:
                client.send(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
            except:
                pass
        finally:
            client.close()
    
    def _get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information"""
        status_info = {
            "core_connected": self.status["core_connected"],
            "ui_running": self.status["ui_running"],
            "uptime": time.time() - self.status["start_time"],
            "uptime_formatted": self._format_uptime(time.time() - self.status["start_time"]),
            "memory_usage": 0,
            "cpu_usage": 0,
            "process_id": os.getpid()
        }
        
        # Add system resource usage if psutil is available
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                status_info["memory_usage"] = process.memory_info().rss / (1024 * 1024)  # MB
                status_info["cpu_usage"] = process.cpu_percent()
            except Exception as e:
                logger.error(f"Error getting resource usage: {e}")
        
        # Add core status if connected
        if self.status["core_connected"] and self.core:
            try:
                core_status = self.connector.get_status()
                status_info["core_status"] = core_status
            except Exception as e:
                logger.error(f"Error getting core status: {e}")
                status_info["core_status"] = {"error": str(e)}
        
        return status_info
    
    def _command_handler(self):
        """Thread function for handling commands from the GUI"""
        logger.info("Command handler thread started")
        
        while not self.exit_event.is_set():
            try:
                # Get command with timeout
                try:
                    command, params = self.command_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Process command
                logger.debug(f"Processing command: {command} with params: {params}")
                
                if command == "open_ui":
                    self._handle_open_ui()
                elif command == "refresh_status":
                    self._handle_refresh_status()
                elif command == "restart_ui":
                    self._handle_restart_ui()
                elif command == "check_updates":
                    self._handle_check_updates()
                elif command == "open_logs":
                    self._handle_open_logs()
                elif command == "toggle_setting":
                    setting = params.get("setting")
                    if setting and setting in self.config:
                        self.config[setting] = not self.config[setting]
                        self._save_config()
                        logger.info(f"Toggled setting {setting} to {self.config[setting]}")
                elif command == "exit":
                    logger.info("Exit command received")
                    self.exit_event.set()
                    if self.icon:
                        self.icon.stop()
                else:
                    logger.warning(f"Unknown command: {command}")
                
                # Mark as done
                self.command_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in command handler: {e}")
                time.sleep(0.1)  # Prevent CPU spinning on repeated errors
        
        logger.info("Command handler thread stopped")
    
    def _handle_open_ui(self):
        """Handle the open UI command"""
        if self.status["ui_running"]:
            # UI is already running, just focus it
            self._focus_ui()
            return
        
        # Start the UI
        self._start_ui()
    
    def _handle_refresh_status(self):
        """Handle the refresh status command"""
        # Update resource usage
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process(os.getpid())
                self.status["memory_usage"] = process.memory_info().rss / (1024 * 1024)  # MB
                self.status["cpu_usage"] = process.cpu_percent()
            except Exception as e:
                logger.error(f"Error getting resource usage: {e}")
        
        # Check UI status
        self._check_ui_status()
        
        # Check core connection
        if not self.status["core_connected"]:
            self._connect_to_core()
        
        logger.info("Status refreshed")
    
    def _handle_restart_ui(self):
        """Handle the restart UI command"""
        if self.status["ui_running"]:
            # Stop the UI
            self._stop_ui()
            # Wait a moment for it to close
            time.sleep(1)
        
        # Start the UI
        self._start_ui()
    
    def _handle_check_updates(self):
        """Handle the check for updates command"""
        logger.info("Checking for updates...")
        
        # This is a placeholder - in a real implementation, you would check for updates
        # For now, just show a notification that no updates are available
        if self.icon and hasattr(self.icon, 'notify'):
            self.icon.notify(
                "No updates available",
                "You are running the latest version of Lyra."
            )
    
    def _handle_open_logs(self):
        """Handle the open logs command"""
        logs_dir = Path("logs")
        if not logs_dir.exists():
            logs_dir.mkdir(exist_ok=True)
        
        # Open the logs directory using the default file explorer
        try:
            if sys.platform == 'win32':
                os.startfile(logs_dir)
            elif sys.platform == 'darwin':  # macOS
                subprocess.run(['open', logs_dir])
            else:  # Linux
                subprocess.run(['xdg-open', logs_dir])
        except Exception as e:
            logger.error(f"Error opening logs directory: {e}")
            
            if self.icon and hasattr(self.icon, 'notify'):
                self.icon.notify(
                    "Error",
                    f"Could not open logs directory: {e}"
                )
    
    def _start_ui(self):
        """Start the Lyra UI"""
        logger.info("Starting Lyra UI...")
        
        try:
            # Build the command to run the UI
            ui_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lyra_ui.py")
            
            if not os.path.exists(ui_script):
                # Try alternative scripts
                for alt_script in ["airlock_app.py", "run_lyra.py"]:
                    alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), alt_script)
                    if os.path.exists(alt_path):
                        ui_script = alt_path
                        break
            
            if not os.path.exists(ui_script):
                logger.error("Could not find UI script")
                if self.icon and hasattr(self.icon, 'notify'):
                    self.icon.notify(
                        "Error",
                        "Could not find UI script. Please reinstall Lyra."
                    )
                return
            
            # Build command line arguments
            cmd = [sys.executable, ui_script]
            
            # Add port if not default
            if self.config.get("ui_port", 7860) != 7860:
                cmd.extend(["--port", str(self.config.get("ui_port"))])
            
            # Add other arguments
            if self.config.get("dark_mode", True):
                cmd.append("--dark-mode")
            
            # Use a detached process to avoid blocking
            if sys.platform == 'win32':
                # On Windows, use CREATE_NEW_PROCESS_GROUP and DETACHED_PROCESS
                process = subprocess.Popen(
                    cmd, 
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                )
            else:
                # On Unix, just use Popen with start_new_session=True
                process = subprocess.Popen(
                    cmd,
                    start_new_session=True
                )
            
            logger.info(f"UI started with PID {process.pid}")
            # Mark UI as running
            self.status["ui_running"] = True
            
            # Open browser if configured
            if self.config.get("launch_browser", True):
                time.sleep(2)  # Give the UI a moment to start
                port = self.config.get("ui_port", 7860)
                webbrowser.open(f"http://localhost:{port}")
        
        except Exception as e:
            logger.error(f"Error starting UI: {e}")
            if self.icon and hasattr(self.icon, 'notify'):
                self.icon.notify(
                    "Error",
                    f"Could not start Lyra UI: {e}"
                )
    
    def _stop_ui(self):
        """Stop the Lyra UI"""
        logger.info("Stopping Lyra UI...")
        
        # Send stop command to the UI if we can find it
        if PSUTIL_AVAILABLE:
            try:
                for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = process.cmdline()
                        if len(cmdline) < 2:
                            continue
                            
                        # Find any process running lyra_ui.py, airlock_app.py, or run_lyra.py
                        if any(ui_script in cmdline[1] for ui_script in ["lyra_ui.py", "airlock_app.py", "run_lyra.py"]):
                            logger.info(f"Found UI process: {process.pid}")
                            
                            # Different shutdown strategies based on platform
                            if sys.platform == 'win32':
                                # On Windows, try CTRL+C signal first
                                try:
                                    process.send_signal(signal.CTRL_C_EVENT)
                                    logger.info(f"Sent CTRL+C to UI process {process.pid}")
                                except:
                                    # If that fails, terminate the process
                                    process.terminate()
                                    logger.info(f"Terminated UI process {process.pid}")
                            else:
                                # On Unix, use SIGTERM
                                process.terminate()
                                logger.info(f"Terminated UI process {process.pid}")
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
            except Exception as e:
                logger.error(f"Error stopping UI: {e}")
        
        # Mark UI as not running
        self.status["ui_running"] = False
    
    def _focus_ui(self):
        """Focus the Lyra UI by opening it in the browser"""
        port = self.config.get("ui_port", 7860)
        webbrowser.open(f"http://localhost:{port}")
    
    def _check_ui_status(self):
        """Check if the UI is actually running"""
        # This is a simple check - it just looks for processes with the UI script name
        if PSUTIL_AVAILABLE:
            try:
                ui_running = False
                for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        cmdline = process.cmdline()
                        if len(cmdline) < 2:
                            continue
                        
                        # Check if the process is running one of our UI scripts
                        if any(ui_script in cmdline[1] for ui_script in ["lyra_ui.py", "airlock_app.py", "run_lyra.py"]):
                            ui_running = True
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                
                self.status["ui_running"] = ui_running
            except Exception as e:
                logger.error(f"Error checking UI status: {e}")
    
    def run(self):
        """Run the persistent module"""
        logger.info("Starting persistent module...")
        
        # Create the system tray icon if available
        if TRAY_AVAILABLE:
            if not self._create_tray_icon():
                logger.error("Failed to create system tray icon")
                return False
        
        # Start the socket server
        if not self._start_socket_server():
            logger.error("Failed to start socket server")
            return False
        
        # Start the socket listener thread
        socket_thread = threading.Thread(target=self._socket_listener, daemon=True)
        socket_thread.start()
        
        # Start the command handler thread
        command_thread = threading.Thread(target=self._command_handler, daemon=True)
        command_thread.start()
        
        # Mark as running
        self.running = True
        
        # Start UI automatically if configured
        if self.config.get("autostart_ui", False):
            self.command_queue.put(("open_ui", {}))
        
        # Run the icon if available
        if TRAY_AVAILABLE and self.icon:
            logger.info("Running system tray icon")
            self.icon.run()
        else:
            # If no icon, run in a loop until stopped
            logger.info("Running without system tray icon")
            try:
                while self.running and not self.exit_event.is_set():
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received")
                self.running = False
                self.exit_event.set()
        
        # Wait for threads to finish
        logger.info("Waiting for threads to finish...")
        socket_thread.join(timeout=5)
        command_thread.join(timeout=5)
        
        # Close the socket
        if self.socket:
            try:
                self.socket.close()
                logger.info("Socket closed")
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
        
        logger.info("Persistent module stopped")
        return True

def check_already_running(port=37849) -> bool:
    """Check if another instance is already running on the specified port"""
    try:
        # Try to connect to the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        result = s.connect_ex(('localhost', port))
        s.close()
        
        # If the port is open, another instance is running
        if result == 0:
            logger.warning(f"Another instance is already running on port {port}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error checking if another instance is running: {e}")
        return False

def main():
    """Main function to run the persistent module"""
    # Check if another instance is already running
    if check_already_running():
        print("Another instance of Lyra is already running.")
        
        # Try to focus the existing instance
        try:
            # Send a message to the existing instance to focus the UI
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('localhost', 37849))
            s.sendall(json.dumps({"action": "open_ui"}).encode('utf-8'))
            s.close()
            print("Focused the existing instance.")
        except:
            print("Could not communicate with the existing instance.")
        
        return 1
    
    # Create and run the persistent module
    module = PersistentModule()
    module.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
