"""
Thinking Integration module for Lyra
Connects extended thinking with other cognitive modules
"""

import os
import time
import logging
import threading
from typing import Dict, List, Optional, Any
from pathlib import Path

# Set up logging
logger = logging.getLogger("thinking_integration")

class ThinkingCapabilities:
    """
    Integrates core model, extended thinking, and cognitive modules
    to enable sophisticated thinking processes
    """
    
    def __init__(self):
        self.modules_loaded = {}
        self.components = {}
        self._load_components()
        
        # State tracking
        self.thinking_enabled = True
        self.idle_thinking_enabled = True
        self.core_model_available = False
        self.last_thinking_time = 0
        self.min_thinking_interval = 60  # Minimum seconds between active thinking
        
        # Modifiers
        self.boredom_multiplier = 1.0  # Will be adjusted based on boredom level
        self.emotional_influence = {
            "joy": 0.2,      # Positive - happier = more creative thinking
            "sadness": -0.1,  # Negative - sadder = slower, more deliberate thinking
            "anger": -0.2,    # Negative - frustrated = less focused thinking
            "interest": 0.3,  # Positive - interested = more engaged thinking
            "surprise": 0.2,  # Positive - surprised = more novel connections
            "fear": -0.2,     # Negative - fearful = more cautious thinking
            "trust": 0.1      # Positive - trusting = more open thinking
        }
    
    def _load_components(self):
        """Load all available thinking components"""
        # Try to load deep memory
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            self.components["deep_memory"] = get_deep_memory()
            self.modules_loaded["deep_memory"] = True
            logger.info("Deep memory module loaded for thinking capabilities")
        except ImportError:
            logger.warning("Deep memory module not available")
            self.modules_loaded["deep_memory"] = False
        
        # Try to load extended thinking
        try:
            from modules.extended_thinking import get_instance as get_extended_thinking
            self.components["extended_thinking"] = get_extended_thinking()
            self.modules_loaded["extended_thinking"] = True
            logger.info("Extended thinking module loaded")
        except ImportError:
            logger.warning("Extended thinking module not available")
            self.modules_loaded["extended_thinking"] = False
        
        # Try to load metacognition
        try:
            from modules.metacognition import get_instance as get_metacognition
            self.components["metacognition"] = get_metacognition()
            self.modules_loaded["metacognition"] = True
            logger.info("Metacognition module loaded for thinking")
        except ImportError:
            logger.warning("Metacognition module not available")
            self.modules_loaded["metacognition"] = False
            
        # Try to load code auditing
        try:
            from modules.code_auditing import get_instance as get_code_auditor
            self.components["code_auditor"] = get_code_auditor()
            self.modules_loaded["code_auditor"] = True
            logger.info("Code auditor loaded for analysis capabilities")
        except ImportError:
            logger.warning("Code auditing module not available")
            self.modules_loaded["code_auditor"] = False
            
        # Check if fallback LLM (core model) is available
        try:
            from modules.fallback_llm import get_instance as get_fallback_llm
            self.components["core_model"] = get_fallback_llm()
            self.modules_loaded["core_model"] = True
            self.core_model_available = True
            logger.info("Core model loaded for thinking capabilities")
        except ImportError:
            logger.warning("Core model not available")
            self.modules_loaded["core_model"] = False
            
        # Try to load emotional core for emotional influence
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            self.components["emotional_core"] = get_emotional_core()
            self.modules_loaded["emotional_core"] = True
            logger.info("Emotional core loaded for thinking influence")
        except ImportError:
            logger.warning("Emotional core not available")
            self.modules_loaded["emotional_core"] = False
            
        # Try to load boredom system for dynamic thinking adjustment
        try:
            from modules.boredom import get_instance as get_boredom
            self.components["boredom"] = get_boredom()
            self.modules_loaded["boredom"] = True
            logger.info("Boredom system loaded for dynamic thinking adjustment")
        except ImportError:
            logger.warning("Boredom system not available")
            self.modules_loaded["boredom"] = False
    
    def connect_model_manager(self, model_manager):
        """Connect model manager for access to additional models"""
        # Connect extended thinking if available
        if self.modules_loaded.get("extended_thinking"):
            self.components["extended_thinking"].connect_model_manager(model_manager)
            
        # Connect code auditor if available
        if self.modules_loaded.get("code_auditor") and hasattr(self.components["code_auditor"], "set_llm_interface"):
            # Use best available model for code analysis
            if model_manager and hasattr(model_manager, "get_active_model"):
                active_model = model_manager.get_active_model()
                if active_model:
                    self.components["code_auditor"].set_llm_interface(active_model)
            # Fall back to core model if available
            elif self.modules_loaded.get("core_model"):
                self.components["code_auditor"].set_llm_interface(self.components["core_model"])
                
        logger.info("Connected thinking capabilities with model manager")
    
    def update_thinking_modifiers(self):
        """Update modifiers that affect thinking capabilities based on other modules"""
        # Update boredom multiplier if boredom system is available
        if self.modules_loaded.get("boredom"):
            boredom_level = self.components["boredom"].get_boredom_level()
            # Higher boredom = more likely to engage in extended thinking
            self.boredom_multiplier = 1.0 + (boredom_level * 2.0)
            logger.debug(f"Updated boredom multiplier: {self.boredom_multiplier}")
            
            # If we have extended thinking, adjust task priorities based on boredom
            if self.modules_loaded.get("extended_thinking"):
                ext_thinking = self.components["extended_thinking"]
                # When Lyra is more bored, she thinks more deeply
                if hasattr(ext_thinking.task_manager, "idle_threshold"):
                    # Adjust idle threshold - when bored, start thinking sooner after user inactivity
                    base_threshold = 300  # 5 minutes base
                    adjusted_threshold = max(30, base_threshold * (1.0 - (boredom_level * 0.8)))
                    ext_thinking.task_manager.idle_threshold = adjusted_threshold
        
        # Update emotional influence if emotional core is available
        if self.modules_loaded.get("emotional_core"):
            try:
                # Get current emotional state
                dominant_emotion, intensity = self.components["emotional_core"].get_dominant_emotion()
                
                # Apply emotional influence to thinking systems
                if dominant_emotion in self.emotional_influence:
                    modifier = self.emotional_influence[dominant_emotion] * intensity
                    
                    # If we have extended thinking, apply emotional effects
                    if self.modules_loaded.get("extended_thinking"):
                        ext_thinking = self.components["extended_thinking"]
                        
                        # Modify task progress rates based on emotion
                        # For example, for joyful states, progress slightly faster
                        if hasattr(ext_thinking, "llm_interface"):
                            if modifier > 0:
                                # More progress on positive emotions
                                ext_thinking.llm_interface.thinking_speed_modifier = 1.0 + (modifier * 0.5)
                            else:
                                # Less progress on negative emotions
                                ext_thinking.llm_interface.thinking_speed_modifier = max(0.5, 1.0 + modifier)
                            
                            logger.debug(f"Updated thinking speed modifier to {ext_thinking.llm_interface.thinking_speed_modifier} based on {dominant_emotion}")
            except Exception as e:
                logger.error(f"Error updating emotional influence: {e}")
    
    def record_user_interaction(self):
        """Record that the user has interacted with the system"""
        # Notify extended thinking
        if self.modules_loaded.get("extended_thinking"):
            self.components["extended_thinking"].record_user_interaction()
        
        # Update thinking modifiers after interaction
        self.update_thinking_modifiers()
    
    def enable_all_thinking(self):
        """Enable all thinking capabilities"""
        self.thinking_enabled = True
        self.idle_thinking_enabled = True
        
        # Enable extended thinking
        if self.modules_loaded.get("extended_thinking"):
            self.components["extended_thinking"].enable()
            
        logger.info("All thinking capabilities enabled")
    
    def disable_all_thinking(self):
        """Disable all thinking capabilities"""
        self.thinking_enabled = False
        self.idle_thinking_enabled = False
        
        # Disable extended thinking
        if self.modules_loaded.get("extended_thinking"):
            self.components["extended_thinking"].disable()
            
        logger.info("All thinking capabilities disabled")
    
    def toggle_idle_thinking(self) -> bool:
        """Toggle idle thinking on/off"""
        self.idle_thinking_enabled = not self.idle_thinking_enabled
        
        # Update extended thinking
        if self.modules_loaded.get("extended_thinking"):
            if self.idle_thinking_enabled:
                self.components["extended_thinking"].enable()
            else:
                self.components["extended_thinking"].disable()
                
        logger.info(f"Idle thinking {'enabled' if self.idle_thinking_enabled else 'disabled'}")
        return self.idle_thinking_enabled
    
    def create_thinking_task(self, description: str, task_type: str = "reflection", 
                            priority: float = 0.5, max_duration: int = 600) -> Optional[str]:
        """
        Create a thinking task with adjusted priority based on system state
        
        Args:
            description: What to think about
            task_type: Type of thinking (reflection, exploration, etc.)
            priority: Base priority (0.0 to 1.0)
            max_duration: Maximum duration in seconds
            
        Returns:
            Task ID if successful, None otherwise
        """
        if not self.thinking_enabled or not self.modules_loaded.get("extended_thinking"):
            return None
            
        # Update modifiers before creating task
        self.update_thinking_modifiers()
        
        # Adjust priority based on boredom and emotional state
        adjusted_priority = priority * self.boredom_multiplier
        
        # Ensure priority stays in valid range
        adjusted_priority = max(0.1, min(1.0, adjusted_priority))
        
        # Create task with adjusted priority
        ext_thinking = self.components["extended_thinking"]
        task_id = ext_thinking.create_thinking_task(
            description=description,
            task_type=task_type,
            priority=adjusted_priority,
            max_duration=max_duration
        )
        
        logger.info(f"Created thinking task with priority {adjusted_priority} (base: {priority}, boredom mult: {self.boredom_multiplier})")
        return task_id
    
    def perform_immediate_thinking(self, description: str, task_type: str = "reflection") -> Dict[str, Any]:
        """
        Perform immediate thinking with emotional influence
        
        Args:
            description: What to think about
            task_type: Type of thinking to perform
            
        Returns:
            Dict with thinking results
        """
        if not self.thinking_enabled or not self.modules_loaded.get("extended_thinking"):
            return {"success": False, "error": "Thinking capabilities disabled or unavailable"}
            
        # Update modifiers before thinking
        self.update_thinking_modifiers()
        
        # Get emotional context if available
        emotional_context = None
        if self.modules_loaded.get("emotional_core"):
            try:
                dominant_emotion, intensity = self.components["emotional_core"].get_dominant_emotion()
                mood = self.components["emotional_core"].get_mood_description()
                
                emotional_context = {
                    "dominant_emotion": dominant_emotion,
                    "intensity": intensity,
                    "mood": mood
                }
            except Exception as e:
                logger.error(f"Error getting emotional context: {e}")
        
        # Add emotional context to thinking prompt if available
        if emotional_context:
            if "reflection" in task_type.lower():
                # For reflections, include emotional state in the thinking
                description += f"\n\nConsider how my current emotional state ({emotional_context['dominant_emotion']}, {emotional_context['mood']}) affects my perspective on this."
            
        # Perform the thinking
        ext_thinking = self.components["extended_thinking"]
        result = ext_thinking.perform_immediate_thinking(
            description=description,
            task_type=task_type
        )
        
        return result
    
    def get_thinking_state(self) -> Dict[str, Any]:
        """Get the current state of thinking activities"""
        if not self.modules_loaded.get("extended_thinking"):
            return {"enabled": self.thinking_enabled, "error": "Extended thinking not available"}
            
        # Get state from extended thinking
        state = self.components["extended_thinking"].get_thinking_state()
        
        # Add additional info
        state["boredom_multiplier"] = self.boredom_multiplier
        
        # Add emotional influence if available
        if self.modules_loaded.get("emotional_core"):
            try:
                dominant_emotion, intensity = self.components["emotional_core"].get_dominant_emotion()
                emotional_effect = "neutral"
                
                if dominant_emotion in self.emotional_influence:
                    effect = self.emotional_influence[dominant_emotion] * intensity
                    if effect > 0.1:
                        emotional_effect = "positive"
                    elif effect < -0.1:
                        emotional_effect = "negative"
                
                state["emotional_influence"] = {
                    "dominant_emotion": dominant_emotion,
                    "effect": emotional_effect,
                    "intensity": intensity
                }
            except Exception as e:
                logger.error(f"Error getting emotional influence: {e}")
        
        return state
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        if self.modules_loaded.get("extended_thinking"):
            self.components["extended_thinking"].cleanup()

# Singleton instance
_thinking_capabilities_instance = None

def get_instance():
    """Get the singleton instance of ThinkingCapabilities"""
    global _thinking_capabilities_instance
    if _thinking_capabilities_instance is None:
        _thinking_capabilities_instance = ThinkingCapabilities()
    return _thinking_capabilities_instance
