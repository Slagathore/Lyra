"""
Integration module to connect Lyra's cognitive systems with LLM models
Enables advanced capabilities when appropriate models are available
"""

import os
import time
import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

# Set up logging
logger = logging.getLogger("cognitive_model_integration")

class ModelIntegration:
    """
    Handles integration between cognitive modules and language models,
    enabling more sophisticated cognitive processing when models are available
    """
    
    def __init__(self, model_manager=None):
        """Initialize the integration with optional model manager"""
        self.model_manager = model_manager
        self.llm_available = False
        self.can_generate_embeddings = False
        self.can_generate_summaries = False
        self.loaded_modules = {}
        
        # Check which cognitive modules are available
        self._detect_cognitive_modules()
        
        # If model manager was provided, initialize with it
        if model_manager:
            self.initialize_with_model_manager(model_manager)
    
    def _detect_cognitive_modules(self):
        """Detect which cognitive modules are available"""
        try:
            from modules.metacognition import get_instance as get_metacognition
            self.metacognition = get_metacognition()
            self.loaded_modules["metacognition"] = True
            logger.info("Detected metacognition module")
        except ImportError:
            self.loaded_modules["metacognition"] = False
            logger.info("Metacognition module not available")
        
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            self.deep_memory = get_deep_memory()
            self.loaded_modules["deep_memory"] = True
            logger.info("Detected deep memory module")
        except ImportError:
            self.loaded_modules["deep_memory"] = False
            logger.info("Deep memory module not available")
        
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            self.emotional_core = get_emotional_core()
            self.loaded_modules["emotional_core"] = True
            logger.info("Detected emotional core module")
        except ImportError:
            self.loaded_modules["emotional_core"] = False
            logger.info("Emotional core module not available")
        
        try:
            from modules.cognitive_integration import get_instance as get_cognitive_architecture
            self.cognitive_architecture = get_cognitive_architecture()
            self.loaded_modules["cognitive_architecture"] = True
            logger.info("Detected cognitive architecture")
        except ImportError:
            self.loaded_modules["cognitive_architecture"] = False
            logger.info("Cognitive architecture not available")
    
    def initialize_with_model_manager(self, model_manager) -> bool:
        """
        Initialize integration with the model manager
        
        Args:
            model_manager: The ModelManager instance
            
        Returns:
            True if initialization was successful
        """
        self.model_manager = model_manager
        
        # Check if we have an active LLM
        active_model = None
        if hasattr(model_manager, 'get_active_model'):
            active_model = model_manager.get_active_model()
        
        self.llm_available = active_model is not None
        
        if self.llm_available:
            logger.info(f"LLM integration enabled with model: {active_model.name}")
            
            # Determine available capabilities based on model type
            self.can_generate_embeddings = hasattr(active_model, 'get_embeddings')
            self.can_generate_summaries = True  # Assume any LLM can generate summaries
            
            # Now connect with the cognitive architecture if available
            if self.loaded_modules["cognitive_architecture"]:
                self.cognitive_architecture.connect_with_model_manager(model_manager)
                
            return True
        else:
            logger.warning("No active LLM available. Advanced cognitive features will be limited.")
            return False
    
    def generate_concept_description(self, concept: str) -> Dict[str, Any]:
        """
        Generate a detailed description of a concept using the LLM
        
        Args:
            concept: The concept to describe
            
        Returns:
            Dictionary with description and related information
        """
        if not self.llm_available or not self.model_manager:
            return {"success": False, "error": "No LLM available for concept description"}
        
        try:
            # Create a prompt for the concept description
            prompt = f"""Generate a detailed description of the concept: "{concept}"

Please include:
1. A clear definition of the concept
2. Key aspects or components
3. Related concepts or ideas
4. Practical applications or importance
5. Any relevant context or background

Format your response as a comprehensive but concise explanation of this concept.
"""
            
            # Get the active model and generate the description
            active_model = self.model_manager.get_active_model()
            response = active_model.generate(prompt, max_tokens=500)
            
            # Return the response in a structured format
            return {
                "success": True,
                "concept": concept,
                "description": response,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error generating concept description for '{concept}': {e}")
            return {
                "success": False,
                "concept": concept,
                "error": str(e)
            }
    
    def generate_reflection(self, topic: str = None, reflection_type: str = "general") -> Dict[str, Any]:
        """
        Generate a sophisticated reflection using the LLM and cognitive modules
        
        Args:
            topic: Optional topic to focus the reflection on
            reflection_type: Type of reflection to generate
            
        Returns:
            Dictionary with the reflection and metadata
        """
        if not self.llm_available or not self.model_manager:
            return {"success": False, "error": "No LLM available for reflection"}
        
        try:
            # Gather context from cognitive modules
            context = {
                "emotional_state": None,
                "active_concepts": [],
                "goals": [],
                "recent_memories": []
            }
            
            # Get emotional state if available
            if self.loaded_modules["emotional_core"]:
                try:
                    dominant_emotion, intensity = self.emotional_core.get_dominant_emotion()
                    mood = self.emotional_core.get_mood_description()
                    
                    context["emotional_state"] = {
                        "dominant_emotion": dominant_emotion,
                        "intensity": intensity,
                        "mood": mood
                    }
                except Exception as e:
                    logger.warning(f"Error getting emotional state for reflection: {e}")
            
            # Get active concepts if available
            if self.loaded_modules["metacognition"]:
                try:
                    active_nodes = self.metacognition.get_activated_nodes(limit=5)
                    context["active_concepts"] = active_nodes
                    
                    # Get goals
                    goals = self.metacognition.get_active_goals()
                    context["goals"] = goals
                except Exception as e:
                    logger.warning(f"Error getting metacognitive data for reflection: {e}")
            
            # Get recent memories if available
            if self.loaded_modules["deep_memory"]:
                try:
                    memories = self.deep_memory.get_recent_memories(limit=3)
                    context["recent_memories"] = memories
                except Exception as e:
                    logger.warning(f"Error getting memories for reflection: {e}")
            
            # Create the reflection prompt
            prompt = self._create_reflection_prompt(
                topic=topic or "my current state",
                reflection_type=reflection_type,
                context=context
            )
            
            # Generate the reflection
            active_model = self.model_manager.get_active_model()
            reflection = active_model.generate(prompt, max_tokens=800)
            
            return {
                "success": True,
                "reflection": reflection,
                "topic": topic,
                "type": reflection_type,
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Error generating reflection: {e}")
            return {
                "success": False,
                "error": str(e),
                "topic": topic,
                "type": reflection_type
            }
    
    def _create_reflection_prompt(self, topic: str, reflection_type: str, context: Dict[str, Any]) -> str:
        """Create a prompt for the reflection generation"""
        # Base prompt components
        if reflection_type == "general":
            base_prompt = f"I want to reflect on {topic}. I'll consider my current state, thoughts, and experiences."
        elif reflection_type == "emotional":
            base_prompt = f"I want to reflect on my emotional state regarding {topic}. How do I feel about this?"
        elif reflection_type == "knowledge":
            base_prompt = f"I want to reflect on my understanding of {topic}. What do I know about this subject?"
        elif reflection_type == "goals":
            base_prompt = f"I want to reflect on my goals related to {topic}. What am I trying to achieve?"
        else:
            base_prompt = f"I want to reflect on {topic} from various perspectives."
            
        # Add topic if provided
        if topic:
            base_prompt += f"\nThe focus of this reflection is: {topic}"
        
        # Add context from cognitive modules
        context_sections = []
        
        # Add emotional context
        if context["emotional_state"]:
            emotional_context = "My current emotional state:\n"
            emotional_state = context["emotional_state"]
            emotional_context += f"- Feeling {emotional_state['dominant_emotion']} with intensity {emotional_state['intensity']:.1f}\n"
            emotional_context += f"- Overall mood: {emotional_state['mood']}\n"
            context_sections.append(emotional_context)
        
        # Add active concepts
        if context["active_concepts"]:
            concept_context = "Concepts I'm thinking about:\n"
            for concept, activation in context["active_concepts"]:
                concept_context += f"- {concept} (activation: {activation:.2f})\n"
            context_sections.append(concept_context)
        
        # Add goals
        if context["goals"]:
            goals_context = "My current goals:\n"
            for goal in context["goals"]:
                name = goal.get("name", "Unnamed goal")
                description = goal.get("description", "No description")
                progress = goal.get("progress", 0.0)
                goals_context += f"- {name}: {description} (progress: {progress:.0%})\n"
            context_sections.append(goals_context)
        
        # Add memories
        if context["recent_memories"]:
            memories_context = "Recent experiences:\n"
            for memory in context["recent_memories"]:
                memories_context += f"- {memory['summary']}\n"
            context_sections.append(memories_context)
        
        # Combine all sections
        full_prompt = base_prompt + "\n\n" + "\n".join(context_sections)
        
        # Add final instructions
        full_prompt += """

My reflection should be introspective, show meta-cognitive awareness, and include:
1. Observations about my current state and thinking
2. Insights or patterns I've noticed
3. Questions I might explore further
4. Potential areas for growth or development

Write in first person as if I (Lyra) am reflecting on my own cognitive processes and experiences.
"""
        
        return full_prompt
    
    def enhance_cognitive_response(self, base_response: str, user_message: str, 
                                  context: Dict[str, Any] = None) -> str:
        """
        Enhance a response with cognitive awareness
        
        Args:
            base_response: The original response to enhance
            user_message: The user's message that prompted the response
            context: Additional context for enhancement
            
        Returns:
            Enhanced response with cognitive elements
        """
        if not self.llm_available or not self.model_manager:
            # If no LLM, use the cognitive architecture's basic enhancement
            if self.loaded_modules["cognitive_architecture"]:
                return self.cognitive_architecture.generate_integrated_response(base_response)
            return base_response
        
        try:
            # Gather cognitive context similar to the reflection function
            cognitive_context = {
                "emotional_state": None,
                "active_concepts": [],
                "extracted_concepts": [],
                "user_message": user_message,
                "base_response": base_response
            }
            
            # Additional context if provided
            if context:
                cognitive_context.update(context)
            
            # Get emotional state if available
            if self.loaded_modules["emotional_core"]:
                dominant_emotion, intensity = self.emotional_core.get_dominant_emotion()
                mood = self.emotional_core.get_mood_description()
                
                cognitive_context["emotional_state"] = {
                    "dominant_emotion": dominant_emotion,
                    "intensity": intensity,
                    "mood": mood
                }
            
            # Get active concepts if available
            if self.loaded_modules["metacognition"]:
                # Process the user message to extract concepts
                processing_results = self.metacognition.process_message(user_message)
                cognitive_context["extracted_concepts"] = processing_results.get("extracted_concepts", [])
                cognitive_context["active_concepts"] = processing_results.get("activated_nodes", [])
            
            # Use the model to enhance the response
            active_model = self.model_manager.get_active_model()
            
            # Cognitive enhancement prompt
            prompt = f"""Enhance the following response with cognitive and emotional awareness.

User message: {user_message}

Original response: {base_response}

Cognitive context:
"""

            # Add emotional context if available
            if cognitive_context["emotional_state"]:
                emotional_state = cognitive_context["emotional_state"]
                prompt += f"- Feeling {emotional_state['dominant_emotion']} (intensity: {emotional_state['intensity']:.1f})\n"
                prompt += f"- Overall mood: {emotional_state['mood']}\n"
            
            # Add concepts if available
            if cognitive_context["active_concepts"]:
                prompt += "- Thinking about concepts: "
                concept_names = [name for name, _ in cognitive_context["active_concepts"][:3]]
                prompt += ", ".join(concept_names) + "\n"
            
            prompt += """
Enhance the response by:
1. Reflecting the appropriate emotional tone
2. Including relevant context from active concepts
3. Show metacognitive awareness of my own thinking process

Keep the enhanced response concise and natural. Maintain the core information from the original response.
"""
            
            # Generate the enhanced response
            enhanced_response = active_model.generate(prompt, max_tokens=len(base_response) + 200)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error enhancing response: {e}")
            # Fall back to original response
            return base_response

# Singleton instance
_instance = None

def get_instance(model_manager=None):
    """Get the singleton instance of ModelIntegration"""
    global _instance
    if _instance is None:
        _instance = ModelIntegration(model_manager)
    elif model_manager is not None and _instance.model_manager != model_manager:
        # Update model manager if a new one is provided
        _instance.initialize_with_model_manager(model_manager)
    return _instance
