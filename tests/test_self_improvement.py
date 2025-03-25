"""
Integration tests for the self-improvement module.
"""
import os
import sys
import unittest
import tempfile
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestSelfImprovementIntegration(unittest.TestCase):
    """Test the integration between self-improvement components"""

    def setUp(self):
        """Set up test fixtures"""
        # Skip if the self-improvement module doesn't exist
        module_path = os.path.join("src", "lyra", "self_improvement")
        if not os.path.exists(module_path):
            self.skipTest("Self-improvement module not installed")
            
        # Add src to path if not already added
        src_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
            
        # Import the modules
        from lyra.self_improvement.code_manager import CodeManager
        from lyra.self_improvement.reinforcement_learning import VintixRL
        
        # Create instances
        self.code_manager = CodeManager()
        self.vintix_rl = VintixRL()

    def test_rl_llm_integration(self):
        """Test if VintixRL can use the LLM advisor"""
        # Skip if no LLM advisor
        if not hasattr(self.vintix_rl, "llm_advisor") or self.vintix_rl.llm_advisor is None:
            self.skipTest("LLM advisor not available")
            
        # Simple code with an obvious TODO
        code = "def example():\n    # TODO: Implement this function\n    pass"
        
        # Get improvement suggestions
        suggestions = self.vintix_rl.get_improvement_suggestions(code, {"file_path": "test.py"})
        
        # Should have at least one suggestion (the TODO implementation)
        self.assertGreaterEqual(len(suggestions), 1)
        
        # At least one suggestion should be about the TODO
        todo_suggestions = [s for s in suggestions if "todo" in s["type"].lower()]
        self.assertGreaterEqual(len(todo_suggestions), 1)

    def test_code_manager_vintixrl_integration(self):
        """Test if CodeManager and VintixRL can work together"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(b"def test_function():\n    # This is a test function\n    return True")
            
        try:
            # Get the file content
            content = self.code_manager.get_file_content(tmp_path)
            
            # Record a code change
            change_idx = self.vintix_rl.record_code_change(
                tmp_path,
                "Test change",
                content, 
                content + "\n\ndef another_function():\n    return False"
            )
            
            # Verify the change was recorded
            self.assertGreaterEqual(change_idx, 0)
            
            # Record feedback
            success = self.vintix_rl.record_feedback(
                change_idx,
                True,
                "This is good test feedback"
            )
            
            self.assertTrue(success)
            
        finally:
            # Clean up the temporary file
            os.unlink(tmp_path)

if __name__ == "__main__":
    unittest.main()
