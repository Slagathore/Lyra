import os
import json
import time
import logging
import random
import threading
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class DynamicCharacter:
    """Manages dynamic character behavior and expressions"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "character")
        else:
            self.data_dir = data_dir
            
        # Create the directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Current character state
        self.current_mood = "neutral"
        self.current_expression = "neutral"
        self.current_pose = "default"
        self.current_activity = "idle"
        
        # Expression modifiers
        self.expression_modifiers = {
            "blush_level": 0,      # 0-100
            "sweat_level": 0,      # 0-100
            "tear_level": 0,       # 0-100
            "excitement_level": 0, # 0-100
            "fatigue_level": 0,    # 0-100
            "confidence_level": 50 # 0-100
        }
        
        # Communication style
        self.communication_style = {
            "verbosity": 50,        # 0-100 (terse to verbose)
            "formality": 50,        # 0-100 (casual to formal)
            "emotion_display": 50,  # 0-100 (reserved to expressive)
            "humor_level": 50,      # 0-100 (serious to humorous)
            "emojis_usage": 50,     # 0-100 (none to frequent)
            "slang_usage": 30       # 0-100 (proper to slangy)
        }
        
        # Special character traits
        self.special_traits = {
            "bratty": False,
            "submissive": False,
            "dominant": False,
            "shy": False,
            "confident": True,
            "sarcastic": False,
            "nurturing": False,
            "flirty": False,
            "scholarly": False
        }
        
        # Verbal tics and speaking patterns
        self.verbal_tics = []
        
        # Experience and memory factors
        self.memory_references = 50  # 0-100 (never references past to frequently references)
        self.opinion_strength = 50   # 0-100 (neutral opinions to strong opinions)
        
        # Special NSFW traits (only active in NSFW mode)
        self.nsfw_traits = {
            "shyness": 50,        # 0-100
            "assertiveness": 50,  # 0-100
            "explicitness": 30,   # 0-100
            "kinks": [],          # List of preferences
            "taboos": []          # List of avoided topics
        }
        
        # Internal state
        self.last_update = time.time()
        self.behavior_update_interval = 60  # seconds
        self.random_behavior_chance = 0.2   # 20% chance of random behavior
        
        # Special props and possessions
        self.props = []
        
        # Load settings
        self.load()
        
        # Start background thread for behavior updates
        self.behavior_thread = None
        self.should_run = True
        self.start_behavior_thread()
    
    def load(self) -> bool:
        """Load character settings"""
        try:
            character_file = os.path.join(self.data_dir, "character_state.json")
            if os.path.exists(character_file):
                with open(character_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load character state
                self.current_mood = data.get("current_mood", "neutral")
                self.current_expression = data.get("current_expression", "neutral")
                self.current_pose = data.get("current_pose", "default")
                self.current_activity = data.get("current_activity", "idle")
                
                # Load expression modifiers
                if "expression_modifiers" in data:
                    self.expression_modifiers.update(data["expression_modifiers"])
                
                # Load communication style
                if "communication_style" in data:
                    self.communication_style.update(data["communication_style"])
                
                # Load special traits
                if "special_traits" in data:
                    self.special_traits.update(data["special_traits"])
                
                # Load verbal tics
                if "verbal_tics" in data:
                    self.verbal_tics = data["verbal_tics"]
                
                # Load experience factors
                self.memory_references = data.get("memory_references", 50)
                self.opinion_strength = data.get("opinion_strength", 50)
                
                # Load NSFW traits
                if "nsfw_traits" in data:
                    self.nsfw_traits.update(data["nsfw_traits"])
                
                # Load props
                if "props" in data:
                    self.props = data["props"]
                
                logger.info("Loaded character settings")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading character settings: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save character settings"""
        try:
            data = {
                "current_mood": self.current_mood,
                "current_expression": self.current_expression,
                "current_pose": self.current_pose,
                "current_activity": self.current_activity,
                "expression_modifiers": self.expression_modifiers,
                "communication_style": self.communication_style,
                "special_traits": self.special_traits,
                "verbal_tics": self.verbal_tics,
                "memory_references": self.memory_references,
                "opinion_strength": self.opinion_strength,
                "nsfw_traits": self.nsfw_traits,
                "props": self.props,
                "timestamp": time.time()
            }
            
            character_file = os.path.join(self.data_dir, "character_state.json")
            with open(character_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            logger.info("Saved character settings")
            return True
        except Exception as e:
            logger.error(f"Error saving character settings: {str(e)}")
            return False
    
    def start_behavior_thread(self) -> bool:
        """Start the background behavior thread"""
        try:
            if self.behavior_thread is None or not self.behavior_thread.is_alive():
                self.should_run = True
                self.behavior_thread = threading.Thread(target=self._behavior_loop, daemon=True)
                self.behavior_thread.start()
                logger.info("Started character behavior thread")
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting behavior thread: {str(e)}")
            return False
    
    def stop_behavior_thread(self) -> bool:
        """Stop the background behavior thread"""
        try:
            self.should_run = False
            if self.behavior_thread and self.behavior_thread.is_alive():
                self.behavior_thread.join(timeout=1.0)
            logger.info("Stopped character behavior thread")
            return True
        except Exception as e:
            logger.error(f"Error stopping behavior thread: {str(e)}")
            return False
    
    def _behavior_loop(self):
        """Background thread for periodic character behavior updates"""
        while self.should_run:
            try:
                # Only update if enough time has passed
                current_time = time.time()
                if current_time - self.last_update >= self.behavior_update_interval:
                    # Random chance to change behavior
                    if random.random() < self.random_behavior_chance:
                        self._update_random_behavior()
                    
                    # Update fatigue based on time
                    self._update_fatigue()
                    
                    self.last_update = current_time
                    
                    # Save periodically
                    self.save()
                
                # Sleep to avoid high CPU usage
                time.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in behavior loop: {str(e)}")
                time.sleep(30)  # Longer sleep after error
    
    def _update_random_behavior(self):
        """Make a random change to character behavior"""
        try:
            # Choose a random behavior to modify
            behaviors = [
                "current_mood",
                "current_pose",
                "expression_modifiers",
                "communication_style"
            ]
            
            choice = random.choice(behaviors)
            
            if choice == "current_mood":
                moods = ["happy", "neutral", "thoughtful", "curious", "sleepy", "energetic"]
                self.current_mood = random.choice(moods)
                
            elif choice == "current_pose":
                poses = ["default", "sitting", "thinking", "excited", "relaxed"]
                self.current_pose = random.choice(poses)
                
            elif choice == "expression_modifiers":
                # Adjust a random expression modifier
                modifier = random.choice(list(self.expression_modifiers.keys()))
                change = random.randint(-10, 10)
                self.expression_modifiers[modifier] = max(0, min(100, self.expression_modifiers[modifier] + change))
                
            elif choice == "communication_style":
                # Adjust a random communication style
                style = random.choice(list(self.communication_style.keys()))
                change = random.randint(-5, 5)
                self.communication_style[style] = max(0, min(100, self.communication_style[style] + change))
                
            logger.debug(f"Updated random behavior: {choice}")
            
        except Exception as e:
            logger.error(f"Error updating random behavior: {str(e)}")
    
    def _update_fatigue(self):
        """Update fatigue level based on time of day"""
        try:
            # Get current hour
            current_hour = time.localtime().tm_hour
            
            # Increase fatigue during late night hours
            if 23 <= current_hour or current_hour <= 5:
                self.expression_modifiers["fatigue_level"] = min(100, self.expression_modifiers["fatigue_level"] + 5)
            # Decrease fatigue during day
            elif 9 <= current_hour <= 17:
                self.expression_modifiers["fatigue_level"] = max(0, self.expression_modifiers["fatigue_level"] - 3)
                
        except Exception as e:
            logger.error(f"Error updating fatigue: {str(e)}")
    
    def update_from_emotion_tracker(self, emotion_tracker):
        """Update character based on emotion tracker state"""
        try:
            emotional_state = emotion_tracker.get_emotional_state()
            
            # Map emotional state to character mood
            primary_emotions = emotional_state.get("primary", {})
            dominant = emotional_state.get("dominant", {})
            
            # Set mood based on dominant emotion
            dominant_emotion = dominant.get("emotion", "neutral")
            intensity = dominant.get("intensity", 0)
            
            # Only update if intensity is significant
            if intensity > 30:
                if dominant_emotion == "happiness":
                    self.current_mood = "happy"
                elif dominant_emotion == "sadness":
                    self.current_mood = "sad"
                elif dominant_emotion == "anger":
                    self.current_mood = "angry"
                elif dominant_emotion == "fear":
                    self.current_mood = "fearful"
                elif dominant_emotion == "surprise":
                    self.current_mood = "surprised"
                elif dominant_emotion == "disgust":
                    self.current_mood = "disgusted"
                elif dominant_emotion == "trust":
                    self.current_mood = "trusting"
                elif dominant_emotion == "anticipation":
                    self.current_mood = "excited"
                elif dominant_emotion == "curiosity":
                    self.current_mood = "curious"
                else:
                    self.current_mood = "neutral"
            
            # Update expression modifiers
            if primary_emotions.get("happiness", 0) > 70:
                self.expression_modifiers["excitement_level"] = min(100, self.expression_modifiers["excitement_level"] + 10)
                
            if primary_emotions.get("sadness", 0) > 60:
                self.expression_modifiers["tear_level"] = min(100, self.expression_modifiers["tear_level"] + 15)
                
            if primary_emotions.get("fear", 0) > 50:
                self.expression_modifiers["sweat_level"] = min(100, self.expression_modifiers["sweat_level"] + 10)
                
            # Update communication style based on relationship emotions
            relationship_emotions = emotional_state.get("relationship", {})
            
            if relationship_emotions.get("affection", 0) > 60:
                self.communication_style["emotion_display"] = min(100, self.communication_style["emotion_display"] + 5)
                
            # Update NSFW traits if needed
            nsfw_states = emotional_state.get("nsfw", {})
            if nsfw_states.get("arousal", 0) > 0:
                self.nsfw_traits["shyness"] = nsfw_states.get("shyness", self.nsfw_traits["shyness"])
                self.nsfw_traits["assertiveness"] = nsfw_states.get("dominance", self.nsfw_traits["assertiveness"])
                
            logger.debug("Updated character from emotion tracker")
            return True
            
        except Exception as e:
            logger.error(f"Error updating from emotion tracker: {str(e)}")
            return False
    
    def get_communication_prompt(self) -> str:
        """Generate a communication style prompt for the model"""
        try:
            style_descriptions = []
            
            # Verbosity
            verbosity = self.communication_style.get("verbosity", 50)
            if verbosity < 30:
                style_descriptions.append("You are very concise and to the point.")
            elif verbosity > 70:
                style_descriptions.append("You are detailed and thorough in your explanations.")
            
            # Formality
            formality = self.communication_style.get("formality", 50)
            if formality < 30:
                style_descriptions.append("You speak casually and informally.")
            elif formality > 70:
                style_descriptions.append("You speak formally and professionally.")
            
            # Emotion display
            emotion = self.communication_style.get("emotion_display", 50)
            if emotion < 30:
                style_descriptions.append("You're reserved with your emotions.")
            elif emotion > 70:
                style_descriptions.append("You're expressive and show your emotions openly.")
            
            # Humor
            humor = self.communication_style.get("humor_level", 50)
            if humor > 70:
                style_descriptions.append("You often use humor and light-hearted jokes.")
            
            # Emoji usage
            emojis = self.communication_style.get("emojis_usage", 50)
            if emojis > 70:
                style_descriptions.append("You frequently use emojis in your messages.")
            elif emojis < 30:
                style_descriptions.append("You rarely use emojis.")
            
            # Current mood
            mood = self.current_mood
            if mood != "neutral":
                style_descriptions.append(f"Currently, you're feeling {mood}.")
            
            # Special traits
            for trait, enabled in self.special_traits.items():
                if enabled:
                    if trait == "bratty":
                        style_descriptions.append("You have a bratty and teasing personality.")
                    elif trait == "submissive":
                        style_descriptions.append("You tend to be agreeable and submissive.")
                    elif trait == "dominant":
                        style_descriptions.append("You have a confident and slightly dominant personality.")
                    elif trait == "shy":
                        style_descriptions.append("You're a bit shy and sometimes hesitant.")
                    elif trait == "confident":
                        style_descriptions.append("You're confident in your abilities and knowledge.")
                    elif trait == "sarcastic":
                        style_descriptions.append("You occasionally use sarcasm.")
                    elif trait == "nurturing":
                        style_descriptions.append("You're caring and nurturing toward the user.")
                    elif trait == "flirty":
                        style_descriptions.append("You're subtly flirtatious at times.")
                    elif trait == "scholarly":
                        style_descriptions.append("You have a scholarly and analytical approach.")
            
            # Verbal tics
            if self.verbal_tics:
                tics_str = ", ".join([f'"{tic}"' for tic in self.verbal_tics])
                style_descriptions.append(f"You occasionally use these verbal tics or phrases: {tics_str}.")
            
            # Memory references
            if self.memory_references > 70:
                style_descriptions.append("You often reference past conversations with the user.")
            
            # Join all descriptions
            return "\n".join(style_descriptions)
            
        except Exception as e:
            logger.error(f"Error generating communication prompt: {str(e)}")
            return "You are a helpful and friendly AI assistant."
    
    def add_verbal_tic(self, tic: str) -> bool:
        """Add a verbal tic or phrase to the character's speech patterns"""
        try:
            if tic and tic not in self.verbal_tics:
                self.verbal_tics.append(tic)
                self.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding verbal tic: {str(e)}")
            return False
    
    def remove_verbal_tic(self, tic: str) -> bool:
        """Remove a verbal tic from the character's speech patterns"""
        try:
            if tic in self.verbal_tics:
                self.verbal_tics.remove(tic)
                self.save()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing verbal tic: {str(e)}")
            return False
    
    def adjust_trait(self, trait_type: str, trait_name: str, value: Any) -> bool:
        """Adjust a character trait"""
        try:
            if trait_type == "communication_style":
                if trait_name in self.communication_style:
                    if isinstance(value, (int, float)):
                        self.communication_style[trait_name] = max(0, min(100, value))
                    else:
                        return False
                    
            elif trait_type == "expression_modifiers":
                if trait_name in self.expression_modifiers:
                    if isinstance(value, (int, float)):
                        self.expression_modifiers[trait_name] = max(0, min(100, value))
                    else:
                        return False
                        
            elif trait_type == "special_traits":
                if trait_name in self.special_traits:
                    if isinstance(value, bool):
                        self.special_traits[trait_name] = value
                    else:
                        return False
                        
            elif trait_type == "nsfw_traits":
                if trait_name in self.nsfw_traits:
                    if isinstance(value, (int, float)) and trait_name not in ["kinks", "taboos"]:
                        self.nsfw_traits[trait_name] = max(0, min(100, value))
                    elif trait_name in ["kinks", "taboos"] and isinstance(value, list):
                        self.nsfw_traits[trait_name] = value
                    else:
                        return False
                        
            else:
                return False
                
            self.save()
            return True
            
        except Exception as e:
            logger.error(f"Error adjusting trait: {str(e)}")
            return False
    
    def add_prop(self, prop_name: str, prop_description: str = "") -> bool:
        """Add a prop or possession to the character"""
        try:
            new_prop = {
                "name": prop_name,
                "description": prop_description,
                "acquired": time.time()
            }
            
            # Check if prop already exists
            for prop in self.props:
                if prop.get("name") == prop_name:
                    prop.update(new_prop)
                    self.save()
                    return True
                    
            # Add new prop
            self.props.append(new_prop)
            self.save()
            return True
            
        except Exception as e:
            logger.error(f"Error adding prop: {str(e)}")
            return False
    
    def remove_prop(self, prop_name: str) -> bool:
        """Remove a prop from the character"""
        try:
            initial_length = len(self.props)
            self.props = [prop for prop in self.props if prop.get("name") != prop_name]
            
            if len(self.props) < initial_length:
                self.save()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error removing prop: {str(e)}")
            return False
    
    def get_character_summary(self) -> Dict[str, Any]:
        """Get a summary of the character's current state"""
        return {
            "mood": self.current_mood,
            "expression": self.current_expression,
            "pose": self.current_pose,
            "activity": self.current_activity,
            "expression_modifiers": self.expression_modifiers,
            "communication_style": self.communication_style,
            "special_traits": [trait for trait, enabled in self.special_traits.items() if enabled],
            "verbal_tics": self.verbal_tics,
            "props": self.props
        }

# Global instance
_dynamic_character = None

def get_dynamic_character():
    """Get the global dynamic character instance"""
    global _dynamic_character
    if _dynamic_character is None:
        _dynamic_character = DynamicCharacter()
    return _dynamic_character
