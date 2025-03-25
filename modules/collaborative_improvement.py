import os
import json
import time
import random
import re
import logging
from pathlib import Path
import numpy as np
from typing import List, Dict, Tuple, Optional, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("collaborative_improvement")

class TextProcessor:
    """Handles text cleaning and key concept extraction."""
    
    def __init__(self):
        self.stop_words = set([
            "a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "by", "in",
            "of", "is", "are", "am", "was", "were", "be", "been", "being"
        ])
    
    def clean(self, text):
        """Clean and normalize text."""
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_key_concepts(self, text):
        """Extract key concepts from the text."""
        # Split into words
        words = text.split()
        
        # Remove stop words
        filtered_words = [word for word in words if word not in self.stop_words]
        
        # Get word frequencies
        word_freq = {}
        for word in filtered_words:
            if word in word_freq:
                word_freq[word] += 1
            else:
                word_freq[word] = 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top concepts (words with frequency > 1)
        key_concepts = [word for word, freq in sorted_words if freq > 1]
        
        # If not enough concepts, just take the top ones
        if len(key_concepts) < 3:
            key_concepts = [word for word, _ in sorted_words[:min(5, len(sorted_words))]]
        
        return {
            "original_text": text,
            "key_concepts": key_concepts,
            "word_frequencies": dict(sorted_words)
        }


class DeepLearner:
    """Performs deep learning analysis on processed text data."""
    
    def __init__(self):
        self.embedding_dimension = 128
        self.model_initialized = False
        self.theme_clusters = {}
    
    def _initialize_model(self):
        """Initialize a simple deep learning model for text analysis."""
        logger.info("Initializing deep learning model")
        self.model_initialized = True
    
    def _create_embeddings(self, text_data):
        """Create embeddings for text data."""
        if not self.model_initialized:
            self._initialize_model()
            
        # Simplified embedding creation for demonstration
        embedding = np.random.randn(self.embedding_dimension)
        return embedding / np.linalg.norm(embedding)  # Normalize
    
    def _identify_themes(self, embeddings, conversation_history):
        """Identify themes from embeddings and conversation history."""
        # Extract all text from conversation history
        all_text = " ".join([msg["content"] for msg in conversation_history])
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Filter out common words
        common_words = set(["the", "and", "a", "to", "of", "is", "in", "that", "it", "with"])
        filtered_words = [w for w in words if w not in common_words and len(w) > 3]
        
        # Count word frequencies
        word_counts = {}
        for word in filtered_words:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
                
        # Sort by frequency
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Extract top themes
        themes = [word for word, count in sorted_words[:5]]
        return themes
    
    def analyze(self, processed_data, conversation_history):
        """Analyze processed data to extract insights."""
        # Create embeddings for the text
        embeddings = self._create_embeddings(processed_data["original_text"])
        
        # Identify themes
        main_themes = self._identify_themes(embeddings, conversation_history)
        
        # Generate sentiment score (placeholder)
        sentiment_score = random.uniform(-1.0, 1.0)
        
        # Generate complexity score (placeholder)
        complexity_score = random.uniform(0.0, 1.0)
        
        return {
            "embeddings": embeddings.tolist(),
            "main_themes": main_themes,
            "sentiment_score": sentiment_score,
            "complexity_score": complexity_score,
            "timestamp": time.time()
        }


