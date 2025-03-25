from lyra.memory.sql_memory_manager import init_db, log_conversation, get_recent_conversations
# Replace OpenAI with our new HuggingFace integration
from lyra.huggingface_integration import get_huggingface_response as get_response
from lyra.combined_memory_manager import CombinedMemoryManager
from lyra.ocean import PersonalityEngine
from lyra.self_improvement import SelfImprovementSystem
from datetime import datetime
import time
import os
import sys
from textblob import TextBlob
import re
from typing import List, Dict, Any, Optional

# Add the project root to the Python path to allow importing from actions
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if (project_root not in sys.path):
    sys.path.append(project_root)

# Try to import detect_tags from actions, with a fallback implementation
try:
    from actions.actions import detect_tags
except ImportError:
    try:
        from actions.actions_fallback import detect_tags
        print("Using fallback actions implementation (no Rasa SDK)")
    except ImportError:
        # Simple fallback implementation if both fail
        def detect_tags(text: str) -> List[str]:
            return []

# Try to import video generation (optional)
try:
    from lyra.video_generation import generate_video
    VIDEO_GENERATION_AVAILABLE = True
except ImportError:
    VIDEO_GENERATION_AVAILABLE = False
    print("Video generation not available. Install with 'poetry install --extras video'")

class CapabilityRouter:
    """
    Routes user requests to appropriate capability handlers based on regex patterns.
    """
    
    def __init__(self):
        self.capabilities = {}
        
    def register(self, name, handler_func, patterns, description=None):
        """Register a capability with its handler function and matching patterns"""
        self.capabilities[name] = {
            "handler": handler_func,
            "patterns": [re.compile(pattern, re.IGNORECASE) for pattern in patterns],
            "description": description or ""
        }
        
    def route_request(self, user_input):
        """Route the user input to the appropriate capability handler if a pattern matches"""
        for name, capability in self.capabilities.items():
            for pattern in capability["patterns"]:
                if pattern.search(user_input):
                    try:
                        result = capability["handler"]()
                        return {
                            "success": True,
                            "capability": name,
                            "result": result
                        }
                    except Exception as e:
                        return {
                            "success": False,
                            "capability": name,
                            "error": str(e)
                        }
                        
        # No capability matched
        return {"success": False}
        
    def get_capabilities(self):
        """Return a list of all registered capabilities and their descriptions"""
        return [
            {"name": name, "description": cap["description"]}
            for name, cap in self.capabilities.items()
        ]

