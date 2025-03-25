"""
Code management utilities for Lyra to analyze and modify its own codebase.
"""
import os
import sys
import importlib
import ast
from typing import Dict, List, Any

# Make GitPython optional
git = None
try:
    import git
except ImportError:
    # GitPython is optional - version control features will be limited
    pass

# Make autopep8 optional
autopep8 = None
try:
    import autopep8 
except ImportError:
    # autopep8 is optional - code formatting will be disabled
    pass

class CodeManager:
    """A class that allows Lyra to manage its own code"""

    def __init__(self, repo_path=None):
        """Initialize with the repository path"""
        self.repo_path = repo_path or os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        try:
            self.repo = git.Repo(self.repo_path)
        except Exception as e:
            print(f"Warning: Could not initialize Git repository: {e}")
            self.repo = None
        self.src_path = os.path.join(self.repo_path, 'src')

    def get_module_structure(self) -> Dict[str, Any]:
        """Get the structure of the Lyra module"""
        result = {}
        for root, dirs, files in os.walk(self.src_path):
            if "__pycache__" in root or ".git" in root:
                continue
            rel_path = os.path.relpath(root, self.repo_path)
            path_parts = rel_path.split(os.sep)
            current = result
            for part in path_parts:
                if part not in current:
                    current[part] = {}
                current = current[part]
            for file in files:
                if file.endswith(".py"):
                    current[file] = os.path.join(root, file)
        return result

    def get_file_ast(self, file_path: str) -> ast.Module:
        """Parse a Python file into an AST"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return ast.parse(content)

    def get_class_methods(self, file_path: str, class_name: str) -> List[str]:
        """Get methods of a class in a file"""
        tree = self.get_file_ast(file_path)
        methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append(item.name)
        return methods

    def modify_file(self, file_path: str, new_content: str, format_code: bool = True) -> bool:
        """Modify a file with new content"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if format_code and file_path.endswith('.py') and autopep8:
                    # Format the Python code if autopep8 is available
                    formatted_content = autopep8.fix_code(new_content)
                    f.write(formatted_content)
                else:
                    f.write(new_content)
            return True
        except Exception as e:
            print(f"Error modifying file: {e}")
            return False

    def get_file_content(self, file_path: str) -> str:
        """Get the content of a file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def reload_module(self, module_name: str) -> bool:
        """Reload a Python module to reflect changes"""
        try:
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            else:
                importlib.__import__(module_name)
            return True
        except Exception as e:
            print(f"Error reloading module: {e}")
            return False
            
    def commit_changes(self, message: str) -> bool:
        """Commit changes to the repository"""
        if not self.repo:
            print("Git repository not initialized")
            return False
            
        try:
            self.repo.git.add('.')
            self.repo.git.commit('-m', message)
            return True
        except Exception as e:
            print(f"Error committing changes: {e}")
            return False

    def push_changes(self, branch: str = 'master') -> bool:
        """Push changes to remote repository"""
        if not self.repo:
            print("Git repository not initialized")
            return False
            
        try:
            self.repo.git.push('origin', branch)
            return True
        except Exception as e:
            print(f"Error pushing changes: {e}")
            return False
