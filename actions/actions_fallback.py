"""
Fallback implementations for Rasa SDK dependencies
This allows Lyra to run without Rasa installed
"""
from typing import Any, Text, Dict, List

# Mock Rasa SDK classes
class Action:
    """Mock Action class"""
    def name(self) -> Text:
        return "action_default"
        
    def run(self, *args, **kwargs):
        return []

class Tracker:
    """Mock Tracker class"""
    def __init__(self):
        self.latest_message = {"text": ""}
        self.slots = {}
        
    def get_slot(self, slot_name):
        return self.slots.get(slot_name)

class CollectingDispatcher:
    """Mock CollectingDispatcher class"""
    def __init__(self):
        self.messages = []
        
    def utter_message(self, text=None, **kwargs):
        if text:
            self.messages.append(text)

# Function to detect tags in text
def detect_tags(text: str) -> List[str]:
    """
    Detect tags/topics in a piece of text
    
    Args:
        text: Text to analyze
        
    Returns:
        List of detected tags
    """
    import re
    
    # Common topics to detect
    topic_keywords = {
        "technology": ["tech", "computer", "software", "hardware", "gadget", "digital", "ai", "programming"],
        "health": ["health", "fitness", "exercise", "diet", "medical", "wellness", "doctor"],
        "science": ["science", "research", "discovery", "experiment", "theory", "scientific"],
        "art": ["art", "design", "creative", "painting", "drawing", "sculpture"],
        "music": ["music", "song", "band", "concert", "album", "musical", "singer"],
        "travel": ["travel", "trip", "vacation", "destination", "tourist", "journey"],
        "food": ["food", "recipe", "cooking", "cuisine", "dish", "meal", "restaurant"],
        "business": ["business", "finance", "money", "investment", "market", "company"],
        "education": ["education", "school", "learning", "teaching", "student", "academic"],
        "gaming": ["game", "gaming", "player", "playing", "videogame", "console"],
        "movie": ["movie", "film", "cinema", "theater", "actor", "director"],
        "book": ["book", "novel", "reading", "author", "literature", "story"],
        "sports": ["sport", "team", "player", "game", "competition", "athlete"],
        "politics": ["politics", "government", "policy", "election", "political", "vote"],
        "nature": ["nature", "environment", "animal", "plant", "ecology", "wildlife"],
        "weather": ["weather", "climate", "temperature", "forecast", "storm", "rain", "snow"],
        "history": ["history", "historical", "ancient", "past", "century"],
        "philosophy": ["philosophy", "philosophical", "ethics", "moral", "logic", "metaphysics"],
        "relationships": ["relationship", "dating", "marriage", "partner", "romantic", "love"],
        "family": ["family", "parent", "child", "sibling", "relative", "mom", "dad"],
        "personal": ["personal", "self", "improvement", "goal", "motivation", "life"],
    }
    
    # Prepare text for matching
    text_lower = text.lower()
    detected_tags = set()
    
    # Detect topics based on keyword presence
    for topic, keywords in topic_keywords.items():
        if any(re.search(r'\b' + keyword + r'\b', text_lower) for keyword in keywords):
            detected_tags.add(topic)
    
    # Detect question types
    if any(q in text_lower for q in ["what", "who", "when", "where", "why", "how"]):
        detected_tags.add("question")
    
    # Detect emotional content
    emotion_patterns = {
        "happy": ["happy", "joy", "excited", "glad", "pleased", "delighted", "smile"],
        "sad": ["sad", "upset", "unhappy", "depressed", "disappointed", "miserable"],
        "angry": ["angry", "mad", "upset", "frustrated", "annoyed", "irritated"],
        "fearful": ["afraid", "scared", "fearful", "terrified", "anxious", "nervous"],
        "surprised": ["surprised", "shocked", "astonished", "amazed", "startled"],
    }
    
    for emotion, patterns in emotion_patterns.items():
        if any(re.search(r'\b' + pattern + r'\b', text_lower) for pattern in patterns):
            detected_tags.add(emotion)
    
    return list(detected_tags)
