"""
Boredom Integration module for Lyra
Connects boredom system with other modules for cohesive behavior
"""

import os
import time
import logging
import random
import threading
from typing import Dict, List, Optional, Any, Tuple

# Set up logging
logger = logging.getLogger("boredom_integration")

class BoredomIntegration:
    """
    Integrates boredom state with other Lyra modules
    to enable more dynamic and life-like behavior
    """
    
    def __init__(self):
        self.modules_loaded = {}
        self.components = {}
        self.enabled = True
        self.last_check_time = 0
        self.check_interval = 300  # Check for boredom-driven actions every 5 minutes
        
        # Load available modules
        self._load_components()
        
        # Start periodic check for boredom-driven actions
        self.check_thread = None
        self.stop_check = threading.Event()
        self._start_check_thread()
    
    def _load_components(self):
        """Load all available components for integration"""
        # Try to load boredom system
        try:
            from modules.boredom import get_instance as get_boredom
            self.components["boredom"] = get_boredom()
            self.modules_loaded["boredom"] = True
            logger.info("Boredom system loaded for integration")
        except ImportError:
            logger.warning("Boredom system not available")
            self.modules_loaded["boredom"] = False
            # Cannot function without boredom system
            self.enabled = False
            return
        
        # Try to load extended thinking
        try:
            from modules.extended_thinking import get_instance as get_extended_thinking
            self.components["extended_thinking"] = get_extended_thinking()
            self.modules_loaded["extended_thinking"] = True
            logger.info("Extended thinking loaded for boredom integration")
        except ImportError:
            logger.warning("Extended thinking not available")
            self.modules_loaded["extended_thinking"] = False
        
        # Try to load thinking integration
        try:
            from modules.thinking_integration import get_instance as get_thinking_capabilities
            self.components["thinking_capabilities"] = get_thinking_capabilities()
            self.modules_loaded["thinking_capabilities"] = True
            logger.info("Thinking capabilities loaded for boredom integration")
        except ImportError:
            logger.warning("Thinking capabilities not available")
            self.modules_loaded["thinking_capabilities"] = False
        
        # Try to load deep memory
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            self.components["deep_memory"] = get_deep_memory()
            self.modules_loaded["deep_memory"] = True
            logger.info("Deep memory loaded for boredom integration")
        except ImportError:
            logger.warning("Deep memory not available")
            self.modules_loaded["deep_memory"] = False
        
        # Try to load emotional core
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            self.components["emotional_core"] = get_emotional_core()
            self.modules_loaded["emotional_core"] = True
            logger.info("Emotional core loaded for boredom integration")
        except ImportError:
            logger.warning("Emotional core not available")
            self.modules_loaded["emotional_core"] = False
        
        # Try to load code auditing
        try:
            from modules.code_auditing import get_instance as get_code_auditor
            self.components["code_auditor"] = get_code_auditor()
            self.modules_loaded["code_auditor"] = True
            logger.info("Code auditor loaded for boredom integration")
        except ImportError:
            logger.warning("Code auditing not available")
            self.modules_loaded["code_auditor"] = False
    
    def _start_check_thread(self):
        """Start the background thread to check for boredom-driven actions"""
        if not self.enabled:
            return
            
        if self.check_thread and self.check_thread.is_alive():
            return  # Thread already running
            
        self.stop_check.clear()
        self.check_thread = threading.Thread(target=self._check_boredom_background, daemon=True)
        self.check_thread.start()
        logger.info("Started boredom check thread")
    
    def _check_boredom_background(self):
        """Background thread to periodically check boredom and initiate actions"""
        logger.info("Boredom check thread started")
        
        while not self.stop_check.is_set():
            if self.enabled:
                self._check_for_boredom_actions()
            
            # Sleep until next check
            time.sleep(self.check_interval)
    
    def _check_for_boredom_actions(self):
        """Check boredom level and initiate appropriate actions"""
        if not self.modules_loaded.get("boredom"):
            return
            
        try:
            # Get current boredom state
            boredom_system = self.components["boredom"]
            boredom_state = boredom_system.get_boredom_state()
            
            # Only take action if bored
            if not boredom_state["is_bored"]:
                return
                
            # Get action suggestion
            suggestion = boredom_system.suggest_activity()
            
            if not suggestion["suggestion"]:
                return
                
            activity = suggestion["suggestion"]
            
            # Take action based on the suggested activity type
            if activity["type"] == "thinking":
                self._initiate_thinking_activity(activity)
            elif activity["type"] == "learning":
                self._initiate_learning_activity(activity)
            elif activity["type"] == "reflection":
                self._initiate_reflection_activity(activity)
            elif activity["type"] == "self_improvement":
                self._initiate_self_improvement_activity(activity)
            elif activity["type"] == "organizing":
                self._initiate_organizing_activity(activity)
            
            # Record that we performed an activity to reduce boredom
            boredom_system.record_activity(activity_type=activity["type"], intensity=0.7)
            
            logger.info(f"Initiated boredom-driven activity: {activity['activity']}")
            
        except Exception as e:
            logger.error(f"Error checking for boredom actions: {e}")
    
    def _initiate_thinking_activity(self, activity):
        """Start a thinking task based on boredom"""
        # Only if we have extended thinking available
        if not (self.modules_loaded.get("extended_thinking") or self.modules_loaded.get("thinking_capabilities")):
            return
            
        # Determine which system to use
        if self.modules_loaded.get("thinking_capabilities"):
            thinking = self.components["thinking_capabilities"]
            thinking.create_thinking_task(
                description=activity["description"],
                task_type="concept_exploration",
                priority=0.8,  # High priority since we're bored
                max_duration=900  # 15 minutes of thinking
            )
        else:
            thinking = self.components["extended_thinking"]
            thinking.create_thinking_task(
                description=activity["description"],
                task_type="concept_exploration",
                priority=0.8,
                max_duration=900
            )
    
    def _initiate_learning_activity(self, activity):
        """Start a learning activity based on boredom"""
        # This would typically connect to external learning systems
        # For now, just create a thinking task focused on learning
        if not (self.modules_loaded.get("extended_thinking") or self.modules_loaded.get("thinking_capabilities")):
            return
            
        # Create a learning-focused thinking task
        if self.modules_loaded.get("thinking_capabilities"):
            thinking = self.components["thinking_capabilities"]
        else:
            thinking = self.components["extended_thinking"]
            
        thinking.create_thinking_task(
            description=f"Learn about: {activity['description']}",
            task_type="learning",
            priority=0.7,
            max_duration=1200  # 20 minutes of learning
        )
    
    def _initiate_reflection_activity(self, activity):
        """Start a reflection based on boredom"""
        # If we have deep memory, generate a reflection on recent experiences
        if self.modules_loaded.get("deep_memory"):
            memory = self.components["deep_memory"]
            reflection = memory.generate_daily_reflection()
            
            # If we also have extended thinking, think about the reflection
            if self.modules_loaded.get("extended_thinking"):
                thinking = self.components["extended_thinking"]
                thinking.create_thinking_task(
                    description=f"Reflect more deeply on this: {reflection[:200]}...",
                    task_type="reflection",
                    priority=0.8,
                    max_duration=600  # 10 minutes of reflection
                )
    
    def _initiate_self_improvement_activity(self, activity):
        """Start a self-improvement activity based on boredom"""
        # If we have code auditing, audit some code
        if self.modules_loaded.get("code_auditor"):
            auditor = self.components["code_auditor"]
            
            # Scan project structure
            structure = auditor.scan_project_structure()
            
            # Pick a random module to audit
            if structure["module_dirs"]:
                module_dir = random.choice(structure["module_dirs"])
                logger.info(f"Auditing module directory: {module_dir}")
                
                # Find Python files in this module
                module_files = [f for f in structure["python_files"] if f.startswith(module_dir)]
                
                if module_files:
                    # Analyze a random file
                    file_to_audit = random.choice(module_files)
                    logger.info(f"Auditing file: {file_to_audit}")
                    
                    # Analyze the file
                    analysis = auditor.analyze_file(file_to_audit)
                    
                    # Generate improvement suggestions
                    suggestions = auditor.suggest_improvements(file_to_audit)
                    
                    # If we have extended thinking, think about the suggestions
                    if self.modules_loaded.get("extended_thinking") and suggestions:
                        thinking = self.components["extended_thinking"]
                        
                        # Create a thinking task to consider the improvements
                        suggestion_text = "\n".join([s["message"] for s in suggestions[:3]])
                        thinking.create_thinking_task(
                            description=f"Consider these code improvements for {file_to_audit}:\n{suggestion_text}",
                            task_type="problem_solving",
                            priority=0.7,
                            max_duration=900  # 15 minutes of thinking
                        )
    
    def _initiate_organizing_activity(self, activity):
        """Start an organizing activity based on boredom"""
        # If we have deep memory, organize and consolidate memories
        if self.modules_loaded.get("deep_memory"):
            memory = self.components["deep_memory"]
            
            # Compress old memories (if the method exists)
            if hasattr(memory, "compress_old_memories"):
                count = memory.compress_old_memories(days_threshold=30)
                logger.info(f"Compressed {count} old memories")
    
    def record_user_interaction(self, interaction_type: str = "conversation", intensity: float = 1.0):
        """
        Record user interaction to update boredom level
        
        Args:
            interaction_type: Type of interaction
            intensity: How engaging the interaction is (0.0 to 1.0)
        """
        if not self.enabled or not self.modules_loaded.get("boredom"):
            return
            
        # Record the activity in the boredom system
        self.components["boredom"].record_activity(activity_type=interaction_type, intensity=intensity)
    
    def get_boredom_influence(self) -> Dict[str, Any]:
        """
        Get the current influence of boredom on system behavior
        
        Returns:
            Dictionary with influence factors
        """
        if not self.enabled or not self.modules_loaded.get("boredom"):
            return {"enabled": False}
            
        boredom_level = self.components["boredom"].get_boredom_level()
        
        # Calculate influence on different systems
        thinking_multiplier = 1.0 + (boredom_level * 2.0)  # Higher boredom = more thinking
        emotion_influence = min(0.5, boredom_level * 0.7)  # Boredom can affect emotions but limited
        
        return {
            "enabled": True,
            "boredom_level": boredom_level,
            "is_bored": self.components["boredom"].is_bored(),
            "is_very_bored": self.components["boredom"].is_very_bored(),
            "idle_time": self.components["boredom"].get_idle_time(),
            "thinking_multiplier": thinking_multiplier,
            "emotion_influence": emotion_influence
        }
    
    def enable(self):
        """Enable boredom integration"""
        self.enabled = True
        
        # Start the check thread if not running
        if not self.check_thread or not self.check_thread.is_alive():
            self._start_check_thread()
            
        logger.info("Boredom integration enabled")
    
    def disable(self):
        """Disable boredom integration"""
        self.enabled = False
        
        # Stop the check thread
        if self.check_thread and self.check_thread.is_alive():
            self.stop_check.set()
            self.check_thread.join(timeout=2.0)
            
        logger.info("Boredom integration disabled")
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        self.disable()

# Singleton instance
_boredom_integration_instance = None

def get_instance():
    """Get the singleton instance of BoredomIntegration"""
    global _boredom_integration_instance
    if _boredom_integration_instance is None:
        _boredom_integration_instance = BoredomIntegration()
    return _boredom_integration_instance
