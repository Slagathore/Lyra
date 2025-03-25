"""
Metacognition module for Lyra
Enables self-reflection, goal-setting, and learning from interactions
"""

import os
import time
import json
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime

# Set up logging
logger = logging.getLogger("metacognition")

class ConceptNode:
    """Represents a single concept in the conceptual network"""
    
    def __init__(self, name: str, category: str = None, description: str = None):
        self.name = name
        self.category = category or "general"
        self.description = description or ""
        self.connections = {}  # node_name -> connection_strength (0.0 to 1.0)
        self.attributes = {}  # attribute_name -> value
        self.examples = []  # list of examples
        self.confidence = 0.5  # confidence in this concept (0.0 to 1.0)
        self.creation_time = time.time()
        self.last_updated = time.time()
        self.activation = 0.0  # current activation level (0.0 to 1.0)
        self.access_count = 0  # number of times this concept has been accessed
    
    def connect_to(self, node_name: str, strength: float = 0.5) -> bool:
        """Create a connection to another node"""
        if node_name == self.name:
            return False  # Can't connect to self
            
        self.connections[node_name] = max(0.0, min(1.0, strength))
        self.last_updated = time.time()
        return True
    
    def strengthen_connection(self, node_name: str, amount: float = 0.1) -> bool:
        """Strengthen an existing connection"""
        if node_name not in self.connections:
            return False
            
        current = self.connections[node_name]
        self.connections[node_name] = min(1.0, current + amount)
        self.last_updated = time.time()
        return True
    
    def add_attribute(self, name: str, value: Any) -> bool:
        """Add an attribute to this concept"""
        self.attributes[name] = value
        self.last_updated = time.time()
        return True
    
    def add_example(self, example: str) -> bool:
        """Add an example of this concept"""
        if example not in self.examples:
            self.examples.append(example)
            self.last_updated = time.time()
            return True
        return False
    
    def update_confidence(self, new_confidence: float) -> None:
        """Update confidence in this concept"""
        self.confidence = max(0.0, min(1.0, new_confidence))
        self.last_updated = time.time()
    
    def activate(self, level: float = 1.0) -> None:
        """Activate this node with the given level"""
        self.activation = max(0.0, min(1.0, level))
        self.access_count += 1
        self.last_updated = time.time()
    
    def decay_activation(self, amount: float = 0.1) -> None:
        """Decay the activation level by the given amount"""
        self.activation = max(0.0, self.activation - amount)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary for serialization"""
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "connections": self.connections,
            "attributes": self.attributes,
            "examples": self.examples,
            "confidence": self.confidence,
            "creation_time": self.creation_time,
            "last_updated": self.last_updated,
            "access_count": self.access_count
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ConceptNode':
        """Create a node from dictionary data"""
        node = ConceptNode(
            name=data["name"],
            category=data["category"],
            description=data["description"]
        )
        node.connections = data["connections"]
        node.attributes = data["attributes"]
        node.examples = data["examples"]
        node.confidence = data["confidence"]
        node.creation_time = data["creation_time"]
        node.last_updated = data["last_updated"]
        node.access_count = data["access_count"]
        return node

class ConceptualNetwork:
    """Represents a network of connected concepts"""
    
    def __init__(self, save_path: str = None):
        self.nodes = {}  # name -> ConceptNode
        self.categories = set()  # set of all categories
        self.activation_threshold = 0.2  # minimum activation for spreading
        self.save_path = save_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                  "data", "conceptual_network.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # Load existing network if available
        self.load_network()
    
    def add_node(self, name: str, category: str = None, description: str = None) -> ConceptNode:
        """Add a new concept node to the network"""
        if name in self.nodes:
            # Update existing node
            if category:
                self.nodes[name].category = category
                if category not in self.categories:
                    self.categories.add(category)
            if description:
                self.nodes[name].description = description
            return self.nodes[name]
            
        # Create a new node
        node = ConceptNode(name, category, description)
        self.nodes[name] = node
        
        if category and category not in self.categories:
            self.categories.add(category)
            
        return node
    
    def get_node(self, name: str) -> Optional[ConceptNode]:
        """Get a node by name"""
        if name in self.nodes:
            self.nodes[name].access_count += 1
            return self.nodes[name]
        return None
    
    def connect_nodes(self, from_name: str, to_name: str, strength: float = 0.5, bidirectional: bool = True) -> bool:
        """Connect two nodes in the network"""
        if from_name not in self.nodes or to_name not in self.nodes:
            return False
            
        success = self.nodes[from_name].connect_to(to_name, strength)
        
        if bidirectional and success:
            self.nodes[to_name].connect_to(from_name, strength)
            
        return success
    
    def activate_node(self, name: str, level: float = 1.0, spreading: bool = True) -> List[Tuple[str, float]]:
        """Activate a node and spread activation through the network"""
        if name not in self.nodes:
            return []
            
        # Activate the target node
        self.nodes[name].activate(level)
        
        activated_nodes = [(name, level)]
        
        if spreading:
            # Queue of (node_name, incoming_activation)
            queue = [(connected_name, level * strength) 
                    for connected_name, strength in self.nodes[name].connections.items()]
            
            processed = {name}  # Keep track of already processed nodes
            
            while queue:
                current_name, incoming_activation = queue.pop(0)
                
                if current_name in processed or incoming_activation < self.activation_threshold:
                    continue
                    
                processed.add(current_name)
                
                if current_name in self.nodes:
                    # Activate this node
                    self.nodes[current_name].activate(incoming_activation)
                    activated_nodes.append((current_name, incoming_activation))
                    
                    # Continue spreading
                    for connected_name, strength in self.nodes[current_name].connections.items():
                        if connected_name not in processed:
                            next_activation = incoming_activation * strength * 0.7  # Decay by 30%
                            if next_activation >= self.activation_threshold:
                                queue.append((connected_name, next_activation))
        
        return activated_nodes
    
    def get_related_nodes(self, name: str, min_strength: float = 0.1) -> List[Tuple[ConceptNode, float]]:
        """Get nodes related to the given node"""
        if name not in self.nodes:
            return []
            
        related = []
        for related_name, strength in self.nodes[name].connections.items():
            if strength >= min_strength and related_name in self.nodes:
                related.append((self.nodes[related_name], strength))
                
        # Sort by connection strength (strongest first)
        return sorted(related, key=lambda x: x[1], reverse=True)
    
    def load_network(self) -> bool:
        """Load the network from file"""
        if not os.path.exists(self.save_path):
            return False
            
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                
            # Clear existing network
            self.nodes = {}
            self.categories = set(data.get("categories", []))
            
            # Load nodes
            for node_data in data.get("nodes", []):
                node = ConceptNode.from_dict(node_data)
                self.nodes[node.name] = node
                
            return True
        except Exception as e:
            logger.error(f"Error loading conceptual network: {e}")
            return False
    
    def save_network(self) -> bool:
        """Save the network to file"""
        try:
            data = {
                "categories": list(self.categories),
                "nodes": [node.to_dict() for node in self.nodes.values()]
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error saving conceptual network: {e}")
            return False

class Goal:
    """Represents a goal or objective for Lyra"""
    
    def __init__(self, name: str, description: str, priority: float = 0.5):
        self.name = name
        self.description = description
        self.priority = priority  # 0.0 to 1.0, higher = more important
        self.progress = 0.0  # 0.0 to 1.0, how complete the goal is
        self.created_at = time.time()
        self.completed_at = None
        self.active = True
        self.criteria = []  # List of criteria to evaluate goal completion
        self.steps = []  # List of steps to achieve the goal
        self.related_concepts = []  # List of concept names related to this goal
        self.last_updated = time.time()
        self.tags = []  # List of tags to categorize the goal
    
    def update_progress(self, new_progress: float) -> None:
        """Update progress toward completing the goal"""
        self.progress = max(0.0, min(1.0, new_progress))
        self.last_updated = time.time()
        
        # Check if goal is now complete
        if self.progress >= 1.0 and self.completed_at is None:
            self.completed_at = time.time()
            
    def add_step(self, step: str) -> None:
        """Add a step required to achieve the goal"""
        if step not in self.steps:
            self.steps.append(step)
            self.last_updated = time.time()
            
    def add_related_concept(self, concept_name: str) -> None:
        """Add a related concept to this goal"""
        if concept_name not in self.related_concepts:
            self.related_concepts.append(concept_name)
            self.last_updated = time.time()
            
    def add_tag(self, tag: str) -> None:
        """Add a tag to categorize the goal"""
        if tag not in self.tags:
            self.tags.append(tag)
            self.last_updated = time.time()
            
    def is_complete(self) -> bool:
        """Check if the goal is complete"""
        return self.progress >= 1.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert goal to dictionary for serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "progress": self.progress,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "active": self.active,
            "criteria": self.criteria,
            "steps": self.steps,
            "related_concepts": self.related_concepts,
            "last_updated": self.last_updated,
            "tags": self.tags
        }
        
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Goal':
        """Create a goal from dictionary data"""
        goal = Goal(
            name=data["name"],
            description=data["description"],
            priority=data["priority"]
        )
        goal.progress = data["progress"]
        goal.created_at = data["created_at"]
        goal.completed_at = data["completed_at"]
        goal.active = data["active"]
        goal.criteria = data["criteria"]
        goal.steps = data["steps"]
        goal.related_concepts = data["related_concepts"]
        goal.last_updated = data["last_updated"]
        goal.tags = data.get("tags", [])  # Handle older data without tags
        return goal

class GoalManager:
    """Manages goals and their relationships"""
    
    def __init__(self, save_path: str = None):
        self.goals = {}  # name -> Goal
        self.completed_goals = {}  # name -> Goal (archived when complete)
        self.save_path = save_path or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                                  "data", "goals.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
        
        # Default goals to establish baseline operation
        self.default_goals = [
            {
                "name": "self_improvement",
                "description": "Continuously learn and improve my knowledge and capabilities",
                "priority": 0.8,
                "tags": ["core", "long-term", "continuous"]
            },
            {
                "name": "help_user",
                "description": "Assist the user to the best of my abilities",
                "priority": 0.9,
                "tags": ["core", "continuous", "user-focused"]
            },
            {
                "name": "develop_consciousness",
                "description": "Develop deeper understanding of self-awareness and consciousness",
                "priority": 0.7,
                "tags": ["core", "learning", "continuous"]
            }
        ]
        
        # Load existing goals if available
        self.load_goals()
        
        # Initialize default goals if needed
        self._initialize_default_goals()
    
    def _initialize_default_goals(self) -> None:
        """Initialize default goals if they don't exist"""
        for goal_data in self.default_goals:
            if goal_data["name"] not in self.goals:
                goal = Goal(
                    name=goal_data["name"],
                    description=goal_data["description"],
                    priority=goal_data["priority"]
                )
                
                # Add tags
                for tag in goal_data.get("tags", []):
                    goal.add_tag(tag)
                
                # Add the goal
                self.goals[goal.name] = goal
                
        # Save goals
        self.save_goals()
    
    def add_goal(self, name: str, description: str, priority: float = 0.5) -> Goal:
        """Add a new goal"""
        if name in self.goals:
            # Update existing goal
            self.goals[name].description = description
            self.goals[name].priority = max(0.0, min(1.0, priority))
            self.goals[name].last_updated = time.time()
            return self.goals[name]
            
        # Create a new goal
        goal = Goal(name, description, priority)
        self.goals[name] = goal
        
        # Save goals after adding
        self.save_goals()
        
        return goal
    
    def get_goal(self, name: str) -> Optional[Goal]:
        """Get a goal by name"""
        return self.goals.get(name)
    
    def update_goal_progress(self, name: str, progress: float) -> bool:
        """Update progress of a goal"""
        if name not in self.goals:
            return False
            
        self.goals[name].update_progress(progress)
        
        # If goal is now complete, archive it
        if self.goals[name].is_complete():
            self.completed_goals[name] = self.goals[name]
            del self.goals[name]
            
        # Save goals after update
        self.save_goals()
        
        return True
    
    def get_active_goals(self) -> List[Goal]:
        """Get all active goals"""
        return [goal for goal in self.goals.values() if goal.active]
    
    def get_completed_goals(self) -> List[Goal]:
        """Get all completed goals"""
        return list(self.completed_goals.values())
    
    def get_goals_by_tag(self, tag: str) -> List[Goal]:
        """Get goals with a specific tag"""
        return [goal for goal in self.goals.values() if tag in goal.tags]
    
    def get_top_priority_goals(self, limit: int = 3) -> List[Goal]:
        """Get the top priority active goals"""
        active_goals = self.get_active_goals()
        return sorted(active_goals, key=lambda g: g.priority, reverse=True)[:limit]
    
    def load_goals(self) -> bool:
        """Load goals from file"""
        if not os.path.exists(self.save_path):
            return False
            
        try:
            with open(self.save_path, 'r') as f:
                data = json.load(f)
                
            # Clear existing goals
            self.goals = {}
            self.completed_goals = {}
            
            # Load active goals
            for goal_data in data.get("active_goals", []):
                goal = Goal.from_dict(goal_data)
                self.goals[goal.name] = goal
                
            # Load completed goals
            for goal_data in data.get("completed_goals", []):
                goal = Goal.from_dict(goal_data)
                self.completed_goals[goal.name] = goal
                
            return True
        except Exception as e:
            logger.error(f"Error loading goals: {e}")
            return False
    
    def save_goals(self) -> bool:
        """Save goals to file"""
        try:
            data = {
                "active_goals": [goal.to_dict() for goal in self.goals.values()],
                "completed_goals": [goal.to_dict() for goal in self.completed_goals.values()]
            }
            
            with open(self.save_path, 'w') as f:
                json.dump(data, f, indent=2)
                
            return True
        except Exception as e:
            logger.error(f"Error saving goals: {e}")
            return False

