"""
Persistence Setup for Lyra
Configures Lyra to run as a background Windows service
"""

import os
import sys
import argparse
import logging
import platform
import subprocess
import winreg
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("persistence_setup.log")
    ]
)
logger = logging.getLogger("persistence_setup")

# Check if we're on Windows
if platform.system() != "Windows":
    logger.error("Persistence service is only supported on Windows")
    sys.exit(1)

def create_config():
    """Create the persistence configuration file"""
    config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config")
    config_path = os.path.join(config_dir, "persistence_config.json")
    
    # Create config directory if it doesn't exist
    os.makedirs(config_dir, exist_ok=True)
    
    # Default configuration
    default_config = {
        "autostart": True,
        "startup_delay": 30,  # Seconds to wait after system startup
        "service_name": "LyraAIService",
        "display_name": "Lyra AI Background Service",
        "description": "Provides persistent background operation for Lyra AI",
        "telegram_enabled": True,
        "system_tray_enabled": True,
        "hotkeys_enabled": True,
        "api_enabled": True,
        "api_port": 5000,
        "log_level": "INFO",
        "python_path": sys.executable,
    }
    
    # Write default config if it doesn't exist
    if not os.path.exists(config_path):
        import json
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        logger.info(f"Created default configuration at {config_path}")
    
    return config_path

def install_service():
    """Install Lyra as a Windows service"""
    # First, create/update configuration
    config_path = create_config()
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    service_script = os.path.join(script_dir, "persistence_service.py")
    
    # Check if nssm is available
    nssm_path = os.path.join(script_dir, "tools", "nssm.exe")
    if not os.path.exists(nssm_path):
        # Create tools directory
        os.makedirs(os.path.join(script_dir, "tools"), exist_ok=True)
        
        # Need to download nssm
        logger.info("NSSM not found, attempting to download...")
        try:
            import requests
            nssm_url = "https://nssm.cc/release/nssm-2.24.zip"
            zip_path = os.path.join(script_dir, "tools", "nssm.zip")
            
            # Download the zip file
            response = requests.get(nssm_url)
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            
            # Extract nssm.exe
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract the 64-bit version
                for file in zip_ref.namelist():
                    if "win64" in file and file.endswith("nssm.exe"):
                        zip_ref.extract(file, os.path.join(script_dir, "tools"))
                        # Move the file to the right location
                        os.rename(
                            os.path.join(script_dir, "tools", file),
                            nssm_path
                        )
                        break
            
            # Clean up the zip file
            os.remove(zip_path)
            
            if not os.path.exists(nssm_path):
                logger.error("Failed to extract nssm.exe")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading NSSM: {e}")
            logger.info("Please download NSSM manually from https://nssm.cc and place nssm.exe in tools/")
            return False
    
    # Check if service already exists
    import json
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    service_name = config["service_name"]
    
    # Check if service is already installed
    try:
        result = subprocess.run(["sc", "query", service_name], capture_output=True, text=True)
        service_exists = result.returncode == 0
    except Exception:
        service_exists = False
    
    if service_exists:
        # Stop and remove existing service
        logger.info(f"Service {service_name} already exists, removing...")
        try:
            subprocess.run(["sc", "stop", service_name], check=False)
            subprocess.run(["sc", "delete", service_name], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error removing existing service: {e}")
            return False
    
    # Install the new service using NSSM
    try:
        # Create the service
        cmd = [
            nssm_path, "install", service_name, sys.executable,
            os.path.join(script_dir, "persistence_service.py")
        ]
        subprocess.run(cmd, check=True)
        
        # Configure service properties
        subprocess.run([nssm_path, "set", service_name, "DisplayName", config["display_name"]], check=True)
        subprocess.run([nssm_path, "set", service_name, "Description", config["description"]], check=True)
        subprocess.run([nssm_path, "set", service_name, "AppDirectory", script_dir], check=True)
        
        # Configure startup type - FIXED: Using correct NSSM startup type values
        startup_type = "SERVICE_AUTO_START" if config["autostart"] else "SERVICE_DEMAND_START"
        subprocess.run([nssm_path, "set", service_name, "Start", startup_type], check=True)
        
        # Configure restart behavior
        subprocess.run([nssm_path, "set", service_name, "AppRestartDelay", "10000"], check=True)  # 10 seconds
        
        # Configure stdout/stderr redirection to log files
        log_dir = os.path.join(script_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        subprocess.run([nssm_path, "set", service_name, "AppStdout", os.path.join(log_dir, "service_stdout.log")], check=True)
        subprocess.run([nssm_path, "set", service_name, "AppStderr", os.path.join(log_dir, "service_stderr.log")], check=True)
        
        logger.info(f"Service {service_name} installed successfully")
        
        # Optionally start the service
        if config["autostart"]:
            logger.info("Starting service...")
            subprocess.run(["sc", "start", service_name], check=True)
            logger.info("Service started")
        
        # Add to startup registry
        if config["autostart"]:
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run")
                winreg.SetValueEx(key, "LyraAI", 0, winreg.REG_SZ, f'net start "{service_name}"')
                winreg.CloseKey(key)
                logger.info("Added to startup registry")
            except Exception as e:
                logger.warning(f"Could not add to startup registry: {e}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing service: {e}")
        return False

def uninstall_service():
    """Uninstall the Lyra Windows service"""
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "persistence_config.json")
    
    # Get service name from config
    service_name = "LyraAIService"  # Default
    if os.path.exists(config_path):
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        service_name = config.get("service_name", service_name)
    
    # Check if service exists
    try:
        result = subprocess.run(["sc", "query", service_name], capture_output=True, text=True)
        service_exists = result.returncode == 0
    except Exception:
        service_exists = False
    
    if not service_exists:
        logger.info(f"Service {service_name} not found")
        return True
    
    # Stop and remove the service
    try:
        logger.info(f"Stopping service {service_name}...")
        subprocess.run(["sc", "stop", service_name], check=False)
        
        # Wait for service to stop
        time.sleep(2)
        
        logger.info(f"Removing service {service_name}...")
        subprocess.run(["sc", "delete", service_name], check=True)
        
        # Remove from startup registry
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_WRITE)
            try:
                winreg.DeleteValue(key, "LyraAI")
            except FileNotFoundError:
                pass  # Key doesn't exist, which is fine
            winreg.CloseKey(key)
        except Exception as e:
            logger.warning(f"Could not remove from startup registry: {e}")
        
        logger.info(f"Service {service_name} uninstalled successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error uninstalling service: {e}")
        return False

def main():
    """Main entry point for persistence setup"""
    parser = argparse.ArgumentParser(description="Lyra Persistence Setup")
    
    # Add arguments
    parser.add_argument("--install", action="store_true", help="Install Lyra as a Windows service")
    parser.add_argument("--uninstall", action="store_true", help="Uninstall the Lyra Windows service")
    parser.add_argument("--config", action="store_true", help="Create/update configuration only")
    
    args = parser.parse_args()
    
    # If no arguments, show help
    if not (args.install or args.uninstall or args.config):
        parser.print_help()
        return
    
    # Process arguments
    if args.config:
        config_path = create_config()
        logger.info(f"Configuration created/updated at {config_path}")
    
    if args.install:
        if install_service():
            logger.info("Lyra persistence service installed successfully")
        else:
            logger.error("Failed to install Lyra persistence service")
            sys.exit(1)
    
    if args.uninstall:
        if uninstall_service():
            logger.info("Lyra persistence service uninstalled successfully")
        else:
            logger.error("Failed to uninstall Lyra persistence service")
            sys.exit(1)

if __name__ == "__main__":
    main()
