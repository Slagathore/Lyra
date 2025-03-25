"""
Helper utility to initialize cognitive modules
"""

import logging
import importlib
import time
from typing import Dict, List, Optional, Any

# Set up logging
logger = logging.getLogger("cognitive_initializer")

class CognitiveInitializer:
    """Initialize cognitive modules for Lyra"""
    
    def __init__(self, model_manager=None):
        """
        Initialize the cognitive initializer
        
        Args:
            model_manager: Optional model manager to connect with
        """
        self.model_manager = model_manager
        self.modules = {}
        
        # Define the initialization order (important for dependencies)
        self.initialization_order = [
            "metacognition",
            "emotional_core",
            "deep_memory",
            "boredom",
            "thinking_integration",
            "cognitive_integration",
            "cognitive_model_integration"
        ]
    
    def initialize_all(self) -> Dict[str, bool]:
        """
        Initialize all cognitive modules in order
        
        Returns:
            Dictionary of module statuses
        """
        results = {}
        
        for module_name in self.initialization_order:
            success = self.initialize_module(module_name)
            results[module_name] = success
        
        # Connect modules with model manager if provided
        if self.model_manager:
            self.connect_with_model_manager()
        
        # Connect modules with each other
        self.connect_modules()
        
        return results
    
    def initialize_module(self, module_name: str) -> bool:
        """
        Initialize a specific cognitive module
        
        Args:
            module_name: Name of the module to initialize
            
        Returns:
            True if initialization was successful
        """
        logger.info(f"Initializing {module_name}...")
        
        try:
            # Import the module
            module_path = f"modules.{module_name}"
            
            try:
                module = importlib.import_module(module_path)
            except ImportError:
                logger.warning(f"Module {module_path} not found")
                return False
            
            # Check if it has get_instance function
            if hasattr(module, 'get_instance'):
                instance = module.get_instance()
                self.modules[module_name] = instance
                logger.info(f"Successfully initialized {module_name}")
                return True
            else:
                logger.warning(f"Module {module_path} has no get_instance function")
                return False
        
        except Exception as e:
            logger.error(f"Error initializing {module_name}: {e}")
            return False
    
    def connect_with_model_manager(self) -> bool:
        """
        Connect cognitive modules with the model manager
        
        Returns:
            True if any connections were established
        """
        if not self.model_manager:
            logger.warning("No model manager provided")
            return False
        
        connected = False
        
        # Connect cognitive integration
        if "cognitive_integration" in self.modules:
            try:
                cognitive = self.modules["cognitive_integration"]
                if hasattr(cognitive, 'connect_with_model_manager'):
                    cognitive.connect_with_model_manager(self.model_manager)
                    logger.info("Connected cognitive_integration with model_manager")
                    connected = True
            except Exception as e:
                logger.error(f"Error connecting cognitive_integration: {e}")
        
        # Connect cognitive model integration
        if "cognitive_model_integration" in self.modules:
            try:
                model_integration = self.modules["cognitive_model_integration"]
                if hasattr(model_integration, 'initialize_with_model_manager'):
                    model_integration.initialize_with_model_manager(self.model_manager)
                    logger.info("Connected cognitive_model_integration with model_manager")
                    connected = True
            except Exception as e:
                logger.error(f"Error connecting cognitive_model_integration: {e}")
        
        return connected
    
    def connect_modules(self) -> bool:
        """
        Connect cognitive modules with each other
        
        Returns:
            True if any connections were established
        """
        connected = False
        
        # Connect metacognition with deep memory
        if "metacognition" in self.modules and "deep_memory" in self.modules:
            try:
                metacognition = self.modules["metacognition"]
                deep_memory = self.modules["deep_memory"]
                
                if hasattr(metacognition, 'connect_with_memory'):
                    metacognition.connect_with_memory(deep_memory)
                    logger.info("Connected metacognition with deep_memory")
                    connected = True
            except Exception as e:
                logger.error(f"Error connecting metacognition with deep_memory: {e}")
        
        # Connect emotional core with metacognition
        if "emotional_core" in self.modules and "metacognition" in self.modules:
            try:
                emotional = self.modules["emotional_core"]
                metacognition = self.modules["metacognition"]
                
                if hasattr(emotional, 'connect_with_metacognition'):
                    emotional.connect_with_metacognition(metacognition)
                    logger.info("Connected emotional_core with metacognition")
                    connected = True
            except Exception as e:
                logger.error(f"Error connecting emotional_core with metacognition: {e}")
        
        # Connect boredom with cognitive integration
        if "boredom" in self.modules and "cognitive_integration" in self.modules:
            try:
                boredom = self.modules["boredom"]
                cognitive = self.modules["cognitive_integration"]
                
                if hasattr(boredom, 'connect_with_cognitive'):
                    boredom.connect_with_cognitive(cognitive)
                    logger.info("Connected boredom with cognitive_integration")
                    connected = True
            except Exception as e:
                logger.error(f"Error connecting boredom with cognitive_integration: {e}")
        
        return connected
    
    def get_module(self, module_name: str) -> Any:
        """
        Get a specific module instance
        
        Args:
            module_name: Name of the module to get
            
        Returns:
            Module instance or None if not found
        """
        return self.modules.get(module_name)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all cognitive modules
        
        Returns:
            Dictionary with module statuses
        """
        status = {}
        
        for module_name, instance in self.modules.items():
            # Check if the module has a get_status method
            if hasattr(instance, 'get_status'):
                try:
                    module_status = instance.get_status()
                    status[module_name] = module_status
                except Exception as e:
                    status[module_name] = {"error": str(e)}
            else:
                # Basic status if no get_status method
                status[module_name] = {"available": True}
        
        # Add overall status
        status["initialized_modules"] = list(self.modules.keys())
        status["missing_modules"] = [m for m in self.initialization_order if m not in self.modules]
        
        return status

# Singleton instance
_initializer = None

def initialize_cognitive_modules(model_manager=None) -> Dict[str, bool]:
    """
    Initialize all cognitive modules
    
    Args:
        model_manager: Optional model manager to connect with
    
    Returns:
        Dictionary with initialization results
    """
    global _initializer
    if _initializer is None:
        _initializer = CognitiveInitializer(model_manager)
    
    return _initializer.initialize_all()

def get_cognitive_module(module_name: str) -> Any:
    """
    Get a specific cognitive module
    
    Args:
        module_name: Name of the module to get
    
    Returns:
        Module instance or None if not found
    """
    global _initializer
    if _initializer is None:
        return None
    
    return _initializer.get_module(module_name)

def get_cognitive_status() -> Dict[str, Any]:
    """
    Get status of cognitive modules
    
    Returns:
        Dictionary with module statuses
    """
    global _initializer
    if _initializer is None:
        return {"error": "Cognitive modules not initialized"}
    
    return _initializer.get_status()

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Initialize cognitive modules
    results = initialize_cognitive_modules()
    
    print("\nCognitive Modules Initialization Results:")
    for module, success in results.items():
        status = "✓ Initialized" if success else "✗ Failed"
        print(f"  {module}: {status}")
    
    # Print status
    status = get_cognitive_status()
    print("\nAvailable Cognitive Modules:")
    for module in status.get("initialized_modules", []):
        print(f"  - {module}")
    
    if status.get("missing_modules"):
        print("\nMissing Cognitive Modules:")
        for module in status.get("missing_modules", []):
            print(f"  - {module}")
