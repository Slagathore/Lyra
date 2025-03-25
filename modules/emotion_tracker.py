import os
import json
import time
import logging
import threading
import random
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class EmotionTracker:
    """Tracks and manages character emotions based on interactions"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "emotions")
        else:
            self.data_dir = data_dir
            
        # Create the directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Emotion states
        self.primary_emotions = {
            "happiness": 50,
            "sadness": 20,
            "anger": 10,
            "fear": 15,
            "surprise": 30,
            "disgust": 10,
            "trust": 60,
            "anticipation": 40
        }
        
        # Complex emotional states derived from primary emotions
        self.derived_emotions = {
            "joy": 0,            # High happiness, low sadness
            "serenity": 0,       # Moderate happiness, low anger
            "ecstasy": 0,        # Very high happiness
            "acceptance": 0,     # High trust, low disgust
            "terror": 0,         # High fear
            "apprehension": 0,   # Moderate fear
            "rage": 0,           # High anger
            "annoyance": 0,      # Low anger
            "vigilance": 0,      # High anticipation
            "interest": 0,       # Moderate anticipation
            "amazement": 0,      # High surprise, moderate happiness
            "distraction": 0,    # Low surprise
            "boredom": 0,        # Low anticipation, low surprise
            "pensiveness": 0,    # Low sadness
            "grief": 0,          # High sadness
            "loathing": 0,       # High disgust
            "remorse": 0,        # Sadness + disgust
            "optimism": 0,       # Anticipation + happiness
            "love": 0,           # Joy + trust
            "submission": 0,     # Trust + fear
            "awe": 0,            # Fear + surprise
            "disappointment": 0, # Surprise + sadness
            "unease": 0,         # Sadness + disgust
            "contempt": 0,       # Anger + disgust
            "aggressiveness": 0, # Anticipation + anger
            "pride": 0,          # Anger + joy
            "curiosity": 0       # Trust + surprise
        }
        
        # Relationship-specific emotions
        self.relationship_emotions = {
            "affection": 40,
            "attachment": 30,
            "longing": 20,
            "jealousy": 10,
            "admiration": 40,
            "compassion": 50
        }
        
        # Contextual emotional states
        self.contextual_states = {
            "stress": 20,
            "relaxation": 40,
            "concentration": 50,
            "confusion": 20,
            "enthusiasm": 60,
            "lethargy": 15
        }
        
        # Special NSFW-related emotional states (only active when NSFW drive is high)
        self.nsfw_states = {
            "arousal": 0,
            "intimacy": 0,
            "shyness": 0,
            "dominance": 0,
            "submission_desire": 0,
            "playfulness": 0
        }
        
        # Initialize the last update time
        self.last_update_time = time.time()
        self.last_save_time = time.time()
        self.save_interval = 300  # 5 minutes
        
        # Random fluctuation settings
        self.fluctuation_rate = 0.1  # Small random changes to emotions
        self.fluctuation_interval = 600  # 10 minutes
        
        # Recent emotion triggers
        self.recent_triggers = []
        self.max_triggers = 10  # Maximum number of recent triggers to remember
        
        # Dominant emotion cache
        self.dominant_emotion = "neutral"
        self.dominant_intensity = 0
        
        # Load previous emotional state if available
        self.load()
        
        # Update derived emotions
        self.update_derived_emotions()
    
    def load(self) -> bool:
        """Load emotional state from disk"""
        try:
            emotion_path = os.path.join(self.data_dir, "emotional_state.json")
            if os.path.exists(emotion_path):
                with open(emotion_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Load primary emotions
                if "primary_emotions" in data:
                    for emotion, value in data["primary_emotions"].items():
                        if emotion in self.primary_emotions:
                            self.primary_emotions[emotion] = value
                
                # Load relationship emotions
                if "relationship_emotions" in data:
                    for emotion, value in data["relationship_emotions"].items():
                        if emotion in self.relationship_emotions:
                            self.relationship_emotions[emotion] = value
                
                # Load contextual states
                if "contextual_states" in data:
                    for state, value in data["contextual_states"].items():
                        if state in self.contextual_states:
                            self.contextual_states[state] = value
                
                # Load NSFW states
                if "nsfw_states" in data:
                    for state, value in data["nsfw_states"].items():
                        if state in self.nsfw_states:
                            self.nsfw_states[state] = value
                
                # Load recent triggers
                if "recent_triggers" in data:
                    self.recent_triggers = data["recent_triggers"][-self.max_triggers:]
                
                logger.info("Loaded emotional state")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading emotional state: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save emotional state to disk"""
        try:
            data = {
                "primary_emotions": self.primary_emotions,
                "relationship_emotions": self.relationship_emotions,
                "contextual_states": self.contextual_states,
                "nsfw_states": self.nsfw_states,
                "derived_emotions": self.derived_emotions,
                "recent_triggers": self.recent_triggers,
                "dominant_emotion": self.dominant_emotion,
                "dominant_intensity": self.dominant_intensity,
                "timestamp": time.time()
            }
            
            emotion_path = os.path.join(self.data_dir, "emotional_state.json")
            with open(emotion_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.last_save_time = time.time()
            logger.debug("Saved emotional state")
            return True
        except Exception as e:
            logger.error(f"Error saving emotional state: {str(e)}")
            return False
    
    def update_derived_emotions(self):
        """Update derived emotional states based on primary emotions"""
        try:
            p = self.primary_emotions  # Alias for readability
            
            # Calculate derived emotions using Plutchik's wheel of emotions
            # Joy-related emotions
            self.derived_emotions["joy"] = self._weighted_emotion([
                (p["happiness"], 0.8), 
                (-p["sadness"], 0.2)
            ])
            
            self.derived_emotions["serenity"] = self._weighted_emotion([
                (p["happiness"], 0.5), 
                (-p["anger"], 0.4),
                (p["trust"], 0.1)
            ])
            
            self.derived_emotions["ecstasy"] = p["happiness"] if p["happiness"] > 80 else 0
            
            # Trust-related emotions
            self.derived_emotions["acceptance"] = self._weighted_emotion([
                (p["trust"], 0.7), 
                (-p["disgust"], 0.3)
            ])
            
            # Fear-related emotions
            self.derived_emotions["terror"] = p["fear"] if p["fear"] > 75 else 0
            
            self.derived_emotions["apprehension"] = p["fear"] * 0.6
            
            # Anger-related emotions
            self.derived_emotions["rage"] = p["anger"] if p["anger"] > 75 else 0
            
            self.derived_emotions["annoyance"] = p["anger"] * 0.4
            
            # Anticipation-related emotions
            self.derived_emotions["vigilance"] = p["anticipation"] if p["anticipation"] > 75 else 0
            
            self.derived_emotions["interest"] = p["anticipation"] * 0.6
            
            # Surprise-related emotions
            self.derived_emotions["amazement"] = self._weighted_emotion([
                (p["surprise"], 0.7), 
                (p["happiness"], 0.3)
            ]) if p["surprise"] > 70 else 0
            
            self.derived_emotions["distraction"] = p["surprise"] * 0.4
            
            # Sadness-related emotions
            self.derived_emotions["grief"] = p["sadness"] if p["sadness"] > 75 else 0
            
            self.derived_emotions["pensiveness"] = p["sadness"] * 0.5
            
            # Disgust-related emotions
            self.derived_emotions["loathing"] = p["disgust"] if p["disgust"] > 75 else 0
            
            # Composite emotions (dyads)
            self.derived_emotions["remorse"] = self._weighted_emotion([
                (p["sadness"], 0.5), 
                (p["disgust"], 0.5)
            ])
            
            self.derived_emotions["optimism"] = self._weighted_emotion([
                (p["anticipation"], 0.5), 
                (p["happiness"], 0.5)
            ])
            
            self.derived_emotions["love"] = self._weighted_emotion([
                (self.derived_emotions["joy"], 0.5), 
                (p["trust"], 0.5)
            ])
            
            self.derived_emotions["submission"] = self._weighted_emotion([
                (p["trust"], 0.5), 
                (p["fear"], 0.5)
            ])
            
            self.derived_emotions["awe"] = self._weighted_emotion([
                (p["fear"], 0.5), 
                (p["surprise"], 0.5)
            ])
            
            self.derived_emotions["disappointment"] = self._weighted_emotion([
                (p["surprise"], 0.4), 
                (p["sadness"], 0.6)
            ])
            
            self.derived_emotions["unease"] = self._weighted_emotion([
                (p["sadness"], 0.4), 
                (p["disgust"], 0.6)
            ])
            
            self.derived_emotions["contempt"] = self._weighted_emotion([
                (p["anger"], 0.5), 
                (p["disgust"], 0.5)
            ])
            
            self.derived_emotions["aggressiveness"] = self._weighted_emotion([
                (p["anticipation"], 0.4), 
                (p["anger"], 0.6)
            ])
            
            self.derived_emotions["pride"] = self._weighted_emotion([
                (p["anger"], 0.3), 
                (self.derived_emotions["joy"], 0.7)
            ])
            
            self.derived_emotions["curiosity"] = self._weighted_emotion([
                (p["trust"], 0.3), 
                (p["surprise"], 0.4),
                (p["anticipation"], 0.3)
            ])
            
            # Boredom is special - it's higher when both anticipation and surprise are low
            self.derived_emotions["boredom"] = 100 - ((p["anticipation"] + p["surprise"]) / 2)
            
            # Calculate the dominant emotion
            self._calculate_dominant_emotion()
            
        except Exception as e:
            logger.error(f"Error updating derived emotions: {str(e)}")
    
    def _weighted_emotion(self, components: List[Tuple[float, float]]) -> float:
        """Calculate weighted value from emotion components
        
        Args:
            components: List of (emotion_value, weight) tuples
        
        Returns:
            float: Weighted emotion value (0-100)
        """
        total = 0
        weight_sum = 0
        
        for value, weight in components:
            total += value * weight
            weight_sum += weight
            
        if weight_sum == 0:
            return 0
            
        result = total / weight_sum
        return max(0, min(100, result))  # Clamp to 0-100 range
    
    def _calculate_dominant_emotion(self):
        """Determine the current dominant emotion"""
        # Combine all emotion dictionaries
        all_emotions = {}
        all_emotions.update(self.primary_emotions)
        all_emotions.update(self.derived_emotions)
        
        # Find the emotion with the highest value
        max_emotion = max(all_emotions.items(), key=lambda x: x[1])
        
        self.dominant_emotion = max_emotion[0]
        self.dominant_intensity = max_emotion[1]
    
    def apply_emotional_trigger(self, trigger_type: str, intensity: float = 1.0, target_emotions: Optional[Dict[str, float]] = None):
        """Apply an emotional trigger to change emotional state
        
        Args:
            trigger_type: Type of trigger (e.g., "compliment", "argument")
            intensity: How strongly this affects emotions (0.0-2.0)
            target_emotions: Optional dict of specific emotions to modify and by how much
        """
        try:
            # Record the trigger
            self.recent_triggers.append({
                "type": trigger_type,
                "intensity": intensity,
                "timestamp": time.time()
            })
            
            # Trim triggers list if needed
            if len(self.recent_triggers) > self.max_triggers:
                self.recent_triggers = self.recent_triggers[-self.max_triggers:]
            
            # If specific emotions are targeted, update them
            if target_emotions:
                for emotion, change in target_emotions.items():
                    self._modify_emotion(emotion, change * intensity)
            else:
                # Otherwise apply predefined changes based on trigger type
                if trigger_type == "compliment":
                    self._modify_emotion("happiness", 5 * intensity)
                    self._modify_emotion("trust", 3 * intensity)
                    self._modify_emotion("sadness", -2 * intensity)
                    self.relationship_emotions["affection"] += 2 * intensity
                    
                elif trigger_type == "criticism":
                    self._modify_emotion("sadness", 3 * intensity)
                    self._modify_emotion("anger", 2 * intensity)
                    self._modify_emotion("happiness", -3 * intensity)
                    
                elif trigger_type == "surprise_event":
                    self._modify_emotion("surprise", 8 * intensity)
                    
                elif trigger_type == "threat":
                    self._modify_emotion("fear", 6 * intensity)
                    self._modify_emotion("trust", -3 * intensity)
                    
                elif trigger_type == "flirtation":
                    self.relationship_emotions["affection"] += 4 * intensity
                    self._modify_emotion("happiness", 3 * intensity)
                    if self.nsfw_states["arousal"] > 0:
                        self.nsfw_states["arousal"] += 5 * intensity
                        
                # Add more trigger types as needed
            
            # Update derived emotions after changes
            self.update_derived_emotions()
            
            # Save if it's been a while
            current_time = time.time()
            if current_time - self.last_save_time > self.save_interval:
                self.save()
                
        except Exception as e:
            logger.error(f"Error applying emotional trigger: {str(e)}")
    
    def _modify_emotion(self, emotion: str, amount: float):
        """Modify a specific emotion value, with bounds checking
        
        Args:
            emotion: The emotion to modify
            amount: Amount to change the emotion by (positive or negative)
        """
        # Check which emotion dictionary contains this emotion
        if emotion in self.primary_emotions:
            self.primary_emotions[emotion] = max(0, min(100, self.primary_emotions[emotion] + amount))
        elif emotion in self.relationship_emotions:
            self.relationship_emotions[emotion] = max(0, min(100, self.relationship_emotions[emotion] + amount))
        elif emotion in self.contextual_states:
            self.contextual_states[emotion] = max(0, min(100, self.contextual_states[emotion] + amount))
        elif emotion in self.nsfw_states:
            self.nsfw_states[emotion] = max(0, min(100, self.nsfw_states[emotion] + amount))
    
    def get_emotional_state(self) -> Dict[str, Any]:
        """Get the current emotional state summary"""
        return {
            "primary": self.primary_emotions,
            "derived": self.derived_emotions,
            "relationship": self.relationship_emotions,
            "contextual": self.contextual_states,
            "nsfw": self.nsfw_states,
            "dominant": {
                "emotion": self.dominant_emotion,
                "intensity": self.dominant_intensity
            },
            "recent_triggers": self.recent_triggers
        }
    
    def get_emotional_response(self, text: str) -> Tuple[str, Dict[str, float]]:
        """Analyze text and determine appropriate emotional response
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (dominant_emotion, emotion_dict)
        """
        # Simple analysis based on keywords
        emotions = {
            "happiness": 0,
            "sadness": 0,
            "anger": 0,
            "fear": 0,
            "surprise": 0
        }
        
        # Very simple keyword spotting (would be better with NLP)
        happy_words = ["happy", "joy", "wonderful", "love", "excited", "great"]
        sad_words = ["sad", "disappointing", "sorry", "unhappy", "depressed", "miss you"]
        angry_words = ["angry", "upset", "annoying", "frustrating", "hate", "mad"]
        fear_words = ["afraid", "scared", "worried", "nervous", "terrified", "anxious"]
        surprise_words = ["wow", "surprising", "amazing", "unbelievable", "shocked", "unexpected"]
        
        text_lower = text.lower()
        
        # Count emotion keywords
        for word in happy_words:
            if word in text_lower:
                emotions["happiness"] += 1
                
        for word in sad_words:
            if word in text_lower:
                emotions["sadness"] += 1
                
        for word in angry_words:
            if word in text_lower:
                emotions["anger"] += 1
                
        for word in fear_words:
            if word in text_lower:
                emotions["fear"] += 1
                
        for word in surprise_words:
            if word in text_lower:
                emotions["surprise"] += 1
        
        # Normalize values
        total = sum(emotions.values())
        if total > 0:
            for emotion in emotions:
                emotions[emotion] = (emotions[emotion] / total) * 100
        
        # Determine dominant detected emotion
        if total > 0:
            dominant = max(emotions.items(), key=lambda x: x[1])
            return dominant[0], emotions
        else:
            return "neutral", emotions
    
    def get_mood_description(self) -> str:
        """Get a textual description of the current mood"""
        # Get the dominant emotion and its intensity
        emotion = self.dominant_emotion
        intensity = self.dominant_intensity
        
        # Return appropriate description
        if intensity < 20:
            return "neutral"
        elif intensity < 40:
            return f"slightly {emotion}"
        elif intensity < 60:
            return f"moderately {emotion}"
        elif intensity < 80:
            return f"quite {emotion}"
        else:
            return f"extremely {emotion}"
    
    def get_nsfw_level(self) -> int:
        """Get the current NSFW level based on emotional state"""
        arousal = self.nsfw_states.get("arousal", 0)
        
        if arousal < 10:
            return 0
        elif arousal < 30:
            return 1
        elif arousal < 50:
            return 2
        elif arousal < 70:
            return 3
        else:
            return 4
    
    def update_nsfw_state(self, nsfw_drive: int):
        """Update NSFW emotional states based on drive level
        
        Args:
            nsfw_drive: NSFW drive level (0-10)
        """
        # Only activate these emotional states when NSFW drive is set
        if nsfw_drive >= 7:
            # High NSFW drive, emotions become more active
            baseline = (nsfw_drive - 6) * 10  # 10-40 baseline
            
            # Set baseline values with some randomization
            self.nsfw_states["arousal"] = baseline + random.randint(-10, 10)
            self.nsfw_states["intimacy"] = baseline + random.randint(-5, 15)
            self.nsfw_states["playfulness"] = baseline + random.randint(0, 20)
            
            # These are personality dependent, so preserve existing values but ensure minimums
            self.nsfw_states["shyness"] = max(self.nsfw_states["shyness"], baseline/2)
            self.nsfw_states["dominance"] = max(self.nsfw_states["dominance"], baseline/2)
            self.nsfw_states["submission_desire"] = max(self.nsfw_states["submission_desire"], baseline/2)
        else:
            # Low NSFW drive, reset these emotions
            self.nsfw_states["arousal"] = 0
            self.nsfw_states["intimacy"] = 0
            self.nsfw_states["playfulness"] = 0
            # Leave others intact for personality continuity

# Global instance
_emotion_tracker = None

def get_emotion_tracker():
    """Get the global emotion tracker instance"""
    global _emotion_tracker
    if _emotion_tracker is None:
        _emotion_tracker = EmotionTracker()
    return _emotion_tracker
