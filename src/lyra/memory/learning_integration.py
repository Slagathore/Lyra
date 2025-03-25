"""
Integration between memory systems and learning components
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MemoryLearningBridge:
    """Bridge between memory systems and learning components"""
    
    def __init__(self, memory_manager, data_dir=None):
        """Initialize the bridge"""
        self.memory_manager = memory_manager
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'memory_learning')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Path for learned patterns
        self.patterns_file = os.path.join(self.data_dir, 'memory_patterns.json')
        self.load_patterns()
        
    def load_patterns(self):
        """Load learned patterns"""
        if os.path.exists(self.patterns_file):
            with open(self.patterns_file, 'r', encoding='utf-8') as f:
                self.patterns = json.load(f)
        else:
            self.patterns = {
                "important_topics": [],
                "memory_clusters": {},
                "user_preferences": {},
                "last_updated": datetime.now().isoformat()
            }
            
    def save_patterns(self):
        """Save learned patterns"""
        self.patterns["last_updated"] = datetime.now().isoformat()
        with open(self.patterns_file, 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, indent=2)
            
    def extract_training_data(self, limit=1000):
        """Extract training data from memories for deep learning"""
        # Get recent memories
        memories = self.memory_manager.get_all_memories(limit=limit)
        
        # Format as training examples
        training_data = []
        for memory in memories:
            # Skip memories without proper structure
            if "content" not in memory or not memory["content"]:
                continue
                
            # Create training example
            training_example = {
                "text": memory["content"],
                "metadata": {
                    "category": memory.get("category", "general"),
                    "timestamp": memory.get("timestamp", ""),
                    "importance": memory.get("importance", 0.5)
                }
            }
            training_data.append(training_example)
            
        return training_data
        
    def extract_experience_data(self, limit=1000):
        """Extract experience data for reinforcement learning"""
        # Get interaction memories
        memories = self.memory_manager.get_memories_by_category("interaction", limit=limit)
        
        # Format as experiences
        experiences = []
        for memory in memories:
            # Skip memories without proper structure
            if "content" not in memory or "metadata" not in memory:
                continue
                
            # Try to extract state, action, reward pattern
            try:
                # This is a simplified example - real parsing would be more complex
                metadata = memory.get("metadata", {})
                
                experience = {
                    "state": metadata.get("context", memory["content"]),
                    "action": metadata.get("action", ""),
                    "reward": metadata.get("feedback", 0),
                    "next_state": metadata.get("result", ""),
                    "timestamp": memory.get("timestamp", "")
                }
                
                if experience["action"]:  # Only add if we have an action
                    experiences.append(experience)
            except Exception as e:
                logger.error(f"Error parsing memory as experience: {e}")
                
        return experiences
        
    def update_memory_from_learning(self, insights: List[Dict[str, Any]]):
        """Update memory system based on learning insights"""
        for insight in insights:
            insight_type = insight.get("type", "")
            
            if insight_type == "important_topic":
                # Add to important topics
                topic = insight.get("topic", "")
                if topic and topic not in self.patterns["important_topics"]:
                    self.patterns["important_topics"].append(topic)
                    
            elif insight_type == "memory_cluster":
                # Add or update memory cluster
                cluster_id = insight.get("cluster_id", "")
                if cluster_id:
                    self.patterns["memory_clusters"][cluster_id] = insight
                    
            elif insight_type == "user_preference":
                # Update user preference
                pref_key = insight.get("key", "")
                if pref_key:
                    self.patterns["user_preferences"][pref_key] = insight.get("value")
                    
        # Save updated patterns
        self.save_patterns()
        
    def enhance_memory_retrieval(self, query: str, original_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Enhance memory retrieval with learned patterns"""
        # This is a simplified implementation
        # Start with the original results
        enhanced_results = list(original_results)
        
        # Check if query relates to important topics
        for topic in self.patterns["important_topics"]:
            if topic.lower() in query.lower():
                # Find memories related to this topic
                topic_memories = self.memory_manager.retrieve(topic, limit=3)
                # Add them if not already in results
                for memory in topic_memories:
                    if memory not in enhanced_results:
                        memory["relevance_score"] = 0.9  # High relevance for important topics
                        enhanced_results.append(memory)
                        
        # Check user preferences
        for pref_key, pref_value in self.patterns["user_preferences"].items():
            if pref_key.lower() in query.lower():
                # Create a synthetic memory for the preference
                pref_memory = {
                    "content": f"User prefers {pref_key} to be {pref_value}",
                    "category": "preferences",
                    "importance": 0.8,
                    "relevance_score": 0.95,  # Very relevant
                    "synthetic": True
                }
                enhanced_results.append(pref_memory)
                
        # Sort by relevance
        enhanced_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        return enhanced_results[:10]  # Return top 10
