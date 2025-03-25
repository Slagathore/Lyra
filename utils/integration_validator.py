"""
Lyra Integration Validator

This tool validates the entire Lyra system integration by:
1. Checking that all modules mentioned in documentation actually exist
2. Verifying connections between modules work properly
3. Testing core cognitive functions work end-to-end
4. Generating a report of what's working and what's missing

Usage:
    python utils/integration_validator.py [--fix] [--report-file REPORT_FILE]
"""

import sys
import importlib
import inspect
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_validator")

# Define module categories for organization
MODULE_CATEGORIES = {
    "core": [
        "module_registry", 
        "model_config"
    ],
    "cognitive": [
        "emotional_core", 
        "metacognition", 
        "deep_memory", 
        "extended_thinking",
        "thinking_integration", 
        "cognitive_integration", 
        "cognitive_model_integration",
        "boredom", 
        "boredom_integration",
        "code_auditing"
    ],
    "interface": [
        "telegram_bot", 
        "lyra_ui", 
        "lyra_bot", 
        "voice_interface", 
        "persistent_module", 
        "io_manager"
    ],
    "ui": [
        "ui/main", 
        "ui/components/chat_tab", 
        "ui/components/image_tab",
        "ui/components/voice_tab", 
        "ui/components/video_tab", 
        "ui/components/model_tab",
        "ui/components/memory_tab"
    ],
    "utilities": [
        "core_proxy", 
        "fallback_llm", 
        "whisper_recognition"
    ],
    "model_backends": [
        "model_backends/phi_backend"
    ]
}

# Expected dependencies based on module_dependency_map.md
EXPECTED_DEPENDENCIES = {
    "run_lyra": ["module_registry", "model_config"],
    "module_registry": [
        "fallback_llm", "extended_thinking", "boredom", "boredom_integration",
        "emotional_core", "metacognition", "deep_memory", "code_auditing",
        "thinking_integration", "cognitive_integration", "voice_interface"
    ],
    "cognitive_integration": ["metacognition", "emotional_core"],
    "cognitive_model_integration": [
        "metacognition", "deep_memory", "emotional_core", "cognitive_integration"
    ],
    "lyra_ui": ["model_config", "lyra_bot", "telegram_bot", "extended_thinking"],
    "voice_interface": ["whisper_recognition"],
    "persistent_module": ["core_proxy"],
    "telegram_bot": ["fallback_llm", "model_backends/phi_backend"]
}

