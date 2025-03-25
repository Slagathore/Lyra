"""
Test script for Lyra's cognitive architecture
"""
import os
import sys
import time
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cognition_test.log")
    ]
)
logger = logging.getLogger("cognition_test")

# Add the project directory to the Python path
sys.path.append(str(Path(__file__).parent))

def test_metacognition():
    """Test the metacognition module"""
    try:
        from modules.metacognition import get_instance as get_metacognition
        
        meta = get_metacognition()
        logger.info("Metacognition module loaded successfully")
        
        # Test concept creation
        concept = "consciousness"
        node = meta.conceptual_network.add_node(
            concept, 
            "philosophy", 
            "The state of being aware of and able to think about one's surroundings and existence"
        )
        
        # Test concept connections
        meta.conceptual_network.connect_nodes("consciousness", "self_awareness", 0.9, bidirectional=True)
        meta.conceptual_network.connect_nodes("consciousness", "cognition", 0.8, bidirectional=True)
        meta.conceptual_network.connect_nodes("consciousness", "perception", 0.7, bidirectional=True)
        
        # Test activation
        activated = meta.conceptual_network.activate_node(concept, spreading=True)
        logger.info(f"Activated nodes: {activated}")
        
        # Test goal creation
        goal = meta.goal_manager.add_goal(
            "understand_consciousness",
            "Develop a deeper understanding of consciousness and self-awareness",
            priority=0.8
        )
        goal.add_step("Study theories of consciousness")
        goal.add_step("Reflect on my own conscious experiences")
        goal.add_step("Integrate concepts of consciousness with other cognitive processes")
        
        # Test reflection
        reflection = meta.self_reflection.reflect_on_knowledge(concept)
        logger.info(f"Reflection on {concept}: {reflection}")
        
        goal_reflection = meta.self_reflection.reflect_on_goals()
        logger.info(f"Goal reflection: {goal_reflection}")
        
        # Test message processing
        message = "I'm curious about the nature of consciousness and how it relates to self-awareness"
        result = meta.process_message(message)
        logger.info(f"Message processing result: {result}")
        
        # Save the network
        meta.conceptual_network.save_network()
        meta.goal_manager.save_goals()
        
        return True
    except Exception as e:
        logger.error(f"Error testing metacognition: {e}")
        return False

def test_emotional_core():
    """Test the emotional core module"""
    try:
        from modules.emotional_core import get_instance as get_emotional_core
        
        emotional = get_emotional_core()
        logger.info("Emotional core module loaded successfully")
        
        # Test processing emotions from a message
        message = "I'm feeling really happy today because everything is going well!"
        result = emotional.process_user_message(message)
        logger.info(f"Emotional processing result: {result}")
        
        # Get dominant emotion
        dominant, intensity = emotional.get_dominant_emotion()
        logger.info(f"Dominant emotion: {dominant} ({intensity:.2f})")
        
        # Get mood description
        mood = emotional.get_mood_description()
        logger.info(f"Current mood: {mood}")
        
        # Test emotional response generation
        response = emotional.generate_emotional_response(message)
        logger.info(f"Emotional response: {response}")
        
        # Test emotional modulation
        base_response = "This is a neutral response without emotional coloring."
        modulated = emotional.modulate_response(base_response)
        logger.info(f"Modulated response: {modulated}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing emotional core: {e}")
        return False

def test_deep_memory():
    """Test the deep memory module"""
    try:
        from modules.deep_memory import get_instance as get_deep_memory
        
        memory = get_deep_memory()
        logger.info("Deep memory module loaded successfully")
        
        # Test storing an interaction
        user_message = "What's your favorite type of music?"
        my_response = "I appreciate many genres, but I particularly enjoy classical compositions for their complexity and emotional range."
        
        # Create a simulated emotional state
        emotional_state = {
            "dominant_emotion": "joy",
            "intensity": 0.7,
            "emotions": {
                "joy": 0.7,
                "interest": 0.8,
                "trust": 0.6
            }
        }
        
        # Store the interaction
        memory_id = memory.store_interaction(user_message, my_response, emotional_state)
        logger.info(f"Stored interaction with ID: {memory_id}")
        
        # Test storing a reflection
        reflection = "Music is a fascinating topic that connects to emotions, cultural expressions, and mathematical patterns. I notice that discussing music often elicits positive emotional responses from users."
        reflection_id = memory.store_reflection(reflection, related_memory_ids=[memory_id])
        logger.info(f"Stored reflection with ID: {reflection_id}")
        
        # Test recalling similar experiences
        similar = memory.recall_similar("What kind of music do you like?")
        logger.info(f"Recalled {len(similar)} similar memories")
        
        # Test recalling by emotion
        emotional_memories = memory.recall_by_emotion("joy")
        logger.info(f"Recalled {len(emotional_memories)} memories associated with joy")
        
        # Test daily reflection generation
        daily_reflection = memory.generate_daily_reflection()
        logger.info(f"Daily reflection: {daily_reflection}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing deep memory: {e}")
        return False

