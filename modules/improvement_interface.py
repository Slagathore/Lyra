import gradio as gr
import json
import os
import time
from pathlib import Path
import logging
from modules.collaborative_improvement import CollaborativeImprovement
from modules.media_integration import MediaIntegrator
import matplotlib.pyplot as plt
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("improvement_interface")

class CollaborativeImprovementInterface:
    def __init__(self):
        self.improvement_module = CollaborativeImprovement()
        self.media_integrator = MediaIntegrator()
        self.session_id = f"session_{int(time.time())}"
        self.history = []
        self.cycle_count = 0
        
        # Add visualization capabilities
        # Use the DataVisualizer class defined in this file
        self.data_visualizer = DataVisualizer()
        self.visualization_enabled = True
        logger.info("Visualization module loaded successfully")
        
        self._initialize()
    
    def _initialize(self):
        """Initialize model formats and paths."""
        # Define common model formats and their associated file patterns
        self.model_formats = {
            "gguf": [".gguf"],
            "ggml": [".ggml", ".bin"],
            "pytorch": [".pt", ".pth", ".bin"],
            "safetensors": [".safetensors"],
            "gptq": [".gptq", ".qt", ".quantized"]
        }
        
        # Define chat formats for different model types
        self.chat_formats = {
            "llama": "<|system|>\n{system_prompt}\n<|user|>\n{prompt}\n<|assistant|>\n",
            "mistral": "<s>[INST] {system_prompt}\n{prompt} [/INST]",
            "vicuna": "USER: {prompt}\nASSISTANT:",
            "openchat": "GPT4 Correct User: {prompt}<|end_of_turn|>GPT4 Correct Assistant:"
        }
        
        # Create necessary directories
        os.makedirs(self.models_dir, exist_ok=True)
        logger.info(f"Models directory: {self.models_dir}")
    
    def start_conversation(self, topic=None):
        """Start a new conversation cycle."""
        result = self.improvement_module.start_cycle(topic)
        self.history = []
        self.cycle_count = 0
        self.history.append(("assistant", result["response"]))
        
        # Update cycle info
        cycle_info = {
            "status": "Conversation started",
            "cycle": self.cycle_count,
            "active_components": ["text_processor"]
        }
        
        return "", self.history, cycle_info
    
    def process_message(self, message, history):
        """Process a user message and continue the improvement cycle."""
        if not message.strip():
            return "", history, {}
        
        # Check for media generation request
        media_response = self.media_integrator.get_media_response(message)
        
        # Update history with user message
        history.append((message, ""))
        
        # Process through the improvement module
        result = self.improvement_module.process_user_input(message)
        self.cycle_count += 1
        
        # If media was detected, modify the response to include it
        response_text = result["response"]
        if (media_response["has_media"]):
            # In a full implementation, this would include the actual media
            response_text = media_response["response_text"] + "\n\n" + response_text
        
        # Add visualization if available and appropriate for the content
        if self.visualization_enabled and result.get("learning_results"):
            try:
                # Check if the conversation contains visualizable data
                themes = result["learning_results"]["main_themes"]
                sentiment = result["learning_results"]["sentiment_score"]
                
                if any(vis_topic in " ".join(themes).lower() for vis_topic in ["data", "chart", "graph", "visualization", "trend", "statistics"]):
                    viz_path = self.data_visualizer.create_insight_visualization(
                        result["learning_results"], 
                        self.cycle_count
                    )
                    cycle_info["visualization"] = {
                        "path": viz_path,
                        "type": "insight_graph"
                    }
                    response_text += f"\n\nI've also created a visualization of these insights that might help illustrate the relationships between concepts."
            except Exception as e:
                logger.error(f"Error creating visualization: {e}")
        
        # Update history with assistant response
        history[-1] = (history[-1][0], response_text)
        
        # Update cycle info with process details
        cycle_info = {
            "status": "Processing complete",
            "cycle": self.cycle_count,
            "topics": result["learning_results"]["main_themes"],
            "sentiment": round(result["learning_results"]["sentiment_score"], 2),
            "complexity": round(result["learning_results"]["complexity_score"], 2),
            "active_components": [
                "text_processor", 
                "deep_learner", 
                "llm_consultant", 
                "reinforcement_learner"
            ]
        }
        
        # Add media info if present
        if media_response["has_media"]:
            cycle_info["media_generated"] = {
                "type": media_response["media_type"],
                "id": media_response["media_id"]
            }
            cycle_info["active_components"].append("media_integrator")
        
        # Add code improvement info if present
        if result.get("code_improvements"):
            cycle_info["code_improvements"] = {
                "count": len(result["code_improvements"].get("suggestions", [])),
                "modules": [s["module"] for s in result["code_improvements"].get("suggestions", [])]
            }
            cycle_info["active_components"].append("code_improver")
        
        # Save the session state
        self._save_session_state()
        
        return "", history, cycle_info
    
    def _save_session_state(self):
        """Save the current session state."""
        session_dir = Path("sessions")
        session_dir.mkdir(exist_ok=True)
        
        session_path = session_dir / f"{self.session_id}.json"
        
        session_data = {
            "session_id": self.session_id,
            "history": self.history,
            "cycle_count": self.cycle_count,
            "timestamp": time.time()
        }
        
        try:
            with open(session_path, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session state saved to {session_path}")
        except Exception as e:
            logger.error(f"Error saving session state: {e}")
    
    def create_ui(self):
        """Create the Gradio UI for the improvement interface."""
        with gr.Blocks(title="AI Self-Improvement Interface") as interface:
            gr.HTML("<h1>Collaborative Learning & Self-Improvement</h1>")
            gr.HTML("<p>Engage in a conversation that helps the AI learn and improve through a multi-stage process.</p>")
            
            with gr.Row():
                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(height=600)
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            show_label=False,
                            placeholder="Type your message here...",
                            container=False
                        )
                    
                    with gr.Row():
                        submit_btn = gr.Button("Send")
                        clear_btn = gr.Button("Clear")
                        start_btn = gr.Button("Start New Conversation")
                
                with gr.Column(scale=1):
                    gr.HTML("<h3>Process Overview</h3>")
                    gr.HTML("""
                    <ol>
                        <li>Initial conversation with you</li>
                        <li>Text cleaning & analysis</li>
                        <li>Deep learning processing</li>
                        <li>Consultation with other LLMs</li>
                        <li>Reinforcement learning</li>
                        <li>Human feedback (that's you!)</li>
                    </ol>
                    """)
                    
                    gr.HTML("<h3>Current Cycle Information</h3>")
                    cycle_info = gr.JSON(
                        {"status": "Ready to start", "cycle": 0},
                        label="Learning Progress"
                    )
                    
                    gr.HTML("<h3>Media Generation</h3>")
                    gr.Markdown("""
                    You can request media generation by using phrases like:
                    - "Create an image of..."
                    - "Generate a video showing..."
                    - "Make a 3D model of..."
                    """)
            
            # Event handlers
            start_btn.click(
                fn=self.start_conversation,
                inputs=[],
                outputs=[msg, chatbot, cycle_info]
            )
            
            msg.submit(
                fn=self.process_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, cycle_info]
            )
            
            submit_btn.click(
                fn=self.process_message,
                inputs=[msg, chatbot],
                outputs=[msg, chatbot, cycle_info]
            )
            
            clear_btn.click(
                fn=lambda: ("", [], {"status": "Ready to start", "cycle": 0}),
                inputs=[],
                outputs=[msg, chatbot, cycle_info]
            )
            
        return interface

