import os
import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import numpy as np
# Update the import to use local LLM
from lyra.huggingface_integration import get_huggingface_response as get_response

class SelfImprovementSystem:
    """
    A system for Lyra to reflect on interactions, learn from them, and improve over time.
    
    This implements the recursive self-improvement loop described in the architecture.
    """
    
    def __init__(self, reflection_path: str = "./reflections"):
        self.reflection_path = Path(reflection_path)
        self.reflection_path.mkdir(exist_ok=True)
        self.daily_reflections = []
        self.strengths = []
        self.weaknesses = []
        self.improvement_ideas = []
        self._load_reflections()
        
    def _load_reflections(self):
        """Load past reflections if they exist"""
        reflection_file = self.reflection_path / "reflections.json"
        if reflection_file.exists():
            try:
                with open(reflection_file, "r") as f:
                    data = json.load(f)
                    self.daily_reflections = data.get("reflections", [])
                    self.strengths = data.get("strengths", [])
                    self.weaknesses = data.get("weaknesses", [])
                    self.improvement_ideas = data.get("improvement_ideas", [])
            except Exception as e:
                print(f"Error loading reflections: {e}")
                
    def _save_reflections(self):
        """Save current reflections to disk"""
        reflection_file = self.reflection_path / "reflections.json"
        try:
            with open(reflection_file, "w") as f:
                json.dump({
                    "reflections": self.daily_reflections,
                    "strengths": self.strengths,
                    "weaknesses": self.weaknesses,
                    "improvement_ideas": self.improvement_ideas
                }, f, indent=2)
        except Exception as e:
            print(f"Error saving reflections: {e}")
            
    def reflect_on_conversation(self, user_message: str, bot_response: str, tags: List[str]) -> Dict[str, Any]:
        """
        Reflect on a single conversation turn to extract learnings
        
        Args:
            user_message: The user's message
            bot_response: Lyra's response
            tags: Any tags associated with the conversation
            
        Returns:
            A dictionary containing reflections and learnings
        """
        # Create a prompt for self-reflection
        reflection_prompt = f"""
        I'm Lyra, an AI assistant engaged in continuous self-improvement. 
        I want to reflect on this conversation to improve myself.
        
        User message: "{user_message}"
        My response: "{bot_response}"
        Tags: {', '.join(tags)}
        
        Please help me reflect on this interaction by answering:
        1. What did I do well in this response?
        2. What could I have improved?
        3. What did I learn about the user from this exchange?
        4. How can I use this to improve future responses?
        """
        
        # Get AI to reflect on the conversation - using local LLM
        reflection_response = get_response(
            reflection_prompt, 
            max_tokens=300,
            temperature=0.7,
            context_type="technical"
        )
        
        # Process the reflection response
        reflection_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "user_message": user_message,
            "bot_response": bot_response,
            "tags": tags,
            "reflection": reflection_response
        }
        
        # Add to daily reflections
        self.daily_reflections.append(reflection_data)
        if len(self.daily_reflections) > 100:  # Keep only the last 100 reflections
            self.daily_reflections = self.daily_reflections[-100:]
            
        self._save_reflections()
        
        return reflection_data
        
    def generate_daily_summary(self) -> str:
        """
        Generate a daily summary of interactions and learnings.
        This would typically run at the end of the day.
        
        Returns:
            A summarized report of learnings
        """
        # Only process if we have reflections
        if not self.daily_reflections:
            return "No interactions to summarize yet."
            
        # Get recent reflections (last 24 hours)
        now = datetime.datetime.now()
        recent_reflections = []
        for reflection in self.daily_reflections:
            try:
                timestamp = datetime.datetime.fromisoformat(reflection["timestamp"])
                if (now - timestamp).total_seconds() < 86400:  # Within 24 hours
                    recent_reflections.append(reflection)
            except:
                continue
                
        if not recent_reflections:
            return "No recent interactions to summarize."
            
        # Create a summary prompt
        tags_list = []
        for r in recent_reflections:
            tags_list.extend(r.get("tags", []))
            
        unique_tags = list(set(tags_list))
        
        summary_prompt = f"""
        I'm Lyra, and I want to generate a daily summary of my interactions.
        
        I had {len(recent_reflections)} conversations today with these tags: {', '.join(unique_tags)}
        
        Please help me summarize:
        1. What patterns did I notice in user requests?
        2. What were my main strengths today?
        3. What were my main areas for improvement?
        4. What specific actions can I take to improve tomorrow?
        5. What new skills or knowledge would be most valuable to acquire?
        
        For context, here are some recent reflections:
        {recent_reflections[-3:]}
        """
        
        # Get AI to summarize - using local LLM
        summary_response = get_response(
            summary_prompt,
            max_tokens=500,
            temperature=0.7,
            context_type="technical"
        )
        
        # Extract action items for improvement
        improvement_prompt = f"""
        Based on this summary of my day:
        
        {summary_response}
        
        Please extract 3-5 specific, actionable improvements I can make. Format as a list of items.
        """
        
        improvements = get_response(
            improvement_prompt,
            max_tokens=300,
            temperature=0.7,
            context_type="technical"
        )
        
        # Save improvements
        self.improvement_ideas.extend([idea.strip() for idea in improvements.split('\n') if idea.strip()])
        self._save_reflections()
        
        return f"Daily Summary:\n\n{summary_response}\n\nImprovement Ideas:\n\n{improvements}"
        
    def get_improvement_suggestions(self, context: str = "") -> List[str]:
        """
        Get personalized improvement suggestions based on context.
        
        Args:
            context: Optional context string to guide suggestions
            
        Returns:
            List of improvement suggestions
        """
        if not self.improvement_ideas:
            return ["No improvement ideas yet. Interact more to generate insights."]
            
        # If we have context, filter the ideas to find relevant ones
        if context:
            context_lower = context.lower()
            relevant_ideas = []
            
            for idea in self.improvement_ideas:
                # Check if any word in the idea appears in the context
                words = idea.lower().split()
                if any(word in context_lower for word in words if len(word) > 3):
                    relevant_ideas.append(idea)
                    
            # Return relevant ideas or fall back to recent ones
            return relevant_ideas if relevant_ideas else self.improvement_ideas[-3:]
        
        # Without context, return the 3 most recent ideas
        return self.improvement_ideas[-3:]
