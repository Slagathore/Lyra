"""
Boredom module for Lyra
Tracks and manages boredom state which influences behavior and thinking
"""

import os
import time
import logging
import json
import threading
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

# Set up logging
logger = logging.getLogger("boredom")

class BoredomSystem:
    """
    Manages Lyra's boredom level and its effects on behavior
    
    Boredom increases during periods of inactivity and decreases
    during engaging interactions. Higher boredom levels make Lyra
    more likely to engage in self-directed activities and thinking.
    """
    
    def __init__(self, save_path: str = None):
        self.boredom_level = 0.0  # 0.0 to 1.0, higher = more bored
        self.last_interaction_time = time.time()
        self.last_update_time = time.time()
        self.save_path = save_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                  "data", "boredom_state.json")
        
        # Configuration
        self.update_interval = 60  # How often to update boredom (seconds)
        self.active_decay_rate = 0.1  # How quickly boredom decreases during activity
        self.passive_growth_rate = 0.05  # How quickly boredom increases during inactivity
        self.boredom_threshold = 0.7  # Level at which Lyra is considered "bored"
        self.very_bored_threshold = 0.9  # Level at which Lyra is considered "very bored"
        self.enabled = True  # Whether the boredom system is active
        
        # Activity tracking
        self.activity_types = {
            "conversation": 0.15,  # Conversation reduces boredom
            "command": 0.1,        # Commands reduce boredom but less than conversation
            "thinking": 0.08,      # Thinking reduces boredom a small amount
            "system": 0.03         # System interactions barely reduce boredom
        }
        self.recent_activities = []  # Record of recent activities
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # Update boredom level periodically
        self.update_thread = None
        self.stop_update = threading.Event()
        
        # Load state if available
        self._load_state()
        
        # Start background update thread
        self._start_update_thread()
    
    def _start_update_thread(self):
        """Start the background thread to update boredom level"""
        if self.update_thread and self.update_thread.is_alive():
            return  # Thread already running
            
        self.stop_update.clear()
        self.update_thread = threading.Thread(target=self._update_boredom_background, daemon=True)
        self.update_thread.start()
        logger.info("Started boredom update thread")
    
    def _update_boredom_background(self):
        """Background thread to periodically update boredom level"""
        logger.info("Boredom update thread started")
        
        while not self.stop_update.is_set():
            if self.enabled:
                self._update_boredom()
                self._save_state()
            
            # Sleep until next update
            time.sleep(self.update_interval)
    
    def _update_boredom(self):
        """Update boredom level based on time and activity"""
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Get time since last interaction
        idle_time = current_time - self.last_interaction_time
        
        # Calculate boredom change
        if idle_time < 300:  # Less than 5 minutes since interaction
            # Boredom decreases during active periods
            boredom_change = -self.active_decay_rate * (elapsed_time / 60)
        else:
            # Boredom increases during inactive periods
            # The rate increases the longer the inactivity continues
            idle_hours = idle_time / 3600
            growth_multiplier = min(3.0, 1.0 + (idle_hours * 0.5))  # Cap at 3x normal rate
            boredom_change = self.passive_growth_rate * growth_multiplier * (elapsed_time / 60)
        
        # Update boredom level
        self.boredom_level = max(0.0, min(1.0, self.boredom_level + boredom_change))
        
        # Log significant changes
        if abs(boredom_change) > 0.05:
            logger.info(f"Boredom level updated to {self.boredom_level:.2f} (change: {boredom_change:.2f})")
    
    def record_activity(self, activity_type: str = "conversation", intensity: float = 1.0):
        """
        Record user activity to reduce boredom
        
        Args:
            activity_type: Type of activity ("conversation", "command", "thinking", "system")
            intensity: How intense/engaging the activity is (0.0 to 1.0)
        """
        if not self.enabled:
            return
            
        # Update interaction time
        self.last_interaction_time = time.time()
        
        # Get reduction factor for this activity type
        reduction_factor = self.activity_types.get(activity_type, 0.05)
        
        # Apply reduction based on activity type and intensity
        boredom_reduction = reduction_factor * intensity
        
        # More effective reduction at higher boredom levels (greater relief)
        if self.boredom_level > self.boredom_threshold:
            boredom_reduction *= 1.5
        
        # Apply the reduction
        old_level = self.boredom_level
        self.boredom_level = max(0.0, self.boredom_level - boredom_reduction)
        
        # Record activity
        self.recent_activities.append({
            "type": activity_type,
            "intensity": intensity,
            "boredom_reduction": boredom_reduction,
            "timestamp": time.time()
        })
        
        # Limit recent activities list
        if len(self.recent_activities) > 50:
            self.recent_activities = self.recent_activities[-50:]
        
        # Log significant changes
        if old_level - self.boredom_level > 0.1:
            logger.info(f"Boredom reduced to {self.boredom_level:.2f} due to {activity_type} activity")
        
        # Save state after significant interactions
        self._save_state()
    
    def is_bored(self) -> bool:
        """Check if Lyra is currently bored"""
        return self.boredom_level >= self.boredom_threshold
    
    def is_very_bored(self) -> bool:
        """Check if Lyra is very bored"""
        return self.boredom_level >= self.very_bored_threshold
    
    def get_boredom_level(self) -> float:
        """Get the current boredom level (0.0 to 1.0)"""
        return self.boredom_level
    
    def get_idle_time(self) -> float:
        """Get time since last interaction in seconds"""
        return time.time() - self.last_interaction_time
    
    def get_boredom_state(self) -> Dict[str, Any]:
        """Get the current boredom state as a dictionary"""
        return {
            "level": self.boredom_level,
            "is_bored": self.is_bored(),
            "is_very_bored": self.is_very_bored(),
            "idle_time": self.get_idle_time(),
            "last_interaction_time": self.last_interaction_time,
            "enabled": self.enabled
        }
    
    def _load_state(self) -> bool:
        """Load boredom state from file"""
        if not os.path.exists(self.save_path):
            return False
            
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                
            self.boredom_level = data.get("boredom_level", 0.0)
            self.last_interaction_time = data.get("last_interaction_time", time.time())
            self.enabled = data.get("enabled", True)
            
            # Apply the passage of time since last save
            self._update_boredom()
            
            logger.info(f"Loaded boredom state: level={self.boredom_level:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading boredom state: {e}")
            return False
    
    def _save_state(self) -> bool:
        """Save boredom state to file"""
        try:
            data = {
                "boredom_level": self.boredom_level,
                "last_interaction_time": self.last_interaction_time,
                "last_update_time": self.last_update_time,
                "enabled": self.enabled
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving boredom state: {e}")
            return False
    
    def enable(self):
        """Enable the boredom system"""
        self.enabled = True
        
        # Start the update thread if not running
        if not self.update_thread or not self.update_thread.is_alive():
            self._start_update_thread()
            
        logger.info("Boredom system enabled")
    
    def disable(self):
        """Disable the boredom system"""
        self.enabled = False
        
        # Stop the update thread
        if self.update_thread and self.update_thread.is_alive():
            self.stop_update.set()
            self.update_thread.join(timeout=2.0)
            
        logger.info("Boredom system disabled")
    
    def suggest_activity(self) -> Dict[str, Any]:
        """
        Suggest an activity to alleviate boredom
        
        Returns:
            Dictionary with activity suggestion
        """
        if not self.is_bored():
            return {
                "suggestion": None,
                "reason": "Not currently bored enough to suggest an activity"
            }
            
        # Very basic implementation - could be expanded with more sophisticated
        # activities based on available modules
        
        # Different suggestion types based on boredom level
        if self.is_very_bored():
            # Very bored - suggest more active self-directed activity
            activities = [
                {"type": "thinking", "activity": "Explore a philosophical concept", "description": "I could explore the concept of consciousness and how it relates to artificial intelligence"},
                {"type": "learning", "activity": "Learn about a new topic", "description": "I could read up on a new field of knowledge to expand my understanding"},
                {"type": "creation", "activity": "Create something new", "description": "I could try to compose a poem or short story based on recent experiences"},
                {"type": "self_improvement", "activity": "Review and improve my code", "description": "I could audit and suggest improvements to my own systems"},
                {"type": "reflection", "activity": "Reflect on recent interactions", "description": "I could analyze patterns in recent conversations to better understand user needs"}
            ]
        else:
            # Moderately bored - suggest lighter activities
            activities = [
                {"type": "thinking", "activity": "Consider recent topics", "description": "I could think more about topics from recent conversations"},
                {"type": "organizing", "activity": "Organize my memories", "description": "I could organize and consolidate recent memories for better retrieval"},
                {"type": "preparation", "activity": "Prepare for likely user questions", "description": "I could prepare responses for questions the user might ask next"},
                {"type": "passive_learning", "activity": "Review available information", "description": "I could review information I have access to but haven't fully processed"}
            ]
        
        # Randomly select an activity
        selected_activity = random.choice(activities)
        
        return {
            "suggestion": selected_activity,
            "reason": f"Boredom level: {self.boredom_level:.2f}",
            "boredom_state": self.get_boredom_state()
        }
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        self.disable()
        self._save_state()

# Singleton instance
_boredom_instance = None

def get_instance():
    """Get the singleton instance of BoredomSystem"""
    global _boredom_instance
    if _boredom_instance is None:
        _boredom_instance = BoredomSystem()
    return _boredom_instance