def create_collaborative_improvement_interface():
    """Factory function to create and return a new interface instance."""
    interface = CollaborativeImprovementInterface()
    return interface.create_ui()

class DataVisualizer:
    def __init__(self):
        self.output_dir = Path("visualizations")
        self.output_dir.mkdir(exist_ok=True)
        logger.info("DataVisualizer initialized")
        
    def create_insight_visualization(self, learning_results, cycle_count):
        """
        Create a visualization based on learning results.
        
        Args:
            learning_results (dict): Dictionary containing analysis results
            cycle_count (int): Current conversation cycle number
            
        Returns:
            str: Path to the saved visualization
        """
        # Create a simple visualization based on themes and sentiment
        themes = learning_results.get("main_themes", [])
        sentiment = learning_results.get("sentiment_score", 0)
        
        # Generate a simple bar chart for themes
        plt.figure(figsize=(10, 6))
        
        # If we have themes, plot them
        if themes:
            # Limit to top 5 themes for readability
            if len(themes) > 5:
                themes = themes[:5]
                
            # Create synthetic relevance scores if not available
            relevance = learning_results.get("theme_relevance", 
                                            np.linspace(0.9, 0.5, len(themes)))
            
            plt.bar(themes, relevance)
            plt.title(f"Main Conversation Themes (Cycle {cycle_count})")
            plt.ylabel("Relevance Score")
            plt.ylim(0, 1.0)
            plt.xticks(rotation=45, ha="right")
            
        # Save the visualization
        output_path = self.output_dir / f"insight_cycle_{cycle_count}.png"
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return str(output_path)
