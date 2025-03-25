"""
Error handling utility for Lyra
Provides standardized exception handling across all components
"""

import logging
import traceback
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Tuple

# Set up logging
logger = logging.getLogger("error_handler")

class ErrorHandler:
    """
    Centralized error handling for Lyra components
    Provides standardized exception catching, logging, and recovery
    """
    
    def __init__(self, component_name: str, log_dir: str = "logs"):
        """
        Initialize the error handler
        
        Args:
            component_name: Name of the component using this handler
            log_dir: Directory for error logs
        """
        self.component_name = component_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Error log file specific to this component
        self.error_log_file = self.log_dir / f"{component_name}_errors.log"
        
        # Set up a file handler for this component
        self.file_handler = logging.FileHandler(self.error_log_file)
        self.file_handler.setLevel(logging.ERROR)
        self.file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        
        # Add handler to logger
        logger.addHandler(self.file_handler)
        
        # Store last errors for diagnostics
        self.last_errors = []
        self.max_stored_errors = 100
        
        # Recovery handlers
        self.recovery_handlers = {}
    
    def handle_exception(self, e: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle an exception in a standardized way
        
        Args:
            e: The exception to handle
            context: Optional context information about when/where the exception occurred
            
        Returns:
            Dictionary with error information
        """
        # Create error info
        error_info = {
            "timestamp": time.time(),
            "component": self.component_name,
            "exception_type": type(e).__name__,
            "exception_message": str(e),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        # Log the error
        logger.error(
            f"Exception in {self.component_name}: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        
        # Store in last errors
        self.last_errors.append(error_info)
        if len(self.last_errors) > self.max_stored_errors:
            self.last_errors = self.last_errors[-self.max_stored_errors:]
        
        # Write to error log file
        self._write_error_to_log(error_info)
        
        # Try to recover if handler available
        recovery_result = self._try_recovery(error_info)
        if recovery_result:
            error_info["recovery"] = recovery_result
        
        return error_info
    
    def _write_error_to_log(self, error_info: Dict[str, Any]):
        """Write detailed error information to the component's error log"""
        try:
            with open(self.error_log_file, 'a') as f:
                f.write(f"\n--- ERROR at {time.ctime(error_info['timestamp'])} ---\n")
                f.write(f"Component: {error_info['component']}\n")
                f.write(f"Exception: {error_info['exception_type']}: {error_info['exception_message']}\n")
                f.write(f"Context: {json.dumps(error_info['context'])}\n")
                f.write(f"Traceback:\n{error_info['traceback']}\n")
                f.write("-" * 80 + "\n")
        except Exception as log_error:
            logger.error(f"Failed to write to error log: {log_error}")
    
    def register_recovery_handler(self, exception_type: type, handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Register a recovery handler for a specific exception type
        
        Args:
            exception_type: The exception type to handle
            handler: Function that takes error info and returns recovery results
        """
        self.recovery_handlers[exception_type] = handler
    
    def _try_recovery(self, error_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Try to recover from an error using registered handlers
        
        Args:
            error_info: Information about the error
            
        Returns:
            Recovery information or None if no recovery was attempted
        """
        exception_type_name = error_info["exception_type"]
        
        # Find the exception type in registered handlers
        for exc_type, handler in self.recovery_handlers.items():
            if exc_type.__name__ == exception_type_name:
                try:
                    recovery_result = handler(error_info)
                    logger.info(f"Recovery for {exception_type_name} successful")
                    return recovery_result
                except Exception as recovery_error:
                    logger.error(f"Recovery for {exception_type_name} failed: {recovery_error}")
                    return {
                        "attempted": True,
                        "successful": False,
                        "error": str(recovery_error)
                    }
        
        return None
    
    def safe_call(self, func: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
        """
        Safely call a function with exception handling
        
        Args:
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Tuple of (success, result, error_info)
        """
        try:
            result = func(*args, **kwargs)
            return True, result, None
        except Exception as e:
            error_info = self.handle_exception(e, {
                "function": func.__name__,
                "args": str(args),
                "kwargs": str(kwargs)
            })
            return False, None, error_info
    
    def get_error_report(self) -> Dict[str, Any]:
        """
        Generate an error report for diagnostics
        
        Returns:
            Dictionary with error statistics and recent errors
        """
        report = {
            "component": self.component_name,
            "total_errors": len(self.last_errors),
            "recent_errors": self.last_errors[-10:],  # Last 10 errors
            "error_counts_by_type": {}
        }
        
        # Count errors by type
        for error in self.last_errors:
            exc_type = error["exception_type"]
            if exc_type not in report["error_counts_by_type"]:
                report["error_counts_by_type"][exc_type] = 0
            report["error_counts_by_type"][exc_type] += 1
        
        return report

# Set up a global handler that can be used for system-wide functions
_global_handler = ErrorHandler("lyra_system")

def handle_global_exception(e: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle an exception using the global error handler
    
    Args:
        e: The exception to handle
        context: Optional context information
    
    Returns:
        Dictionary with error information
    """
    return _global_handler.handle_exception(e, context)

def safe_global_call(func: Callable, *args, **kwargs) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
    """
    Safely call a function using the global error handler
    
    Args:
        func: Function to call
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
    
    Returns:
        Tuple of (success, result, error_info)
    """
    return _global_handler.safe_call(func, *args, **kwargs)

def install_global_exception_handler():
    """Install a global exception hook to catch unhandled exceptions"""
    def global_exception_hook(exc_type, exc_value, exc_traceback):
        """Global exception hook that logs unhandled exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't capture keyboard interrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        _global_handler.handle_exception(exc_value, {
            "unhandled": True,
            "hook": "global_exception_hook"
        })
        
        # Call the default exception hook
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # Install the hook
    sys.excepthook = global_exception_hook
    logger.info("Global exception handler installed")
