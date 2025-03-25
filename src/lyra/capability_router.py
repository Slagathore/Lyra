"""
Router for mapping natural language requests to Lyra's capabilities
"""
import re
import inspect
from typing import Dict, Any, Callable, List, Optional
import logging

logger = logging.getLogger(__name__)

class CapabilityRouter:
    """Routes natural language requests to specific Lyra capabilities"""
    
    def __init__(self):
        self.capabilities = {}
        self.patterns = {}
        
    def register(self, name: str, function: Callable, patterns: List[str], description: str = ""):
        """Register a capability with associated trigger patterns"""
        self.capabilities[name] = {
            "function": function,
            "patterns": patterns,
            "description": description,
            "signature": inspect.signature(function)
        }
        
        # Compile regex patterns for efficient matching
        self.patterns[name] = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        
    def find_capability(self, text: str) -> Optional[Dict[str, Any]]:
        """Find the first capability that matches the input text"""
        for name, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    return {
                        "name": name,
                        "capability": self.capabilities[name],
                        "match": pattern.search(text)
                    }
        return None
        
    def route_request(self, text: str) -> Dict[str, Any]:
        """Route a natural language request to the appropriate capability"""
        match = self.find_capability(text)
        if not match:
            return {
                "success": False,
                "error": "No matching capability found",
                "message": "I don't know how to do that yet."
            }
            
        capability = match["capability"]
        function = capability["function"]
        
        try:
            # Extract parameters from text (basic implementation)
            # A more sophisticated implementation would use NLP for parameter extraction
            params = {}
            result = function(**params)
            
            return {
                "success": True,
                "capability": match["name"],
                "result": result
            }
        except Exception as e:
            logger.error(f"Error executing capability {match['name']}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"I encountered an error when trying to {match['name']}: {str(e)}"
            }
            
    def get_available_capabilities(self) -> List[Dict[str, Any]]:
        """Get a list of all available capabilities"""
        return [
            {
                "name": name,
                "description": info["description"],
                "example_triggers": info["patterns"]
            }
            for name, info in self.capabilities.items()
        ]
