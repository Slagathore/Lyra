import json
import os

class MemoryManager:
    def __init__(self, file_path="conversation_history.json"):
        """
        Initializes the memory manager.
        
        Parameters:
            file_path (str): Path to the JSON file used for persisting conversation history.
        """
        self.file_path = file_path
        self.memory = []
        self.load_memory()

    def load_memory(self):
        """
        Loads conversation history from the file if it exists.
        """
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.memory = json.load(f)
            except Exception as e:
                print("Error loading memory:", e)
                self.memory = []
        else:
            self.memory = []

    def save_memory(self):
        """
        Saves the current conversation history to the file.
        """
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print("Error saving memory:", e)

    def add_memory(self, entry):
        """
        Adds a new conversation entry to memory and persists it.
        
        Parameters:
            entry (dict): A dictionary representing a conversation turn (e.g., {"user": "...", "bot": "..."}).
        """
        self.memory.append(entry)
        self.save_memory()

    def get_memory(self):
        """
        Retrieves the entire conversation history.
        
        Returns:
            list: A list of conversation entries.
        """
        return self.memory

    def clear_memory(self):
        """
        Clears all conversation history and updates the file.
        """
        self.memory = []
        self.save_memory()


# Example usage and testing:
if __name__ == "__main__":
    mm = MemoryManager()
    
    # Add sample conversation entries
    mm.add_memory({"user": "Hello", "bot": "Hi there!"})
    mm.add_memory({"user": "How are you?", "bot": "I'm doing well, thanks!"})
    
    # Retrieve and print conversation history
    history = mm.get_memory()
    print("Current Conversation History:")
    for entry in history:
        print(f"User: {entry.get('user')}\nBot: {entry.get('bot')}\n")
