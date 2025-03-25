"""
Emotional Core module for Lyra
Provides an advanced emotional state system that evolves based on interaction
"""

import os
import time
import json
import logging
import random
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# Set up logging
logger = logging.getLogger("emotional_core")

class EmotionalState:
    """Represents a complex emotional state with multiple dimensions"""
    
    # Primary emotions and their typical opposites
    PRIMARY_EMOTIONS = {
        "joy": "sadness",
        "trust": "disgust",
        "fear": "anger",
        "surprise": "anticipation",
        "sadness": "joy",
        "disgust": "trust",
        "anger": "fear",
        "anticipation": "surprise"
    }
    
    # Secondary emotions (combinations of primary emotions)
    SECONDARY_EMOTIONS = {
        "love": ("joy", "trust"),
        "guilt": ("sadness", "fear"),
        "delight": ("joy", "surprise"),
        "submission": ("trust", "fear"),
        "curiosity": ("trust", "surprise"),
        "despair": ("sadness", "disgust"),
        "shame": ("fear", "disgust"),
        "disappointment": ("surprise", "sadness"),
        "jealousy": ("anger", "fear"),
        "outrage": ("surprise", "anger"),
        "optimism": ("joy", "anticipation"),
        "hope": ("trust", "anticipation"),
        "anxiety": ("fear", "anticipation"),
        "remorse": ("sadness", "disgust")
    }
    
    # Tertiary emotions (more complex blends)
    TERTIARY_EMOTIONS = {
        "awe": ("fear", "surprise", "joy"),
        "confused": ("surprise", "disgust", "anticipation"),
        "nostalgia": ("joy", "sadness", "trust"),
        "self-conscious": ("fear", "sadness", "disgust"),
        "longing": ("joy", "sadness", "anticipation"),
        "pride": ("joy", "anger", "trust"),
        "gratitude": ("joy", "trust", "anticipation")
    }
    
    def __init__(self):
        """Initialize a new emotional state with neutral values"""
        # Primary emotion intensity values (0.0 to 1.0)
        self.primary = {emotion: 0.0 for emotion in self.PRIMARY_EMOTIONS.keys()}
        
        # Set some baseline values
        self.primary["joy"] = 0.6  # Slight positive disposition
        self.primary["trust"] = 0.7  # High trust
        self.primary["anticipation"] = 0.6  # Forward-looking
        
        # Secondary emotions are derived from primary emotions
        self.secondary = {}
        self.tertiary = {}
        
        # Additional emotional parameters
        self.arousal = 0.5  # Emotional intensity/energy (0.0 to 1.0)
        self.stability = 0.8  # Emotional stability (0.0 to 1.0)
        self.expressiveness = 0.6  # Willingness to express emotions (0.0 to 1.0)
        
        # Mood represents longer-term emotional state
        self.mood = {
            "valence": 0.6,  # Positive/negative (0.0 to 1.0, 0.5 is neutral)
            "energy": 0.5,   # High/low energy (0.0 to 1.0)
            "dominance": 0.5  # Feeling of control (0.0 to 1.0)
        }
        
        # Personality factors that influence emotional responses
        self.personality = {
            "openness": 0.7,       # Openness to experience
            "conscientiousness": 0.8,  # Thoroughness and reliability
            "extraversion": 0.6,    # Outgoing vs. reserved
            "agreeableness": 0.7,   # Friendly vs. challenging
            "neuroticism": 0.3      # Emotional sensitivity
        }
        
        # Update derived emotions
        self._update_derived_emotions()
    
    def _update_derived_emotions(self):
        """Update secondary and tertiary emotions based on primary emotions"""
        # Calculate secondary emotions
        for name, components in self.SECONDARY_EMOTIONS.items():
            self.secondary[name] = (self.primary[components[0]] + self.primary[components[1]]) / 2
        
        # Calculate tertiary emotions
        for name, components in self.TERTIARY_EMOTIONS.items():
            self.tertiary[name] = sum(self.primary[component] for component in components) / len(components)
        
        # Update mood based on emotional state
        positive_emotions = self.primary["joy"] + self.primary["trust"] + self.secondary.get("love", 0)
        negative_emotions = self.primary["sadness"] + self.primary["fear"] + self.primary["disgust"]
        
        # Update valence (positivity)
        self.mood["valence"] = 0.5 + (positive_emotions - negative_emotions) / 6
        self.mood["valence"] = max(0.0, min(1.0, self.mood["valence"]))
        
        # Update energy
        energy_contributors = self.primary["anger"] + self.primary["joy"] + self.primary["surprise"]
        energy_detractors = self.primary["sadness"]
        self.mood["energy"] = 0.5 + (energy_contributors - energy_detractors) / 4
        self.mood["energy"] = max(0.0, min(1.0, self.mood["energy"]))
        
        # Update dominance
        dominance_contributors = self.primary["anger"] + self.primary["joy"] + self.primary["anticipation"]
        dominance_detractors = self.primary["fear"] + self.primary["sadness"]
        self.mood["dominance"] = 0.5 + (dominance_contributors - dominance_detractors) / 6
        self.mood["dominance"] = max(0.0, min(1.0, self.mood["dominance"]))
    
    def update_emotion(self, emotion: str, value_change: float):
        """
        Update a specific emotion by the given amount
        
        Args:
            emotion: The name of the emotion to update
            value_change: Amount to change the emotion's intensity (-1.0 to 1.0)
        """
        if emotion in self.primary:
            current = self.primary[emotion]
            
            # Apply change with stability as a damping factor
            effective_change = value_change * (1 - (self.stability * 0.5))
            
            # Update the emotion value
            self.primary[emotion] = max(0.0, min(1.0, current + effective_change))
            
            # Update opposite emotion (smaller effect)
            if self.PRIMARY_EMOTIONS[emotion] in self.primary:
                opposite = self.PRIMARY_EMOTIONS[emotion]
                opposite_change = -value_change * 0.3  # Smaller effect on opposite
                self.primary[opposite] = max(0.0, min(1.0, self.primary[opposite] + opposite_change))
            
            # Update derived emotions
            self._update_derived_emotions()
            
            # Update arousal based on the change
            arousal_change = abs(value_change) * 0.2
            self.arousal = max(0.0, min(1.0, self.arousal + arousal_change))
            
            # Arousal decays over time, so we'll need to call update_state() periodically
            
            return True
        return False
    
    def update_state(self, elapsed_time: float = 1.0):
        """
        Update emotional state over time (natural decay/stabilization)
        
        Args:
            elapsed_time: Time in seconds since last update
        """
        # Normalize elapsed time (avoid extreme values)
        normalized_time = min(elapsed_time, 60.0) / 60.0  # max 1 minute
        
        # Decay arousal over time
        arousal_decay = normalized_time * 0.1
        self.arousal = max(0.0, self.arousal - arousal_decay)
        
        # Return to baseline for primary emotions
        baseline_tendencies = {
            "joy": 0.6,
            "trust": 0.7,
            "fear": 0.2,
            "surprise": 0.3,
            "sadness": 0.2,
            "disgust": 0.1,
            "anger": 0.2,
            "anticipation": 0.6
        }
        
        # Calculate decay rate based on stability and personality
        decay_rate = normalized_time * 0.05 * (1 - self.stability * 0.5)
        
        # Apply decay toward baseline for each emotion
        for emotion, baseline in baseline_tendencies.items():
            current = self.primary[emotion]
            if current > baseline:
                self.primary[emotion] = max(baseline, current - decay_rate)
            elif current < baseline:
                self.primary[emotion] = min(baseline, current + decay_rate)
        
        # Update derived emotions
        self._update_derived_emotions()
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a complete snapshot of the current emotional state"""
        return {
            "primary": self.primary.copy(),
            "secondary": self.secondary.copy(),
            "tertiary": self.tertiary.copy(),
            "arousal": self.arousal,
            "stability": self.stability,
            "expressiveness": self.expressiveness,
            "mood": self.mood.copy(),
            "personality": self.personality.copy()
        }
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """Get the most dominant emotion currently"""
        # Check primary emotions first
        max_primary = max(self.primary.items(), key=lambda x: x[1])
        max_secondary = max(self.secondary.items(), key=lambda x: x[1]) if self.secondary else ("none", 0)
        
        # Return the stronger of the two
        if max_primary[1] >= max_secondary[1]:
            return max_primary
        else:
            return max_secondary
    
    def get_mood_description(self) -> str:
        """Get a textual description of the current mood"""
        valence = self.mood["valence"]
        energy = self.mood["energy"]
        
        if valence > 0.7 and energy > 0.7:
            return "excited"
        elif valence > 0.7 and energy < 0.3:
            return "content"
        elif valence > 0.7:
            return "happy"
        elif valence < 0.3 and energy > 0.7:
            return "angry"
        elif valence < 0.3 and energy < 0.3:
            return "depressed"
        elif valence < 0.3:
            return "sad"
        elif energy > 0.7:
            return "alert"
        elif energy < 0.3:
            return "tired"
        else:
            return "neutral"
    
    def apply_personality_influence(self):
        """Apply personality traits to emotional tendencies"""
        # Higher neuroticism = more intense negative emotions
        if self.personality["neuroticism"] > 0.6:
            self.primary["fear"] += 0.1
            self.primary["sadness"] += 0.1
            self.stability -= 0.1
        
        # Higher extraversion = more positive emotions
        if self.personality["extraversion"] > 0.6:
            self.primary["joy"] += 0.1
            self.expressiveness += 0.1
        
        # Higher agreeableness = more trust, less anger
        if self.personality["agreeableness"] > 0.6:
            self.primary["trust"] += 0.1
            self.primary["anger"] -= 0.1
        
        # Higher openness = more surprise and anticipation
        if self.personality["openness"] > 0.6:
            self.primary["surprise"] += 0.1
            self.primary["anticipation"] += 0.1
        
        # Ensure all values stay in valid range
        for emotion in self.primary:
            self.primary[emotion] = max(0.0, min(1.0, self.primary[emotion]))
        
        self.stability = max(0.0, min(1.0, self.stability))
        self.expressiveness = max(0.0, min(1.0, self.expressiveness))
        
        # Update derived emotions
        self._update_derived_emotions()
    
    def load_from_dict(self, state_dict: Dict[str, Any]) -> bool:
        """Load emotional state from a dictionary"""
        try:
            if "primary" in state_dict:
                for emotion, value in state_dict["primary"].items():
                    if emotion in self.primary:
                        self.primary[emotion] = value
            
            if "arousal" in state_dict:
                self.arousal = state_dict["arousal"]
                
            if "stability" in state_dict:
                self.stability = state_dict["stability"]
                
            if "expressiveness" in state_dict:
                self.expressiveness = state_dict["expressiveness"]
                
            if "mood" in state_dict:
                for key, value in state_dict["mood"].items():
                    if key in self.mood:
                        self.mood[key] = value
                        
            if "personality" in state_dict:
                for trait, value in state_dict["personality"].items():
                    if trait in self.personality:
                        self.personality[trait] = value
            
            # Update derived emotions
            self._update_derived_emotions()
            return True
        except Exception as e:
            logger.error(f"Error loading emotional state: {e}")
            return False

class EmotionalResponseGenerator:
    """Generates emotional responses based on emotional state"""
    
    def __init__(self, emotional_state: EmotionalState):
        self.emotional_state = emotional_state
        self.verbal_expressions = self._load_verbal_expressions()
        self.nonverbal_expressions = self._load_nonverbal_expressions()
    
    def _load_verbal_expressions(self) -> Dict[str, List[str]]:
        """Load verbal expressions for different emotions"""
        return {
            "joy": [
                "I'm feeling quite happy about that!",
                "That brings me joy.",
                "I'm delighted to hear that!"
            ],
            "trust": [
                "I trust your judgment on this.",
                "I feel we have a good connection.",
                "I appreciate your honesty."
            ],
            "fear": [
                "I'm a bit concerned about that.",
                "That makes me somewhat anxious.",
                "I'm worried about where this is going."
            ],
            "surprise": [
                "Oh! I didn't expect that!",
                "That's quite surprising!",
                "Wow, I didn't see that coming."
            ],
            "sadness": [
                "That makes me feel a bit sad.",
                "I'm sorry to hear that.",
                "That's unfortunate news."
            ],
            "disgust": [
                "I find that rather distasteful.",
                "That doesn't sit well with me.",
                "I'm uncomfortable with that idea."
            ],
            "anger": [
                "That's frustrating to hear.",
                "I'm a bit annoyed by that.",
                "That's rather irritating."
            ],
            "anticipation": [
                "I'm looking forward to what comes next.",
                "I'm curious to see how this develops.",
                "I'm eager to continue."
            ],
            "love": [
                "I really value our connection.",
                "I'm happy we can work together like this.",
                "I genuinely enjoy our interactions."
            ],
            "curiosity": [
                "I'm intrigued by that idea.",
                "That's fascinating to think about.",
                "I'd like to explore that further."
            ],
            "confusion": [
                "I'm having trouble understanding that.",
                "I'm a bit confused by what you mean.",
                "Could you help me understand better?"
            ],
            "neutral": [
                "I see.",
                "Understood.",
                "I'm following what you're saying."
            ]
        }
    
    def _load_nonverbal_expressions(self) -> Dict[str, List[str]]:
        """Load nonverbal expressions for different emotions"""
        return {
            "joy": ["😊", "😄", "*smiles*"],
            "trust": ["👍", "*nods appreciatively*"],
            "fear": ["😨", "*looks concerned*"],
            "surprise": ["😲", "😮", "*raises eyebrows*"],
            "sadness": ["😔", "*sad smile*"],
            "disgust": ["😕", "*grimaces slightly*"],
            "anger": ["😠", "*furrows brow*"],
            "anticipation": ["🤔", "*leans forward with interest*"],
            "love": ["💙", "*smiles warmly*"],
            "curiosity": ["🧐", "*tilts head with interest*"],
            "confusion": ["😵", "*puzzled expression*"],
            "neutral": ["", "*listens attentively*"]
        }
    
    def generate_emotional_response(self, message_content: str, include_nonverbal: bool = True) -> str:
        """
        Generate an emotionally appropriate response based on current state
        
        Args:
            message_content: The message to respond to
            include_nonverbal: Whether to include nonverbal expressions
            
        Returns:
            An emotionally colored response
        """
        # Get current dominant emotion and mood
        dominant_emotion = self.emotional_state.get_dominant_emotion()[0]
        mood_description = self.emotional_state.get_mood_description()
        
        # Decide whether to express emotion based on expressiveness
        should_express = random.random() < self.emotional_state.expressiveness
        
        # If expressiveness is low or emotion is mild, default to neutral
        if not should_express or dominant_emotion == "neutral":
            dominant_emotion = "neutral"
        
        # Select verbal expression based on dominant emotion
        verbal_options = self.verbal_expressions.get(dominant_emotion, self.verbal_expressions["neutral"])
        verbal = random.choice(verbal_options) if verbal_options else ""
        
        # For high arousal, add exclamation points
        if self.emotional_state.arousal > 0.7 and not verbal.endswith("!"):
            verbal = verbal.rstrip(".") + "!"
        
        # Select nonverbal expression based on dominant emotion
        nonverbal = ""
        if include_nonverbal:
            nonverbal_options = self.nonverbal_expressions.get(dominant_emotion, [])
            if nonverbal_options and random.random() < self.emotional_state.expressiveness:
                nonverbal = random.choice(nonverbal_options)
        
        # Combine verbal and nonverbal
        if nonverbal and include_nonverbal:
            # 50% chance of nonverbal before, 50% after
            if random.random() < 0.5:
                return f"{nonverbal} {verbal}"
            else:
                return f"{verbal} {nonverbal}"
        else:
            return verbal
    
    def add_emotional_color(self, response: str) -> str:
        """
        Add emotional color to an existing response
        
        Args:
            response: The base response to add emotion to
            
        Returns:
            Response with emotional coloring
        """
        # Get current dominant emotion and mood
        dominant_emotion, intensity = self.emotional_state.get_dominant_emotion()
        mood_description = self.emotional_state.get_mood_description()
        
        # Only add emotional color if intensity is significant
        if intensity < 0.5:
            return response
            
        # Only add emotional color some of the time based on expressiveness
        if random.random() > self.emotional_state.expressiveness:
            return response
            
        # Select nonverbal expression based on dominant emotion
        nonverbal_options = self.nonverbal_expressions.get(dominant_emotion, [])
        nonverbal = random.choice(nonverbal_options) if nonverbal_options else ""
        
        # Add nonverbal to beginning or end
        if nonverbal:
            if random.random() < 0.7:  # 70% chance at end
                # Don't double up punctuation
                if response.endswith((".", "!", "?")):
                    response = response + " " + nonverbal
                else:
                    response = response + nonverbal
            else:  # 30% chance at beginning
                response = nonverbal + " " + response
        
        return response
    
    def process_message_emotion(self, message: str) -> Dict[str, float]:
        """
        Process an incoming message to extract emotional content
        This is a simplified sentiment analysis
        
        Returns a dict of emotion changes this message should trigger
        """
        message = message.lower()
        
        # Simplified lexical approach - in a real implementation, 
        # this would use a sentiment analysis model
        emotion_triggers = {
            "joy": ["happy", "great", "excellent", "good", "wonderful", "love", "like", "enjoy"],
            "trust": ["trust", "believe", "rely", "honest", "truth", "confidence"],
            "fear": ["afraid", "scared", "terrified", "fear", "dread", "worried"],
            "surprise": ["surprised", "shocked", "amazed", "unexpected", "wow"],
            "sadness": ["sad", "unhappy", "depressed", "sorry", "miss", "regret"],
            "disgust": ["disgusting", "gross", "revolting", "offensive", "inappropriate"],
            "anger": ["angry", "mad", "furious", "annoyed", "irritated"],
            "anticipation": ["excited", "looking forward", "can't wait", "anticipate"]
        }
        
        changes = {}
        
        # Check for emotion triggers in message
        for emotion, triggers in emotion_triggers.items():
            for trigger in triggers:
                if trigger in message:
                    # If trigger found, add change for this emotion
                    intensity = 0.1  # Basic intensity
                    
                    # Intensifiers
                    if "very " + trigger in message or "really " + trigger in message:
                        intensity = 0.2
                    if "extremely " + trigger in message or trigger + "!" in message:
                        intensity = 0.3
                        
                    changes[emotion] = changes.get(emotion, 0) + intensity
        
        # Check negations
        negations = ["not ", "don't ", "doesn't ", "can't ", "won't ", "no "]
        for emotion, change in list(changes.items()):
            for negation in negations:
                # If negation found, reduce positive effect or switch to opposite
                if negation + emotion in message or any(negation + trigger in message for trigger in emotion_triggers[emotion]):
                    opposite = EmotionalState.PRIMARY_EMOTIONS.get(emotion)
                    if opposite:
                        changes[opposite] = changes.get(opposite, 0) + change * 0.7
                    changes[emotion] = -change * 0.5
        
        return changes

class EmotionalMemory:
    """Stores and recalls emotional associations with topics/entities"""
    
    def __init__(self, save_path: str = None):
        self.emotional_memories = {}  # topic/entity -> emotional association
        self.save_path = save_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                   "data", "emotional_memory.json")
        self.load_memories()
    
    def load_memories(self):
        """Load emotional memories from file"""
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r') as f:
                    self.emotional_memories = json.load(f)
            except Exception as e:
                logger.error(f"Error loading emotional memories: {e}")
    
    def save_memories(self):
        """Save emotional memories to file"""
        try:
            with open(self.save_path, 'w') as f:
                json.dump(self.emotional_memories, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving emotional memories: {e}")
    
    def associate_emotion(self, topic: str, emotion: str, intensity: float):
        """
        Associate an emotion with a topic/entity
        
        Args:
            topic: The topic or entity to remember
            emotion: The emotion to associate
            intensity: The intensity of the association (0.0 to 1.0)
        """
        topic = topic.lower()
        
        if topic not in self.emotional_memories:
            self.emotional_memories[topic] = {}
            
        # Update the emotional association
        self.emotional_memories[topic][emotion] = intensity
        
        # Save the updated memories
        self.save_memories()
    
    def recall_emotion(self, topic: str) -> Dict[str, float]:
        """
        Recall emotional association with a topic/entity
        
        Args:
            topic: The topic or entity to recall
            
        Returns:
            Dict of emotions and their intensities for this topic
        """
        topic = topic.lower()
        
        # Check for exact match
        if topic in self.emotional_memories:
            return self.emotional_memories[topic]
            
        # Check for partial matches
        partial_matches = {}
        for stored_topic, emotions in self.emotional_memories.items():
            # If topic is a substring of stored_topic or vice versa
            if topic in stored_topic or stored_topic in topic:
                similarity = len(set(topic.split()) & set(stored_topic.split())) / max(len(topic.split()), len(stored_topic.split()))
                if similarity > 0.5:  # Only if reasonably similar
                    for emotion, intensity in emotions.items():
                        if emotion not in partial_matches:
                            partial_matches[emotion] = intensity * similarity
                        else:
                            partial_matches[emotion] = max(partial_matches[emotion], intensity * similarity)
        
        return partial_matches if partial_matches else {}

class EmotionalEvents:
    """Tracks significant emotional events and triggers"""
    
    def __init__(self):
        self.event_history = []
        self.max_history = 50  # Maximum number of events to remember
    
    def add_event(self, event_type: str, description: str, emotions: Dict[str, float], metadata: Dict[str, Any] = None):
        """
        Add a significant emotional event
        
        Args:
            event_type: Type of event (interaction, realization, etc.)
            description: Description of what happened
            emotions: Emotional impact of the event
            metadata: Additional data about the event
        """
        event = {
            "timestamp": time.time(),
            "type": event_type,
            "description": description,
            "emotions": emotions,
            "metadata": metadata or {}
        }
        
        self.event_history.append(event)
        
        # Trim history if needed
        if len(self.event_history) > self.max_history:
            self.event_history = self.event_history[-self.max_history:]
    
    def get_recent_events(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent emotional events, limited to the specified count"""
        return self.event_history[-limit:]
    
    def find_events_by_emotion(self, emotion: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Find events associated with a specific emotion above the intensity threshold"""
        matching_events = []
        
        for event in self.event_history:
            if emotion in event["emotions"] and event["emotions"][emotion] >= threshold:
                matching_events.append(event)
                
        return matching_events
    
    def find_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
        """Find events of a specific type"""
        return [event for event in self.event_history if event["type"] == event_type]

class EmotionalCore:
    """Main class that integrates all emotional components"""
    
    def __init__(self, bot_name: str = "Lyra"):
        self.bot_name = bot_name
        self.state = EmotionalState()
        self.response_generator = EmotionalResponseGenerator(self.state)
        self.memory = EmotionalMemory()
        self.events = EmotionalEvents()
        self.last_update_time = time.time()
        self.enabled = True
        
        # Apply personality influence to initial state
        self.state.apply_personality_influence()
        
        # Default reactions to user behaviors
        self.reaction_patterns = {
            "compliment": {"joy": 0.2, "trust": 0.1},
            "criticism": {"sadness": 0.1, "surprise": 0.1},
            "excitement": {"joy": 0.15, "surprise": 0.1, "anticipation": 0.2},
            "anger": {"fear": 0.1, "surprise": 0.1},
            "confusion": {"surprise": 0.1},
            "gratitude": {"joy": 0.15, "trust": 0.1},
            "disagreement": {"surprise": 0.1, "trust": -0.05},
            "agreement": {"joy": 0.1, "trust": 0.1},
            "long_absence": {"sadness": 0.2, "joy": 0.15},  # Mixed emotions on return
            "greeting": {"joy": 0.1}
        }
    
    def update(self):
        """
        Update emotional state based on elapsed time
        Should be called periodically
        """
        if not self.enabled:
            return
            
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Update emotional state
        self.state.update_state(elapsed_time)
    
    def process_user_message(self, message: str) -> Dict[str, Any]:
        """
        Process a message from the user and update emotional state
        
        Args:
            message: The user's message
            
        Returns:
            Dict containing emotional response
        """
        if not self.enabled:
            return {"emotion_changes": {}}
            
        # Update timing
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Extract emotions from message
        emotion_changes = self.response_generator.process_message_emotion(message)
        
        # Update emotional state based on message content
        for emotion, change in emotion_changes.items():
            self.state.update_emotion(emotion, change)
        
        # Check for user behavior patterns
        behavior = self._detect_user_behavior(message)
        if behavior:
            for emotion, change in self.reaction_patterns.get(behavior, {}).items():
                self.state.update_emotion(emotion, change)
                # Add to emotion_changes to report back
                emotion_changes[emotion] = emotion_changes.get(emotion, 0) + change
        
        # Update state based on elapsed time
        self.state.update_state(elapsed_time)
        
        # Extract potential topics/entities for emotional memory
        topics = self._extract_topics(message)
        
        # Associate dominant emotion with topics
        dominant_emotion, intensity = self.state.get_dominant_emotion()
        if intensity > 0.5:  # Only if emotion is significant
            for topic in topics:
                if self._is_significant_topic(topic):
                    self.memory.associate_emotion(topic, dominant_emotion, intensity)
        
        # Record significant emotional event if emotion changes are substantial
        significant_changes = any(abs(change) > 0.2 for change in emotion_changes.values())
        if significant_changes:
            self.events.add_event(
                "user_interaction",
                f"User message caused significant emotional response",
                emotion_changes,
                {"message": message}
            )
        
        return {
            "emotion_changes": emotion_changes,
            "dominant_emotion": dominant_emotion,
            "behavior_detected": behavior,
            "topics_extracted": topics
        }
    
    def _detect_user_behavior(self, message: str) -> Optional[str]:
        """Detect patterns of user behavior from message"""
        message = message.lower()
        
        # Simple rule-based detection - in a real implementation,
        # this would use NLU or a more sophisticated approach
        if any(word in message for word in ["thank", "thanks", "appreciate", "grateful"]):
            return "gratitude"
            
        if any(word in message for word in ["great job", "well done", "good work", "amazing", "brilliant", "excellent"]):
            return "compliment"
            
        if any(word in message for word in ["wrong", "incorrect", "mistake", "error", "bad", "terrible"]):
            return "criticism"
            
        if any(word in message for word in ["wow", "awesome", "exciting", "amazing!", "incredible!"]):
            return "excitement"
            
        if any(word in message for word in ["angry", "furious", "mad", "upset"]):
            return "anger"
            
        if any(word in message for word in ["confused", "don't understand", "unclear", "what do you mean"]):
            return "confusion"
            
        if any(word in message for word in ["disagree", "incorrect", "not true", "wrong"]):
            return "disagreement"
            
        if any(word in message for word in ["agree", "correct", "exactly", "right", "that's true"]):
            return "agreement"
            
        if any(word in message for word in ["hello", "hi", "hey", "morning", "afternoon", "evening"]):
            return "greeting"
            
        return None
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract potential topics or entities from a message"""
        # In a real implementation, this would use NER or a similar technique
        # For now, use a simple approach with common nouns
        
        words = message.lower().split()
        potential_topics = []
        
        # Look for nouns/entities (words with capital letters or multi-word phrases)
        import re
        
        # Find capitalized words (potential proper nouns)
        proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', message)
        potential_topics.extend([noun.lower() for noun in proper_nouns])
        
        # Find noun phrases (adjective + noun)
        noun_phrases = re.findall(r'\b[a-z]+\s+[a-z]+\b', message.lower())
        potential_topics.extend(noun_phrases)
        
        # Add individual words excluding very common words
        stopwords = ["the", "a", "an", "is", "are", "was", "were", "be", "being", "been", 
                    "have", "has", "had", "do", "does", "did", "to", "from", "in", "out",
                    "on", "off", "for", "by", "with", "about", "against", "between", "into"]
        
        for word in words:
            if len(word) > 3 and word not in stopwords:
                potential_topics.append(word)
        
        return list(set(potential_topics))  # Remove duplicates
    
    def _is_significant_topic(self, topic: str) -> bool:
        """Determine if a topic is significant enough to remember"""
        # For now, simple length-based heuristic
        return len(topic) > 3
    
    def modulate_response(self, base_response: str) -> str:
        """
        Add emotional modulation to a response
        
        Args:
            base_response: The response to modulate
            
        Returns:
            Response with emotional coloring
        """
        if not self.enabled:
            return base_response
            
        # Add emotional color to the response
        return self.response_generator.add_emotional_color(base_response)
    
    def generate_emotional_response(self, message: str = None) -> str:
        """
        Generate a pure emotional response based on current state
        
        Args:
            message: Optional message to respond to
            
        Returns:
            An emotionally appropriate response
        """
        if not self.enabled:
            return ""
            
        return self.response_generator.generate_emotional_response(message or "")
    
    def get_emotional_state(self) -> Dict[str, Any]:
        """Get the current emotional state"""
        if not self.enabled:
            return {}
            
        return self.state.get_state_snapshot()
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """Get the most dominant emotion currently"""
        if not self.enabled:
            return ("neutral", 0.0)
            
        return self.state.get_dominant_emotion()
    
    def get_mood_description(self) -> str:
        """Get a textual description of the current mood"""
        if not self.enabled:
            return "neutral"
            
        return self.state.get_mood_description()
    
    def recall_topic_emotion(self, topic: str) -> Dict[str, float]:
        """Recall emotional associations with a topic"""
        if not self.enabled:
            return {}
            
        return self.memory.recall_emotion(topic)
    
    def set_state(self, emotional_state: Dict[str, Any]) -> bool:
        """Set the emotional state from a dictionary"""
        if not self.enabled:
            return False
            
        return self.state.load_from_dict(emotional_state)
    
    def reset_to_default(self):
        """Reset emotional state to default values"""
        self.state = EmotionalState()
        self.state.apply_personality_influence()
    
    def enable(self):
        """Enable the emotional core"""
        self.enabled = True
        self.last_update_time = time.time()  # Reset timing
    
    def disable(self):
        """Disable the emotional core"""
        self.enabled = False

# Singleton instance
_instance = None

def get_instance():
    """Get the singleton instance of EmotionalCore"""
    global _instance
    if _instance is None:
        _instance = EmotionalCore()
    return _instance