class LLMConsultant:
    """Consults other LLMs for feedback and insights."""
    
    def __init__(self):
        self.available_llms = [
            {"name": "internal_model_1", "specialization": "reasoning"},
            {"name": "internal_model_2", "specialization": "creativity"},
            {"name": "internal_model_3", "specialization": "knowledge"}
        ]
    
    def _select_llms(self, data, learning_results):
        """Select appropriate LLMs to consult based on the data."""
        # Simple selection logic
        selected_llms = []
        
        # If sentiment is negative, add reasoning model
        if learning_results.get("sentiment_score", 0) < 0:
            selected_llms.append(next(llm for llm in self.available_llms if llm["specialization"] == "reasoning"))
        
        # If complexity is high, add knowledge model
        if learning_results.get("complexity_score", 0) > 0.7:
            selected_llms.append(next(llm for llm in self.available_llms if llm["specialization"] == "knowledge"))
        
        # Always add creativity model
        selected_llms.append(next(llm for llm in self.available_llms if llm["specialization"] == "creativity"))
        
        # Deduplicate
        seen = set()
        selected_llms = [x for x in selected_llms if not (x["name"] in seen or seen.add(x["name"]))]
        
        return selected_llms
    
    def _format_prompt(self, llm, data, learning_results, conversation_history):
        """Format a prompt for a specific LLM."""
        # Extract the last few messages for context
        recent_messages = conversation_history[-3:] if len(conversation_history) >= 3 else conversation_history
        context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_messages])
        
        # Format based on specialization
        if llm["specialization"] == "reasoning":
            return f"Analyze the following conversation and identify logical patterns and reasoning:\n\n{context}"
        elif llm["specialization"] == "creativity":
            return f"Generate creative insights and ideas based on this conversation:\n\n{context}"
        elif llm["specialization"] == "knowledge":
            themes = ", ".join(learning_results.get("main_themes", ["general knowledge"]))
            return f"Provide factual knowledge and educational insights related to these themes: {themes}\n\nContext:\n{context}"
        else:
            return f"Analyze this conversation and provide helpful insights:\n\n{context}"
    
    def _query_llm(self, llm, prompt):
        """Query a specific LLM with a prompt."""
        # Simulate response based on specialization
        if llm["specialization"] == "reasoning":
            responses = [
                "I notice a pattern of conditional logic in the discussion. Consider exploring counterfactual scenarios.",
                "The conversation shows deductive reasoning. Try introducing inductive elements for broader insights.",
                "There's an opportunity to apply syllogistic reasoning to strengthen the argument structure."
            ]
        elif llm["specialization"] == "creativity":
            responses = [
                "Try connecting these concepts to domains outside AI, like biology or architecture, for fresh perspectives.",
                "Consider using metaphorical thinking to reframe the problem in a novel way.",
                "Exploring contrasting viewpoints could reveal unexpected innovation opportunities."
            ]
        else:
            responses = [
                "Research in this area has recently focused on transfer learning across multiple domains.",
                "Historical approaches to this problem often overlooked the contextual variables you've identified.",
                "The theoretical framework you're discussing connects to established work in distributed systems."
            ]
        
        return random.choice(responses)
    
    def get_feedback(self, processed_data, learning_results, conversation_history):
        """Get feedback from other LLMs."""
        # Select LLMs to consult
        selected_llms = self._select_llms(processed_data, learning_results)
        
        feedback = []
        for llm in selected_llms:
            # Format prompt
            prompt = self._format_prompt(llm, processed_data, learning_results, conversation_history)
            
            # Query LLM
            response = self._query_llm(llm, prompt)
            
            # Add to feedback
            feedback.append({
                "llm": llm["name"],
                "specialization": llm["specialization"],
                "response": response
            })
        
        # Extract insights from feedback
        insights = [item["response"] for item in feedback]
        
        return {
            "feedback": feedback,
            "insights": insights,
            "consulted_llms": [llm["name"] for llm in selected_llms],
            "timestamp": time.time()
        }


