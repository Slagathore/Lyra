"""
Implementation runner for Lyra to test and deploy code changes.
"""
import os
import sys
import importlib
import traceback
import datetime
from typing import Dict, List, Any, Tuple

class ImplementationRunner:
    """A class to test and run implementations of Lyra code"""

    def __init__(self, repo_path=None):
        """Initialize with the repository path"""
        self.repo_path = repo_path or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.src_path = os.path.join(self.repo_path, 'src')
        self.test_path = os.path.join(self.repo_path, 'tests')
        self.backup_dir = os.path.join(self.repo_path, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

    def backup_file(self, file_path: str) -> str:
        """Create a backup of a file before modification"""
        if not os.path.exists(file_path):
            return None

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.basename(file_path)
        backup_path = os.path.join(self.backup_dir, f"{filename}_{timestamp}.bak")

        try:
            with open(file_path, 'r', encoding='utf-8') as src:
                content = src.read()

            with open(backup_path, 'w', encoding='utf-8') as dst:
                dst.write(content)

            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None

    def test_implementation(self, module_path: str) -> Tuple[bool, Dict[str, Any]]:
        """Test an implementation by importing it"""
        try:
            # This is a relative import path like 'lyra.self_improvement.code_manager'
            start_time = datetime.datetime.now()
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)
            end_time = datetime.datetime.now()

            result = {
                "success": True,
                "import_time": (end_time - start_time).total_seconds(),
                "module": module_path,
                "error": None
            }
            return True, result
        except Exception as e:
            result = {
                "success": False,
                "import_time": 0,
                "module": module_path,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            return False, result

    def run_module(self, module_path: str, function: str = None, args: List = None, kwargs: Dict = None) -> Tuple[bool, Any]:
        """Run a specific function in a module"""
        try:
            # This is a relative import path like 'lyra.self_improvement.code_manager'
            if module_path in sys.modules:
                module = importlib.reload(sys.modules[module_path])
            else:
                module = importlib.import_module(module_path)

            if function:
                func = getattr(module, function)
                result = func(*(args or []), **(kwargs or {}))
                return True, result
            return True, None
        except Exception as e:
            print(f"Error running module: {e}")
            return False, None
