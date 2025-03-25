"""
Self-improvement module for Lyra

This module contains components that enable Lyra to analyze and improve its own code:
- code_manager: Tools for managing and modifying code
- reinforcement_learning: Learning from past code changes
- llm_advisor: Integration with external LLMs for code advice
- github_integration: GitHub repository interaction
- implementation_runner: Testing and running code implementations
- error_handler: Centralized error handling
"""

# Re-export key classes for easier imports
from .code_manager import CodeManager
from .reinforcement_learning import VintixRL
from .llm_advisor import LLMAdvisor
from .github_integration import GitHubIntegration
from .implementation_runner import ImplementationRunner
from .error_handler import ErrorHandler

__all__ = [
    'CodeManager', 
    'VintixRL', 
    'LLMAdvisor', 
    'GitHubIntegration', 
    'ImplementationRunner',
    'ErrorHandler'
]
