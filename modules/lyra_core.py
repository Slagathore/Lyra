"""
Lyra Core module
Central component that connects the UI, system tray, and cognitive architecture
"""

import logging
import time
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger("lyra_core")

class LyraCore:
    """
    Core implementation of Lyra's central processing system
    Connects UI components with cognitive architecture
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls):
        """Get the singleton instance"""
        if cls._instance is None:
            cls._instance = LyraCore()
        return cls._instance
    
    def __init__(self):
        """Initialize the core"""
        self.start_time = time.time()
        self.last_activity = time.time()
        
        # Track connected components
        self.components = {}
        
        # Initialize model manager first as other components depend on it
        self._initialize_model_manager()
        
        # Initialize cognitive components
        self._initialize_cognitive_components()
        
        # Track persistent connections
        self.connected_clients = {}
        
        logger.info("Lyra Core initialized")
    
    def _initialize_model_manager(self):
        """Initialize the model manager"""
        try:
            # Try multiple possible import paths
            try:
                # Try relative import first
                from .model_config import get_manager
            except ImportError:
                try:
                    # Try absolute import from project root
                    from modules.model_config import get_manager
                except ImportError:
                    # Try importing from parent directory
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from model_config import get_manager
            
            self.model_manager = get_manager()
            self.components["model_manager"] = self.model_manager
            logger.info("Model manager initialized")
        except ImportError:
            logger.warning("Model manager not available, using fallback")
            self.model_manager = DummyModelManager()
            self.components["model_manager"] = self.model_manager
    
    def _initialize_cognitive_components(self):
        """Initialize cognitive components"""
        # Initialize cognitive architecture
        try:
            try:
                # Try relative import first
                from .cognitive_integration import get_instance as get_cognitive_architecture
            except ImportError:
                try:
                    # Try absolute import from project root
                    from modules.cognitive_integration import get_instance as get_cognitive_architecture
                except ImportError:
                    # Try importing from parent directory
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from cognitive_integration import get_instance as get_cognitive_architecture
            
        # Initialize model integration
        try:
            try:
                # Try relative import first
                from .cognitive_model_integration import get_instance as get_model_integration
            except ImportError:
                try:
                    # Try absolute import from project root
                    from modules.cognitive_model_integration import get_instance as get_model_integration
                except ImportError:
        # Initialize IO manager
        try:
            try:
                # Try relative import first
                from .io_manager import get_instance as get_io_manager
            except ImportError:
                try:
                    # Try absolute import from project root
                    from modules.io_manager import get_instance as get_io_manager
                except ImportError:
                    # Try importing from parent directory
                    import sys
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from io_manager import get_instance as get_io_manager
            
            self.io_manager = get_io_manager(core_instance=self)
            self.components["io_manager"] = self.io_manager
            logger.info("IO manager initialized")
        except ImportError:
            logger.warning("IO manager not available")
            self.io_manager = None
            logger.warning("Cognitive model integration not available")
            self.model_integration = None
            logger.warning("Cognitive architecture not available")
            self.cognitive_architecture = None
        
        # Initialize model integration
        try:
            from modules.cognitive_model_integration import get_instance as get_model_integration
            self.model_integration = get_model_integration(self.model_manager)
            self.components["model_integration"] = self.model_integration
            logger.info("Cognitive model integration initialized")
        except ImportError:
            logger.warning("Cognitive model integration not available")
            self.model_integration = None
        
        # Initialize IO manager
        try:
            from modules.io_manager import get_instance as get_io_manager
            self.io_manager = get_io_manager(core_instance=self)
            self.components["io_manager"] = self.io_manager
            logger.info("IO manager initialized")
        except ImportError:
            logger.warning("IO manager not available")
            self.io_manager = None
    
    def process_message(self, message, metadata=None):
        """
        Process a message and return a response
        
        Args:
            message: The user's message
            metadata: Additional metadata about the message
            
        Returns:
            Dictionary with the response and metadata
        """
        self.last_activity = time.time()
        
        # Default metadata if none provided
        if metadata is None:
            metadata = {"source": "unknown", "timestamp": time.time()}
        
        try:
            # Log the incoming message
            logger.info(f"Processing message: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # Process through cognitive architecture if available
            cognitive_results = None
            if self.cognitive_architecture:
                try:
                    cognitive_results = self.cognitive_architecture.process_user_message(message)
                    logger.debug(f"Cognitive processing results: {cognitive_results}")
                except Exception as e:
                    logger.error(f"Error in cognitive processing: {e}")
            
            # Generate response using the model manager
            if self.model_manager:
                try:
                    # Get active model
                    active_model = self.model_manager.get_active_model()
                    
                    if active_model:
                        # Generate a response with the model
                        prompt = self._build_prompt(message, cognitive_results)
                        response_text = active_model.generate(prompt)
                        
                        # Enhance the response with cognitive awareness if available
                        if self.model_integration:
                            try:
                                enhanced_response = self.model_integration.enhance_cognitive_response(
                                    base_response=response_text,
                                    user_message=message,
                                    context={
                                        "cognitive_results": cognitive_results,
                                        "metadata": metadata
                                    }
                                )
                                if enhanced_response:
                                    response_text = enhanced_response
                            except Exception as e:
                                logger.error(f"Error enhancing response: {e}")
                        
                        # Generate reflection if needed
                        reflection = None
                        if cognitive_results and cognitive_results.get("should_reflect", False) and self.cognitive_architecture:
                            try:
                                reflection = self.cognitive_architecture.generate_reflection(
                                    user_message=message,
                                    response=response_text,
                                    processing_results=cognitive_results
                                )
                            except Exception as e:
                                logger.error(f"Error generating reflection: {e}")
                        
                        # Store interaction in memory if cognitive architecture is available
                        if self.cognitive_architecture:
                            try:
                                memory_id = self.cognitive_architecture.store_interaction_with_response(
                                    user_message=message,
                                    response=response_text,
                                    reflection=reflection,
                                    processing_results=cognitive_results
                                )
                                logger.debug(f"Stored interaction with ID: {memory_id}")
                            except Exception as e:
                                logger.error(f"Error storing interaction: {e}")
                        
                        # Prepare the response
                        result = {
                            "success": True,
                            "response": response_text,
                            "source": "model",
                            "model": active_model.name if hasattr(active_model, 'name') else "unknown",
                            "reflection": reflection,
                            "insights": cognitive_results.get("insights", []) if cognitive_results else [],
                            "timestamp": time.time()
                        }
                        
                        return result
                    else:
                        logger.warning("No active model available")
                except Exception as e:
                    logger.error(f"Error generating response: {e}")
            
            # Fallback response if model generation failed
            return {
                "success": True,
                "response": f"I processed your message: '{message}', but couldn't generate a proper response.",
                "source": "fallback",
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "success": False,
                "error": str(e),
                "response": "I encountered an error while processing your message.",
                "source": "error",
                "timestamp": time.time()
            }
    
    def _build_prompt(self, message: str, cognitive_results: Optional[Dict[str, Any]] = None) -> str:
        """Build a prompt for the language model based on the message and cognitive results"""
        # Simple prompt with just the message
        prompt = f"User: {message}\n\nAssistant: "
        
        # If we have cognitive results, we could create a more sophisticated prompt
        # This is a simple implementation, but you could make it more complex
        if cognitive_results:
            # Add insights if available
            insights = cognitive_results.get("insights", [])
            if insights:
                insights_str = "\n".join([f"- {insight}" for insight in insights])
                prompt = f"Consider these insights while responding:\n{insights_str}\n\nUser: {message}\n\nAssistant: "
            
            # Add emotional context if available
            emotional = cognitive_results.get("emotional")
            if emotional and "dominant_emotion" in emotional:
                dominant_emotion = emotional["dominant_emotion"]
                prompt = f"The user seems to be feeling {dominant_emotion}.\n\nUser: {message}\n\nAssistant: "
        
        return prompt
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the core and its components
        
        Returns:
            Dictionary with status information
        """
        uptime = time.time() - self.start_time
        
        status = {
            "status": "running",
            "uptime": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "last_activity": time.time() - self.last_activity,
            "last_activity_formatted": self._format_uptime(time.time() - self.last_activity),
            "components": {}
        }
        
        # Add component status
        for name, component in self.components.items():
            if hasattr(component, 'get_status'):
                try:
                    component_status = component.get_status()
                    status["components"][name] = component_status
                except Exception as e:
                    status["components"][name] = {"error": str(e)}
            else:
                status["components"][name] = {"status": "active"}
        
        # Add model info if available
        if self.model_manager:
            active_model = self.model_manager.get_active_model()
            if (active_model):
                status["active_model"] = {
                    "name": active_model.name if hasattr(active_model, 'name') else "unknown",
                    "type": active_model.__class__.__name__
                }
            else:
                status["active_model"] = None
        
        return status
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in seconds to a human-readable string"""
        days, remainder = divmod(seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif hours > 0:
            return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        elif minutes > 0:
            return f"{int(minutes)}m {int(seconds)}s"
        else:
            return f"{int(seconds)}s"
    
    def register_client(self, client_id, callback=None):
        """Register a client for callbacks"""
        self.connected_clients[client_id] = {
            "callback": callback,
            "last_seen": time.time()
        }
        logger.info(f"Client {client_id} registered")
        return True
    
    def unregister_client(self, client_id):
        """Unregister a client"""
        if client_id in self.connected_clients:
            del self.connected_clients[client_id]
            logger.info(f"Client {client_id} unregistered")
            return True
        return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration"""
        # Load configuration from file if it exists
        config_file = Path("config/core_config.json")
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        # Default configuration
        return {
            "model": {
                "default_model": "phi2",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "cognitive": {
                "metacognition_enabled": True,
                "emotional_core_enabled": True,
                "deep_memory_enabled": True,
                "reflection_threshold": 0.7,
                "min_reflection_interval": 3600
            },
            "io": {
                "save_chat_history": True,
                "max_chat_history": 100
            }
        }
    
    def update_config(self, config_updates: Dict[str, Any]) -> bool:
        """Update the configuration"""
        try:
            # Get current config
            current_config = self.get_config()
            
            # Recursive update function
            def update_dict(d, u):
                for k, v in u.items():
                    if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                        d[k] = update_dict(d[k], v)
                    else:
                        d[k] = v
                return d
            
            # Update the config
            updated_config = update_dict(current_config, config_updates)
            
            # Save to file
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            with open(config_dir / "core_config.json", "w") as f:
                json.dump(updated_config, f, indent=2)
            
            # Apply updates to components
            self._apply_config_updates(config_updates)
            
            return True
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False
    
    def _apply_config_updates(self, config_updates: Dict[str, Any]):
        """Apply configuration updates to components"""
        # Apply cognitive configuration updates
        if "cognitive" in config_updates and self.cognitive_architecture:
            cognitive_config = config_updates["cognitive"]
            
            # Update metacognition
            if "metacognition_enabled" in cognitive_config:
                self.cognitive_architecture.metacognition_enabled = cognitive_config["metacognition_enabled"]
            
            # Update deep memory
            if "deep_memory_enabled" in cognitive_config:
                self.cognitive_architecture.deep_memory_enabled = cognitive_config["deep_memory_enabled"]
            
            # Update reflection threshold
            if "reflection_threshold" in cognitive_config:
                self.cognitive_architecture.reflection_threshold = cognitive_config["reflection_threshold"]
            
            # Update reflection interval
            if "min_reflection_interval" in cognitive_config:
                self.cognitive_architecture.min_reflection_interval = cognitive_config["min_reflection_interval"]
        
        # Apply model configuration updates
        if "model" in config_updates and self.model_manager:
            model_config = config_updates["model"]
            
            # Update default model
            if "default_model" in model_config:
                try:
                    self.model_manager.load_model(model_config["default_model"])
                except Exception as e:
                    logger.error(f"Error loading default model: {e}")

class DummyModelManager:
    """Simple dummy model manager for when the real one isn't available"""
    
    def __init__(self):
        self.models = {}
        self.active_model = DummyModel("DummyModel")
    
    def get_active_model(self):
        """Get the active model"""
        return self.active_model
    
    def get_status(self):
        """Get the model manager status"""
        return {
            "status": "active",
            "active_model": "dummy",
            "available_models": 0
        }

class DummyModel:
    """Dummy model implementation for testing"""
    
    def __init__(self, name):
        self.name = name
        self.loaded = True
    
    def generate(self, prompt, max_tokens=100):
        """Generate text based on the prompt"""
        return f"This is a dummy response to: {prompt[:50]}..."

# Singleton instance
_core_instance = None

def get_instance():
    """Get the singleton instance"""
    global _core_instance
    if _core_instance is None:
        _core_instance = LyraCore.get_instance()
    return _core_instance

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    # Create an instance of the core
    core = get_instance()
    
    # Test message processing
    response = core.process_message("Hello, Lyra!")
    logger.info(f"Response: {response}")
    
    # Display core status
    status = core.get_status()
    logger.info(f"Core status: {status}")
