"""
I/O Manager module for Lyra
Handles input/output operations across different interfaces
"""

import os
import sys
import logging
import threading
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Set up logging
logger = logging.getLogger("io_manager")

class IOManager:
    """
    Manages input and output operations for Lyra across various interfaces
    including console, web, and persistent UI
    """
    
    def __init__(self, core_instance=None, config_manager=None):
        """
        Initialize the IO Manager
        
        Args:
            core_instance: Reference to the Lyra core
            config_manager: Reference to the configuration manager
        """
        self.core_instance = core_instance
        self.config_manager = config_manager
        self.config = {}
        self.input_processors = {}
        self.output_handlers = {}
        self.persistent_ui = None
        
        # Load configuration if config manager is provided
        if self.config_manager:
            self.config = self.config_manager.get_module_config("io_manager", {})
        
        # Initialize modules
        self.initialize_modules()
    
    def initialize_modules(self):
        """Initialize input/output modules"""
        # Initialize basic console I/O by default
        self.register_input_processor("console", self.console_input_processor)
        self.register_output_handler("console", self.console_output_handler)
        
        # Initialize persistent module if not running in headless mode
        if not self.config.get("headless_mode", False):
            try:
                # Dynamic import to avoid circular dependencies
                from modules import persistent_module
                
                self.persistent_ui = persistent_module.get_instance(
                    core_instance=self.core_instance,
                    config_manager=self.config_manager
                )
                self.persistent_ui.run()
                logger.info("Persistent UI initialized")
            except Exception as e:
                logger.error(f"Error initializing persistent UI: {e}")
                self.persistent_ui = None
        else:
            logger.info("Running in headless mode, persistent UI disabled")
            self.persistent_ui = None
    
    def register_input_processor(self, name: str, processor_func):
        """
        Register an input processor function
        
        Args:
            name: Name of the processor
            processor_func: Function that processes input
        """
        self.input_processors[name] = processor_func
        logger.info(f"Registered input processor: {name}")
    
    def register_output_handler(self, name: str, handler_func):
        """
        Register an output handler function
        
        Args:
            name: Name of the handler
            handler_func: Function that handles output
        """
        self.output_handlers[name] = handler_func
        logger.info(f"Registered output handler: {name}")
    
    def process_input(self, input_text: str, source: str = "console", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process input from any source
        
        Args:
            input_text: The input text to process
            source: Source of the input
            metadata: Additional metadata about the input
            
        Returns:
            Dictionary with the processed result
        """
        if not input_text:
            return {"success": False, "error": "Empty input"}
        
        # Log the input
        logger.info(f"Input from {source}: {input_text[:50]}{'...' if len(input_text) > 50 else ''}")
        
        # Process through the core if available
        if self.core_instance:
            try:
                # Create metadata if not provided
                if metadata is None:
                    metadata = {}
                
                # Add source and timestamp to metadata
                metadata["source"] = source
                if "timestamp" not in metadata:
                    metadata["timestamp"] = time.time()
                
                # Process through core
                result = self.core_instance.process_message(input_text, metadata)
                
                # Process output if there's a response
                if result and "response" in result:
                    self.process_output(result["response"], "text", result)
                
                return result
            except Exception as e:
                logger.error(f"Error processing input through core: {e}")
                error_response = {
                    "success": False,
                    "error": str(e),
                    "response": "I encountered an error while processing your input.",
                    "source": source
                }
                self.process_output(error_response["response"], "text", error_response)
                return error_response
        else:
            logger.warning("No core instance available to process input")
            response = {
                "success": True,
                "response": "Core not initialized. Input received but cannot be fully processed.",
                "source": source
            }
            self.process_output(response["response"], "text", response)
            return response
    
    def process_output(self, output: Any, output_type: str = "text", metadata: Dict[str, Any] = None):
        """
        Process output to all registered handlers
        
        Args:
            output: The output to process
            output_type: Type of output (text, image, etc.)
            metadata: Additional metadata about the output
        """
        if output is None:
            return
        
        # Convert output to string if it's not already
        if output_type == "text" and not isinstance(output, str):
            output = str(output)
        
        # Log the output
        if output_type == "text":
            logger.info(f"Output: {output[:50]}{'...' if len(output) > 50 else ''}")
        else:
            logger.info(f"Output of type {output_type}")
        
        # Send to persistent UI if available
        if self.persistent_ui and output_type == "text":
            try:
                self.persistent_ui.message_queue.put(output)
            except Exception as e:
                logger.error(f"Error sending to persistent UI: {e}")
        
        # Send to all registered output handlers
        for name, handler in self.output_handlers.items():
            try:
                handler(output, output_type, metadata)
            except Exception as e:
                logger.error(f"Error in output handler {name}: {e}")
    
    def console_input_processor(self, input_text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Default console input processor"""
        return self.process_input(input_text, "console", metadata)
    
    def console_output_handler(self, output: Any, output_type: str = "text", metadata: Dict[str, Any] = None):
        """Default console output handler"""
        if output_type == "text":
            print(f"Lyra: {output}")
        else:
            print(f"[Output of type {output_type}]")

# Singleton instance
_instance = None

def get_instance(core_instance=None, config_manager=None):
    """Get the singleton instance of IOManager"""
    global _instance
    if _instance is None:
        _instance = IOManager(core_instance, config_manager)
    elif core_instance is not None and _instance.core_instance != core_instance:
        # Update the core instance if a new one is provided
        _instance.core_instance = core_instance
        logger.info("Updated core instance in IO Manager")
    return _instance

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()]
    )
    
    # Check platform and admin status
    if sys.platform == 'win32':
        try:
            import ctypes
            admin_status = ctypes.windll.shell32.IsUserAnAdmin()
            logger.info(f"Running on Windows with admin rights: {bool(admin_status)}")
        except:
            logger.info("Running on Windows, admin status unknown")
    else:
        logger.info(f"Running on {sys.platform}")
    
    # Simple test of the IO Manager
    io_manager = get_instance()
    
    # Test input/output
    result = io_manager.process_input("Hello, Lyra!")
    print(f"Result: {result}")