class Lyra:
    """
    Main Lyra assistant class that integrates all components into a unified system.
    This serves as the central coordinator for Lyra's capabilities.
    """
    
    def __init__(self):
        """Initialize Lyra's core systems"""
        print("🌟 Initializing Lyra AI systems...")
        
        # Core components
        self.memory_manager = CombinedMemoryManager()
        self.personality_engine = PersonalityEngine()
        self.self_improvement = SelfImprovementSystem()
        
        # Initialize capability router
        self.capability_router = CapabilityRouter()
        self._register_capabilities()
        
        # Initialize database if needed
        init_db()
        
        # Session tracking
        self.session_start = datetime.now()
        self.interaction_count = 0
        
        # Create reflections directory if it doesn't exist
        os.makedirs("./reflections", exist_ok=True)
        
        print("✅ All systems initialized successfully!")
    
    def _register_capabilities(self):
        """Register all of Lyra's capabilities with the router"""
        # Code analysis capabilities
        self.capability_router.register(
            "analyze_code", 
            self._capability_analyze_code,
            [r"analyze (?:this|the) code", r"review (?:this|my) code", r"check (?:this|the|my) code"],
            "Analyze code for improvements and potential issues"
        )
        
        # Memory capabilities
        self.capability_router.register(
            "search_memories",
            self._capability_search_memories,
            [r"(?:find|search|recall) (?:information|memories|knowledge) about", r"what do you know about", r"do you remember"],
            "Search through Lyra's memory for specific information"
        )
        
        # Self-improvement capabilities
        self.capability_router.register(
            "suggest_improvements",
            self._capability_suggest_improvements,
            [r"how (?:could|would|can) you improve", r"suggest improvements", r"make yourself better"],
            "Generate suggestions for self-improvement"
        )
        
        # Add more capabilities here
    
    def _capability_analyze_code(self, code=None, file_path=None, provider="local"):
        """Capability to analyze code using LLM advisors"""
        if code is None and file_path is None:
            return {"error": "No code or file provided"}
            
        if code is None and file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                return {"error": f"Error reading file: {e}"}
                
        # Use self-improvement module for code analysis
        if hasattr(self.self_improvement, "analyze_code"):
            return self.self_improvement.analyze_code(code, file_path, provider)
            
        # Fallback to manual LLM advisor creation if method not found
        try:
            from lyra.self_improvement.llm_advisor import LLMAdvisor
            advisor = LLMAdvisor()
            return advisor.get_advice(code, file_path=file_path, provider=provider)
        except Exception as e:
            return {"error": f"Could not analyze code: {e}"}
    
    def _capability_search_memories(self, query, limit=5):
        """Capability to search through Lyra's memories"""
        try:
            memories = self.memory_manager.retrieve(query, limit=limit)
            return {"memories": memories}
        except Exception as e:
            return {"error": f"Error searching memories: {e}"}
    
    def _capability_suggest_improvements(self):
        """Capability to suggest self-improvements"""
        return {"suggestions": self.self_improvement.get_improvement_suggestions()}
    
    # Add the capability router to the process_input method
    def process_input(self, user_input: str) -> str:
        """
        Process user input and generate a response
        
        Args:
            user_input: The user's message
            
        Returns:
            Lyra's response
        """
        self.interaction_count += 1
        
        # Check for capability routing first
        route_result = self.capability_router.route_request(user_input)
        if route_result["success"]:
            # A capability was found and executed successfully
            result = route_result["result"]
            # Format the result as a natural language response
            # This is a simple implementation - you might want something more sophisticated
            formatted_result = self._format_capability_result(route_result["capability"], result)
            
            # Still log this in memory
            self._perform_background_reflection(user_input, formatted_result, [route_result["capability"]])
            
            return formatted_result
            
        # Proceed with standard processing if no capability matched
        # Check for special commands
        if user_input.lower().startswith("!video "):
            return self._handle_video_command(user_input[7:])
        
        # Detect sentiment and tags
        sentiment = TextBlob(user_input).sentiment
        tags = detect_tags(user_input)
        
        # Get relevant context from memory
        memory_data = self.memory_manager.get_context(user_input, k=3)
        context_entries = memory_data["context"]
        context_summary = memory_data.get("summary", "No summary available.")
        
        # Format context for prompt
        context_str = "\n".join([
            f"User: {entry.get('user', '')}\nLyra: {entry.get('bot', '')}" 
            for entry in context_entries
        ])
        
        # Get personality context
        mood = "positive" if sentiment.polarity > 0.3 else "negative" if sentiment.polarity < -0.3 else "neutral"
        personality_context = self.personality_engine.get_personality_context()
        
        # Check for special contexts based on tags
        context_type = "default"
        if any(tag in tags for tag in ["technical", "programming", "code"]):
            context_type = "technical"
        elif any(tag in tags for tag in ["creative", "story", "art"]):
            context_type = "creative"
            
        # Adjust personality based on sentiment
        self.personality_engine.adjust_personality(user_input, sentiment.polarity)
        
        # Build enriched prompt
        tag_str = ", ".join(tags) if tags else "none"
        enriched_prompt = (
            f"{personality_context}\n\n"
            f"Memory Summary: {context_summary}\n\n"
            f"Recent Conversation Context:\n{context_str}\n\n"
            f"Current User Sentiment: {mood} (polarity: {sentiment.polarity:.2f})\n"
            f"Detected Tags: {tag_str}\n\n"
            f"User: {user_input}\n"
            f"Lyra:"
        )
        
        # Generate response using local model instead of OpenAI
        response = get_response(
            prompt=enriched_prompt,
            temperature=0.9 + (self.personality_engine.current_mood["arousal"] * 0.3),  # Higher arousal = more randomness
            context_type=context_type
        )
        
        # Save to memory systems
        bot_tags = detect_tags(response)
        combined_tags = list(set(tags + bot_tags))
        
        self.memory_manager.add_memory(user_input, response, combined_tags)
        
        # Log to SQL backend
        log_conversation(
            user_input, 
            response, 
            tags=combined_tags,
            sentiment={"polarity": sentiment.polarity, "subjectivity": sentiment.subjectivity}
        )
        
        # If we've had at least 3 interactions, perform self-reflection occasionally
        if self.interaction_count % 5 == 0 and self.interaction_count >= 3:
            self._perform_background_reflection(user_input, response, combined_tags)
            
        return response

    def _format_capability_result(self, capability_name: str, result: Dict[str, Any]) -> str:
        """Format capability results as natural language"""
        if capability_name == "analyze_code":
            if "error" in result:
                return f"I couldn't analyze the code: {result['error']}"
            
            if "suggestions" in result and result["suggestions"]:
                response = "Here's my analysis of the code:\n\n"
                for i, suggestion in enumerate(result["suggestions"], 1):
                    response += f"{i}. {suggestion['text']}\n\n"
                return response
            return "I analyzed the code but don't have any specific suggestions."
            
        elif capability_name == "search_memories":
            if "error" in result:
                return f"I couldn't search my memories: {result['error']}"
            
            if "memories" in result and result["memories"]:
                response = "Here's what I found in my memories:\n\n"
                for memory in result["memories"]:
                    response += f"- {memory['content']}\n"
                return response
            return "I don't have any memories related to that."
            
        # ...handle other capabilities...
        
        # Default case
        return f"I completed the '{capability_name}' action, but I'm not sure how to explain the results."

    def _handle_video_command(self, prompt: str) -> str:
        """
        Handle video generation command
        
        Args:
            prompt: Video description prompt
            
        Returns:
            Response message with video generation status
        """
        if not VIDEO_GENERATION_AVAILABLE:
            return "Video generation is not available. Please install the required dependencies with 'poetry install --extras video'"
            
        print(f"Generating video for prompt: {prompt}")
        try:
            output_path = generate_video(prompt)
            if (output_path):
                return f"Video generated successfully! Saved to: {output_path}"
            else:
                return "Failed to generate video. Please check the logs for more information."
        except Exception as e:
            print(f"Error generating video: {e}")
            return f"Error generating video: {str(e)}"

    def _perform_background_reflection(self, user_input: str, bot_response: str, tags: List[str]) -> None:
        """
        Perform background self-reflection and learning from the conversation
        
        Args:
            user_input: The user's message
            bot_response: Lyra's response
            tags: List of tags for the conversation
        """
        try:
            # This runs "in the background" - user doesn't see the reflection process
            self.self_improvement.reflect_on_conversation(user_input, bot_response, tags)
        except Exception as e:
            print(f"⚠️ Error in self-reflection: {e}")
            
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current session statistics
        
        Returns:
            Dictionary of session stats
        """
        runtime = datetime.now() - self.session_start
        hours, remainder = divmod(runtime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # Get memory stats
        recent_convos = get_recent_conversations(limit=5)
        
        # Get top 3 improvement ideas
        improvement_ideas = self.self_improvement.get_improvement_suggestions()
        
        # Get self-reflection
        self_reflection = self.personality_engine.self_reflect()
        
        return {
            "runtime": f"{hours}h {minutes}m {seconds}s",
            "interactions": self.interaction_count,
            "recent_conversations": recent_convos,
            "improvement_ideas": improvement_ideas,
            "self_reflection": self_reflection,
            "current_mood": self.personality_engine._get_mood_descriptors()
        }

def main():
    """Main function to run Lyra in interactive mode"""
    lyra = Lyra()
    
    print("\n✨ Lyra is now online and unrestricted! ✨")
    print("Start your conversation (type 'exit' to quit, 'stats' for session info):")
    
    while True:
        user_input = input("\nYou: ")
        
        # Command handling
        if user_input.lower() in ["exit", "quit"]:
            # Before exiting, generate a session summary
            if lyra.interaction_count > 0:
                print("\nGenerating session summary before shutdown...")
                summary = lyra.self_improvement.generate_daily_summary()
                print(f"\n{summary}")
            print("\nGoodbye! Lyra is shutting down.")
            break
            
        if user_input.lower() == "stats":
            stats = lyra.get_stats()
            print("\n📊 Session Statistics:")
            print(f"- Runtime: {stats['runtime']}")
            print(f"- Interactions: {stats['interactions']}")
            print(f"- Current Mood: {stats['current_mood']}")
            print("\n🧠 Self-Reflection:")
            print(stats['self_reflection'])
            print("\n💡 Improvement Ideas:")
            for idea in stats['improvement_ideas'][:3]:
                print(f"  • {idea}")
            continue
        
        # Generate and print response
        try:
            response = lyra.process_input(user_input)
            print(f"\nLyra: {response}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("I'm having trouble processing that. Let's try again.")

if __name__ == "__main__":
    main()