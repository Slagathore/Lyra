"""
Utility to help components connect to the Lyra core
"""

import os
import sys
import logging
import importlib
import time
from pathlib import Path
from typing import Optional, Any, Dict, List

# Set up logging
logger = logging.getLogger("core_connector")

class CoreConnector:
    """
    Utility class that helps components connect to the Lyra core
    Provides fallback mechanisms when the core isn't available
    """
    
    def __init__(self, retry_attempts=3, retry_delay=2):
        """
        Initialize the connector
        
        Args:
            retry_attempts: Number of connection attempts before failing
            retry_delay: Delay between retry attempts in seconds
        """
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.core = None
        
        # Track core module location
        self.core_module_path = None
        
        # Try to connect to the core
        self._connect_to_core()
    
    def _connect_to_core(self) -> bool:
        """
        Try to connect to the Lyra core
        
        Returns:
            True if connection was successful
        """
        # Try to load core location from config file first
        core_location = self._load_core_location()
        
        if core_location and "core_module" in core_location:
            # Try to connect using the configured module
            core_module_path = core_location["core_module"]
            
            for attempt in range(self.retry_attempts):
                try:
                    logger.info(f"Attempting to connect to core via {core_module_path} (attempt {attempt+1})")
                    
                    # Add the core path to sys.path if provided
                    if "core_path" in core_location and core_location["core_path"]:
                        core_path = core_location["core_path"]
                        if core_path not in sys.path:
                            sys.path.insert(0, core_path)
                            logger.info(f"Added {core_path} to sys.path")
                    
                    # Import the module
                    module = importlib.import_module(core_module_path)
                    
                    # Try to get the core instance
                    if hasattr(module, 'get_instance'):
                        self.core = module.get_instance()
                        if self.core:
                            self.core_module_path = core_module_path
                            logger.info(f"Successfully connected to core via {core_module_path}")
                            return True
                except Exception as e:
                    logger.warning(f"Error connecting to core via {core_module_path}: {e}")
                    if attempt < self.retry_attempts - 1:
                        time.sleep(self.retry_delay)
        
        # Try standard locations if configured module failed
        if not self.core:
            standard_paths = [
                "modules.lyra_core",
                "lyra_core",
                "core",
                "modules.core",
                "src.lyra.core"
            ]
            
            for module_path in standard_paths:
                for attempt in range(self.retry_attempts):
                    try:
                        logger.info(f"Attempting to connect to core via {module_path} (attempt {attempt+1})")
                        module = importlib.import_module(module_path)
                        
                        # Try to get the core instance
                        if hasattr(module, 'get_instance'):
                            self.core = module.get_instance()
                            if self.core:
                                self.core_module_path = module_path
                                logger.info(f"Successfully connected to core via {module_path}")
                                return True
                    except ImportError:
                        # This module doesn't exist, try the next one
                        break
                    except Exception as e:
                        logger.warning(f"Error connecting to core via {module_path}: {e}")
                        if attempt < self.retry_attempts - 1:
                            time.sleep(self.retry_delay)
        
        # Create a local dummy core if all else fails
        if not self.core:
            logger.warning("Could not connect to any real core, creating a local dummy core")
            from ..modules.lyra_core import LyraCore
            self.core = LyraCore.get_instance()
            self.core_module_path = "modules.lyra_core"
            return True
        
        return False
    
    def _load_core_location(self) -> Optional[Dict[str, Any]]:
        """
        Load core location from config file
        
        Returns:
            Dictionary with core location information or None if not found
        """
        config_file = Path("config/core_location.json")
        if config_file.exists():
            try:
                import json
                with open(config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Error reading core location config: {e}")
        
        return None
    
    def process_message(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a message through the core
        
        Args:
            message: The message to process
            metadata: Optional metadata about the message
            
        Returns:
            Response dictionary from the core
        """
        if not self.core:
            return {
                "success": False,
                "error": "No core connection available",
                "response": "I'm sorry, I can't process your message because I'm not connected to the Lyra core."
            }
        
        try:
            result = self.core.process_message(message, metadata)
            return result
        except Exception as e:
            logger.error(f"Error processing message through core: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your message."
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of the core
        
        Returns:
            Status dictionary from the core
        """
        if not self.core:
            return {
                "status": "disconnected",
                "error": "No core connection available"
            }
        
        try:
            if hasattr(self.core, 'get_status'):
                return self.core.get_status()
            else:
                return {
                    "status": "connected",
                    "note": "Core doesn't support status reporting"
                }
        except Exception as e:
            logger.error(f"Error getting core status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def register_client(self, client_id: str, callback=None) -> bool:
        """
        Register a client with the core
        
        Args:
            client_id: Unique identifier for the client
            callback: Optional callback function for events
            
        Returns:
            True if registration was successful
        """
        if not self.core:
            return False
        
        try:
            if hasattr(self.core, 'register_client'):
                return self.core.register_client(client_id, callback)
            else:
                return False
        except Exception as e:
            logger.error(f"Error registering client with core: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if connected to the core
        
        Returns:
            True if connected to a core
        """
        return self.core is not None
    
    def get_core(self):
        """
        Get the core instance
        
        Returns:
            The core instance or None if not connected
        """
        return self.core
    
    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the core connection
        
        Returns:
            Dictionary with connection information
        """
        return {
            "connected": self.core is not None,
            "module_path": self.core_module_path,
            "core_type": self.core.__class__.__name__ if self.core else None,
            "has_models": hasattr(self.core, 'model_manager') if self.core else False,
            "has_cognitive": hasattr(self.core, 'cognitive_architecture') if self.core else False
        }

# Singleton instance
_connector_instance = None

def get_connector() -> CoreConnector:
    """
    Get the singleton instance of CoreConnector
    
    Returns:
        CoreConnector instance
    """
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = CoreConnector()
    return _connector_instance

def get_core():
    """
    Get the Lyra core instance
    
    Returns:
        Lyra core instance or None if not available
    """
    connector = get_connector()
    return connector.get_core()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Create connector and test it
    connector = get_connector()
    print(f"Connected: {connector.is_connected()}")
    print(f"Connection info: {connector.get_connection_info()}")
    
    if connector.is_connected():
        # Get status
        status = connector.get_status()
        print(f"Core status: {status}")
        
        # Process a test message
        response = connector.process_message("Hello from the core connector test!")
        print(f"Response: {response}")
