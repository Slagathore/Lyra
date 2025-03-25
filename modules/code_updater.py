import os
import re
import logging
import json
import time
from pathlib import Path
import difflib
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("code_updater")

class CodeUpdater:
    """
    Handles automatic implementation of code improvements suggested by the
    collaborative improvement module.
    """
    
    def __init__(self, config_path=None):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Path to record suggestions and implementations
        self.suggestions_path = Path(self.config.get("suggestions_path", "improvements/suggestions"))
        self.implementations_path = Path(self.config.get("implementations_path", "improvements/implementations"))
        
        # Create directories if they don't exist
        self.suggestions_path.mkdir(parents=True, exist_ok=True)
        self.implementations_path.mkdir(parents=True, exist_ok=True)
        
        # Track suggestions and implementations
        self.suggestions = {}
        self.implementations = {}
        
        # Load existing suggestions and implementations
        self._load_existing_data()
        
        logger.info("Code updater initialized")
    
    def _load_config(self, config_path):
        """Load configuration from file or use defaults."""
        default_config = {
            "max_file_size": 1024 * 1024,  # 1MB
            "backup_before_change": True,
            "suggestions_path": "improvements/suggestions",
            "implementations_path": "improvements/implementations",
            "allowed_modules": ["collaborative_improvement", "media_integration", "improvement_interface"],
            "restricted_dirs": ["system", "core", "security"],
            "auto_implementation_threshold": 0.8  # Only auto-implement if impact score is high
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
    
    def _load_existing_data(self):
        """Load existing suggestions and implementations from disk."""
        # Load suggestions
        for suggestion_file in self.suggestions_path.glob("*.json"):
            try:
                with open(suggestion_file, 'r') as f:
                    suggestion_data = json.load(f)
                    suggestion_id = suggestion_file.stem
                    self.suggestions[suggestion_id] = suggestion_data
            except Exception as e:
                logger.warning(f"Error loading suggestion file {suggestion_file}: {e}")
        
        # Load implementations
        for impl_file in self.implementations_path.glob("*.json"):
            try:
                with open(impl_file, 'r') as f:
                    impl_data = json.load(f)
                    impl_id = impl_file.stem
                    self.implementations[impl_id] = impl_data
            except Exception as e:
                logger.warning(f"Error loading implementation file {impl_file}: {e}")
        
        logger.info(f"Loaded {len(self.suggestions)} suggestions and {len(self.implementations)} implementations")
    
    def save_suggestion(self, suggestion_data):
        """Save a code improvement suggestion."""
        suggestion_id = f"suggestion_{int(time.time())}_{suggestion_data.get('module', 'unknown')}"
        
        # Add metadata
        suggestion_data["id"] = suggestion_id
        suggestion_data["timestamp"] = time.time()
        suggestion_data["status"] = "pending"
        
        # Save to suggestions dictionary
        self.suggestions[suggestion_id] = suggestion_data
        
        # Save to file
        suggestion_file = self.suggestions_path / f"{suggestion_id}.json"
        try:
            with open(suggestion_file, 'w') as f:
                json.dump(suggestion_data, f, indent=2)
            logger.info(f"Saved suggestion {suggestion_id} to {suggestion_file}")
            return suggestion_id
        except Exception as e:
            logger.error(f"Error saving suggestion {suggestion_id}: {e}")
            return None
    
    def save_implementation(self, implementation_data):
        """Save a code improvement implementation."""
        implementation_id = f"implementation_{int(time.time())}_{implementation_data.get('module', 'unknown')}"
        
        # Add metadata
        implementation_data["id"] = implementation_id
        implementation_data["timestamp"] = time.time()
        implementation_data["status"] = "completed"
        
        # Save to implementations dictionary
        self.implementations[implementation_id] = implementation_data
        
        # Save to file
        implementation_file = self.implementations_path / f"{implementation_id}.json"
        try:
            with open(implementation_file, 'w') as f:
                json.dump(implementation_data, f, indent=2)
            logger.info(f"Saved implementation {implementation_id} to {implementation_file}")
            return implementation_id
        except Exception as e:
            logger.error(f"Error saving implementation {implementation_id}: {e}")
            return None
    
    def is_safe_to_modify(self, file_path):
        """Check if it's safe to modify a file."""
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            logger.warning(f"File does not exist: {file_path}")
            return False
        
        # Check file size
        if path.stat().st_size > self.config["max_file_size"]:
            logger.warning(f"File too large to modify safely: {file_path}")
            return False
        
        # Check if in restricted directory
        for restricted_dir in self.config["restricted_dirs"]:
            if restricted_dir in str(path):
                logger.warning(f"File in restricted directory: {file_path}")
                return False
        
        # Check if file is part of an allowed module
        allowed = False
        for allowed_module in self.config["allowed_modules"]:
            if allowed_module in str(path):
                allowed = True
                break
        
        if not allowed:
            logger.warning(f"File not in an allowed module: {file_path}")
            return False
        
        return True
    
    def create_backup(self, file_path):
        """Create a backup of a file before modifying it."""
        path = Path(file_path)
        if not path.exists():
            return False
        
        backup_dir = path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"{path.name}.{int(time.time())}.bak"
        try:
            with open(path, 'r') as source, open(backup_path, 'w') as target:
                target.write(source.read())
            logger.info(f"Created backup of {file_path} at {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating backup of {file_path}: {e}")
            return False
    
    def apply_suggestion(self, suggestion_id, auto_mode=False):
        """
        Apply a code improvement suggestion.
        Returns the implementation ID if successful, None otherwise.
        """
        # Get the suggestion
        suggestion = self.suggestions.get(suggestion_id)
        if not suggestion:
            logger.error(f"Suggestion not found: {suggestion_id}")
            return None
        
        # Check if already implemented
        if suggestion.get("status") == "implemented":
            logger.warning(f"Suggestion already implemented: {suggestion_id}")
            return None
        
        # Get file path
        module = suggestion.get("module")
        file_path = self._get_file_path_for_module(module)
        if not file_path:
            logger.error(f"Could not determine file path for module: {module}")
            return None
        
        # Check if safe to modify
        if not self.is_safe_to_modify(file_path):
            logger.error(f"Not safe to modify file: {file_path}")
            return None
        
        # Check auto-implementation threshold
        if auto_mode and suggestion.get("estimated_impact", 0) < self.config["auto_implementation_threshold"]:
            logger.info(f"Impact score too low for auto-implementation: {suggestion.get('estimated_impact')}")
            return None
        
        # Create backup if configured
        if self.config["backup_before_change"]:
            self.create_backup(file_path)
        
        # Apply the change
        success, diff = self._apply_code_change(file_path, suggestion)
        
        if not success:
            logger.error(f"Failed to apply suggestion {suggestion_id} to {file_path}")
            return None
        
        # Update suggestion status
        suggestion["status"] = "implemented"
        
        # Save updated suggestion
        suggestion_file = self.suggestions_path / f"{suggestion_id}.json"
        with open(suggestion_file, 'w') as f:
            json.dump(suggestion, f, indent=2)
        
        # Create implementation record
        implementation_data = {
            "suggestion_id": suggestion_id,
            "file_path": str(file_path),
            "module": module,
            "diff": diff,
            "timestamp": time.time(),
            "auto_mode": auto_mode
        }
        
        # Save implementation
        implementation_id = self.save_implementation(implementation_data)
        
        logger.info(f"Successfully applied suggestion {suggestion_id} to {file_path}")
        return implementation_id
    
    def _get_file_path_for_module(self, module):
        """Determine the file path for a module."""
        module_to_file = {
            "text_processing": "modules/collaborative_improvement.py",
            "conversation_flow": "modules/improvement_interface.py",
            "learning_system": "modules/collaborative_improvement.py",
            "data_storage": "modules/collaborative_improvement.py",
            "feedback_integration": "modules/collaborative_improvement.py",
            "media_processing": "modules/media_integration.py"
        }
        
        file_path = module_to_file.get(module)
        if file_path:
            return Path(file_path)
        return None
    
    def _apply_code_change(self, file_path, suggestion) -> Tuple[bool, str]:
        """
        Apply a code change based on a suggestion.
        Returns a tuple of (success, diff).
        """
        # Read the file
        try:
            with open(file_path, 'r') as f:
                original_content = f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return False, ""
        
        # Get the code example and description
        code_example = suggestion.get("code_example", "")
        description = suggestion.get("description", "")
        
        # Find the appropriate insertion point
        # This is a simplified implementation - in a real system, 
        # this would use AST parsing to find the right location
        
        # For now, just try to find the class or function that matches the module
        module = suggestion.get("module")
        
        # Define patterns to look for based on module
        patterns = {
            "text_processing": r"class TextProcessor",
            "conversation_flow": r"def process_message",
            "learning_system": r"class DeepLearner",
            "data_storage": r"def save_state",
            "feedback_integration": r"class LLMConsultant",
            "media_processing": r"class MediaIntegrator"
        }
        
        pattern = patterns.get(module)
        if not pattern:
            logger.error(f"No pattern defined for module: {module}")
            return False, ""
        
        # Find the pattern
        match = re.search(pattern, original_content)
        if not match:
            logger.error(f"Could not find pattern '{pattern}' in file {file_path}")
            return False, ""
        
        # Find the end of the class/function
        start_pos = match.start()
        
        # Find the class or function definition
        class_or_func_line = original_content[start_pos:].split("\n")[0]
        
        # Insert the code after the class/function definition
        indent_match = re.match(r'^(\s*)', class_or_func_line)
        indent = indent_match.group(1) if indent_match else ""
        # Add one level of indentation
        indent += "    "
        
        # Format the code example with the proper indentation
        formatted_code = "\n\n" + indent + f"# Auto-implemented improvement: {description}\n"
        for line in code_example.split("\n"):
            formatted_code += indent + line + "\n"
        
        # Insert the code
        insert_pos = start_pos + len(class_or_func_line) + 1  # +1 for the newline
        new_content = original_content[:insert_pos] + formatted_code + original_content[insert_pos:]
        
        # Generate diff
        diff = list(difflib.unified_diff(
            original_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=str(file_path),
            tofile=str(file_path) + " (modified)"
        ))
        diff_str = "".join(diff)
        
        # Write the modified content
        try:
            with open(file_path, 'w') as f:
                f.write(new_content)
            logger.info(f"Successfully modified {file_path}")
            return True, diff_str
        except Exception as e:
            logger.error(f"Error writing to file {file_path}: {e}")
            return False, diff_str
    
    def get_pending_suggestions(self):
        """Get all pending suggestions."""
        return {k: v for k, v in self.suggestions.items() if v.get("status") == "pending"}
    
    def get_implemented_suggestions(self):
        """Get all implemented suggestions."""
        return {k: v for k, v in self.suggestions.items() if v.get("status") == "implemented"}
    
    def get_all_suggestions(self):
        """Get all suggestions."""
        return self.suggestions
    
    def get_all_implementations(self):
        """Get all implementations."""
        return self.implementations
