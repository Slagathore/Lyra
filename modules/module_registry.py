"""
Module Registry for Lyra
Manages module initialization order and dependencies
"""

import os
import sys
import time
import logging
import importlib
from typing import Dict, List, Any, Optional, Callable

# Set up logging
logger = logging.getLogger("module_registry")

class ModuleRegistry:
    """
    Manages Lyra's module initialization and dependencies
    Provides a central registry for all modules and their status
    """
    
    def __init__(self):
        self.modules = {}  # name -> module instance
        self.module_status = {}  # name -> initialization status
        self.dependencies = {}  # name -> list of dependency names
        self.initialization_order = []  # ordered list for initialization
        self.module_getters = {}  # name -> getter function
    
    def register_module(self, name: str, getter_func: Callable, 
                       dependencies: List[str] = None, autoload: bool = True):
        """
        Register a module with the registry
        
        Args:
            name: Module name
            getter_func: Function to get module instance (typically get_instance)
            dependencies: List of modules this module depends on
            autoload: Whether to automatically load this module
        """
        self.module_getters[name] = getter_func
        self.module_status[name] = "registered"
        self.dependencies[name] = dependencies or []
        
        # Calculate initialization order if not a circular dependency
        self._update_initialization_order()
        
        # Autoload if requested
        if autoload:
            self.load_module(name)
    
    def _update_initialization_order(self):
        """Calculate module initialization order based on dependencies"""
        # Start with modules with no dependencies
        order = []
        visited = set()
        temp_mark = set()
        
        def visit(module_name):
            """DFS traversal for topological sort"""
            if module_name in temp_mark:
                # Circular dependency, break it
                logger.warning(f"Circular dependency detected for {module_name}")
                return
                
            if module_name not in visited and module_name in self.dependencies:
                temp_mark.add(module_name)
                
                # Visit all dependencies first
                for dep in self.dependencies[module_name]:
                    if dep in self.module_getters:
                        visit(dep)
                
                visited.add(module_name)
                temp_mark.remove(module_name)
                order.append(module_name)
        
        # Visit all modules
        for module_name in self.module_getters.keys():
            if module_name not in visited:
                visit(module_name)
        
        self.initialization_order = order
    
    def load_module(self, name: str) -> bool:
        """
        Load a specific module
        
        Args:
            name: Module name to load
            
        Returns:
            True if successful, False otherwise
        """
        if name not in self.module_getters:
            logger.error(f"Module {name} not registered")
            return False
            
        if name in self.modules:
            logger.debug(f"Module {name} already loaded")
            return True
            
        # Check dependencies
        for dep in self.dependencies.get(name, []):
            if dep not in self.modules:
                # Try to load dependency
                success = self.load_module(dep)
                if not success:
                    logger.error(f"Failed to load dependency {dep} for module {name}")
                    self.module_status[name] = "dependency_failed"
                    return False
        
        # Load the module
        try:
            self.module_status[name] = "loading"
            module_instance = self.module_getters[name]()
            self.modules[name] = module_instance
            self.module_status[name] = "loaded"
            logger.info(f"Loaded module: {name}")
            return True
        except Exception as e:
            logger.error(f"Error loading module {name}: {e}")
            self.module_status[name] = "failed"
            return False
    
    def load_all_modules(self) -> Dict[str, bool]:
        """
        Load all registered modules in dependency order
        
        Returns:
            Dictionary of module names to success status
        """
        results = {}
        
        # Load modules in initialization order
        for name in self.initialization_order:
            results[name] = self.load_module(name)
            
        return results
    
    def get_module(self, name: str) -> Any:
        """
        Get a module instance by name
        
        Args:
            name: Module name
            
        Returns:
            Module instance or None if not loaded
        """
        return self.modules.get(name)
    
    def get_all_modules(self) -> Dict[str, Any]:
        """Get all loaded modules"""
        return self.modules.copy()
    
    def get_status(self, name: str) -> str:
        """
        Get module status by name
        
        Args:
            name: Module name
            
        Returns:
            Status string
        """
        return self.module_status.get(name, "unknown")
    
    def get_all_status(self) -> Dict[str, str]:
        """Get status of all modules"""
        return self.module_status.copy()

# Singleton instance
_registry_instance = None

def get_registry() -> ModuleRegistry:
    """Get the singleton registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModuleRegistry()
        
        # Register core modules
        try:
            from modules.fallback_llm import get_instance as get_fallback_llm
            _registry_instance.register_module("fallback_llm", get_fallback_llm, [])
        except ImportError:
            logger.warning("Fallback LLM not available for registration")
        
        try:
            from modules.extended_thinking import get_instance as get_extended_thinking
            _registry_instance.register_module("extended_thinking", get_extended_thinking, ["fallback_llm"])
        except ImportError:
            logger.warning("Extended thinking not available for registration")
        
        try:
            from modules.boredom import get_instance as get_boredom
            _registry_instance.register_module("boredom", get_boredom, [])
        except ImportError:
            logger.warning("Boredom system not available for registration")
        
        try:
            from modules.boredom_integration import get_instance as get_boredom_integration
            _registry_instance.register_module("boredom_integration", get_boredom_integration, 
                                              ["boredom", "extended_thinking"])
        except ImportError:
            logger.warning("Boredom integration not available for registration")
        
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            _registry_instance.register_module("emotional_core", get_emotional_core, [])
        except ImportError:
            logger.warning("Emotional core not available for registration")
        
        try:
            from modules.metacognition import get_instance as get_metacognition
            _registry_instance.register_module("metacognition", get_metacognition, 
                                              ["emotional_core"])
        except ImportError:
            logger.warning("Metacognition not available for registration")
        
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            _registry_instance.register_module("deep_memory", get_deep_memory, [])
        except ImportError:
            logger.warning("Deep memory not available for registration")
        
        try:
            from modules.code_auditing import get_instance as get_code_auditor
            _registry_instance.register_module("code_auditor", get_code_auditor, [])
        except ImportError:
            logger.warning("Code auditor not available for registration")
        
        try:
            from modules.thinking_integration import get_instance as get_thinking_integration
            _registry_instance.register_module("thinking_integration", get_thinking_integration, 
                                              ["extended_thinking", "emotional_core", "metacognition"])
        except ImportError:
            logger.warning("Thinking integration not available for registration")
        
        try:
            from modules.cognitive_integration import get_instance as get_cognitive_integration
            _registry_instance.register_module("cognitive_integration", get_cognitive_integration,
                                              ["emotional_core", "deep_memory", "metacognition", 
                                               "thinking_integration"])
        except ImportError:
            logger.warning("Cognitive integration not available for registration")
        
        try:
            from voice_interface import get_instance as get_voice_interface
            _registry_instance.register_module("voice_interface", get_voice_interface, [])
        except ImportError:
            logger.warning("Voice interface not available for registration")
            
    return _registry_instance

def initialize_all_modules() -> Dict[str, str]:
    """Initialize all modules and return their status"""
    registry = get_registry()
    registry.load_all_modules()
    return registry.get_all_status()
