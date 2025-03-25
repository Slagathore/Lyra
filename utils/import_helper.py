# g:\AI\Lyra\utils\import_helper.py
"""
Helper utilities for handling module imports.
Makes it easier to handle optional dependencies and provide fallbacks.
"""
import importlib
import sys
import logging
from typing import Optional, Callable, Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

def safe_import(module_name: str, package: Optional[str] = None):
    """
    Safely import a module with proper error handling.
    
    Args:
        module_name: Name of the module to import
        package: Optional package name for relative imports
        
    Returns:
        The imported module or None if import failed
    """
    try:
        return importlib.import_module(module_name, package)
    except ImportError as e:
        logger.warning(f"Could not import module '{module_name}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error importing module '{module_name}': {e}")
        return None

def import_optional_dependency(name: str, extra: str = "", min_version: Optional[str] = None):
    """
    Import an optional dependency, with a custom error message when missing.
    
    Args:
        name: Module name to import
        extra: Additional context for error message
        min_version: Minimum required version
        
    Returns:
        The imported module if successful
    
    Raises:
        ImportError: With a custom error message if module cannot be imported
    """
    try:
        module = importlib.import_module(name)
        
        # Check version if required
        if min_version and hasattr(module, "__version__"):
            if parse_version(module.__version__) < parse_version(min_version):
                msg = (
                    f"Module '{name}' has version {module.__version__} but "
                    f"version >= {min_version} is required. {extra}"
                )
                raise ImportError(msg)
        
        return module
    except ImportError:
        msg = f"Optional module '{name}' not found. {extra}"
        raise ImportError(msg)

def parse_version(version_str: str) -> Tuple:
    """
    Parse version string into comparable tuple.
    
    Args:
        version_str: Version string (e.g., "1.2.3")
        
    Returns:
        Tuple of integers representing the version
    """
    # FIXED: More robust version parsing to handle non-numeric components
    parts = []
    for part in version_str.split('.'):
        try:
            parts.append(int(part))
        except ValueError:
            # Handle non-numeric parts (like '1.2.3a')
            # Split at the first non-numeric character
            for i, char in enumerate(part):
                if not char.isdigit():
                    numeric_part = part[:i]
                    break
            else:
                numeric_part = part
                
            # Add the numeric part if it exists
            if numeric_part:
                parts.append(int(numeric_part))
            # Add a 0 for trailing parts to ensure consistent comparisons
            else:
                parts.append(0)
    
    return tuple(parts)

def import_or_stub(module_name: str, stub_factory: Callable[[], Any], package: Optional[str] = None):
    """
    Import a module or create a stub if import fails.
    
    Args:
        module_name: Name of the module to import
        stub_factory: Function that creates a stub object to use if import fails
        package: Optional package name for relative imports
        
    Returns:
        Either the imported module or a stub object
    """
    module = safe_import(module_name, package)
    if module is None:
        return stub_factory()
    return module

# Add the project's root directory to Python path
def add_project_root_to_path():
    """Add the project root directory to Python's import path."""
    import os
    from pathlib import Path
    
    # Get the project root (parent of utils directory)
    root_dir = Path(__file__).parent.parent
    
    # Add to path if not already there
    if str(root_dir) not in sys.path:
        sys.path.append(str(root_dir))
        logger.debug(f"Added {root_dir} to Python path")

# Call this when the module is imported
add_project_root_to_path()