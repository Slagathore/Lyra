"""
Cognitive Connector utility for Lyra
Helps connect and integrate cognitive components
"""

import logging
import importlib
import time
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Set up logging
logger = logging.getLogger("cognitive_connector")

class CognitiveConnector:
    """
    Utility to connect and monitor cognitive components
    Ensures proper initialization and communication between components
    """
    
    def __init__(self):
        """Initialize the cognitive connector"""
        self.components = {}
        self.model_manager = None
        self.initialization_order = [
            "metacognition",
            "emotional_core",
            "deep_memory",
            "thinking_integration",
            "cognitive_integration",
            "cognitive_model_integration"
        ]
        self.initialization_complete = False
    
    def initialize_all(self, model_manager=None) -> Dict[str, bool]:
        """
        Initialize all cognitive components in the correct order
        
        Args:
            model_manager: Optional model manager to connect with components
            
        Returns:
            Dictionary mapping component names to initialization status
        """
        self.model_manager = model_manager
        results = {}
        
        # First phase: Load each component
        for component_name in self.initialization_order:
            results[component_name] = self._initialize_component(component_name)
        
        # Second phase: Connect components to each other
        self._connect_components()
        
        # Track initialization completion
        self.initialization_complete = all(results.values())
        
        return results
    
    def _initialize_component(self, component_name: str) -> bool:
        """
        Initialize a single cognitive component
        
        Args:
            component_name: Name of the component to initialize
            
        Returns:
            True if initialization was successful
        """
        # Skip if already initialized
        if component_name in self.components:
            return True
            
        try:
            # Try to import the component
            module_path = f"modules.{component_name}"
            logger.info(f"Initializing cognitive component: {component_name}")
            
            try:
                module = importlib.import_module(module_path)
            except ImportError:
                logger.warning(f"Module {module_path} not found")
                return False
            
            # Get the component instance
            if hasattr(module, 'get_instance'):
                instance = module.get_instance()
                self.components[component_name] = instance
                logger.info(f"Successfully initialized {component_name}")
                return True
            else:
                logger.warning(f"Module {module_path} has no get_instance() function")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing {component_name}: {e}")
            return False
    
    def _connect_components(self):
        """Connect components to each other based on dependencies"""
        # Connect cognitive integration with model manager
        if "cognitive_integration" in self.components and self.model_manager:
            try:
                cognitive_integration = self.components["cognitive_integration"]
                if hasattr(cognitive_integration, 'connect_with_model_manager'):
                    cognitive_integration.connect_with_model_manager(self.model_manager)
                    logger.info("Connected cognitive_integration with model_manager")
            except Exception as e:
                logger.error(f"Error connecting cognitive_integration with model_manager: {e}")
        
        # Connect cognitive model integration with model manager
        if "cognitive_model_integration" in self.components and self.model_manager:
            try:
                model_integration = self.components["cognitive_model_integration"]
                if hasattr(model_integration, 'initialize_with_model_manager'):
                    model_integration.initialize_with_model_manager(self.model_manager)
                    logger.info("Connected cognitive_model_integration with model_manager")
            except Exception as e:
                logger.error(f"Error connecting cognitive_model_integration with model_manager: {e}")
    
    def get_component(self, component_name: str) -> Optional[Any]:
        """
        Get a cognitive component by name
        
        Args:
            component_name: Name of the component to get
            
        Returns:
            The component instance or None if not available
        """
        return self.components.get(component_name)
    
    def is_initialized(self) -> bool:
        """
        Check if all components are initialized
        
        Returns:
            True if all required components are initialized
        """
        return self.initialization_complete
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the status of all cognitive components
        
        Returns:
            Dictionary with component status information
        """
        status = {
            "initialized": self.initialization_complete,
            "components": {},
            "timestamp": time.time()
        }
        
        # Get status of each component
        for name, component in self.components.items():
            if hasattr(component, 'get_status'):
                try:
                    component_status = component.get_status()
                    status["components"][name] = component_status
                except Exception as e:
                    status["components"][name] = {"error": str(e)}
            else:
                # Basic status if no get_status method
                status["components"][name] = {"available": True}
        
        # Check for missing components
        for component_name in self.initialization_order:
            if component_name not in self.components:
                status["components"][component_name] = {"available": False}
        
        return status
    
    def process_message(self, message: str) -> Dict[str, Any]:
        """
        Process a message through the cognitive architecture
        
        Args:
            message: The message to process
            
        Returns:
            Processing results from cognitive components
        """
        results = {
            "success": False,
            "insights": [],
            "components_used": []
        }
        
        # Use cognitive integration if available
        if "cognitive_integration" in self.components:
            try:
                cognitive_integration = self.components["cognitive_integration"]
                if hasattr(cognitive_integration, 'process_user_message'):
                    cognitive_results = cognitive_integration.process_user_message(message)
                    results.update(cognitive_results)
                    results["success"] = True
                    results["components_used"].append("cognitive_integration")
            except Exception as e:
                logger.error(f"Error processing message through cognitive_integration: {e}")
        
        # Use metacognition directly if cognitive integration is not available
        elif "metacognition" in self.components:
            try:
                metacognition = self.components["metacognition"]
                if hasattr(metacognition, 'process_message'):
                    metacognition_results = metacognition.process_message(message)
                    results["metacognition"] = metacognition_results
                    if "insights" in metacognition_results:
                        results["insights"].extend(metacognition_results["insights"])
                    results["success"] = True
                    results["components_used"].append("metacognition")
            except Exception as e:
                logger.error(f"Error processing message through metacognition: {e}")
        
        # Use emotional core directly if available
        if "emotional_core" in self.components and "emotional_core" not in results["components_used"]:
            try:
                emotional_core = self.components["emotional_core"]
                if hasattr(emotional_core, 'process_user_message'):
                    emotional_results = emotional_core.process_user_message(message)
                    results["emotional"] = emotional_results
                    results["success"] = True
                    results["components_used"].append("emotional_core")
            except Exception as e:
                logger.error(f"Error processing message through emotional_core: {e}")
        
        return results
    
    def generate_reflection(self, topic: str = None) -> Optional[str]:
        """
        Generate a reflection using available cognitive components
        
        Args:
            topic: Optional topic to focus the reflection on
            
        Returns:
            Generated reflection or None if not available
        """
        # Try cognitive model integration first
        if "cognitive_model_integration" in self.components:
            try:
                model_integration = self.components["cognitive_model_integration"]
                if hasattr(model_integration, 'generate_reflection'):
                    result = model_integration.generate_reflection(topic=topic)
                    if result and result.get("success"):
                        return result["reflection"]
            except Exception as e:
                logger.error(f"Error generating reflection through model_integration: {e}")
        
        # Fall back to cognitive integration
        if "cognitive_integration" in self.components:
            try:
                cognitive_integration = self.components["cognitive_integration"]
                if hasattr(cognitive_integration, 'generate_daily_reflection'):
                    reflection = cognitive_integration.generate_daily_reflection()
                    return reflection
            except Exception as e:
                logger.error(f"Error generating reflection through cognitive_integration: {e}")
        
        return None

# Singleton instance
_connector_instance = None

def get_connector() -> CognitiveConnector:
    """Get the singleton instance of CognitiveConnector"""
    global _connector_instance
    if _connector_instance is None:
        _connector_instance = CognitiveConnector()
    return _connector_instance

def initialize_cognitive_components(model_manager=None) -> Dict[str, bool]:
    """
    Initialize all cognitive components
    
    Args:
        model_manager: Optional model manager to connect with components
        
    Returns:
        Dictionary mapping component names to initialization status
    """
    connector = get_connector()
    return connector.initialize_all(model_manager)

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Test the connector
    connector = get_connector()
    
    # Initialize components
    initialization_results = connector.initialize_all()
    print(f"Initialization results: {initialization_results}")
    
    # Test processing a message
    if connector.is_initialized():
        results = connector.process_message("Hello, I'm testing the cognitive connector!")
        print(f"Processing results: {results}")
        
        # Test generating a reflection
        reflection = connector.generate_reflection("cognitive systems")
        if reflection:
            print(f"Generated reflection: {reflection}")
        else:
            print("No reflection generated")
    
    # Print status
    status = connector.get_status()
    print(f"Cognitive components status: {status}")
