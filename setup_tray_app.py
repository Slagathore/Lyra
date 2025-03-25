#!/usr/bin/env python3
"""
Setup script for Lyra System Tray application
Installs required dependencies and creates configuration files
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    min_version = (3, 7, 0)
    current_version = sys.version_info[:3]
    
    if current_version < min_version:
        print(f"Error: Python {min_version[0]}.{min_version[1]}.{min_version[2]} or higher is required")
        print(f"Current version: {current_version[0]}.{current_version[1]}.{current_version[2]}")
        return False
    
    return True

def install_dependencies():
    """Install required dependencies"""
    requirements = [
        "pystray",           # System tray functionality
        "pillow",            # Image handling for system tray icon
        "psutil",            # Process management
        "requests",          # HTTP requests
        "websocket-client"   # WebSocket client for UI communication
    ]
    
    print("Installing required dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade"] + requirements)
        print("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False

def create_config_directories():
    """Create configuration directories"""
    directories = [
        "config",
        "logs",
        "data",
        "data/state",
        "data/health"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True, parents=True)
        print(f"Created directory: {directory}")

def create_default_configs():
    """Create default configuration files"""
    # Persistent module config
    persistent_config = {
        "autostart_ui": False,
        "minimize_to_tray": True,
        "check_for_updates": True,
        "ui_port": 7860,
        "dark_mode": True,
        "show_notifications": True,
        "start_minimized": False,
        "launch_browser": True
    }
    
    # Core location config (for connecting to the core)
    core_location = {
        "core_module": "modules.lyra_core",
        "core_path": str(Path.cwd()),
        "setup_date": "auto-config"
    }
    
    # Write configs
    with open("config/persistent_config.json", "w") as f:
        json.dump(persistent_config, f, indent=2)
    
    with open("config/core_location.json", "w") as f:
        json.dump(core_location, f, indent=2)
    
    print("Created default configuration files")

def test_tray_functionality():
    """Test if system tray functionality works"""
    print("Testing system tray functionality...")
    
    try:
        import pystray
        from PIL import Image
        
        print("Required modules for system tray are available.")
        print("To test if the system tray actually works, run: python simple_tray_test.py")
        return True
    except ImportError as e:
        print(f"Error: {e}")
        print("System tray functionality may not work correctly.")
        return False

def main():
    """Main setup function"""
    print("Lyra System Tray Application Setup")
    print("==================================")
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        print("Warning: Some dependencies could not be installed.")
        print("The application may not function correctly.")
    
    # Create directories
    create_config_directories()
    
    # Create default configs
    create_default_configs()
    
    # Test system tray functionality
    test_tray_functionality()
    
    print("\nSetup complete!")
    print("You can now run the system tray application with:")
    if platform.system() == "Windows":
        print("  run_lyra_tray.bat")
    else:
        print("  python modules/persistent_module.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
