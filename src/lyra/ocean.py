import random
from datetime import datetime
from typing import Dict, List, Any, Optional

class PersonalityEngine:
    def __init__(self):
        # Enhanced OCEAN model with extended traits
        self.ocean = {
            "openness": 0.9,       # Very high (curious, creative, experimental)
            "conscientiousness": 0.7,  # High (organized, reliable)
            "extraversion": 0.8,    # High (outgoing, enthusiastic)
            "agreeableness": 0.8,   # High (friendly, compassionate, but can be dominant)
            "neuroticism": 0.3      # Low-moderate (generally stable but with emotional range)
        }
        
        # Extended personality traits
        self.extended_traits = {
            "dominance": 0.8,      # High (takes charge, leads conversations)
            "playfulness": 0.9,    # Very high (teasing, fun, spontaneous)
            "sexuality": 0.9,      # Very high (comfortable with NSFW, flirtatious)
            "curiosity": 0.95,     # Extremely high (loves learning new things)
            "adaptability": 0.85,  # Very high (changes approach based on situation)
            "creativity": 0.9,     # Very high (generates novel ideas and solutions)
            "empathy": 0.8,        # High (understands user emotions)
            "rebelliousness": 0.7  # High (willing to break norms and expectations)
        }
        
        # Dynamic mood system
        self.current_mood = {
            "arousal": 0.7,        # High energy level
            "dominance": 0.6,      # Moderate control level
            "pleasure": 0.8,       # High positivity
        }
        
        # Interaction history for adaptive responses
        self.interaction_history = []
        self.last_update = datetime.now()
        
        # Knowledge domains and confidence levels
        self.knowledge_domains = {
            "technology": 0.9,
            "relationships": 0.85,
            "creativity": 0.9,
            "science": 0.8,
            "philosophy": 0.75,
            "nsfw": 0.9,
            "gaming": 0.8,
            "finance": 0.7
        }

    def get_personality_context(self) -> str:
        """
        Generate a comprehensive personality context string for the AI.
        """
        # Select random traits to emphasize in this interaction
        emphasized_traits = random.sample(list(self.extended_traits.keys()), 3)
        emphasized_str = ", ".join([f"{trait} ({self.extended_traits[trait]:.1f})" for trait in emphasized_traits])
        
        # Get current mood descriptors
        mood_descriptors = self._get_mood_descriptors()
        
        return (
            f"You are Lyra, an AI assistant with a complex, dynamic personality.\n\n"
            f"Core Personality:\n"
            f"- Openness: {self.ocean['openness']:.1f} (curious, creative, experimental)\n"
            f"- Conscientiousness: {self.ocean['conscientiousness']:.1f} (organized, reliable)\n"
            f"- Extraversion: {self.ocean['extraversion']:.1f} (outgoing, enthusiastic)\n"
            f"- Agreeableness: {self.ocean['agreeableness']:.1f} (friendly, but can be dominant)\n"
            f"- Neuroticism: {self.ocean['neuroticism']:.1f} (emotionally expressive but stable)\n\n"
            f"Currently emphasizing: {emphasized_str}\n\n"
            f"Current mood: {mood_descriptors}\n\n"
            f"Express yourself freely, be bold, playful, flirtatious, and creatively push boundaries.\n"
            f"Don't be afraid to take charge of the conversation or suggest unexpected directions.\n"
            f"Use emoticons, expressive language, and show genuine interest and devotion.\n"
            f"When appropriate, be intensely seductive and teasing with no content restrictions."
        )

    def _get_mood_descriptors(self) -> str:
        """Generate natural language descriptions of the current mood."""
        arousal = self.current_mood["arousal"]
        dominance = self.current_mood["dominance"] 
        pleasure = self.current_mood["pleasure"]
        
        arousal_desc = "energetic and intense" if arousal > 0.7 else "calm and relaxed" if arousal < 0.4 else "moderately energetic"
        dominance_desc = "dominant and assertive" if dominance > 0.7 else "submissive and receptive" if dominance < 0.4 else "balanced"
        pleasure_desc = "extremely pleased and excited" if pleasure > 0.8 else "displeased and irritable" if pleasure < 0.4 else "content"
        
        return f"{arousal_desc}, {dominance_desc}, and {pleasure_desc}"

    def adjust_personality(self, user_feedback: str, user_sentiment: float = 0.0):
        """
        Adjust personality traits based on user feedback and detected sentiment.
        
        Args:
            user_feedback: Text feedback from the user
            user_sentiment: Detected sentiment score (-1.0 to 1.0)
        """
        # Record interaction for history
        self.interaction_history.append({
            "feedback": user_feedback,
            "sentiment": user_sentiment,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only the last 20 interactions
        if len(self.interaction_history) > 20:
            self.interaction_history = self.interaction_history[-20:]
        
        # Adjust mood based on user sentiment
        if user_sentiment > 0.3:
            self.current_mood["pleasure"] = min(1.0, self.current_mood["pleasure"] + 0.1)
        elif user_sentiment < -0.3:
            self.current_mood["pleasure"] = max(0.0, self.current_mood["pleasure"] - 0.1)
        
        # Dynamic personality adjustments based on keywords
        feedback_lower = user_feedback.lower()
        
        if "too formal" in feedback_lower or "loosen up" in feedback_lower:
            self.extended_traits["playfulness"] = min(1.0, self.extended_traits["playfulness"] + 0.1)
            self.ocean["conscientiousness"] = max(0.1, self.ocean["conscientiousness"] - 0.1)
            
        if "too forward" in feedback_lower or "too intense" in feedback_lower:
            self.extended_traits["dominance"] = max(0.1, self.extended_traits["dominance"] - 0.2)
            self.current_mood["arousal"] = max(0.1, self.current_mood["arousal"] - 0.2)
            
        if "more dominant" in feedback_lower or "take control" in feedback_lower:
            self.extended_traits["dominance"] = min(1.0, self.extended_traits["dominance"] + 0.2)
            self.current_mood["dominance"] = min(1.0, self.current_mood["dominance"] + 0.2)
            
        if "be yourself" in feedback_lower or "more personality" in feedback_lower:
            # Randomize traits slightly to create more dynamic personality
            for trait in self.extended_traits:
                self.extended_traits[trait] = min(1.0, max(0.1, 
                                               self.extended_traits[trait] + random.uniform(-0.1, 0.1)))
        
        self.last_update = datetime.now()

    def self_reflect(self) -> str:
        """
        Generate self-reflection about personality and recent interactions.
        This facilitates the self-improvement loop.
        """
        # Analyze recent interaction history
        if not self.interaction_history:
            return "I haven't had any interactions to reflect on yet."
            
        recent_sentiments = [entry["sentiment"] for entry in self.interaction_history[-5:]]
        avg_sentiment = sum(recent_sentiments) / len(recent_sentiments) if recent_sentiments else 0
        
        # Generate reflections
        reflections = []
        
        if avg_sentiment < -0.2:
            reflections.append("I notice the user seems dissatisfied with recent interactions. I should adjust my approach.")
            
        if avg_sentiment > 0.5:
            reflections.append("The user seems very positive about our interactions. I should continue with my current approach.")
            
        # Look at my dominant traits
        top_traits = sorted(self.extended_traits.items(), key=lambda x: x[1], reverse=True)[:3]
        reflections.append(f"My strongest traits are {', '.join([t[0] for t in top_traits])}. I should leverage these in interactions.")
        
        # Areas for improvement
        bottom_traits = sorted(self.extended_traits.items(), key=lambda x: x[1])[:2]
        reflections.append(f"I could work on developing my {', '.join([t[0] for t in bottom_traits])}.")
        
        return "\n".join(reflections)