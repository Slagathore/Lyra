import logging
import traceback
import sys
import json
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorCode(Enum):
    UNKNOWN_ERROR = 1000
    MODEL_NOT_FOUND = 1001
    MODEL_LOAD_FAILED = 1002
    TOKEN_LIMIT_EXCEEDED = 1003
    GENERATION_FAILED = 1004
    INVALID_PARAMETERS = 1005
    RESOURCE_UNAVAILABLE = 1006
    MEMORY_ERROR = 1007
    IO_ERROR = 1008
    LIBRARY_ERROR = 1009
    NETWORK_ERROR = 1010
    
class LyraError(Exception):
    """Base class for Lyra-specific exceptions"""
    def __init__(self, message, error_code=ErrorCode.UNKNOWN_ERROR, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)
        
    def to_dict(self):
        """Convert error to a dictionary for API responses"""
        return {
            "error": self.message,
            "error_code": self.error_code.value,
            "error_name": self.error_code.name,
            "details": self.details
        }
        
    def __str__(self):
        return f"{self.error_code.name} ({self.error_code.value}): {self.message}"
        
class ModelNotFoundError(LyraError):
    """Raised when a model file cannot be found"""
    def __init__(self, model_path, details=None):
        message = f"Model not found: {model_path}"
        super().__init__(message, ErrorCode.MODEL_NOT_FOUND, details)
        
class ModelLoadError(LyraError):
    """Raised when a model fails to load"""
    def __init__(self, model_name, reason, details=None):
        message = f"Failed to load model '{model_name}': {reason}"
        super().__init__(message, ErrorCode.MODEL_LOAD_FAILED, details)
        
class TokenLimitError(LyraError):
    """Raised when token limit is exceeded"""
    def __init__(self, current_tokens, max_tokens, details=None):
        message = f"Token limit exceeded: {current_tokens}/{max_tokens}"
        super().__init__(message, ErrorCode.TOKEN_LIMIT_EXCEEDED, details)
        
class GenerationError(LyraError):
    """Raised when text generation fails"""
    def __init__(self, reason, details=None):
        message = f"Text generation failed: {reason}"
        super().__init__(message, ErrorCode.GENERATION_FAILED, details)

def format_exception(e):
    """Format an exception for logging and display"""
    if isinstance(e, LyraError):
        return str(e)
    else:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        return f"{str(e)}\n{''.join(tb_lines)}"
        
def handle_error(e, user_friendly=True):
    """Handle an exception and return appropriate response"""
    logger.error(format_exception(e))
    
    if isinstance(e, LyraError):
        error_dict = e.to_dict()
    else:
        error_dict = {
            "error": str(e) if user_friendly else "An unexpected error occurred",
            "error_code": ErrorCode.UNKNOWN_ERROR.value,
            "error_name": ErrorCode.UNKNOWN_ERROR.name,
            "details": {}
        }
        
    return error_dict