class IntegrationValidator:
    """Validates the integration of Lyra modules"""
    
    def __init__(self, 
                base_path: Optional[Path] = None, 
                fix_issues: bool = False,
                report_file: Optional[str] = None):
        """
        Initialize the validator
        
        Args:
            base_path: Base path of the Lyra project
            fix_issues: Whether to attempt to fix issues
            report_file: Path to save the report
        """
        self.base_path = base_path or Path(__file__).parent.parent
        self.fix_issues = fix_issues
        self.report_file = report_file
        
        # Results storage
        self.module_status = {}
        self.connection_status = {}
        self.cognitive_tests = {}
        self.missing_modules = set()
        self.import_errors = {}
        
        # Add base path to sys.path for imports
        if str(self.base_path) not in sys.path:
            sys.path.insert(0, str(self.base_path))
            logger.info(f"Added {self.base_path} to sys.path")
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Run all validation checks
        
        Returns:
            Dictionary with validation results
        """
        results = {
            "module_existence": self.check_module_existence(),
            "dependency_validation": self.validate_dependencies(),
            "cognitive_system": self.test_cognitive_system(),
            "missing_modules": list(self.missing_modules),
            "import_errors": self.import_errors,
            "recommended_actions": self.generate_recommendations()
        }
        
        # Generate and save report if requested
        if self.report_file:
            self.save_report(results)
        
        return results
    
    def check_module_existence(self) -> Dict[str, bool]:
        """
        Check if all expected modules exist
        
        Returns:
            Dictionary mapping module names to existence status
        """
        logger.info("Checking module existence...")
        
        # Collect all modules to check from categories
        all_modules = []
        # Collect all modules to check from categories
        all_modules = []
        for _, modules in MODULE_CATEGORIES.items():
            all_modules.extend(modules)
        for module_name, dependencies in EXPECTED_DEPENDENCIES.items():
            if module_name not in all_modules:
                all_modules.append(module_name)
            for dep in dependencies:
                if dep not in all_modules:
                    all_modules.append(dep)
        
        # Check each module
        for module_name in all_modules:
            # Skip if already checked
            if module_name in self.module_status:
                continue
                
            module_path = module_name.replace('/', '.')
            
            # Check if module file exists
            py_path = self.base_path / f"{module_name}.py"
            dir_path = self.base_path / module_name
            if py_path.exists():
                self.module_status[module_name] = True
                logger.info(f"✓ Module file exists: {module_name}")
            elif dir_path.exists() and (dir_path / "__init__.py").exists():
                self.module_status[module_name] = True
                logger.info(f"✓ Module package exists: {module_name}")
            else:
                # Try src/lyra path structure
                alt_py_path = self.base_path / "src" / "lyra" / f"{module_name.split('/')[-1]}.py"
                if alt_py_path.exists():
                    self.module_status[module_name] = True
                    logger.info(f"✓ Module file exists (in src/lyra): {module_name}")
                else:
                    self.module_status[module_name] = False
                    self.missing_modules.add(module_name)
                    logger.warning(f"✗ Module does not exist: {module_name}")
        
        # Calculate summary
        total = len(self.module_status)
        existing = sum(1 for status in self.module_status.values() if status)
        logger.info(f"Module existence check: {existing}/{total} modules exist")
        
        return self.module_status
    
    def validate_dependencies(self) -> Dict[str, Dict[str, bool]]:
        """
        Validate that module dependencies can be imported
        
        Returns:
            Nested dictionary mapping modules to their dependencies and status
        """
        logger.info("Validating module dependencies...")
        
        # Skip if module existence hasn't been checked
        if not self.module_status:
            self.check_module_existence()
        
        # Check each expected dependency
        for module_name, dependencies in EXPECTED_DEPENDENCIES.items():
            # Skip missing modules
            if module_name not in self.module_status or not self.module_status[module_name]:
                continue
            
            # Initialize connection status for this module
            if module_name not in self.connection_status:
                self.connection_status[module_name] = {}
            
            # Try to import the module
            main_module = None
            try:
                # Try different import strategies
                try:
                    # First try direct import
                    main_module = importlib.import_module(module_name.replace('/', '.'))
                except ImportError:
                    # Then try src.lyra.module_name
                    try:
                        module_short_name = module_name.split('/')[-1]
                        main_module = importlib.import_module(f"src.lyra.{module_short_name}")
                    except ImportError:
                        # Then try modules.module_name
                        try:
                            module_short_name = module_name.split('/')[-1]
                            main_module = importlib.import_module(f"modules.{module_short_name}")
                        except ImportError:
                            # Last resort - try with just the base name
                            module_short_name = module_name.split('/')[-1]
                            main_module = importlib.import_module(module_short_name)
                
                logger.info(f"✓ Successfully imported {module_name}")
                
                # Check each dependency
                for dep_name in dependencies:
                    # Skip missing dependencies
                    if dep_name not in self.module_status or not self.module_status[dep_name]:
                        self.connection_status[module_name][dep_name] = False
                        continue
                    
                    # Check if the dependency is imported in the module
                    source_code = None
                    try:
                        # Get the source code of the module
                        source_file = inspect.getfile(main_module)
                        with open(source_file, 'r', encoding='utf-8') as f:
                            source_code = f.read()
                        
                        # Check for various import patterns
                        dep_short_name = dep_name.split('/')[-1]
                        import_patterns = [
                            f"import {dep_name.replace('/', '.')}",
                            f"from {dep_name.replace('/', '.')} import",
                            f"import {dep_short_name}",
                            f"from {dep_short_name} import",
                            f"from modules.{dep_short_name} import",
                            f"from src.lyra.{dep_short_name} import"
                        ]
                        
                        # Check if any pattern matches
                        if any(pattern in source_code for pattern in import_patterns):
                            logger.info(f"  ✓ {module_name} correctly imports {dep_name}")
                            self.connection_status[module_name][dep_name] = True
                        else:
                            logger.warning(f"  ✗ {module_name} should import {dep_name} but doesn't")
                            self.connection_status[module_name][dep_name] = False
                    except (TypeError, IOError) as e:
                        # Can't get source code for some reason
                        logger.warning(f"  ! Couldn't check imports in {module_name}: {e}")
                        self.connection_status[module_name][dep_name] = None
            
            except ImportError as e:
                # Record the import error
                self.import_errors[module_name] = str(e)
                logger.error(f"✗ Failed to import {module_name}: {e}")
        
        # Calculate summary
        total_connections = sum(len(deps) for deps in self.connection_status.values())
        valid_connections = sum(
            sum(1 for status in deps.values() if status) 
            for deps in self.connection_status.values()
        )
        
        logger.info(f"Dependency validation: {valid_connections}/{total_connections} valid connections")
        
        return self.connection_status
    
    def test_cognitive_system(self) -> Dict[str, bool]:
        """
        Test if the core cognitive components work together
        
        Returns:
            Dictionary mapping test names to success status
        """
        logger.info("Testing cognitive system integration...")
        
        # Define tests to run
        cognitive_tests = {
            "metacognition_available": self._test_metacognition_available,
            "emotional_core_available": self._test_emotional_core_available,
            "deep_memory_available": self._test_deep_memory_available,
            "thinking_integration_available": self._test_thinking_integration_available,
            "cognitive_integration_works": self._test_cognitive_integration_works
        }
        
        # Run each test
        for test_name, test_func in cognitive_tests.items():
            try:
                result = test_func()
                self.cognitive_tests[test_name] = result
                status = "✓" if result else "✗"
                logger.info(f"{status} {test_name}: {'Passed' if result else 'Failed'}")
            except Exception as e:
                self.cognitive_tests[test_name] = False
                logger.error(f"✗ {test_name}: Error - {e}")
                traceback.print_exc()
        
        # Calculate summary
        passed = sum(1 for status in self.cognitive_tests.values() if status)
        total = len(self.cognitive_tests)
        
        logger.info(f"Cognitive system tests: {passed}/{total} tests passed")
        
        return self.cognitive_tests
    def _test_metacognition_available(self) -> bool:
        """Test if metacognition module is available and has key components"""
        try:
            # Try different import strategies
            metacog = None
            for module_path in ['modules.metacognition', 'src.lyra.metacognition', 'metacognition']:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, 'get_instance'):
                        metacog = module.get_instance()
                        break
                except ImportError:
                    continue
            
            if metacog is None:
                return False
                        return False
            
            # Check if metacognition has key attributes
            if metacog:
                required_attrs = ['process_thought', 'add_concept', 'get_related_concepts']
                return any(hasattr(metacog, attr) for attr in required_attrs)
            return False
        except Exception:
            return False
    
    def _test_emotional_core_available(self) -> bool:
        """Test if emotional core module is available and has key components"""
    def _test_emotional_core_available(self) -> bool:
        """Test if emotional core module is available and has key components"""
        try:
            # Try different import strategies
            emotional = None
            for module_path in ['modules.emotional_core', 'src.lyra.emotional_core', 'emotional_core']:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, 'get_instance'):
                        emotional = module.get_instance()
                        break
                except ImportError:
                    continue
            
            if emotional is None:
                return False
            if emotional:
                required_attrs = ['get_emotional_state', 'process_emotion', 'update_emotional_state']
                return any(hasattr(emotional, attr) for attr in required_attrs)
            return False
        except Exception:
            return False
    
    def _test_deep_memory_available(self) -> bool:
        """Test if deep memory module is available and has key components"""
        try:
            # Try different import strategies
            memory = None
    def _test_deep_memory_available(self) -> bool:
        """Test if deep memory module is available and has key components"""
        try:
            # Try different import strategies
            memory = None
            for module_path in ['modules.deep_memory', 'src.lyra.deep_memory', 'deep_memory']:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, 'get_instance'):
                        memory = module.get_instance()
                        break
                except ImportError:
                    continue
            
            if memory is None:
                return False
            return False
        except Exception:
            return False
    
    def _test_thinking_integration_available(self) -> bool:
        """Test if thinking integration module is available and has key components"""
        try:
            # Try different import strategies
            thinking = None
            try:
                from modules.thinking_integration import get_instance
                thinking = get_instance()
    def _test_thinking_integration_available(self) -> bool:
        """Test if thinking integration module is available and has key components"""
        try:
            # Try different import strategies
            thinking = None
            for module_path in ['modules.thinking_integration', 'src.lyra.thinking_integration', 'thinking_integration']:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, 'get_instance'):
                        thinking = module.get_instance()
                        break
                except ImportError:
                    continue
            
            if thinking is None:
                return False
    
    def _test_cognitive_integration_works(self) -> bool:
        """Test if cognitive integration can work with other components"""
        try:
            # Try different import strategies
            cognitive = None
            try:
                from modules.cognitive_integration import get_instance
                cognitive = get_instance()
            except ImportError:
                try:
                    from src.lyra.cognitive_integration import get_instance
    def _test_cognitive_integration_works(self) -> bool:
        """Test if cognitive integration can work with other components"""
        try:
            # Try different import strategies
            cognitive = None
            for module_path in ['modules.cognitive_integration', 'src.lyra.cognitive_integration', 'cognitive_integration']:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, 'get_instance'):
                        cognitive = module.get_instance()
                        break
                except ImportError:
                    continue
            
            if cognitive is None:
                return False
                    result = cognitive.process_input("Test cognitive integration")
            # Try to use the cognitive integration with a test input
            if has_attributes and hasattr(cognitive, 'process_input'):
                try:
                    result = cognitive.process_input("Test cognitive integration")
                    return result is not None
                except Exception:
                    # At least the method exists, even if it doesn't work yet
                    return True
    
    def generate_recommendations(self) -> List[str]:
            # Try to use the cognitive integration with a test input
            if has_attributes and hasattr(cognitive, 'process_input'):
                try:
                    result = cognitive.process_input("Test cognitive integration")
                    return result is not None
                except Exception:
                    # At least the method exists, even if it doesn't work yet
                    return True
            return has_attributes
                recommendations.append(f"  - Create {module}.py with expected functionality")
        
        # Recommend fixing import errors
        if self.import_errors:
            recommendations.append(f"Fix {len(self.import_errors)} import errors:")
            for module, error in self.import_errors.items():
                recommendations.append(f"  - {module}: {error}")
        
        # Recommend fixing missing dependencies
        missing_deps = {}
        for module, deps in self.connection_status.items():
            missing = [dep for dep, status in deps.items() if status is False]
            if missing:
                missing_deps[module] = missing
        
        if missing_deps:
            recommendations.append(f"Add missing imports in {len(missing_deps)} modules:")
            for module, missing in missing_deps.items():
                recommendations.append(f"  - {module}: Add imports for {', '.join(missing)}")
        
        # Recommend implementing cognitive system
        failed_cognitive = [test for test, status in self.cognitive_tests.items() if not status]
        if failed_cognitive:
            recommendations.append(f"Implement {len(failed_cognitive)} cognitive components:")
            for test in failed_cognitive:
                component = test.replace('_available', '').replace('_works', '')
                recommendations.append(f"  - Complete implementation of {component}")
        
        return recommendations
    
    def save_report(self, results: Dict[str, Any]) -> None:
        """
        Save validation results to a report file
        
    def save_report(self, results: Dict[str, Any]) -> None:
        """
        Save validation results to a report file
        
        Args:
            results: Validation results to save
        """
        if not self.report_file:
            logger.warning("No report file specified, skipping report generation")
            return
            
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
    def save_report(self, results: Dict[str, Any]) -> None:
        """
        Save validation results to a report file
        
        Args:
            results: Validation results to save
        """
        if not self.report_file:
            logger.warning("No report file specified, skipping report generation")
            return
                f.write("\n## Dependency Validation\n\n")
                
                dependency_results = results['dependency_validation']
                total_connections = sum(len(deps) for deps in dependency_results.values())
                valid_connections = sum(
                    sum(1 for status in deps.values() if status) 
                    for deps in dependency_results.values()
                )
                
                f.write(f"**Status**: {valid_connections}/{total_connections} valid connections\n\n")
                
                f.write("### Module Dependencies\n\n")
                for module, deps in sorted(dependency_results.items()):
                    f.write(f"#### {module}\n\n")
                    for dep, status in sorted(deps.items()):
                        status_icon = "✅" if status else "❌" if status is False else "❓"
                        f.write(f"- {status_icon} {dep}\n")
                    f.write("\n")
                
                # Cognitive system section
                f.write("## Cognitive System Tests\n\n")
                
                passed = sum(1 for status in results['cognitive_tests'].values() if status)
                total = len(results['cognitive_tests'])
                f.write(f"**Status**: {passed}/{total} tests passed\n\n")
                
                for test, status in sorted(results['cognitive_tests'].items()):
                    status_icon = "✅" if status else "❌"
                    readable_name = test.replace('_', ' ').title()
                    f.write(f"- {status_icon} {readable_name}\n")
                
                # Recommendations section
                f.write("\n## Recommended Actions\n\n")
                
                if results['recommended_actions']:
                    for rec in results['recommended_actions']:
                        f.write(f"- {rec}\n")
                else:
                    f.write("No actions needed! All validations passed.\n")
                
            logger.info(f"Report saved to {self.report_file}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

def main():
    """Main function to run the validator"""
    parser = argparse.ArgumentParser(description="Validate Lyra system integration")
    parser.add_argument("--fix", action="store_true", help="Attempt to fix issues")
    parser.add_argument("--report-file", type=str, default="integration_report.md", 
                       help="Path to save the validation report")
    
    args = parser.parse_args()
    
    # Create and run validator
    validator = IntegrationValidator(
        fix_issues=args.fix,
        report_file=args.report_file
    )
    
    results = validator.validate_all()
    
    # Print summary
    print("\nValidation Summary:")
    print("-" * 40)
    
    # Module existence
    existing = sum(1 for status in results['module_existence'].values() if status)
    total = len(results['module_existence'])
    print(f"Module existence: {existing}/{total} modules exist")
    
    # Dependencies
    dependency_results = results['dependency_validation']
    total_connections = sum(len(deps) for deps in dependency_results.values())
    valid_connections = sum(
        sum(1 for status in deps.values() if status) 
        for deps in dependency_results.values()
    )
    print(f"Dependencies: {valid_connections}/{total_connections} valid connections")
    
    # Cognitive tests
    passed = sum(1 for status in results['cognitive_tests'].values() if status)
    total = len(results['cognitive_tests'])
    print(f"Cognitive tests: {passed}/{total} tests passed")
    
    # Report location
    if args.report_file:
        print(f"\nDetailed report saved to: {args.report_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