class ReinforcementLearner:
    """Handles reinforcement learning from feedback."""
    
    def __init__(self):
        self.learning_rate = 0.01
        self.previous_states = []
        self.improvement_metrics = {
            "cycles_completed": 0,
            "average_improvement": 0.0,
            "areas_improved": set()
        }
    
    def _calculate_reward(self, learning_results, llm_feedback):
        """Calculate a reward signal based on learning and feedback."""
        # Base reward
        reward = 0.5
        
        # Adjust based on complexity score
        complexity = learning_results.get("complexity_score", 0.5)
        if complexity > 0.7:
            reward += 0.2  # Reward for handling complex topics
        
        # Adjust based on number of insights from LLMs
        insights = llm_feedback.get("insights", [])
        reward += min(len(insights) * 0.1, 0.3)  # Up to 0.3 for insights
        
        # Cap total reward
        return min(reward, 1.0)
    
    def _generate_improvement_ideas(self, learning_results, llm_feedback, reward):
        """Generate ideas for system improvement based on the feedback."""
        # Extract themes from learning results
        themes = learning_results.get("main_themes", [])
        
        # Extract insights from LLM feedback
        insights = llm_feedback.get("insights", [])
        
        # Generate ideas based on themes and insights
        ideas = []
        
        if themes and insights:
            # Mix themes and insights
            if len(themes) > 0:
                theme = random.choice(themes)
                ideas.append(f"Enhance capabilities related to {theme} based on feedback analysis")
            
            if len(insights) > 0:
                insight = random.choice(insights)
                ideas.append(f"Implement system improvements inspired by the insight: '{insight}'")
        
        # Add general improvement ideas
        general_ideas = [
            "Develop more nuanced understanding of context in conversations",
            "Improve ability to track long-term conversation themes",
            "Enhance creativity in generating diverse responses",
            "Develop better metadata tracking for learning opportunities",
            "Refine the consultation process with other LLMs for more targeted insights"
        ]
        
        ideas.extend(random.sample(general_ideas, min(2, len(general_ideas))))
        
        return ideas
    
    def update(self, learning_results, llm_feedback):
        """Update the reinforcement learning model with new data."""
        # Calculate reward
        reward = self._calculate_reward(learning_results, llm_feedback)
        
        # Generate improvement ideas
        improvement_ideas = self._generate_improvement_ideas(learning_results, llm_feedback, reward)
        
        # Update improvement metrics
        self.improvement_metrics["cycles_completed"] += 1
        self.improvement_metrics["average_improvement"] = (
            (self.improvement_metrics["average_improvement"] * (self.improvement_metrics["cycles_completed"] - 1) + reward) / 
            self.improvement_metrics["cycles_completed"]
        )
        
        # Add themes to areas improved
        themes = learning_results.get("main_themes", [])
        for theme in themes:
            self.improvement_metrics["areas_improved"].add(theme)
        
        # Save state for future reference
        self.previous_states.append({
            "learning_results": learning_results,
            "llm_feedback": llm_feedback,
            "reward": reward,
            "timestamp": time.time()
        })
        
        return {
            "reward": reward,
            "ideas": improvement_ideas,
            "improvement_score": reward,
            "metrics": {
                "cycles_completed": self.improvement_metrics["cycles_completed"],
                "average_improvement": self.improvement_metrics["average_improvement"],
                "areas_improved": list(self.improvement_metrics["areas_improved"])
            }
        }


