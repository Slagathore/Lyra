"""
Error handling utilities for Lyra's self-improvement modules.
"""
import os
import sys
import traceback
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class ErrorHandler:
    """Centralized error handling for self-improvement components"""
    
    def __init__(self, log_dir=None):
        """Initialize with optional log directory"""
        self.log_dir = log_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'logs'
        )
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Set up error log file
        log_file = os.path.join(self.log_dir, 'self_improvement_errors.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    def handle_api_error(self, provider: str, response=None, exception=None) -> Tuple[bool, Dict[str, Any]]:
        """Handle errors from API calls"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "success": False
        }
        
        if response:
            error_info["status_code"] = getattr(response, 'status_code', 'unknown')
            try:
                error_info["response_body"] = response.text
            except:
                error_info["response_body"] = "Could not get response text"
        
        if exception:
            error_info["exception_type"] = type(exception).__name__
            error_info["exception_msg"] = str(exception)
            error_info["traceback"] = traceback.format_exc()
            
            # Log the error
            logger.error(f"API error with {provider}: {str(exception)}")
        
        # Create a user-friendly error message
        if response and getattr(response, 'status_code', 0) == 401:
            error_info["user_message"] = f"Authentication failed for {provider}. Check your API key."
        elif response and getattr(response, 'status_code', 0) == 429:
            error_info["user_message"] = f"Rate limit reached for {provider}. Try again later."
        elif response and getattr(response, 'status_code', 0) >= 500:
            error_info["user_message"] = f"Server error from {provider}. Try again later."
        else:
            error_info["user_message"] = f"Error with {provider}: {str(exception)}"
        
        return False, error_info
    
    def handle_module_error(self, module_name: str, function_name: str, exception: Exception) -> Dict[str, Any]:
        """Handle errors from module functions"""
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "module": module_name,
            "function": function_name,
            "exception_type": type(exception).__name__,
            "exception_msg": str(exception),
            "traceback": traceback.format_exc()
        }
        
        # Log the error
        logger.error(f"Error in {module_name}.{function_name}: {str(exception)}")
        
        return error_info
    
    def log_error(self, context: str, error_type: str, details: Dict[str, Any]) -> None:
        """Log an error with context information"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "context": context,
            "type": error_type,
            **details
        }
        
        logger.error(f"{context} error: {error_type}")
        logger.error(f"Details: {details}")
