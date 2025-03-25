"""
Cognitive Integration module for Lyra
Connects metacognition, emotional core, and deep memory to create a cohesive cognitive architecture
"""

import os
import time
import logging
import random
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Set up logging
logger = logging.getLogger("cognitive_integration")

class CognitiveArchitecture:
    """
    Integrates metacognition, emotional core, and deep memory
    to create a more sophisticated cognitive system
    """
    
    def __init__(self):
        self.modules_loaded = {}
        self.components = {}
        self._load_components()
        
        # Integration parameters
        self.reflection_threshold = 0.7  # Threshold for triggering reflection
        self.last_reflection_time = 0
        self.min_reflection_interval = 60 * 60  # Minimum seconds between reflections
        self.metacognition_enabled = True
        self.deep_memory_enabled = True
        self.model_manager = None
    
    def _load_components(self):
        """Load all available cognitive components"""
        # Try to load metacognition module
        try:
            from modules.metacognition import get_instance as get_metacognition
            self.components["metacognition"] = get_metacognition()
            self.modules_loaded["metacognition"] = True
            logger.info("Metacognition module loaded successfully")
        except ImportError:
            logger.warning("Metacognition module not available")
            self.modules_loaded["metacognition"] = False
        
        # Try to load emotional core
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            self.components["emotional_core"] = get_emotional_core()
            self.modules_loaded["emotional_core"] = True
            logger.info("Emotional core module loaded successfully")
        except ImportError:
            logger.warning("Emotional core module not available")
            self.modules_loaded["emotional_core"] = False
        
        # Try to load deep memory
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            self.components["deep_memory"] = get_deep_memory()
            self.modules_loaded["deep_memory"] = True
            logger.info("Deep memory module loaded successfully")
        except ImportError:
            logger.warning("Deep memory module not available")
            self.modules_loaded["deep_memory"] = False
        
        # Try to load screen awareness
        try:
            from modules.screen_awareness import get_instance as get_screen_awareness
            self.components["screen_awareness"] = get_screen_awareness()
            self.modules_loaded["screen_awareness"] = True
            logger.info("Screen awareness module loaded successfully")
        except ImportError:
            logger.warning("Screen awareness module not available")
            self.modules_loaded["screen_awareness"] = False
    
    def connect_with_model_manager(self, model_manager):
        """Connect with a model manager for LLM capabilities"""
        self.model_manager = model_manager
        logger.info(f"Connected with model manager: {self.model_manager}")
        
        # Optional: Initialize model integration if available
        try:
            from modules.cognitive_model_integration import get_instance as get_model_integration
            self.model_integration = get_model_integration(model_manager)
            self.modules_loaded["model_integration"] = True
            logger.info("Model integration module initialized")
        except ImportError:
            logger.warning("Model integration module not available")
            self.modules_loaded["model_integration"] = False
            
        return True
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message through all cognitive components
        
        Args:
            message: The user's message
            
        Returns:
            Dict containing results from all components and integrated insights
        """
        results = {
            "metacognition": None,
            "emotional": None,
            "memories": None,
            "should_reflect": False,
            "insights": []
        }
        
        # Process through metacognition if available
        if self.modules_loaded.get("metacognition") and self.metacognition_enabled:
            meta_results = self.components["metacognition"].process_message(message)
            results["metacognition"] = meta_results
            
            # Extract insights
            if "insights" in meta_results:
                results["insights"].extend(meta_results["insights"])
        
        # Process through emotional core if available
        if self.modules_loaded.get("emotional_core"):
            emotion_results = self.components["emotional_core"].process_user_message(message)
            results["emotional"] = emotion_results
            
            # Look for significant emotional changes
            significant_emotions = self._extract_significant_emotions(emotion_results)
            if significant_emotions:
                results["insights"].append(f"Notable emotional response: {', '.join(significant_emotions)}")
        
        # Store in deep memory if available
        if self.modules_loaded.get("deep_memory") and self.deep_memory_enabled:
            # We'll store the actual interaction later when we have the response
            
            # For now, recall similar memories
            similar_memories = self.components["deep_memory"].recall_similar(message, limit=3)
            results["memories"] = similar_memories
            
            # Extract insights from memories
            if similar_memories:
                memory_insight = "This reminds me of previous interactions about "
                topics = []
                
                for memory in similar_memories:
                    if 'tags' in memory and memory['tags']:
                        topics.extend(memory['tags'][:2])  # Take up to 2 tags from each memory
                    elif 'summary' in memory:
                        # Extract potential topic from summary
                        summary_words = memory['summary'].split()
                        if len(summary_words) > 3:
                            topics.append(" ".join(summary_words[:3]) + "...")
                
                # Deduplicate and limit
                unique_topics = list(set(topics))[:3]
                
                if unique_topics:
                    memory_insight += ", ".join(unique_topics)
                    results["insights"].append(memory_insight)
        
        # Check if we should trigger a reflection
        should_reflect = self._should_trigger_reflection(results)
        results["should_reflect"] = should_reflect
        
        return results
    
    def _extract_significant_emotions(self, emotion_results: Dict[str, Any]) -> List[str]:
        """Extract significant emotions from emotional processing results"""
        significant_emotions = []
        
        if not emotion_results:
            return significant_emotions
            
        # Check for significant emotion changes
        if "emotion_changes" in emotion_results:
            for emotion, change in emotion_results["emotion_changes"].items():
                if abs(change) > 0.2:
                    direction = "increase" if change > 0 else "decrease"
                    significant_emotions.append(f"{emotion} ({direction})")
        
        # Check for dominant emotion
        if "dominant_emotion" in emotion_results and emotion_results.get("dominant_emotion"):
            dominant = emotion_results["dominant_emotion"]
            if dominant not in [item.split()[0] for item in significant_emotions]:
                significant_emotions.append(dominant)
        
        return significant_emotions
    
    def _should_trigger_reflection(self, processing_results: Dict[str, Any]) -> bool:
        """Determine if processing results should trigger a reflection"""
        # Check timing - don't reflect too frequently
        current_time = time.time()
        if current_time - self.last_reflection_time < self.min_reflection_interval:
            return False
        
        # Count significant factors that might trigger reflection
        reflection_score = 0.0
        
        # Check for conceptual insights
        if processing_results.get("metacognition") and "insights" in processing_results["metacognition"]:
            reflection_score += min(0.3, len(processing_results["metacognition"]["insights"]) * 0.1)
        
        # Check for significant emotional changes
        if processing_results.get("emotional") and "emotion_changes" in processing_results["emotional"]:
            emotion_changes = processing_results["emotional"]["emotion_changes"]
            significant_changes = sum(1 for change in emotion_changes.values() if abs(change) > 0.2)
            reflection_score += min(0.3, significant_changes * 0.1)
        
        # Check for relevant memories
        if processing_results.get("memories") and len(processing_results["memories"]) > 0:
            # Higher score if memories are highly similar
            if processing_results["memories"][0].get("similarity", 0) > 0.8:
                reflection_score += 0.2
            else:
                reflection_score += 0.1
        
        # Introduce a small random chance for reflection
        reflection_score += random.random() * 0.1
        
        return reflection_score >= self.reflection_threshold
    
    def generate_reflection(self, user_message: str, response: str, 
                          processing_results: Dict[str, Any]) -> Optional[str]:
        """
        Generate a reflection based on the interaction and processing results
        
        Args:
            user_message: The user's message
            response: Lyra's response
            processing_results: Results from processing the message
            
        Returns:
            A reflection text, or None if no reflection was generated
        """
        if not processing_results.get("should_reflect", False):
            return None
            
        # If model integration is available, use it for more sophisticated reflection
        if self.modules_loaded.get("model_integration") and self.model_manager:
            try:
                reflection_result = self.model_integration.generate_reflection(
                    topic=user_message[:50],  # Use part of the message as topic
                    reflection_type="general"
                )
                if reflection_result and reflection_result.get("success"):
                    return reflection_result["reflection"]
            except Exception as e:
                logger.error(f"Error using model integration for reflection: {e}")
                # Fall back to template-based reflection
        
        # Template-based reflection if no model integration or it failed
        reflection_text = "Reflection:\n"
        
        # Add context from metacognition
        if processing_results.get("metacognition") and self.modules_loaded.get("metacognition"):
            meta = processing_results["metacognition"]
            
            # Get activated concepts
            if "activated_nodes" in meta and meta["activated_nodes"]:
                concepts = [node[0] for node in meta["activated_nodes"][:3]]
                if concepts:
                    reflection_text += f"Concepts involved: {', '.join(concepts)}\n"
            
            # Add extracted concepts if available
            if "extracted_concepts" in meta and meta["extracted_concepts"]:
                reflection_text += f"New concepts: {', '.join(meta['extracted_concepts'][:3])}\n"
        
        # Add emotional context
        if processing_results.get("emotional") and self.modules_loaded.get("emotional_core"):
            emotional = processing_results["emotional"]
            
            if "dominant_emotion" in emotional:
                reflection_text += f"Dominant emotion: {emotional['dominant_emotion']}\n"
            
            if "behavior_detected" in emotional and emotional["behavior_detected"]:
                reflection_text += f"Detected behavior: {emotional['behavior_detected']}\n"
        
        # Add memory connections
        if processing_results.get("memories") and self.modules_loaded.get("deep_memory"):
            memories = processing_results["memories"]
            
            if memories:
                reflection_text += "Related memories:\n"
                for memory in memories[:2]:  # Limit to 2 for brevity
                    summary = memory.get("summary", "")
                    if not summary and "content" in memory:
                        content = memory["content"]
                        summary = content[:50] + "..." if len(content) > 50 else content
                    
                    reflection_text += f"- {summary}\n"
        
        # Add reflective conclusion
        reflection_text += "\nThoughts:\n"
        
        # For now, use template-based reflection - in a real implementation, 
        # this would use an LLM to generate more sophisticated reflections
        templates = [
            "This interaction helps me better understand the user's interests in {topics}.",
            "I notice that discussions about {topics} often involve {emotion} emotions.",
            "I'm developing a better grasp of how to respond to inquiries about {topics}.",
            "My understanding of {topics} continues to evolve through these interactions.",
            "I should remember the user's interest in {topics} for future reference."
        ]
        
        # Extract topics from processing results
        topics = []
        
        # From metacognition
        if processing_results.get("metacognition"):
            meta = processing_results["metacognition"]
            if "extracted_concepts" in meta:
                topics.extend(meta["extracted_concepts"][:2])
            
            if "activated_nodes" in meta and meta["activated_nodes"]:
                topics.extend([node[0] for node in meta["activated_nodes"][:2]])
        
        # From memory tags
        if processing_results.get("memories"):
            for memory in processing_results.get("memories", []):
                for tag in memory.get("tags", []):
                    if not tag.startswith("source:") and not tag.startswith("emotion:"):
                        topics.append(tag)
        
        # Deduplicate and limit
        unique_topics = list(set(topics))[:3]
        if not unique_topics:
            unique_topics = ["this subject"]
        
        # Get emotion if available
        emotion = "neutral"
        if processing_results.get("emotional") and processing_results["emotional"].get("dominant_emotion"):
            emotion = processing_results["emotional"]["dominant_emotion"]
        
        # Select and fill a template
        selected_template = random.choice(templates)
        reflection_conclusion = selected_template.format(
            topics=", ".join(unique_topics),
            emotion=emotion
        )
        
        reflection_text += reflection_conclusion
        
        # Record that we generated a reflection
        self.last_reflection_time = time.time()
        
        return reflection_text
    
    def store_interaction_with_response(self, user_message: str, response: str, 
                                       reflection: str = None,
                                       processing_results: Dict[str, Any] = None) -> str:
        """
        Store a complete interaction with response in memory
        
        Args:
            user_message: The user's message
            response: Lyra's response
            reflection: Optional reflection on the interaction
            processing_results: Results from processing the message
            
        Returns:
            Memory ID of the stored interaction, or None if storage failed
        """
        if not self.modules_loaded.get("deep_memory") or not self.deep_memory_enabled:
            return None
            
        try:
            # Extract emotional state if available
            emotional_state = None
            if processing_results and "emotional" in processing_results and processing_results["emotional"]:
                dominant_emotion = processing_results["emotional"].get("dominant_emotion")
                
                if dominant_emotion:
                    # Create a simplified emotional state representation
                    emotional_state = {
                        "dominant_emotion": dominant_emotion,
                        "intensity": 0.7,  # Default to moderate intensity if not specified
                        "emotions": {}
                    }
                    
                    # Add individual emotions if available
                    if "emotion_changes" in processing_results["emotional"]:
                        for emotion, change in processing_results["emotional"]["emotion_changes"].items():
                            if change > 0:
                                emotional_state["emotions"][emotion] = min(1.0, 0.5 + change)
                    
                    # If no specific emotions, just use the dominant one
                    if not emotional_state["emotions"] and dominant_emotion:
                        emotional_state["emotions"][dominant_emotion] = 0.7
            
            # Store the interaction
            interaction_id = self.components["deep_memory"].store_interaction(
                user_message=user_message,
                my_response=response,
                emotional_state=emotional_state
            )
            
            # If a reflection was generated, store it as well
            if reflection:
                self.components["deep_memory"].store_reflection(
                    reflection_content=reflection,
                    related_memory_ids=[interaction_id] if interaction_id else None,
                    importance=0.8
                )
                
            return interaction_id
            
        except Exception as e:
            logger.error(f"Error storing interaction with response: {e}")
            return None
    
    def should_generate_daily_reflection(self) -> bool:
        """Determine if it's time to generate a daily reflection"""
        # Simple heuristic: once per day
        if not hasattr(self, 'last_daily_reflection'):
            self.last_daily_reflection = 0
            
        current_time = time.time()
        day_in_seconds = 24 * 60 * 60
        
        return (current_time - self.last_daily_reflection) >= day_in_seconds
    
    def generate_daily_reflection(self) -> Optional[str]:
        """Generate a daily reflection based on recent experiences"""
        if not self.modules_loaded.get("deep_memory"):
            return None
            
        reflection = self.components["deep_memory"].generate_daily_reflection()
        self.last_daily_reflection = time.time()
        return reflection
    
    def generate_integrated_response(self, base_response: str) -> str:
        """Generate a response informed by all awareness types"""
        response = base_response
        
        # Use model integration for enhanced response if available
        if self.modules_loaded.get("model_integration") and self.model_manager:
            try:
                enhanced = self.model_integration.enhance_cognitive_response(
                    base_response=base_response,
                    user_message="",  # We don't have the user message here
                    context={}
                )
                if enhanced:
                    return enhanced
            except Exception as e:
                logger.error(f"Error using model integration for response enhancement: {e}")
                # Fall back to basic integration
        
        # Add emotional coloring if available
        if self.modules_loaded.get("emotional_core"):
            response = self.components["emotional_core"].modulate_response(response)
        
        # Add metacognitive insights if available and appropriate
        if self.modules_loaded.get("metacognition") and self.metacognition_enabled:
            # Randomly add insights about active concepts (30% chance)
            import random
            if random.random() < 0.3:
                active_nodes = self.components["metacognition"].conceptual_network.nodes.values()
                active_nodes = [n for n in active_nodes if n.activation > 0.5]
                
                if active_nodes:
                    # Pick a random active concept
                    concept = random.choice(active_nodes).name
                    insights = self.components["metacognition"].get_insights_for_concept(concept)
                    
                    if insights and len(insights) > 1:
                        insight = random.choice(insights[1:])  # Skip the first one which is just the concept name
                        response += f"\n\nI've been thinking about {concept}. {insight}"
        
        return response

# Singleton instance
_architecture_instance = None

def get_instance():
    """Get the singleton instance of CognitiveArchitecture"""
    global _architecture_instance
    if _architecture_instance is None:
        _architecture_instance = CognitiveArchitecture()
    return _architecture_instance

# Integration function for backward compatibility
def get_integrated_awareness():
    """Legacy function to get the CognitiveArchitecture instance"""
    return get_instance()