class CodeImprover:
    """Suggests improvements to the codebase."""
    
    def __init__(self):
        self.improvement_history = []
        self.implementation_status = {}
    
    def _identify_improvement_areas(self, learning_results, llm_feedback, improvement_results):
        """Identify areas in the codebase that could be improved."""
        # Define potential improvement areas
        areas = [
            {"module": "text_processing", "category": "performance", "difficulty": "medium"},
            {"module": "conversation_flow", "category": "user_experience", "difficulty": "easy"},
            {"module": "learning_system", "category": "capabilities", "difficulty": "hard"},
            {"module": "data_storage", "category": "efficiency", "difficulty": "medium"},
            {"module": "feedback_integration", "category": "effectiveness", "difficulty": "medium"}
        ]
        
        # Select areas based on themes and insights
        themes = learning_results.get("main_themes", [])
        
        selected_areas = []
        
        # Select area based on theme if applicable
        if "performance" in " ".join(themes).lower():
            selected_areas.extend([a for a in areas if a["category"] == "performance"])
        
        if "user" in " ".join(themes).lower() or "experience" in " ".join(themes).lower():
            selected_areas.extend([a for a in areas if a["category"] == "user_experience"])
        
        if "learning" in " ".join(themes).lower() or "capabilities" in " ".join(themes).lower():
            selected_areas.extend([a for a in areas if a["category"] == "capabilities"])
        
        # If no areas selected by theme, choose random ones
        if not selected_areas:
            selected_areas = random.sample(areas, min(2, len(areas)))
        
        return selected_areas
    
    def _generate_code_suggestions(self, areas):
        """Generate specific code improvement suggestions."""
        suggestions = []
        
        for area in areas:
            module = area["module"]
            category = area["category"]
            
            # Generate suggestion based on module
            if module == "text_processing":
                suggestions.append({
                    "module": module,
                    "category": category,
                    "description": "Implement advanced tokenization for better concept extraction",
                    "estimated_impact": random.uniform(0.5, 0.9),
                    "code_example": "def improved_tokenize(text):\n    # Use more sophisticated tokenization\n    return advanced_tokens"
                })
            elif module == "conversation_flow":
                suggestions.append({
                    "module": module,
                    "category": category,
                    "description": "Add state tracking to maintain context over longer conversations",
                    "estimated_impact": random.uniform(0.6, 0.9),
                    "code_example": "class ConversationTracker:\n    def __init__(self):\n        self.long_term_memory = {}\n        self.context_window = []"
                })
            elif module == "learning_system":
                suggestions.append({
                    "module": module,
                    "category": category,
                    "description": "Implement embeddings comparison for detecting similar past learning experiences",
                    "estimated_impact": random.uniform(0.7, 0.95),
                    "code_example": "def find_similar_experiences(current_embedding):\n    similarities = [cosine_similarity(current_embedding, e) for e in past_embeddings]\n    return past_experiences[np.argmax(similarities)]"
                })
            else:
                suggestions.append({
                    "module": module,
                    "category": category,
                    "description": "Optimize storage for faster retrieval of conversation history",
                    "estimated_impact": random.uniform(0.4, 0.8),
                    "code_example": "class OptimizedStorage:\n    def __init__(self):\n        self.indexed_history = {}\n        self.fast_lookup_cache = {}"
                })
        
        return suggestions
    
    def suggest_improvements(self, learning_results, llm_feedback, improvement_results):
        """Suggest improvements to the codebase."""
        # Identify areas for improvement
        areas = self._identify_improvement_areas(learning_results, llm_feedback, improvement_results)
        
        # Generate code suggestions
        suggestions = self._generate_code_suggestions(areas)
        
        # Sort by estimated impact
        suggestions.sort(key=lambda x: x["estimated_impact"], reverse=True)
        
        # Record suggestion to history
        self.improvement_history.append({
            "timestamp": time.time(),
            "areas": areas,
            "suggestions": suggestions,
            "based_on": {
                "themes": learning_results.get("main_themes", []),
                "insights": llm_feedback.get("insights", [])
            }
        })
        
        return {
            "areas": areas,
            "suggestions": suggestions,
            "timestamp": time.time()
        }


