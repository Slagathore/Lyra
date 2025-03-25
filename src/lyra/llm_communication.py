"""
Cross-LLM Communication System for Lyra

This module allows Lyra to communicate with other LLM systems through standardized protocols,
enabling collaborative reasoning, peer verification, and distributed tasks.
"""

import os
import json
import time
import requests
import logging
import uuid
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMMessage:
    """Object representing a message in the LLM communication protocol"""
    
    def __init__(self, 
                 content: str, 
                 sender_id: str, 
                 message_type: str = "text",
                 metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize a new message
        
        Args:
            content: The message content
            sender_id: Identifier of the sender
            message_type: Type of message (text, command, query, response)
            metadata: Additional metadata about the message
        """
        self.id = str(uuid.uuid4())
        self.content = content
        self.sender_id = sender_id
        self.timestamp = datetime.now().isoformat()
        self.message_type = message_type
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp,
            "message_type": self.message_type,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LLMMessage':
        """Create message from dictionary"""
        message = cls(
            content=data["content"],
            sender_id=data["sender_id"],
            message_type=data.get("message_type", "text"),
            metadata=data.get("metadata", {})
        )
        message.id = data.get("id", str(uuid.uuid4()))
        message.timestamp = data.get("timestamp", datetime.now().isoformat())
        return message
        
    def __str__(self) -> str:
        return f"{self.sender_id}: {self.content}"

class LLMCommunicator:
    """
    Handles communication between different LLM systems
    
    This class provides methods to:
    1. Send messages to other LLM systems via API or direct interface
    2. Receive and process incoming messages
    3. Manage communication protocols and formats
    4. Track conversation history with external systems
    """
    
    def __init__(self, 
                 system_id: str = "lyra", 
                 api_keys: Optional[Dict[str, str]] = None,
                 endpoints: Optional[Dict[str, str]] = None):
        """
        Initialize the LLM communicator
        
        Args:
            system_id: Identifier for this system
            api_keys: Dictionary of API keys for external services
            endpoints: Dictionary of API endpoints for external LLM systems
        """
        self.system_id = system_id
        self.api_keys = api_keys or {}
        self.endpoints = endpoints or {}
        self.conversation_history: Dict[str, List[LLMMessage]] = {}
        
        # Load API keys from environment if not provided
        if not self.api_keys:
            self._load_api_keys_from_env()
            
        # Register with discovery service if available
        self._register_with_discovery()
        
    def _load_api_keys_from_env(self):
        """Load API keys from environment variables"""
        for key in os.environ:
            if key.endswith("_API_KEY"):
                service = key.replace("_API_KEY", "").lower()
                self.api_keys[service] = os.environ[key]
                
        logger.info(f"Loaded {len(self.api_keys)} API keys from environment")
        
    def _register_with_discovery(self):
        """Register with LLM discovery service if available"""
        discovery_url = os.environ.get("LLM_DISCOVERY_URL")
        if not discovery_url:
            return
            
        try:
            response = requests.post(
                discovery_url,
                json={
                    "system_id": self.system_id,
                    "capabilities": ["text", "reasoning", "memory", "planning"],
                    "endpoint": os.environ.get("LYRA_ENDPOINT", "http://localhost:8000/api")
                },
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("Successfully registered with LLM discovery service")
                
                # Get other available LLMs
                other_systems = response.json().get("systems", [])
                for system in other_systems:
                    if system["system_id"] != self.system_id:
                        self.endpoints[system["system_id"]] = system["endpoint"]
                        
                logger.info(f"Discovered {len(self.endpoints)} other LLM systems")
            else:
                logger.warning(f"Failed to register with discovery service: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error registering with discovery service: {e}")
    
    def send_message(self, 
                    recipient_id: str, 
                    content: str, 
                    message_type: str = "text",
                    metadata: Optional[Dict[str, Any]] = None) -> Optional[LLMMessage]:
        """
        Send a message to another LLM system
        
        Args:
            recipient_id: ID of the recipient system
            content: Message content
            message_type: Type of message
            metadata: Additional metadata
            
        Returns:
            The sent message object or None if sending failed
        """
        message = LLMMessage(
            content=content,
            sender_id=self.system_id,
            message_type=message_type,
            metadata=metadata
        )
        
        # Store in conversation history
        if recipient_id not in self.conversation_history:
            self.conversation_history[recipient_id] = []
            
        self.conversation_history[recipient_id].append(message)
        
        # Send to recipient if endpoint available
        if recipient_id in self.endpoints:
            try:
                endpoint = self.endpoints[recipient_id]
                
                # Add API key to headers if available
                headers = {}
                if recipient_id in self.api_keys:
                    headers["Authorization"] = f"Bearer {self.api_keys[recipient_id]}"
                    
                response = requests.post(
                    f"{endpoint}/receive_message",
                    json=message.to_dict(),
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully sent message to {recipient_id}")
                    
                    # If there's a response, add it to conversation history
                    response_data = response.json().get("response")
                    if response_data:
                        response_message = LLMMessage.from_dict(response_data)
                        self.conversation_history[recipient_id].append(response_message)
                        return response_message
                else:
                    logger.warning(f"Failed to send message to {recipient_id}: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending message to {recipient_id}: {e}")
                
        return message
    
    def receive_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an incoming message from another LLM system
        
        Args:
            message_data: Dictionary containing the message data
            
        Returns:
            Dictionary with processing results and optional response
        """
        # Parse message
        try:
            message = LLMMessage.from_dict(message_data)
            
            # Add to conversation history
            sender = message.sender_id
            if sender not in self.conversation_history:
                self.conversation_history[sender] = []
                
            self.conversation_history[sender].append(message)
            
            logger.info(f"Received message from {sender}: {message.content[:50]}...")
            
            # Process based on message type
            if message.message_type == "query":
                return self._process_query(message)
            elif message.message_type == "command":
                return self._process_command(message)
            else:
                # Default text processing
                return {
                    "status": "received",
                    "message_id": message.id,
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _process_query(self, message: LLMMessage) -> Dict[str, Any]:
        """
        Process a query message that expects a response
        
        Args:
            message: The query message
            
        Returns:
            Response data
        """
        # Get query parameters
        query = message.content
        query_type = message.metadata.get("query_type", "general")
        
        # TODO: Implement actual query processing by integrating with Lyra's systems
        # For now, we'll return a placeholder response
        
        response = LLMMessage(
            content=f"Received your query about '{query}'. This is a placeholder response.",
            sender_id=self.system_id,
            message_type="response",
            metadata={
                "in_response_to": message.id,
                "query_type": query_type,
                "confidence": 0.7
            }
        )
        
        # Add to conversation history
        self.conversation_history[message.sender_id].append(response)
        
        return {
            "status": "processed",
            "message_id": message.id,
            "response": response.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _process_command(self, message: LLMMessage) -> Dict[str, Any]:
        """
        Process a command message that requests an action
        
        Args:
            message: The command message
            
        Returns:
            Command execution results
        """
        # Get command parameters
        command = message.content
        params = message.metadata.get("params", {})
        
        # TODO: Implement actual command processing
        # For now, we'll return a placeholder response
        
        return {
            "status": "acknowledged",
            "message_id": message.id,
            "command": command,
            "result": "Command received but execution not implemented",
            "timestamp": datetime.now().isoformat()
        }
        
    def get_conversation_history(self, partner_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history with a specific LLM system
        
        Args:
            partner_id: ID of the partner system
            
        Returns:
            List of messages in the conversation
        """
        if partner_id in self.conversation_history:
            return [msg.to_dict() for msg in self.conversation_history[partner_id]]
        return []
    
    def discover_systems(self) -> List[str]:
        """
        Discover available LLM systems
        
        Returns:
            List of discovered system IDs
        """
        discovery_url = os.environ.get("LLM_DISCOVERY_URL")
        if not discovery_url:
            return list(self.endpoints.keys())
            
        try:
            response = requests.get(discovery_url, timeout=5)
            if response.status_code == 200:
                systems = response.json().get("systems", [])
                
                # Update endpoints
                for system in systems:
                    if system["system_id"] != self.system_id:
                        self.endpoints[system["system_id"]] = system["endpoint"]
                        
                return [s["system_id"] for s in systems if s["system_id"] != self.system_id]
            else:
                logger.warning(f"Failed to discover systems: {response.status_code}")
        except Exception as e:
            logger.error(f"Error discovering systems: {e}")
            
        return list(self.endpoints.keys())
    
    def collaborative_reasoning(self, 
                             query: str, 
                             partner_ids: List[str],
                             timeout: int = 60) -> Dict[str, Any]:
        """
        Perform collaborative reasoning with multiple LLM systems
        
        Args:
            query: The query/problem to solve
            partner_ids: IDs of partner systems to collaborate with
            timeout: Timeout in seconds
            
        Returns:
            Results from collaborative reasoning
        """
        if not partner_ids:
            logger.warning("No partner systems specified for collaborative reasoning")
            return {"error": "No partner systems specified"}
            
        # Send query to all specified partners
        responses = {}
        start_time = time.time()
        
        for partner_id in partner_ids:
            if partner_id in self.endpoints:
                try:
                    # Create a collaboration message
                    response = self.send_message(
                        recipient_id=partner_id,
                        content=query,
                        message_type="query",
                        metadata={
                            "query_type": "collaboration",
                            "priority": "high",
                            "domain": "reasoning",
                            "requested_details": ["explanation", "confidence", "sources"]
                        }
                    )
                    
                    if response:
                        responses[partner_id] = {
                            "content": response.content,
                            "confidence": response.metadata.get("confidence", 0.0),
                            "explanation": response.metadata.get("explanation", ""),
                            "timestamp": response.timestamp
                        }
                    
                    # Check timeout
                    if time.time() - start_time > timeout:
                        logger.warning("Collaborative reasoning timed out")
                        break
                        
                except Exception as e:
                    logger.error(f"Error in collaborative reasoning with {partner_id}: {e}")
            else:
                logger.warning(f"No endpoint available for {partner_id}")
                
        # Summarize results
        if responses:
            # TODO: Implement actual synthesis of multiple responses
            # For now, just return the collected responses
            return {
                "query": query,
                "responses": responses,
                "systems_consulted": len(responses),
                "total_systems": len(partner_ids),
                "synthesis": "Response synthesis not implemented"
            }
        else:
            return {
                "query": query,
                "error": "No responses received",
                "systems_consulted": 0,
                "total_systems": len(partner_ids)
            }

# Singleton instance
_communicator_instance = None

def get_llm_communicator() -> LLMCommunicator:
    """Get or create the LLM communicator singleton instance"""
    global _communicator_instance
    if _communicator_instance is None:
        _communicator_instance = LLMCommunicator()
    return _communicator_instance

if __name__ == "__main__":
    # Test the LLM communication module
    communicator = get_llm_communicator()
    
    # Discover available systems
    systems = communicator.discover_systems()
    print(f"Discovered systems: {systems}")
    
    # Send a test message if any systems available
    if systems:
        test_recipient = systems[0]
        print(f"Sending test message to {test_recipient}")
        response = communicator.send_message(
            recipient_id=test_recipient,
            content="Hello from Lyra! This is a test message.",
            message_type="text"
        )
        
        if response:
            print(f"Received response: {response}")
