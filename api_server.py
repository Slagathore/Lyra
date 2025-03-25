"""
API Server for Lyra
Provides HTTP API for external applications to interact with Lyra
"""

import os
import sys
import json
import time
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api_server.log")
    ]
)
logger = logging.getLogger("api_server")

# Try to import Flask
try:
    from flask import Flask, request, jsonify
    FLASK_AVAILABLE = True
except ImportError:
    logger.error("Flask not available. Install with: pip install flask")
    FLASK_AVAILABLE = False

class LyraAPI:
    """API server for Lyra"""
    
    def __init__(self, port: int = 5000):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for the API server")
            
        self.port = port
        self.app = Flask("LyraAPI")
        self.lyra_interface = None
        self.modules = {}
        self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Set up routes
        self._setup_routes()
        
        # Load modules
        self._load_modules()
    
    def _load_modules(self):
        """Load Lyra modules for API integration"""
        # First try direct approach with full bot
        try:
            # Try to load the bot interface
            sys.path.append(self.base_path)
            from lyra_bot import LyraBot
            self.lyra_interface = LyraBot()
            logger.info("Loaded Lyra bot interface")
            
            # Try to connect to Phi-4 or other powerful model
            try:
                from model_loader import get_instance as get_model_loader
                model_loader = get_model_loader()
                
                # Look for Phi-4 first
                phi_models = [m for m in model_loader.models if "phi" in m.name.lower()]
                if phi_models:
                    # Try to find Phi-4 specifically
                    for model in phi_models:
                        if "phi-4" in model.name.lower() or "phi4" in model.name.lower():
                            if hasattr(self.lyra_interface, "select_model"):
                                self.lyra_interface.select_model(model.name)
                                logger.info(f"Connected API to Phi-4 model: {model.name}")
                                break
                    
                    # If no Phi-4, use any Phi model
                    if not any("phi-4" in m.name.lower() or "phi4" in m.name.lower() for m in phi_models):
                        if hasattr(self.lyra_interface, "select_model"):
                            self.lyra_interface.select_model(phi_models[0].name)
                            logger.info(f"Connected API to Phi model: {phi_models[0].name}")
            except ImportError as e:
                logger.warning(f"Could not load model loader: {e}")
                
        except ImportError as e:
            logger.warning(f"Could not load Lyra bot interface: {e}")
            
            # Fallback to direct model access
            try:
                from model_backends.phi_backend import PhiInterface
                self.phi_model = PhiInterface("phi-2")
                if self.phi_model.initialize():
                    logger.info("Loaded direct Phi model for API access")
                    
                    # Create a simple wrapper for the API
                    self.lyra_interface = type('SimpleInterface', (), {
                        'generate_response': lambda self, text: self.phi_model.generate_text(text),
                        'phi_model': self.phi_model
                    })()
            except ImportError:
                logger.warning("Could not load direct Phi model")
        
        # Load cognitive modules
        try:
            from modules.extended_thinking import get_instance as get_extended_thinking
            self.modules["extended_thinking"] = get_extended_thinking()
            logger.info("Loaded extended thinking module")
        except ImportError:
            logger.warning("Extended thinking module not available")
        
        # Load boredom system
        try:
            from modules.boredom import get_instance as get_boredom
            self.modules["boredom"] = get_boredom()
            logger.info("Loaded boredom module")
        except ImportError:
            logger.warning("Boredom module not available")
        
        # Load emotional core
        try:
            from modules.emotional_core import get_instance as get_emotional_core
            self.modules["emotional_core"] = get_emotional_core()
            logger.info("Loaded emotional core module")
        except ImportError:
            logger.warning("Emotional core module not available")
        
        # Load deep memory
        try:
            from modules.deep_memory import get_instance as get_deep_memory
            self.modules["deep_memory"] = get_deep_memory()
            logger.info("Loaded deep memory module")
        except ImportError:
            logger.warning("Deep memory module not available")
    
    def _setup_routes(self):
        """Set up API routes"""
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "ok",
                "timestamp": time.time(),
                "modules_available": list(self.modules.keys())
            })
        
        @self.app.route('/api/chat', methods=['POST'])
        def chat():
            """Chat endpoint"""
            data = request.get_json()
            if not data or 'message' not in data:
                return jsonify({"error": "Invalid request, 'message' field required"}), 400
            
            message = data['message']
            user_id = data.get('user_id', 'api_user')
            
            if not self.lyra_interface:
                return jsonify({"error": "Lyra bot interface not available"}), 503
            
            try:
                # Process the message
                response = self.lyra_interface.generate_response(message)
                
                return jsonify({
                    "response": response,
                    "timestamp": time.time()
                })
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/thinking/status', methods=['GET'])
        def thinking_status():
            """Get thinking status"""
            if "extended_thinking" not in self.modules:
                return jsonify({"error": "Extended thinking module not available"}), 503
            
            try:
                thinking = self.modules["extended_thinking"]
                status = thinking.get_thinking_state()
                
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting thinking status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/thinking/create_task', methods=['POST'])
        def create_thinking_task():
            """Create a new thinking task"""
            if "extended_thinking" not in self.modules:
                return jsonify({"error": "Extended thinking module not available"}), 503
            
            data = request.get_json()
            if not data or 'description' not in data:
                return jsonify({"error": "Invalid request, 'description' field required"}), 400
            
            try:
                thinking = self.modules["extended_thinking"]
                task_id = thinking.create_thinking_task(
                    description=data['description'],
                    task_type=data.get('task_type', 'reflection'),
                    priority=float(data.get('priority', 0.5)),
                    max_duration=int(data.get('max_duration', 600))
                )
                
                return jsonify({
                    "task_id": task_id,
                    "status": "created"
                })
            except Exception as e:
                logger.error(f"Error creating thinking task: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/emotional/status', methods=['GET'])
        def emotional_status():
            """Get emotional status"""
            if "emotional_core" not in self.modules:
                return jsonify({"error": "Emotional core module not available"}), 503
            
            try:
                emotional = self.modules["emotional_core"]
                dominant, intensity = emotional.get_dominant_emotion()
                mood = emotional.get_mood_description()
                
                return jsonify({
                    "dominant_emotion": dominant,
                    "intensity": intensity,
                    "mood": mood
                })
            except Exception as e:
                logger.error(f"Error getting emotional status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/boredom/status', methods=['GET'])
        def boredom_status():
            """Get boredom status"""
            if "boredom" not in self.modules:
                return jsonify({"error": "Boredom module not available"}), 503
            
            try:
                boredom = self.modules["boredom"]
                state = boredom.get_boredom_state()
                
                return jsonify(state)
            except Exception as e:
                logger.error(f"Error getting boredom status: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/memory/recall', methods=['POST'])
        def recall_memory():
            """Recall memories based on query"""
            if "deep_memory" not in self.modules:
                return jsonify({"error": "Deep memory module not available"}), 503
            
            data = request.get_json()
            if not data or 'query' not in data:
                return jsonify({"error": "Invalid request, 'query' field required"}), 400
            
            try:
                memory = self.modules["deep_memory"]
                results = memory.recall_similar(data['query'], limit=int(data.get('limit', 5)))
                
                return jsonify({
                    "query": data['query'],
                    "results": results
                })
            except Exception as e:
                logger.error(f"Error recalling memories: {e}")
                return jsonify({"error": str(e)}), 500
    
    def run(self):
        """Run the API server"""
        logger.info(f"Starting API server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Lyra API Server")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the API server on")
    args = parser.parse_args()
    
    try:
        api = LyraAPI(port=args.port)
        api.run()
    except ImportError:
        logger.error("Required dependencies not available")
        logger.info("Please install Flask: pip install flask")
    except Exception as e:
        logger.error(f"Error starting API server: {e}")

if __name__ == "__main__":
    main()