class CollaborativeImprovement:
    """
    A module that facilitates an improvement cycle through:
    1. Initial conversation with user
    2. Processing and cleaning text data
    3. Deep learning analysis
    4. LLM consultation for feedback
    5. Human reinforcement learning
    """
    
    def __init__(self, config_path=None):
        """Initialize the collaborative improvement module."""
        self.topics = [
            "language understanding", "problem solving", "creative thinking",
            "logical reasoning", "emotional intelligence", "knowledge representation",
            "memory systems", "attention mechanisms", "learning optimization"
        ]
        
        self.conversation_history = []
        self.insights = []
        self.improvement_ideas = []
        self.feedback_cycles = 0
        
        # Load configuration if provided
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.text_processor = TextProcessor()
        self.deep_learner = DeepLearner()
        self.llm_consultant = LLMConsultant()
        self.reinforcement_learner = ReinforcementLearner()
        self.code_improver = CodeImprover()
        
        # Add self-modification capability
        try:
            from modules.code_updater import CodeUpdater
            self.code_updater = CodeUpdater()
            self.self_modification_enabled = True
            logger.info("Self-modification capability enabled")
        except ImportError:
            self.self_modification_enabled = False
            logger.info("Self-modification capability not available")
        
        # Add knowledge integration capability
        try:
            from modules.knowledge_integration import KnowledgeIntegrator
            self.knowledge_integrator = KnowledgeIntegrator()
            self.knowledge_enabled = True
            logger.info("Knowledge integration capability enabled")
        except ImportError:
            self.knowledge_enabled = False
            logger.info("Knowledge integration capability not available")
        
        logger.info("Collaborative improvement module initialized")
    
    def _load_config(self, config_path):
        """Load configuration from file or use defaults."""
        default_config = {
            "conversation_depth": 3,
            "cleaning_threshold": 0.7,
            "learning_rate": 0.01,
            "feedback_weight": 0.8,
            "improvement_threshold": 0.6,
            "max_cycles": 5
        }
        
        if not config_path or not os.path.exists(config_path):
            return default_config
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults for any missing keys
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
            return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return default_config
    
    def start_cycle(self, initial_prompt=None):
        """Begin a full improvement cycle."""
        # Step 1: Initial conversation
        initial_topic = self._get_conversation_starter(initial_prompt)
        initial_response = self._generate_initial_response(initial_topic)
        self.conversation_history.append({"role": "assistant", "content": initial_response})
        
        return {
            "response": initial_response,
            "next_step": "user_input",
            "message": "Please provide your thoughts or feedback to continue the cycle."
        }
    
    def _get_conversation_starter(self, user_prompt=None):
        """Generate or use a conversation starter topic."""
        if user_prompt:
            return user_prompt
        return random.choice(self.topics)
    
    def _generate_initial_response(self, topic):
        """Generate an initial conversation response."""
        templates = [
            f"I've been thinking about {topic} lately. It's fascinating how this concept relates to AI systems. What are your thoughts on this area?",
            f"Let's explore {topic} together. This is an area where I'd like to improve my understanding. Do you have any insights to share?",
            f"I'm curious about developing better capabilities in {topic}. Would you be interested in discussing this topic with me?"
        ]
        return random.choice(templates)
    
    def process_user_input(self, user_input):
        """Process user input and continue the improvement cycle."""
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # Step 2: Clean and process text
        cleaned_text = self.text_processor.clean(user_input)
        processed_data = self.text_processor.extract_key_concepts(cleaned_text)
        
        # Step 3: Deep learning analysis
        learning_results = self.deep_learner.analyze(processed_data, self.conversation_history)
        
        # Step 4: Consult other LLMs
        llm_feedback = self.llm_consultant.get_feedback(
            processed_data, 
            learning_results,
            self.conversation_history
        )
        
        # Step 5: Update learning model
        improvement_results = self.reinforcement_learner.update(
            learning_results,
            llm_feedback
        )
        
        # Check if we should suggest codebase improvements
        code_improvements = None
        if improvement_results["improvement_score"] > self.config["improvement_threshold"]:
            code_improvements = self.code_improver.suggest_improvements(
                learning_results,
                llm_feedback,
                improvement_results
            )
            
            # Save suggestions to the code updater for potential automatic implementation
            if self.self_modification_enabled and code_improvements and code_improvements.get("suggestions"):
                for suggestion in code_improvements["suggestions"]:
                    suggestion_id = self.code_updater.save_suggestion(suggestion)
                    logger.info(f"Saved code improvement suggestion: {suggestion_id}")
        
        # Check if we should add knowledge enhancement
        knowledge_results = None
        knowledge_enhancement = ""
        
        if self.knowledge_enabled:
            # Look for knowledge-seeking questions or statements
            knowledge_seeking = any(phrase in user_input.lower() for phrase in 
                                  ["what is", "how does", "tell me about", "explain", 
                                   "definition of", "meaning of", "facts about"])
            
            # If knowledge seeking or high complexity, query knowledge sources
            if knowledge_seeking or learning_results.get("complexity_score", 0) > 0.7:
                try:
                    # Extract key themes for knowledge query
                    query_terms = learning_results.get("main_themes", [])
                    if query_terms:
                        query = " ".join(query_terms[:3])  # Use top 3 themes
                        knowledge_results = self.knowledge_integrator.query_knowledge(query)
                        
                        # Extract most relevant information to enhance response
                        if knowledge_results:
                            knowledge_enhancement = self._format_knowledge_enhancement(knowledge_results)
                except Exception as e:
                    logger.error(f"Error during knowledge enhancement: {e}")
        
        # Generate response to user with potential knowledge enhancement
        response = self._generate_response_with_insights(
            user_input, 
            learning_results,
            llm_feedback,
            improvement_results,
            code_improvements,
            knowledge_enhancement
        )
        
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Increment cycle counter
        self.feedback_cycles += 1
        
        return {
            "response": response,
            "processed_data": processed_data,
            "learning_results": learning_results,
            "llm_feedback": llm_feedback,
            "improvement_results": improvement_results,
            "code_improvements": code_improvements,
            "knowledge_results": knowledge_results,
            "next_step": "user_input" if self.feedback_cycles < self.config["max_cycles"] else "complete",
            "cycle_number": self.feedback_cycles
        }
    
    def _format_knowledge_enhancement(self, knowledge_results):
        """Format knowledge results for inclusion in the response."""
        enhancement = ""
        
        # Process Wikipedia results
        if "wikipedia" in knowledge_results and knowledge_results["wikipedia"].get("results"):
            wiki_result = knowledge_results["wikipedia"]["results"][0]  # Use top result
            enhancement += f"\n\nAccording to Wikipedia: {wiki_result.get('extract', '')[:200]}..."
            
        # Process arXiv results
        if "arxiv" in knowledge_results and knowledge_results["arxiv"].get("results"):
            arxiv_result = knowledge_results["arxiv"]["results"][0]  # Use top result
            enhancement += f"\n\nA recent research paper titled '{arxiv_result.get('title')}' discusses this topic."
        
        # Process local database results
        if "local_database" in knowledge_results and knowledge_results["local_database"].get("results"):
            db_result = knowledge_results["local_database"]["results"][0]  # Use top result
            enhancement += f"\n\nFrom our knowledge base: {db_result.get('content', '')[:200]}..."
        
        return enhancement
    
    def _generate_response_with_insights(self, user_input, learning_results, llm_feedback, 
                                         improvement_results, code_improvements, knowledge_enhancement=""):
        """Generate a response incorporating the insights gained."""
        # Extract main themes from all the data
        main_themes = learning_results.get("main_themes", [])
        llm_insights = llm_feedback.get("insights", [])
        improvement_ideas = improvement_results.get("ideas", [])
        
        # Build response
        response_parts = []
        
        # Acknowledgment
        response_parts.append(f"Thank you for sharing your thoughts on this topic.")
        
        # Add knowledge enhancement if available
        if knowledge_enhancement:
            response_parts.append(knowledge_enhancement)
        
        # Learning insights
        if main_themes:
            response_parts.append(f"From our conversation, I identified these key themes: {', '.join(main_themes[:3])}.")
        
        # LLM consultation insights
        if llm_insights:
            insight = random.choice(llm_insights)
            response_parts.append(f"After consulting with other systems, I gained this insight: {insight}")
        
        # Improvement ideas
        if improvement_ideas:
            idea = random.choice(improvement_ideas)
            response_parts.append(f"This has given me an idea for improvement: {idea}")
        
        # Code improvement suggestion (if any)
        if code_improvements and code_improvements.get("suggestions"):
            suggestion = code_improvements["suggestions"][0]
            response_parts.append(f"I also see a potential way to improve my capabilities: {suggestion['description']}")
        
        # Closing question
        response_parts.append("What do you think about these insights? Do you have further thoughts that could help me understand this better?")
        
        return " ".join(response_parts)
    
    def save_state(self, path=None):
        """Save the current state of the module."""
        if not path:
            path = "collaborative_improvement_state.json"
        
        state = {
            "conversation_history": self.conversation_history,
            "insights": self.insights,
            "improvement_ideas": self.improvement_ideas,
            "feedback_cycles": self.feedback_cycles,
            "timestamp": time.time()
        }
        
        try:
            with open(path, 'w') as f:
                json.dump(state, f, indent=2)
            logger.info(f"State saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            return False
    
    def load_state(self, path):
        """Load a previously saved state."""
        if not os.path.exists(path):
            logger.error(f"State file not found: {path}")
            return False
        
        try:
            with open(path, 'r') as f:
                state = json.load(f)
            
            self.conversation_history = state.get("conversation_history", [])
            self.insights = state.get("insights", [])
            self.improvement_ideas = state.get("improvement_ideas", [])
            self.feedback_cycles = state.get("feedback_cycles", 0)
            
            logger.info(f"State loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return False

    def process_text_data(self, text_data=None):
        """Process text data through deep learning pipeline."""
        if not text_data:
            logger.warning("No text data provided for processing")
            return None
        
        # Process data
        processed_data = self.text_processor.process(text_data)
        logger.info(f"Processed {len(processed_data)} text elements")
        return processed_data