def test_integrated_awareness():
    """Test the integrated awareness module"""
    try:
        from modules.cognitive_integration import get_integrated_awareness
        
        integrated = get_integrated_awareness()
        logger.info("Integrated awareness module loaded successfully")
        
        # Test processing a user message through all systems
        message = "I've been thinking about how consciousness emerges from physical processes in the brain."
        results = integrated.process_user_message(message)
        logger.info(f"Integrated processing results: {results}")
        
        # Test generating a reflection based on the message
        should_reflect = results.get("should_reflect", False)
        if should_reflect:
            reflection = integrated.generate_reflection(message, "I believe consciousness emerges from complex networks of neurons, but there's still much we don't understand about it.")
            logger.info(f"Generated reflection: {reflection}")
        
        # Test integrated response generation
        base_response = "The relationship between physical brain processes and conscious experience is known as the 'hard problem of consciousness' in philosophy of mind."
        enhanced = integrated.generate_integrated_response(base_response)
        logger.info(f"Enhanced response: {enhanced}")
        
        # Test storing the interaction with response
        interaction_id = integrated.store_interaction_with_response(
            message, 
            base_response, 
            reflection=reflection if should_reflect else None, 
            processing_results=results
        )
        logger.info(f"Stored interaction with ID: {interaction_id}")
        
        # Check if daily reflection should be generated
        if integrated.should_generate_daily_reflection():
            daily = integrated.generate_daily_reflection()
            logger.info(f"Daily reflection: {daily}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing integrated awareness: {e}")
        return False

def test_model_integration():
    """Test the model integration module"""
    try:
        from modules.cognitive_model_integration import get_instance as get_model_integration
        
        # This test requires a model manager
        # For testing without a real model, we'll create a simple mock
        class MockModel:
            def __init__(self, name="test_model"):
                self.name = name
                
            def generate_text(self, prompt, max_tokens=100):
                return f"This is a mock response to: {prompt[:50]}..."
                
        class MockModelManager:
            def __init__(self):
                self.models = [MockModel()]
                
            def get_active_model(self):
                return self.models[0]
        
        # Create a mock model manager
        mock_manager = MockModelManager()
        
        # Initialize the model integration
        model_integration = get_model_integration(mock_manager)
        logger.info("Model integration module loaded with mock model manager")
        
        # Test concept description generation
        concept_description = model_integration.generate_concept_description("metacognition")
        logger.info(f"Generated concept description: {concept_description}")
        
        # Test reflection generation
        reflection = model_integration.generate_reflection(topic="learning")
        logger.info(f"Generated reflection: {reflection}")
        
        # Test response enhancement
        base_response = "This is a test response about learning."
        enhanced = model_integration.enhance_cognitive_response(
            base_response, 
            "Tell me about learning",
            {}
        )
        logger.info(f"Enhanced response: {enhanced}")
        
        return True
    except Exception as e:
        logger.error(f"Error testing model integration: {e}")
        return False

def main():
    """Run the cognition test suite"""
    parser = argparse.ArgumentParser(description="Test Lyra's cognitive architecture")
    parser.add_argument("--module", choices=["all", "metacognition", "emotional", "memory", "integrated", "model"], 
                        default="all", help="Which module to test")
    args = parser.parse_args()
    
    results = {}
    
    if args.module in ["all", "metacognition"]:
        logger.info("Testing metacognition module...")
        results["metacognition"] = test_metacognition()
    
    if args.module in ["all", "emotional"]:
        logger.info("Testing emotional core module...")
        results["emotional"] = test_emotional_core()
    
    if args.module in ["all", "memory"]:
        logger.info("Testing deep memory module...")
        results["memory"] = test_deep_memory()
    
    if args.module in ["all", "integrated"]:
        logger.info("Testing integrated awareness module...")
        results["integrated"] = test_integrated_awareness()
    
    if args.module in ["all", "model"]:
        logger.info("Testing model integration module...")
        results["model"] = test_model_integration()
    
    # Print results
    logger.info("Test results:")
    for module, success in results.items():
        logger.info(f"{module}: {'SUCCESS' if success else 'FAILURE'}")
    
    # Overall success if all tests passed
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
