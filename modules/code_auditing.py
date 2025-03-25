"""
Code Auditing module for Lyra
Enables self-code review and improvement capabilities
"""

import os
import re
import ast
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
import importlib.util
import inspect

# Set up logging
logger = logging.getLogger("code_auditing")

class CodeFile:
    """Represents a Python code file for analysis"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = None
        self.ast = None
        self.imports = []
        self.classes = []
        self.functions = []
        self.issues = []
        self.last_analyzed = None
        self.metrics = {}
        
        # Load file content
        self.load_content()
    
    def load_content(self) -> bool:
        """Load content from file"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except Exception as e:
            logger.error(f"Error loading file {self.file_path}: {e}")
            self.content = None
            return False
    
    def parse(self) -> bool:
        """Parse the file and build AST"""
        if not self.content:
            return False
            
        try:
            self.ast = ast.parse(self.content)
            self._extract_structure()
            self.last_analyzed = time.time()
            return True
        except SyntaxError as e:
            self.issues.append({
                "type": "syntax_error",
                "line": e.lineno,
                "message": str(e)
            })
            return False
        except Exception as e:
            logger.error(f"Error parsing {self.file_path}: {e}")
            return False
    
    def _extract_structure(self):
        """Extract structural elements from AST"""
        self.imports = []
        self.classes = []
        self.functions = []
        
        if not self.ast:
            return
            
        for node in ast.walk(self.ast):
            if isinstance(node, ast.Import):
                for name in node.names:
                    self.imports.append({
                        "name": name.name,
                        "alias": name.asname,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for name in node.names:
                    self.imports.append({
                        "name": f"{module}.{name.name}",
                        "alias": name.asname,
                        "line": node.lineno
                    })
            elif isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        methods.append({
                            "name": item.name,
                            "line": item.lineno,
                            "args": self._get_function_args(item)
                        })
                
                self.classes.append({
                    "name": node.name,
                    "line": node.lineno,
                    "methods": methods,
                    "bases": [self._format_expr(base) for base in node.bases]
                })
            elif isinstance(node, ast.FunctionDef) and not isinstance(node.parent, ast.ClassDef):
                self.functions.append({
                    "name": node.name,
                    "line": node.lineno,
                    "args": self._get_function_args(node)
                })
    
    def _get_function_args(self, func_node) -> List[str]:
        """Get function arguments as strings"""
        args = []
        for arg in func_node.args.args:
            args.append(arg.arg)
        return args
    
    def _format_expr(self, expr) -> str:
        """Format a node as a string (simplified)"""
        if isinstance(expr, ast.Name):
            return expr.id
        elif isinstance(expr, ast.Attribute):
            base = self._format_expr(expr.value)
            return f"{base}.{expr.attr}"
        else:
            return "..."
    
    def compute_metrics(self) -> Dict[str, Any]:
        """Compute code quality metrics"""
        if not self.content:
            return {}
            
        lines = self.content.split('\n')
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        
        self.metrics = {
            "total_lines": len(lines),
            "code_lines": len(code_lines),
            "comment_lines": sum(1 for line in lines if line.strip().startswith('#')),
            "blank_lines": sum(1 for line in lines if not line.strip()),
            "classes": len(self.classes),
            "functions": len(self.functions),
            "imports": len(self.imports),
            "average_line_length": sum(len(line) for line in code_lines) / len(code_lines) if code_lines else 0
        }
        
        return self.metrics
    
    def run_static_analysis(self) -> List[Dict[str, Any]]:
        """Run static analysis to find issues"""
        self.issues = []
        
        if not self.content:
            return self.issues
            
        # Check for long lines
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            if len(line) > 100:
                self.issues.append({
                    "type": "style",
                    "line": i + 1,
                    "message": f"Line too long ({len(line)} > 100 characters)"
                })
        
        # Check for undefined names (basic)
        if self.ast:
            defined_names = set()
            for node in ast.walk(self.ast):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    defined_names.add(node.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    defined_names.add(node.id)
            
            for node in ast.walk(self.ast):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    if node.id not in defined_names and node.id not in __builtins__:
                        # Check if it might be an import
                        import_match = False
                        for imp in self.imports:
                            if imp["name"] == node.id or imp["alias"] == node.id:
                                import_match = True
                                break
                        
                        if not import_match:
                            self.issues.append({
                                "type": "possible_undefined",
                                "line": getattr(node, "lineno", 0),
                                "message": f"Possibly undefined name: {node.id}"
                            })
        
        # Run external linters if available
        self._run_pylint()
        self._run_flake8()
        
        return self.issues
    
    def _run_pylint(self):
        """Run pylint on the file if available"""
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", self.file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return  # No issues
                
            import json
            try:
                pylint_issues = json.loads(result.stdout)
                for issue in pylint_issues:
                    self.issues.append({
                        "type": "pylint",
                        "line": issue.get("line", 0),
                        "message": issue.get("message", "Unknown pylint issue"),
                        "symbol": issue.get("symbol", "")
                    })
            except:
                pass  # Could not parse pylint output
                
        except:
            pass  # pylint not available or other error
    
    def _run_flake8(self):
        """Run flake8 on the file if available"""
        try:
            result = subprocess.run(
                ["flake8", "--format=default", self.file_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return  # No issues
                
            # Parse flake8 output (format: file:line:char: code message)
            pattern = r'.*:(\d+):(\d+): ([A-Z]\d+) (.*)'
            for line in result.stdout.split('\n'):
                match = re.match(pattern, line)
                if match:
                    line_num, char, code, message = match.groups()
                    self.issues.append({
                        "type": "flake8",
                        "line": int(line_num),
                        "message": f"{code}: {message}"
                    })
                    
        except:
            pass  # flake8 not available or other error
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the file analysis"""
        if not self.last_analyzed:
            self.parse()
            self.compute_metrics()
            self.run_static_analysis()
            
        return {
            "file_path": self.file_path,
            "last_analyzed": self.last_analyzed,
            "metrics": self.metrics,
            "issue_count": len(self.issues),
            "classes": [cls["name"] for cls in self.classes],
            "functions": [func["name"] for func in self.functions],
            "imports": [imp["name"] for imp in self.imports]
        }
    
    def suggest_improvements(self, llm_interface=None) -> List[Dict[str, Any]]:
        """
        Generate improvement suggestions, optionally using LLM
        
        Args:
            llm_interface: Optional LLM interface for generating improvements
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        
        # Generate basic suggestions based on metrics and issues
        if self.metrics.get("average_line_length", 0) > 80:
            suggestions.append({
                "type": "style",
                "message": "Consider breaking up long lines for better readability"
            })
            
        if self.metrics.get("comment_lines", 0) / max(1, self.metrics.get("code_lines", 1)) < 0.1:
            suggestions.append({
                "type": "documentation",
                "message": "Consider adding more comments to explain complex logic"
            })
            
        # Generate suggestions based on issues
        error_types = [issue["type"] for issue in self.issues]
        if "syntax_error" in error_types:
            suggestions.append({
                "type": "critical",
                "message": "Fix syntax errors before making other improvements"
            })
            
        undefined_vars = [issue for issue in self.issues if issue["type"] == "possible_undefined"]
        if undefined_vars:
            suggestions.append({
                "type": "bug",
                "message": f"Check possibly undefined variables: {', '.join(set(issue['message'].split(':')[1].strip() for issue in undefined_vars))}"
            })
        
        # Use LLM for more advanced suggestions if available
        if llm_interface:
            llm_suggestions = self._get_llm_suggestions(llm_interface)
            suggestions.extend(llm_suggestions)
        
        return suggestions
    
    def _get_llm_suggestions(self, llm_interface) -> List[Dict[str, Any]]:
        """Get code improvement suggestions from an LLM"""
        suggestions = []
        
        # Create a prompt with relevant context
        prompt = f"""Analyze the following Python code and suggest improvements:

```python
{self.content}
```

Issues identified:
{', '.join(issue['message'] for issue in self.issues[:5])}

Please provide 3-5 concrete, actionable suggestions to improve this code.
Focus on:
1. Bug fixes or potential issues
2. Performance improvements
3. Readability enhancements
4. Better practices or patterns

Format each suggestion as a single paragraph explaining the issue and how to fix it.
"""
        
        try:
            # Generate suggestions using the LLM
            response = llm_interface.generate_text(prompt, max_tokens=1000)
            
            # Parse suggestions (simple approach - in a real system, would use more robust parsing)
            suggestion_texts = re.split(r'\n\s*\d+\.|\n\s*-', response)
            for suggestion_text in suggestion_texts[1:]:  # Skip first split which is empty or intro text
                suggestion_text = suggestion_text.strip()
                if suggestion_text:
                    suggestions.append({
                        "type": "llm_suggestion",
                        "message": suggestion_text
                    })
            
        except Exception as e:
            logger.error(f"Error getting LLM suggestions: {e}")
            suggestions.append({
                "type": "error",
                "message": f"Could not generate LLM suggestions: {str(e)}"
            })
        
        return suggestions

class ModuleAnalyzer:
    """Analyzes a Python module for dependencies and structure"""
    
    def __init__(self, module_name: str, module_path: str = None):
        self.module_name = module_name
        self.module_path = module_path
        self.module = None
        self.dependencies = set()
        self.reverse_dependencies = set()
        self.functions = []
        self.classes = []
        self.issues = []
    
    def load_module(self) -> bool:
        """Load the module for analysis"""
        try:
            if self.module_path:
                # Load from file
                spec = importlib.util.spec_from_file_location(self.module_name, self.module_path)
                if not spec:
                    logger.error(f"Could not create spec for {self.module_path}")
                    return False
                    
                self.module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(self.module)
            else:
                # Import by name
                self.module = importlib.import_module(self.module_name)
                
            return True
        except Exception as e:
            logger.error(f"Error loading module {self.module_name}: {e}")
            self.issues.append({
                "type": "import_error",
                "message": f"Could not import module: {str(e)}"
            })
            return False
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze the module structure and dependencies"""
        if not self.module:
            if not self.load_module():
                return {"error": "Could not load module"}
        
        # Get module source file
        module_file = getattr(self.module, "__file__", None)
        if not module_file:
            self.issues.append({
                "type": "analysis_error",
                "message": "Could not locate module source file"
            })
            return {"error": "No source file found"}
            
        # Analyze with CodeFile
        code_file = CodeFile(module_file)
        code_file.parse()
        code_file.compute_metrics()
        code_file.run_static_analysis()
        
        # Extract module-level elements
        self._extract_module_elements()
        
        # Gather dependency information
        self._gather_dependencies()
        
        # Combine with issues from code analysis
        self.issues.extend(code_file.issues)
        
        return {
            "module_name": self.module_name,
            "module_file": module_file,
            "functions": self.functions,
            "classes": self.classes,
            "dependencies": list(self.dependencies),
            "reverse_dependencies": list(self.reverse_dependencies),
            "metrics": code_file.metrics,
            "issues": self.issues
        }
    
    def _extract_module_elements(self):
        """Extract functions and classes from the module"""
        if not self.module:
            return
            
        # Get functions
        self.functions = []
        for name, obj in inspect.getmembers(self.module, inspect.isfunction):
            if obj.__module__ == self.module.__name__:
                self.functions.append({
                    "name": name,
                    "signature": str(inspect.signature(obj)),
                    "doc": inspect.getdoc(obj) or ""
                })
        
        # Get classes
        self.classes = []
        for name, obj in inspect.getmembers(self.module, inspect.isclass):
            if obj.__module__ == self.module.__name__:
                methods = []
                for method_name, method_obj in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith("_") or method_name in ("__init__", "__str__", "__repr__"):
                        methods.append({
                            "name": method_name,
                            "signature": str(inspect.signature(method_obj)),
                            "doc": inspect.getdoc(method_obj) or ""
                        })
                        
                self.classes.append({
                    "name": name,
                    "methods": methods,
                    "doc": inspect.getdoc(obj) or ""
                })
    
    def _gather_dependencies(self):
        """Gather module dependencies"""
        if not self.module:
            return
            
        # Get direct imports
        self.dependencies = set()
        
        # Check module source
        module_file = getattr(self.module, "__file__", None)
        if module_file and module_file.endswith(".py"):
            try:
                with open(module_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            self.dependencies.add(name.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            self.dependencies.add(node.module.split('.')[0])
            except Exception as e:
                logger.error(f"Error analyzing imports: {e}")
        
        # Try to find reverse dependencies
        # This is harder - would need to scan all modules
        # For now, just a placeholder
        self.reverse_dependencies = set()

class CodeAuditor:
    """
    Enables Lyra to audit and improve her own code
    """
    
    def __init__(self, base_path: str = None):
        self.base_path = base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.analyzed_files = {}  # path -> analysis results
        self.improvement_suggestions = {}  # path -> suggestions
        self.llm_interface = None
    
    def set_llm_interface(self, llm_interface):
        """Set LLM interface for advanced analysis"""
        self.llm_interface = llm_interface
        logger.info("LLM interface set for code auditing")
    
    def scan_project_structure(self) -> Dict[str, Any]:
        """Scan the project structure to find Python files"""
        python_files = []
        module_dirs = []
        
        for root, dirs, files in os.walk(self.base_path):
            # Skip common directories to exclude
            if any(excluded in root for excluded in ['.git', '__pycache__', '.venv', 'venv', 'env']):
                continue
                
            # Check if this is a Python module directory
            if '__init__.py' in files:
                rel_path = os.path.relpath(root, self.base_path)
                module_dirs.append(rel_path)
            
            # Find Python files
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.base_path)
                    python_files.append(rel_path)
        
        return {
            "python_files": python_files,
            "module_dirs": module_dirs,
            "base_path": self.base_path
        }
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a specific Python file
        
        Args:
            file_path: Path to the Python file (relative or absolute)
            
        Returns:
            Analysis results
        """
        # Handle relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.base_path, file_path)
            
        # Check if file exists
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        # Create and analyze code file
        code_file = CodeFile(file_path)
        parsed = code_file.parse()
        
        if not parsed:
            return {
                "file_path": file_path,
                "status": "parse_error",
                "issues": code_file.issues
            }
            
        # Run analysis
        code_file.compute_metrics()
        code_file.run_static_analysis()
        
        # Store analysis results
        analysis = {
            "file_path": file_path,
            "status": "analyzed",
            "metrics": code_file.metrics,
            "issues": code_file.issues,
            "classes": code_file.classes,
            "functions": code_file.functions,
            "imports": code_file.imports
        }
        
        self.analyzed_files[file_path] = analysis
        return analysis
    
    def analyze_module(self, module_name: str) -> Dict[str, Any]:
        """
        Analyze a Python module
        
        Args:
            module_name: Name of the module to analyze
            
        Returns:
            Analysis results
        """
        module_analyzer = ModuleAnalyzer(module_name)
        result = module_analyzer.analyze()
        
        # If module has a file, store its analysis
        if "module_file" in result and not "error" in result:
            self.analyzed_files[result["module_file"]] = {
                "file_path": result["module_file"],
                "status": "analyzed",
                "metrics": result.get("metrics", {}),
                "issues": result.get("issues", []),
                "module_name": module_name
            }
            
        return result
    
    def suggest_improvements(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Suggest improvements for a specific file
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of improvement suggestions
        """
        # Handle relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.base_path, file_path)
            
        # Check if we've already analyzed this file
        if file_path not in self.analyzed_files:
            self.analyze_file(file_path)
            
        # If analysis failed, return empty suggestions
        if self.analyzed_files[file_path].get("status") == "parse_error":
            return []
            
        # Create code file for suggestion generation
        code_file = CodeFile(file_path)
        code_file.parse()
        
        # Generate suggestions
        suggestions = code_file.suggest_improvements(self.llm_interface)
        
        # Store suggestions
        self.improvement_suggestions[file_path] = suggestions
        
        return suggestions
    
    def fix_issues(self, file_path: str, issue_types: List[str] = None) -> Dict[str, Any]:
        """
        Attempt to automatically fix issues in a file
        
        Args:
            file_path: Path to the Python file
            issue_types: Types of issues to fix (e.g., ["style", "imports"])
            
        Returns:
            Results of attempted fixes
        """
        # Handle relative paths
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.base_path, file_path)
            
        # Check if file exists
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
            
        # Default to all issue types if none specified
        if not issue_types:
            issue_types = ["style", "imports", "unused", "formatting"]
            
        fixes_applied = []
        fix_count = 0
        
        # Try using external auto-formatters if available
        if "formatting" in issue_types:
            # Try black
            try:
                result = subprocess.run(
                    ["black", file_path],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    fixes_applied.append("Applied black code formatter")
                    fix_count += 1
            except:
                logger.info("black formatter not available")
            
            # Try isort for import sorting
            if "imports" in issue_types:
                try:
                    result = subprocess.run(
                        ["isort", file_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        fixes_applied.append("Applied isort import sorter")
                        fix_count += 1
                except:
                    logger.info("isort not available")
            
            # Try autoflake for unused imports
            if "unused" in issue_types:
                try:
                    result = subprocess.run(
                        ["autoflake", "--in-place", "--remove-unused-variables", file_path],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        fixes_applied.append("Applied autoflake to remove unused imports/variables")
                        fix_count += 1
                except:
                    logger.info("autoflake not available")
        
        # Re-analyze the file after fixes
        updated_analysis = None
        if fix_count > 0:
            updated_analysis = self.analyze_file(file_path)
        
        return {
            "file_path": file_path,
            "fixes_applied": fixes_applied,
            "fix_count": fix_count,
            "updated_analysis": updated_analysis
        }
    
    def get_audit_summary(self) -> Dict[str, Any]:
        """Get a summary of all analyzed files and their issues"""
        if not self.analyzed_files:
            return {"message": "No files have been analyzed yet"}
            
        total_issues = 0
        issue_types = {}
        file_summaries = []
        
        # Compile summary data
        for file_path, analysis in self.analyzed_files.items():
            issues = analysis.get("issues", [])
            total_issues += len(issues)
            
            # Count issue types
            for issue in issues:
                issue_type = issue.get("type", "unknown")
                if issue_type in issue_types:
                    issue_types[issue_type] += 1
                else:
                    issue_types[issue_type] = 1
            
            # Create file summary
            file_summaries.append({
                "file_path": file_path,
                "issue_count": len(issues),
                "metrics": analysis.get("metrics", {})
            })
        
        # Sort files by issue count (most issues first)
        file_summaries.sort(key=lambda x: x["issue_count"], reverse=True)
        
        return {
            "files_analyzed": len(self.analyzed_files),
            "total_issues": total_issues,
            "issue_types": issue_types,
            "file_summaries": file_summaries
        }
    
    def audit_specific_issue(self, issue_type: str) -> Dict[str, Any]:
        """
        Audit for a specific type of issue across all analyzed files
        
        Args:
            issue_type: Type of issue to look for
            
        Returns:
            Audit results for that issue type
        """
        if not self.analyzed_files:
            return {"message": "No files have been analyzed yet"}
            
        matching_issues = []
        
        for file_path, analysis in self.analyzed_files.items():
            issues = analysis.get("issues", [])
            
            for issue in issues:
                if issue.get("type") == issue_type:
                    matching_issues.append({
                        "file_path": file_path,
                        "line": issue.get("line", 0),
                        "message": issue.get("message", "Unknown issue")
                    })
        
        return {
            "issue_type": issue_type,
            "count": len(matching_issues),
            "issues": matching_issues
        }
    
    def analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze project dependencies and imports"""
        if not self.analyzed_files:
            # Analyze all Python files first
            structure = self.scan_project_structure()
            for file_path in structure["python_files"]:
                self.analyze_file(file_path)
        
        # Extract all imports
        all_imports = {}
        
        for file_path, analysis in self.analyzed_files.items():
            imports = analysis.get("imports", [])
            
            for imp in imports:
                import_name = imp.get("name", "").split('.')[0]  # Get top-level package
                
                if import_name:
                    if import_name in all_imports:
                        all_imports[import_name].append(file_path)
                    else:
                        all_imports[import_name] = [file_path]
        
        # Categorize imports
        std_lib_modules = set(sys.builtin_module_names)
        std_lib_modules.update([
            'os', 'sys', 'time', 'datetime', 'logging', 'json', 're', 'math',
            'random', 'collections', 'functools', 'itertools', 'pathlib',
            'threading', 'multiprocessing', 'typing', 'inspect', 'ast'
        ])
        
        internal_modules = []
        external_modules = []
        standard_library = []
        
        for module_name, files in all_imports.items():
            if module_name in std_lib_modules:
                standard_library.append({
                    "name": module_name,
                    "usage_count": len(files),
                    "files": files
                })
            elif os.path.exists(os.path.join(self.base_path, module_name)) or os.path.exists(os.path.join(self.base_path, "modules", module_name)):
                internal_modules.append({
                    "name": module_name,
                    "usage_count": len(files),
                    "files": files
                })
            else:
                external_modules.append({
                    "name": module_name,
                    "usage_count": len(files),
                    "files": files
                })
        
        return {
            "standard_library": standard_library,
            "internal_modules": internal_modules,
            "external_modules": external_modules,
            "total_imports": len(all_imports)
        }

    def audit_self(self) -> Dict[str, Any]:
        """Run an audit on Lyra's own code"""
        # First, scan the project structure
        structure = self.scan_project_structure()
        
        # Analyze core modules first
        core_modules = [
            "metacognition.py", 
            "deep_memory.py", 
            "emotional_core.py",
            "cognitive_integration.py",
            "extended_thinking.py",
            "fallback_llm.py",
            "code_auditing.py"
        ]
        
        # Adjust paths to include modules directory
        core_module_paths = [os.path.join("modules", module) for module in core_modules]
        
        # Analyze core modules
        core_analyses = {}
        for module_path in core_module_paths:
            if module_path in structure["python_files"]:
                analysis = self.analyze_file(module_path)
                core_analyses[module_path] = analysis
        
        # Generate a summary report
        summary = self.get_audit_summary()
        
        # Generate suggestions for modules with issues
        for module_path, analysis in core_analyses.items():
            if analysis.get("issues", []):
                suggestions = self.suggest_improvements(module_path)
                self.improvement_suggestions[module_path] = suggestions
        
        return {
            "summary": summary,
            "core_analyses": core_analyses,
            "improvement_suggestions": self.improvement_suggestions,
            "project_structure": structure
        }

# Singleton instance
_code_auditor_instance = None

def get_instance(base_path: str = None):
    """Get the singleton instance of CodeAuditor"""
    global _code_auditor_instance
    if _code_auditor_instance is None:
        _code_auditor_instance = CodeAuditor(base_path)
    elif base_path is not None and _code_auditor_instance.base_path != base_path:
        # Create a new instance if base path changes
        _code_auditor_instance = CodeAuditor(base_path)
    return _code_auditor_instance
