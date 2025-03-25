"""
Integration module to connect metacognition with other Lyra components
"""

import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger("metacognition_integration")

class LyraIntegratedAwareness:
    """Integrates emotional, screen, and metacognitive awareness"""
    
    def __init__(self):
        # Import modules (delayed import to avoid circular references)
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            self.emotional_core = get_emotional_core()
            self.has_emotions = True
        except ImportError:
            logger.warning("Emotional core not available")
            self.has_emotions = False
        
        try:
            from modules.screen_awareness import get_instance as get_screen_awareness
            self.screen_awareness = get_screen_awareness()
            self.has_screen_awareness = True
        except ImportError:
            logger.warning("Screen awareness not available")
            self.has_screen_awareness = False
            
        try:
            from modules.metacognition import get_instance as get_metacognition
            self.metacognition = get_metacognition()
            self.has_metacognition = True
        except ImportError:
            logger.warning("Metacognition module not available")
            self.has_metacognition = False
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """Process a user message through all awareness modules"""
        results = {
            "emotional": None,
            "metacognitive": None,
            "screen": None
        }
        
        # Process through emotional core
        if self.has_emotions:
            results["emotional"] = self.emotional_core.process_user_message(message)
            
        # Process through metacognition
        if self.has_metacognition:
            # Pass emotional state as context if available
            emotional_context = results["emotional"] if results["emotional"] else None
            results["metacognitive"] = self.metacognition.process_message(message, context={"emotional_state": emotional_context})
            
        # Check if message references screen content
        if self.has_screen_awareness and any(keyword in message.lower() for keyword in ["screen", "see", "looking", "showing"]):
            if self.screen_awareness.enabled:
                screen_state = self.screen_awareness.get_current_screen_state()
                results["screen"] = {"description": self.screen_awareness.describe_screen()}
                
                # If metacognition is available, process screen content conceptually
                if self.has_metacognition and "text" in screen_state:
                    screen_concepts = self.metacognition.self_reflection.extract_concepts(screen_state["text"])
                    for concept in screen_concepts:
                        self.metacognition.conceptual_network.add_node(
                            concept, 
                            "screen_content", 
                            f"Concept observed on screen at {screen_state.get('timestamp')}"
                        )
                    results["screen"]["extracted_concepts"] = screen_concepts
            else:
                results["screen"] = {"error": "Screen awareness not enabled"}
        
        return results
    
    def generate_integrated_response(self, base_response: str) -> str:
        """Generate a response informed by all awareness types"""
        response = base_response
        
        # Add emotional coloring if available
        if self.has_emotions:
            response = self.emotional_core.modulate_response(response)
        
        # Add metacognitive insights if available and appropriate
        if self.has_metacognition and self.metacognition.enabled:
            # Randomly add insights about active concepts (30% chance)
            import random
            if random.random() < 0.3:
                active_nodes = self.metacognition.conceptual_network.nodes.values()
                active_nodes = [n for n in active_nodes if n.activation > 0.5]
                
                if active_nodes:
                    # Pick a random active concept
                    concept = random.choice(active_nodes).name
                    insights = self.metacognition.get_insights_for_concept(concept)
                    
                    if insights and len(insights) > 1:
                        insight = random.choice(insights[1:])  # Skip the first one which is just the concept name
                        response += f"\n\nI've been thinking about {concept}. {insight}"
        
        return response

# Singleton instance
_integration_instance = None

def get_integrated_awareness():
    """Get the singleton instance of LyraIntegratedAwareness"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = LyraIntegratedAwareness()
    return _integration_instance
