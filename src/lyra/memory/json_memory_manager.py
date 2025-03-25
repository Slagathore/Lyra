import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

class JSONMemoryManager:
    def __init__(self, file_path="conversation_history.json"):
        """
        Initializes the JSON memory manager, aiming for human-like curiosity and detailed memory tracking.

        Parameters:
            file_path (str): Path to the JSON file used for persisting conversation history.
        """
        base_dir = os.path.join(os.getcwd(), "src", "lyra", "memory")
        self.file_path = os.path.join(base_dir, file_path)
        self.load_memory()

    def load_memory(self) -> None:
        """
        Loads conversation history from the JSON file.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
                    if not isinstance(self.memory, list):
                        self.memory = []
            except Exception as e:
                print(f"Error loading memory: {e}")
                self.memory = []
        else:
            self.memory = []
    
    def save_memory(self):
        """
        Saves the current memory state to disk.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving memory: {e}")
            
    def add_memory(self, entry: Dict[str, Any]) -> None:
        """
        Adds a new memory entry.
        
        Parameters:
            entry: Dictionary with memory data (user message, bot response, etc.)
        """
        # Ensure timestamp exists
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().isoformat()
            
        self.memory.append(entry)
        self.save_memory()
        
    def get_memory(self) -> List[Dict[str, Any]]:
        """
        Returns all memory entries.
        
        Returns:
            List of all memory entries
        """
        return self.memory
        
    def get_tagged_memory(self, tag: str) -> List[Dict[str, Any]]:
        """
        Returns memory entries with a specific tag.
        
        Parameters:
            tag: Tag to filter by
            
        Returns:
            List of memory entries with the specified tag
        """
        return [entry for entry in self.memory if tag in entry.get("tags", [])]
        
    def get_recent_memory(self, num_entries: int = 5) -> List[Dict[str, Any]]:
        """
        Returns the most recent memory entries.
        
        Parameters:
            num_entries: Number of recent entries to return
            
        Returns:
            List of recent memory entries
        """
        return sorted(
            self.memory, 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )[:num_entries]

if __name__ == "__main__":
    # Test the memory manager
    mm = JSONMemoryManager()
    mm.add_memory({
        "user": "Hello",
        "bot": "Hi there!",
        "tags": ["greeting"]
    })
    print(f"Memory contains {len(mm.get_memory())} entries")
    print(mm.get_recent_memory(1))
