import os
import json
import traceback
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
# Update the import to use local LLM
from lyra.huggingface_integration import get_huggingface_response as get_response
from lyra.combined_memory_manager import CombinedMemoryManager
from lyra.ocean import PersonalityEngine
from lyra.memory.sql_memory_manager import log_conversation
from datetime import datetime
from textblob import TextBlob
import re

def detect_tags(text: str) -> List[str]:
    """
    Enhanced tag detection to categorize conversation content beyond just 'important'.
    This allows Lyra to better organize memories and retrieve relevant context.
    """
    tags = []
    
    # Content importance tags
    if re.search(r'\b(important|remember|don\'t forget|note this|save this)\b', text.lower()):
        tags.append("important")
    if re.search(r'\b(urgent|emergency|immediate|asap|right now)\b', text.lower()):
        tags.append("urgent")
        
    # Conversation type tags
    if re.search(r'\b(help|assist|how to|how do|can you show|explain)\b', text.lower()):
        tags.append("help_request")
    if re.search(r'\b(code|program|script|function|class|bug|error|debug)\b', text.lower()):
        tags.append("technical")
    if re.search(r'\b(philosophy|meaning|life|existence|consciousness)\b', text.lower()):
        tags.append("philosophical")
        
    # Emotional content tags
    if re.search(r'\b(happy|excited|glad|wonderful|amazing)\b', text.lower()):
        tags.append("positive_emotion")
    if re.search(r'\b(sad|upset|frustrated|angry|annoyed)\b', text.lower()):
        tags.append("negative_emotion")
        
    # NSFW/Personal content tags
    if re.search(r'\b(sex|flirt|naughty|kinky|dirty|sexy|hot)\b', text.lower()):
        tags.append("nsfw")
    if re.search(r'\b(personal|private|secret|confidential)\b', text.lower()):
        tags.append("personal")
        
    # Knowledge domain tags
    if re.search(r'\b(chemistry|lab|polymer|hplc|formulation)\b', text.lower()):
        tags.append("chemistry")
    if re.search(r'\b(python|javascript|code|programming|algorithm|database)\b', text.lower()):
        tags.append("programming")
    if re.search(r'\b(crypto|bitcoin|xrp|market|stock|finance|money)\b', text.lower()):
        tags.append("finance")
    if re.search(r'\b(game|rpg|d&d|kingdom death|league|pathfinder)\b', text.lower()):
        tags.append("gaming")
    if re.search(r'\b(metal|jewelry|craft|wood|3d print|blacksmith)\b', text.lower()):
        tags.append("crafting")
        
    # Smart home and device tags
    if re.search(r'\b(light|thermostat|speaker|tv|smart home|device)\b', text.lower()):
        tags.append("smart_home")
        
    return tags

class ActionLogConversation(Action):
    def name(self) -> Text:
        return "action_log_conversation"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            user_message = tracker.latest_message.get("text", "")
            bot_response = next(
                (event["text"] for event in reversed(tracker.events) if event.get("event") == "bot"), 
                "No response logged"
            )
            timestamp = datetime.now().isoformat()

            # Enhanced tagging using our new function
            user_tags = detect_tags(user_message)
            bot_tags = detect_tags(bot_response)
            tags = list(set(user_tags + bot_tags))  # Combine and deduplicate

            sentiment = TextBlob(user_message).sentiment
            log_entry = {
                "user": user_message,
                "bot": bot_response,
                "timestamp": timestamp,
                "tags": tags,
                "sentiment": {
                    "polarity": sentiment.polarity,
                    "subjectivity": sentiment.subjectivity,
                }
            }

            json_file_path = os.path.join(os.getcwd(), "conversation_history.json")
            if os.path.exists(json_file_path):
                with open(json_file_path, "r+", encoding="utf-8") as f:
                    data = json.load(f)
                    data.append(log_entry)
                    f.seek(0)
                    json.dump(data, f, indent=4)
            else:
                with open(json_file_path, "w", encoding="utf-8") as f:
                    json.dump([log_entry], f, indent=4)

            log_file_path = os.path.join(os.getcwd(), "conversation_log.txt")
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"{timestamp}\nUser: {user_message}\nBot: {bot_response}\n\n")

            log_conversation(user_message, bot_response, tags=tags)

            dispatcher.utter_message(text="Conversation logged successfully!")

        except Exception as e:
            print(f"❌ ERROR in ActionLogConversation: {e}")
            traceback.print_exc()
            dispatcher.utter_message(text="Failed to log conversation.")

        return []


class ActionOpenAIChat(Action):
    def name(self) -> Text:
        return "action_openai_chat"

    def __init__(self) -> None:
        super().__init__()
        self.memory_manager = CombinedMemoryManager()
        self.personality_engine = PersonalityEngine()

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_message = tracker.latest_message.get("text", "")

        # Memory retrieval is working correctly
        memory_data = self.memory_manager.get_context(user_message, k=3)
        context_entries = memory_data["context"]
        context_summary = memory_data["summary"]

        context_str = "\n".join(
            [f"User: {entry.get('user', '')}\nBot: {entry.get('bot', '')}" for entry in context_entries]
        )
        sentiment = TextBlob(user_message).sentiment
        mood = "positive" if sentiment.polarity > 0 else "neutral" if sentiment.polarity == 0 else "negative"

        personality_context = f"{self.personality_engine.get_personality_context()}\nCurrent Mood: {mood}"
        
        # Get tags from user message to adjust response
        user_tags = detect_tags(user_message)
        tag_str = ", ".join(user_tags) if user_tags else "none"
        
        # Include tags in prompt to help guide the AI's response
        enriched_prompt = f"{personality_context}\n{context_summary}\nContext:\n{context_str}\n\nDetected conversation tags: {tag_str}\n\nUser: {user_message}\nBot:"

        # Use local LLM instead of OpenAI
        response = get_response(enriched_prompt, context_type="default")

        dispatcher.utter_message(text=response)

        # Enhanced tagging for both user message and bot response
        user_tags = detect_tags(user_message)
        bot_tags = detect_tags(response)
        tags = list(set(user_tags + bot_tags))  # Combine and deduplicate

        # Memory updating works properly
        self.memory_manager.add_memory(user_message, response, tags)

        # SQL logging works as backup
        try:
            log_conversation(user_message, response, tags=tags)
        except Exception as e:
            print("SQL logging error:", e)

        return []