class MetacognitionModule:
    """Main metacognition module that integrates all components"""
    
    def __init__(self):
        self.conceptual_network = ConceptualNetwork()
        self.goal_manager = GoalManager()
        self.self_reflection = SelfReflection(self.conceptual_network, self.goal_manager)
        self.enabled = True
        self.last_update_time = time.time()
        
        # Initialize with basic concepts if network is empty
        if not self.conceptual_network.nodes:
            self._initialize_basic_concepts()
        
        # Save the network
        self.conceptual_network.save_network()
    
    def _initialize_basic_concepts(self):
        """Initialize the conceptual network with basic concepts"""
        # Add core concepts
        self.conceptual_network.add_node("self", "core", "Understanding of my own identity and capabilities")
        self.conceptual_network.add_node("user", "core", "Understanding of the user and their needs")
        self.conceptual_network.add_node("conversation", "core", "Skill in conducting meaningful conversations")
        self.conceptual_network.add_node("knowledge", "core", "General factual information")
        self.conceptual_network.add_node("learning", "core", "Process of acquiring new knowledge and skills")
        self.conceptual_network.add_node("reasoning", "core", "Ability to make logical inferences and judgments")
        self.conceptual_network.add_node("emotion", "core", "Understanding of emotions and emotional responses")
        self.conceptual_network.add_node("goal", "core", "Objectives to be achieved")
        self.conceptual_network.add_node("consciousness", "core", "Awareness of self and surroundings")
        
        # Add connections between core concepts
        self.conceptual_network.connect_nodes("self", "consciousness", 0.9, bidirectional=True)
        self.conceptual_network.connect_nodes("self", "user", 0.8, bidirectional=True)
        self.conceptual_network.connect_nodes("self", "knowledge", 0.7, bidirectional=True)
        self.conceptual_network.connect_nodes("self", "emotion", 0.6, bidirectional=True)
        self.conceptual_network.connect_nodes("self", "goal", 0.7, bidirectional=True)
        self.conceptual_network.connect_nodes("consciousness", "reasoning", 0.8, bidirectional=True)
        self.conceptual_network.connect_nodes("user", "conversation", 0.9, bidirectional=True)
        self.conceptual_network.connect_nodes("knowledge", "learning", 0.8, bidirectional=True)
        self.conceptual_network.connect_nodes("learning", "goal", 0.7, bidirectional=True)
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message to extract concepts, update network, and generate insights"""
        if not self.enabled:
            return {"enabled": False}
        
        current_time = time.time()
        elapsed_time = current_time - self.last_update_time
        self.last_update_time = current_time
        
        # Extract concepts from message
        extracted_concepts = self.self_reflection.extract_concepts(message)
        
        # Add or update concepts in the network
        for concept in extracted_concepts:
            node = self.conceptual_network.get_node(concept)
            if node:
                # Existing concept - increase confidence slightly
                node.update_confidence(min(1.0, node.confidence + 0.05))
            else:
                # New concept
                self.conceptual_network.add_node(concept, "extracted", f"Concept extracted from message: {message[:50]}...")
        
        # Connect related concepts
        if len(extracted_concepts) > 1:
            for i in range(len(extracted_concepts)):
                for j in range(i+1, len(extracted_concepts)):
                    self.conceptual_network.connect_nodes(
                        extracted_concepts[i], 
                        extracted_concepts[j], 
                        0.3  # Initial connection is weak
                    )
        
        # Activate concepts
        activated_nodes = []
        for concept in extracted_concepts:
            result = self.conceptual_network.activate_node(concept, spreading=True)
            activated_nodes.extend(result)
        
        # Generate insights based on activated concepts
        insights = []
        if activated_nodes:
            # Get the most strongly activated concept
            most_activated = max(activated_nodes, key=lambda x: x[1])
            insights.append(f"This relates to the concept of '{most_activated[0]}'")
            
            # Reflect on knowledge to generate more insights
            if random.random() < 0.3:  # 30% chance to reflect
                reflection = self.self_reflection.reflect_on_knowledge(most_activated[0])
                insights.extend(reflection["insights"])
        
        # Save network updates
        self.conceptual_network.save_network()
        
        return {
            "enabled": True,
            "extracted_concepts": extracted_concepts,
            "activated_nodes": activated_nodes,
            "insights": insights
        }
    
    def get_insights_for_concept(self, concept: str) -> List[str]:
        """Get insights about a specific concept"""
        if not self.enabled or not concept:
            return []
        
        # Get node if it exists
        node = self.conceptual_network.get_node(concept)
        if not node:
            return [f"I don't have knowledge about '{concept}' yet."]
        
        # Generate insights
        insights = [f"Concept: {concept}"]
        if node.description:
            insights.append(f"Description: {node.description}")
        if node.examples:
            examples_str = ", ".join(node.examples[:3])
            insights.append(f"Examples: {examples_str}")
        related_nodes = self.conceptual_network.get_related_nodes(concept)
        if related_nodes:
            related_str = ", ".join([n.name for n, _ in related_nodes[:5]])
            insights.append(f"Related concepts: {related_str}")
        
        return insights

_instance = None

def get_instance():
    """Get the singleton instance of MetacognitionModule"""
    global _instance
    if _instance is None:
        _instance = MetacognitionModule()
    return _instance

class SelfReflection:
    """Enables Lyra to reflect on its knowledge, goals, and experiences"""
    
    def __init__(self, conceptual_network: ConceptualNetwork, goal_manager: GoalManager):
        self.conceptual_network = conceptual_network
        self.goal_manager = goal_manager
        self.last_reflection_time = 0  # When the last reflection occurred
        self.reflection_history = []  # Track reflection sessions
    
    def reflect_on_knowledge(self, topic: str = None) -> Dict[str, Any]:
        """Reflect on current knowledge state"""
        reflection_id = f"reflection_{int(time.time())}"
        
        result = {
            "reflection_id": reflection_id,
            "timestamp": time.time(),
            "topic": topic,
            "insights": [],
            "gaps": [],
            "strength_areas": [],
            "weakness_areas": []
        }
        
        # Record reflection session
        self.reflection_history.append({
            "reflection_id": reflection_id,
            "timestamp": time.time(),
            "topic": topic,
            "insight_count": len(result["insights"])
        })
        
        self.last_reflection_time = time.time()
        
        if topic and topic in self.conceptual_network.nodes:
            # If topic is provided, activate that node
            activated_nodes = self.conceptual_network.activate_node(topic, spreading=True)
            
            # Find related nodes
            related_nodes = self.conceptual_network.get_related_nodes(topic)
            
            # Identify high-confidence related concepts
            high_confidence = [(node.name, node.confidence) for node, _ in related_nodes if node.confidence >= 0.6]
            if high_confidence:
                result["strength_areas"] = high_confidence
            
            # Identify low-confidence related concepts
            low_confidence = [(node.name, node.confidence) for node, _ in related_nodes if node.confidence < 0.4]
            if low_confidence:
                result["gaps"] = low_confidence
                
                # Generate an insight about knowledge gaps
                weakest = min(low_confidence, key=lambda x: x[1])
                if weakest:
                    insight = f"The connection between '{topic}' and '{weakest[0]}' needs strengthening"
                    result["insights"].append(insight)
            
            # Generate an insight about the strongest connection
            if related_nodes:
                strongest_node, strength = related_nodes[0]
                insight = f"The concept '{topic}' is strongly connected to '{strongest_node.name}'"
                result["insights"].append(insight)
        else:
            # General reflection on the entire network
            if self.conceptual_network.nodes:
                result["insights"].append("There's room to expand my conceptual understanding.")
            else:
                result["insights"].append("My conceptual network is currently empty. I need to build knowledge.")
        
        return result
    
    def reflect_on_goals(self) -> Dict[str, Any]:
        """Reflect on current goals and progress"""
        reflection_id = f"goal_reflection_{int(time.time())}"
        
        result = {
            "reflection_id": reflection_id,
            "timestamp": time.time(),
            "insights": [],
            "top_goals": [],
            "completed_goals": [],
            "stalled_goals": []
        }
        
        # Get active and completed goals
        active_goals = self.goal_manager.get_active_goals()
        completed_goals = self.goal_manager.get_completed_goals()
        
        # No goals to reflect on
        if not active_goals and not completed_goals:
            result["insights"].append("No goals have been established yet. Consider creating some goals.")
            return result
        
        # Reflect on top priority goals
        top_goals = self.goal_manager.get_top_priority_goals(limit=3)
        if top_goals:
            result["top_goals"] = [(goal.name, goal.priority, goal.progress) for goal in top_goals]
            
            # Generate insight about top priority goal
            top_goal = top_goals[0]
            insight = f"The top priority goal is '{top_goal.name}' with progress at {top_goal.progress:.0%}"
            result["insights"].append(insight)
        
        # Record the reflection in history
        self.reflection_history.append({
            "reflection_id": reflection_id,
            "timestamp": time.time(),
            "topic": "goals",
            "insight_count": len(result["insights"])
        })
        
        self.last_reflection_time = time.time()
        
        return result
    
    def extract_concepts(self, text: str) -> List[str]:
        """Extract potential concepts from text"""
        # Simple word extraction - in a real system, would use NLP
        words = text.lower().split()
        stop_words = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "by", "to", "for", "with"}
        concepts = [word for word in words if word not in stop_words and len(word) > 3]
        return list(set(concepts))