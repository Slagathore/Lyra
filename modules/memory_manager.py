import os
import json
import time
import logging
import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class UserMemoryManager:
    """Manages long-term user memory and preferences"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "user_memory")
        else:
            self.data_dir = data_dir
            
        # Create the directory if it doesn't exist
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.user_file = os.path.join(self.data_dir, "user_profile.json")
        
        # Initialize user profile
        self.user_profile = {
            "name": None,
            "demographics": {},
            "interests": [],
            "preferences": {},
            "locations": [],
            "contacts": {},
            "conversation_history": [],
            "facts": [],
            "last_updated": time.time()
        }
        
        # Load existing user profile if available
        self.load()
    
    def load(self) -> bool:
        """Load user profile from disk"""
        try:
            if os.path.exists(self.user_file):
                with open(self.user_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Update user profile with loaded data
                self.user_profile.update(data)
                
                logger.info("Loaded user profile")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading user profile: {str(e)}")
            return False
    
    def save(self) -> bool:
        """Save user profile to disk"""
        try:
            # Update timestamp
            self.user_profile["last_updated"] = time.time()
            
            with open(self.user_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_profile, f, indent=2)
                
            logger.info("Saved user profile")
            return True
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            return False
    
    def update_from_conversation(self, memory) -> bool:
        """Update user profile based on conversation memory"""
        try:
            # Extract personal information from the conversation
            personal_info = memory.extract_personal_info()
            
            # Update user profile with extracted information
            
            # Update name if found and not already set
            if personal_info["name"] and not self.user_profile["name"]:
                self.user_profile["name"] = personal_info["name"]
                
            # Update interests
            for interest in personal_info["interests"]:
                if interest not in self.user_profile["interests"]:
                    self.user_profile["interests"].append(interest)
                    
            # Update locations
            for location in personal_info["locations"]:
                if location not in self.user_profile["locations"]:
                    self.user_profile["locations"].append(location)
                    
            # Update preferences
            for item, preference in personal_info["preferences"].items():
                self.user_profile["preferences"][item] = preference
                
            # Update facts
            for fact in personal_info["facts"]:
                if fact not in self.user_profile["facts"]:
                    self.user_profile["facts"].append(fact)
                    
            # Add conversation to history
            if memory.conversation_id:
                # Check if this conversation is already in history
                existing = [c for c in self.user_profile["conversation_history"] if c["id"] == memory.conversation_id]
                
                if not existing:
                    # Add new conversation entry
                    self.user_profile["conversation_history"].append({
                        "id": memory.conversation_id,
                        "timestamp": time.time(),
                        "message_count": len(memory.messages)
                    })
                else:
                    # Update existing entry
                    existing[0]["timestamp"] = time.time()
                    existing[0]["message_count"] = len(memory.messages)
                    
            # Limit conversation history to the most recent 100 entries
            if len(self.user_profile["conversation_history"]) > 100:
                self.user_profile["conversation_history"].sort(key=lambda x: x["timestamp"], reverse=True)
                self.user_profile["conversation_history"] = self.user_profile["conversation_history"][:100]
            
            # Save changes
            self.save()
            
            return True
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            return False
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Get the current user profile"""
        return self.user_profile
    
    def set_user_attribute(self, attribute: str, value: Any) -> bool:
        """Set a specific user attribute"""
        try:
            # Handle nested attributes
            if "." in attribute:
                parts = attribute.split(".")
                target = self.user_profile
                
                # Navigate to the nested object
                for part in parts[:-1]:
                    if part not in target:
                        target[part] = {}
                    target = target[part]
                    
                # Set the value
                target[parts[-1]] = value
            else:
                # Set top-level attribute
                self.user_profile[attribute] = value
                
            # Save changes
            self.save()
            
            return True
        except Exception as e:
            logger.error(f"Error setting user attribute: {str(e)}")
            return False
    
    def get_user_attribute(self, attribute: str, default: Any = None) -> Any:
        """Get a specific user attribute"""
        try:
            # Handle nested attributes
            if "." in attribute:
                parts = attribute.split(".")
                target = self.user_profile
                
                # Navigate to the nested object
                for part in parts[:-1]:
                    if part not in target:
                        return default
                    target = target[part]
                    
                # Get the value
                return target.get(parts[-1], default)
            else:
                # Get top-level attribute
                return self.user_profile.get(attribute, default)
                
        except Exception as e:
            logger.error(f"Error getting user attribute: {str(e)}")
            return default
    
    def add_fact(self, fact: str) -> bool:
        """Add a fact about the user"""
        try:
            if fact and fact not in self.user_profile["facts"]:
                self.user_profile["facts"].append(fact)
                self.save()
            return True
        except Exception as e:
            logger.error(f"Error adding user fact: {str(e)}")
            return False
    
    def get_user_summary(self) -> str:
        """Get a text summary of the user profile"""
        try:
            summary_parts = []
            
            if self.user_profile["name"]:
                summary_parts.append(f"Name: {self.user_profile['name']}")
                
            if self.user_profile["locations"]:
                summary_parts.append(f"Locations: {', '.join(self.user_profile['locations'])}")
                
            if self.user_profile["interests"]:
                summary_parts.append(f"Interests: {', '.join(self.user_profile['interests'])}")
                
            if self.user_profile["preferences"]:
                likes = [item for item, pref in self.user_profile["preferences"].items() if pref == "like"]
                dislikes = [item for item, pref in self.user_profile["preferences"].items() if pref == "dislike"]
                
                if likes:
                    summary_parts.append(f"Likes: {', '.join(likes)}")
                if dislikes:
                    summary_parts.append(f"Dislikes: {', '.join(dislikes)}")
                    
            # Add other facts
            other_facts = [fact for fact in self.user_profile["facts"] 
                         if not any(keyword in fact.lower() for keyword in 
                                  ["name", "location", "interest", "like", "dislike"])]
            
            if other_facts:
                summary_parts.append("Other facts:")
                for fact in other_facts[:5]:  # Limit to 5 facts
                    summary_parts.append(f"- {fact}")
                if len(other_facts) > 5:
                    summary_parts.append(f"- Plus {len(other_facts) - 5} more facts")
                    
            # Add conversation history summary
            if self.user_profile["conversation_history"]:
                count = len(self.user_profile["conversation_history"])
                last_time = max([c["timestamp"] for c in self.user_profile["conversation_history"]])
                last_time_str = datetime.datetime.fromtimestamp(last_time).strftime("%Y-%m-%d %H:%M")
                summary_parts.append(f"Conversation history: {count} chats (last: {last_time_str})")
                
            return "\n".join(summary_parts)
        except Exception as e:
            logger.error(f"Error generating user summary: {str(e)}")
            return "Error generating user summary"

# Global instance for user memory
_user_memory_manager = None

def get_user_memory_manager():
    """Get the global user memory manager instance"""
    global _user_memory_manager
    if _user_memory_manager is None:
        _user_memory_manager = UserMemoryManager()
    return _user_memory_manager