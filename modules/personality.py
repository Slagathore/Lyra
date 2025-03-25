import os
import json
import time
import logging
import datetime
import threading
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class PersonalityManager:
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "personality")
        else:
            self.data_dir = data_dir
            
        # Create the directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize personality state
        self.evolving_enabled = False
        self.last_save_time = 0
        self.save_interval = 300  # Save every 5 minutes of changes
        self.last_interaction_time = time.time()
        self.schedule = {}
        self.telegram_username = ""
        
        # Define personality traits with default values
        self.primary_traits = {
            "happiness": 50,
            "sadness": 25,
            "anger": 15,
            "fear": 20,
            "surprise": 60,
            "curiosity": 75,
            "trust": 65,
            "empathy": 80
        }
        
        self.secondary_traits = {
            "confidence": 70,
            "shyness": 30,
            "playfulness": 65,
            "seriousness": 40,
            "kindness": 75,
            "creativity": 80
        }
        
        self.relationship_traits = {
            "romance": 25,
            "sass": 35,
            "loyalty": 90,
            "submissiveness": 40,
            "brattiness": 20,
            "nurturing": 60
        }
        
        self.internal_states = {
            "loneliness": 45,
            "boredom": 30,
            "nsfw_drive": 3,
            "attachment": 50,
            "emotion_volatility": 40
        }
        
        # Boredom increases over time when not interacting
        self.boredom_rate = 1.0  # Points per hour
        self.last_boredom_update = time.time()
        
        # Start background thread for time-based updates
        self.update_thread = None
        self.should_run = True
        
        # Load existing personality if available
        self.load()
        
        # Start background thread if evolving is enabled
        if self.evolving_enabled:
            self.start_background_updates()
    
    def start_background_updates(self):
        """Start the background thread for time-based updates"""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.should_run = True
            self.update_thread = threading.Thread(target=self._background_updates, daemon=True)
            self.update_thread.start()
            logger.info("Started personality background updates")
    
    def stop_background_updates(self):
        """Stop the background thread for time-based updates"""
        self.should_run = False
        if self.update_thread and self.update_thread.is_alive():
            self.update_thread.join(timeout=1.0)
            logger.info("Stopped personality background updates")
    
    def _background_updates(self):
        """Background thread function for time-based trait updates"""
        while self.should_run:
            try:
                # Update time-based traits like boredom
                self._update_time_based_traits()
                
                # Save personality state if needed
                current_time = time.time()
                if current_time - self.last_save_time > self.save_interval:
                    self.save()
                    
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in personality background update: {str(e)}")
                time.sleep(60)  # Still sleep to avoid rapid error loops
    
    def _update_time_based_traits(self):
        """Update traits that change with time"""
        current_time = time.time()
        hours_passed = (current_time - self.last_boredom_update) / 3600.0
        
        if hours_passed > 0.1:  # Only update if at least 6 minutes have passed
            # Increase boredom with time
            boredom_increase = self.boredom_rate * hours_passed
            self.internal_states["boredom"] = min(100, self.internal_states["boredom"] + boredom_increase)
            
            # Update other time-dependent traits
            # Loneliness increases when bored
            if self.internal_states["boredom"] > 50:
                self.internal_states["loneliness"] = min(100, self.internal_states["loneliness"] + (boredom_increase * 0.5))
            
            # Reset the timer
            self.last_boredom_update = current_time
            
            logger.debug(f"Updated time-based traits: boredom={self.internal_states['boredom']:.1f}, loneliness={self.internal_states['loneliness']:.1f}")
    
    def enable_evolution(self, enabled=True):
        """Enable or disable personality evolution"""
        self.evolving_enabled = enabled
        if enabled:
            self.start_background_updates()
        else:
            self.stop_background_updates()
        self.save()
        return self.evolving_enabled
    
    def interact(self):
        """Called when user interacts with the bot to reset idle timer and adjust traits"""
        # Reset interaction time
        self.last_interaction_time = time.time()
        
        # Lower boredom due to interaction
        self.internal_states["boredom"] = max(0, self.internal_states["boredom"] - 15)
        
        # Lower loneliness due to interaction
        self.internal_states["loneliness"] = max(0, self.internal_states["loneliness"] - 10)
        
        # Adjust other traits slightly for natural variation
        for trait in self.primary_traits:
            # Random small adjustment (-2 to +2)
            adjustment = (time.time() % 5) - 2
            self.primary_traits[trait] = max(0, min(100, self.primary_traits[trait] + adjustment))
        
        # Save if it's been a while
        current_time = time.time()
        if current_time - self.last_save_time > self.save_interval:
            self.save()
    
    def set_trait(self, category, name, value):
        """Set a specific trait to a value"""
        trait_dict = self._get_trait_dict(category)
        if not trait_dict or name not in trait_dict:
            return False
        
        value = max(0, min(100 if name != "nsfw_drive" else 10, value))
        trait_dict[name] = value
        
        # Special case for NSFW drive
        if category == "internal" and name == "nsfw_drive" and value >= 7:
            # Activate "downbad" mode
            self._activate_downbad_mode()
        
        return True
    
    def get_trait(self, category, name):
        """Get a specific trait value"""
        trait_dict = self._get_trait_dict(category)
        if not trait_dict or name not in trait_dict:
            return None
        return trait_dict[name]
    
    def get_all_traits(self):
        """Get all personality traits"""
        return {
            "primary": self.primary_traits.copy(),
            "secondary": self.secondary_traits.copy(),
            "relationship": self.relationship_traits.copy(),
            "internal": self.internal_states.copy()
        }
    
    def _get_trait_dict(self, category):
        """Get the appropriate trait dictionary based on category"""
        if category == "primary":
            return self.primary_traits
        elif category == "secondary":
            return self.secondary_traits
        elif category == "relationship":
            return self.relationship_traits
        elif category == "internal":
            return self.internal_states
        return None
    
    def _activate_downbad_mode(self):
        """Activate "downbad" mode when NSFW drive is high"""
        # Adjust relationship traits for downbad mode
        self.relationship_traits["romance"] = min(100, self.relationship_traits["romance"] + 20)
        
        # Brattiness and submissiveness are inversely related in downbad mode
        nsfw_level = self.internal_states["nsfw_drive"]
        if nsfw_level >= 8:
            # Higher NSFW drive increases either brattiness or submissiveness based on existing tendency
            if self.relationship_traits["brattiness"] > self.relationship_traits["submissiveness"]:
                self.relationship_traits["brattiness"] = min(100, self.relationship_traits["brattiness"] + 15)
            else:
                self.relationship_traits["submissiveness"] = min(100, self.relationship_traits["submissiveness"] + 15)
    
    def set_telegram_username(self, username):
        """Set the user's Telegram username"""
        self.telegram_username = username
        self.save()
    
    def get_telegram_username(self):
        """Get the user's Telegram username"""
        return self.telegram_username
    
    def update_schedule(self, day, time_slot, activity):
        """Update the user's schedule for a specific day and time slot"""
        if day not in self.schedule:
            self.schedule[day] = {}
        self.schedule[day][time_slot] = activity
        self.save()
    
    def get_schedule(self, day=None):
        """Get the user's schedule, optionally for a specific day"""
        if day:
            return self.schedule.get(day, {})
        return self.schedule
    
    def save(self):
        """Save the personality state to disk"""
        try:
            state = {
                "evolving_enabled": self.evolving_enabled,
                "last_interaction_time": self.last_interaction_time,
                "last_boredom_update": self.last_boredom_update,
                "primary_traits": self.primary_traits,
                "secondary_traits": self.secondary_traits,
                "relationship_traits": self.relationship_traits,
                "internal_states": self.internal_states,
                "schedule": self.schedule,
                "telegram_username": self.telegram_username
            }
            
            save_path = os.path.join(self.data_dir, "personality_state.json")
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
                
            self.last_save_time = time.time()
            logger.debug("Saved personality state")
            return True
        except Exception as e:
            logger.error(f"Error saving personality state: {str(e)}")
            return False
    
    def load(self):
        """Load the personality state from disk"""
        try:
            save_path = os.path.join(self.data_dir, "personality_state.json")
            if not os.path.exists(save_path):
                logger.info("No saved personality state found")
                return False
                
            with open(save_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                
            # Load state attributes
            self.evolving_enabled = state.get("evolving_enabled", False)
            self.last_interaction_time = state.get("last_interaction_time", time.time())
            self.last_boredom_update = state.get("last_boredom_update", time.time())
            
            # Load traits
            self.primary_traits.update(state.get("primary_traits", {}))
            self.secondary_traits.update(state.get("secondary_traits", {}))
            self.relationship_traits.update(state.get("relationship_traits", {}))
            self.internal_states.update(state.get("internal_states", {}))
            
            # Load other data
            self.schedule = state.get("schedule", {})
            self.telegram_username = state.get("telegram_username", "")
            
            logger.info("Loaded personality state")
            return True
        except Exception as e:
            logger.error(f"Error loading personality state: {str(e)}")
            return False
    
    def detect_tone(self, text):
        """Analyze text to detect emotional tone"""
        # Simple rule-based tone detection
        tone = {
            "happy": 0,
            "sad": 0,
            "angry": 0,
            "fearful": 0,
            "surprised": 0,
            "romantic": 0,
            "neutral": 0
        }
        
        # Simple keyword matching for tone detection
        happy_words = ["happy", "glad", "joy", "excited", "wonderful", "smile", "laugh", "great", "excellent", "amazing"]
        sad_words = ["sad", "unhappy", "disappointed", "sorry", "regret", "depressed", "miss", "lonely", "hurt", "upset"]
        angry_words = ["angry", "mad", "annoyed", "irritated", "frustrated", "rage", "hate", "furious", "offended", "outraged"]
        fearful_words = ["afraid", "scared", "fear", "terrified", "worried", "nervous", "anxious", "panic", "dread", "horror"]
        surprised_words = ["surprised", "shocked", "wow", "whoa", "unexpected", "incredible", "unbelievable", "astonished", "stunned", "amazed"]
        romantic_words = ["love", "kiss", "hug", "embrace", "cuddle", "intimate", "romantic", "lovely", "beautiful", "passionate"]
        
        text_lower = text.lower()
        
        # Count occurrences of each type of word
        for word in happy_words:
            if word in text_lower:
                tone["happy"] += 1
                
        for word in sad_words:
            if word in text_lower:
                tone["sad"] += 1
                
        for word in angry_words:
            if word in text_lower:
                tone["angry"] += 1
                
        for word in fearful_words:
            if word in text_lower:
                tone["fearful"] += 1
                
        for word in surprised_words:
            if word in text_lower:
                tone["surprised"] += 1
                
        for word in romantic_words:
            if word in text_lower:
                tone["romantic"] += 1
        
        # If no emotions detected, consider it neutral
        if sum(tone.values()) == 0:
            tone["neutral"] = 1
        
        # Normalize to get percentages
        total = sum(tone.values())
        if total > 0:
            for key in tone.keys():
                tone[key] = (tone[key] / total) * 100
                
        return tone
    
    def adjust_traits_from_tone(self, tone):
        """Adjust traits based on detected tone"""
        if not self.evolving_enabled:
            return
        
        # Adjust traits based on detected tone
        if tone["happy"] > 20:
            self.primary_traits["happiness"] = min(100, self.primary_traits["happiness"] + 2)
            self.primary_traits["sadness"] = max(0, self.primary_traits["sadness"] - 1)
            
        if tone["sad"] > 20:
            self.primary_traits["sadness"] = min(100, self.primary_traits["sadness"] + 2)
            self.primary_traits["empathy"] = min(100, self.primary_traits["empathy"] + 1)
            
        if tone["angry"] > 20:
            # If user is angry, increase bot's fear slightly and decrease happiness
            self.primary_traits["fear"] = min(100, self.primary_traits["fear"] + 1)
            self.primary_traits["happiness"] = max(0, self.primary_traits["happiness"] - 1)
            
        if tone["romantic"] > 20:
            self.relationship_traits["romance"] = min(100, self.relationship_traits["romance"] + 2)
            self.internal_states["attachment"] = min(100, self.internal_states["attachment"] + 1)
            
        # Save changes if significant adjustment was made
        if any(value > 20 for value in tone.values() if value != "neutral"):
            self.save()

# Global instance
_personality_manager = None

def get_personality_manager():
    """Get the global personality manager instance"""
    global _personality_manager
    if _personality_manager is None:
        _personality_manager = PersonalityManager()
    return _personality_manager
