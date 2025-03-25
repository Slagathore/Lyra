import logging
import json
import requests
import time
import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import socket

# Import base provider
from .base_provider import BaseModel

logger = logging.getLogger("llama_server_provider")

class LlamaServerModel(BaseModel):
    """Provider for LLama models through the llama.cpp HTTP server."""
    
    def __init__(self, config):
        """Initialize with model configuration."""
        # IMPORTANT: Set these attributes BEFORE calling super().__init__
        # Fix for 'port' attribute error - set attributes before initialization
        self.host = config.parameters.get("host", "127.0.0.1")
        self.port = config.parameters.get("port", 8080)
        self.server_url = f"http://{self.host}:{self.port}"
        self.server_process = None
        self.model_info = {}
        
        # Now call the parent class initializer
        super().__init__(config)
        
        # Initialize the connection
        self._initialize()
    
    def _initialize(self):
        """Initialize the connection to the server."""
        # The code can now safely access self.port since it's defined before this method is called
        try:
            # Check if we need to start the server
            if self.config.parameters.get("auto_start_server", True):
                self._start_server()
            
            # Test connection
            self._test_connection()
            
            # Get model information
            self.model_info = self._get_model_info()
            logger.info(f"Connected to llama-server at {self.server_url}")
            if self.model_info:
                logger.info(f"Model info: {self.model_info.get('model_name', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error initializing connection to llama-server: {e}")
            raise
    
    def _start_server(self):
        """Start the llama-server if not already running."""
        # Check if server is already running
        if self._is_server_running():
            logger.info(f"Server already running at {self.server_url}")
            return
        
        try:
            # Import the server launcher
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from scripts.launch_llama_server import launch_server
            
            # Start the server
            logger.info(f"Starting llama-server for model: {self.config.model_name}")
            self.server_process = launch_server(
                model_name=self.config.model_name,
                port=self.port  # <-- Now self.port is properly defined
            )
            
            if not self.server_process:
                raise RuntimeError("Failed to start llama-server")
            
            logger.info(f"llama-server started successfully")
            
        except ImportError:
            logger.error("Could not import launch_llama_server script")
            raise
        except Exception as e:
            logger.error(f"Error starting llama-server: {e}")
            raise
    
    def _is_server_running(self):
        """Check if the server is already running."""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _test_connection(self):
        """Test the connection to the server."""
        max_retries = 10
        retry_delay = 1.0
        
        for i in range(max_retries):
            try:
                response = requests.get(f"{self.server_url}/health", timeout=5)
                if response.status_code == 200:
                    return True
            except requests.RequestException:
                if i == max_retries - 1:
                    raise
            
            logger.info(f"Waiting for server to be ready (attempt {i+1}/{max_retries})...")
            time.sleep(retry_delay)
        
        raise TimeoutError(f"Server did not become ready after {max_retries} attempts")
    
    def _get_model_info(self):
        """Get information about the loaded model."""
        try:
            # Try both API endpoints for model info
            endpoints = ["/props", "/v1/models"]
            
            for endpoint in endpoints:
                try:
                    response = requests.get(f"{self.server_url}{endpoint}", timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        # Handle different response formats
                        if isinstance(data, list) and len(data) > 0:
                            return data[0]  # v1/models returns a list
                        return data
                except:
                    continue
            
            # If we got here, we couldn't get model info
            logger.warning("Could not retrieve model information from server")
            return {}
            
        except Exception as e:
            logger.error(f"Error getting model information: {e}")
            return {}
    
    def generate(self, prompt: str, **kwargs):
        """Generate a response using the chat completion API."""
        try:
            # First try the chat completion API
            try:
                return self.chat_completion([{"role": "user", "content": prompt}], **kwargs)
            except Exception as chat_error:
                logger.warning(f"Chat completion failed, falling back to completion API: {chat_error}")
            
            # Fall back to the completion API
            request_data = {
                "prompt": prompt,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 40),
                "max_tokens": kwargs.get("max_tokens", 512),
                "stop": kwargs.get("stop", []),
                "stream": False
            }
            
            logger.info(f"Sending completion request to server")
            response = requests.post(
                f"{self.server_url}/completion",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=120  # Longer timeout for generation
            )
            
            # Check for errors
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated text
            if "content" in result:
                return result["content"]
            elif "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["text"]
            else:
                logger.warning(f"Unexpected response format: {result}")
                return str(result)
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return f"Error: {str(e)}"
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs):
        """Generate a response using the chat completion API."""
        try:
            # Handle single message - convert to list
            if isinstance(messages, dict):
                messages = [messages]
            
            # Add system message if not present
            has_system = any(msg.get("role") == "system" for msg in messages)
            if not has_system:
                system_message = {"role": "system", "content": "You are a helpful AI assistant."}
                messages.insert(0, system_message)
            
            # Prepare request data
            request_data = {
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "top_k": kwargs.get("top_k", 40),
                "max_tokens": kwargs.get("max_tokens", 512),
                "stream": False
            }
            
            # Rename max_tokens to n_predict if needed
            if "max_tokens" in request_data and "n_predict" not in request_data:
                request_data["n_predict"] = request_data.pop("max_tokens")
            
            # Send the chat completion request
            logger.info(f"Sending chat completion request to server")
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            
            # Check for errors
            response.raise_for_status()
            result = response.json()
            
            # Extract the generated message
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.warning(f"Unexpected response format: {result}")
                return str(result)
            
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources."""
        logger.info("Cleaning up llama server model resources")
        if self.server_process and hasattr(self.server_process, 'terminate'):
            try:
                logger.info("Stopping server process")
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error stopping server: {e}")
                if hasattr(self.server_process, 'kill'):
                    self.server_process.kill()
        
        super().cleanup()
