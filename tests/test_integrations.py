import os
import sys
import unittest

# Add the parent directory to sys.path for imports to work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestLyraIntegrations(unittest.TestCase):
    """Test all major integrations for Lyra"""

    def test_llm_integration(self):
        """Test if llama-cpp-python can be imported"""
        try:
            import llama_cpp
            # Check if the module has the Llama class
            self.assertTrue(hasattr(llama_cpp, 'Llama'))
        except ImportError:
            self.fail("Failed to import llama-cpp-python")

    def test_langchain_integration(self):
        """Test if langchain can be imported and major components work"""
        try:
            import langchain
            from langchain.prompts import PromptTemplate
            
            # Test creating a simple prompt template
            prompt = PromptTemplate(
                input_variables=["topic"],
                template="Please write about {topic}."
            )
            result = prompt.format(topic="AI")
            self.assertEqual(result, "Please write about AI.")
        except ImportError:
            self.fail("Failed to import langchain")
        except Exception as e:
            self.fail(f"Error in langchain: {e}")

    def test_sqlalchemy_integration(self):
        """Test if sqlalchemy can be imported"""
        try:
            import sqlalchemy
            # Create an in-memory database to test functionality
            engine = sqlalchemy.create_engine('sqlite:///:memory:')
            self.assertTrue(engine is not None)
        except ImportError:
            self.fail("Failed to import sqlalchemy")
        except Exception as e:
            self.fail(f"Error in sqlalchemy: {e}")

    @unittest.skipIf(not os.path.exists("src/lyra/self_improvement"), 
                     "Self-improvement module not installed")
    def test_self_improvement_integration(self):
        """Test if self-improvement module works"""
        try:
            # First ensure src is in path
            src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
            if src_path not in sys.path:
                sys.path.insert(0, src_path)
            
            # Import from the module
            from lyra.self_improvement import CodeManager, VintixRL
            
            # Create instances to verify they initialize properly
            cm = CodeManager()
            rl = VintixRL()
            
            # Run a basic test of the CodeManager
            structure = cm.get_module_structure()
            self.assertTrue(isinstance(structure, dict))
            
            # Get some suggestions from the RL module
            suggestions = rl.get_improvement_suggestions("# TODO: Fix this code")
            self.assertTrue(isinstance(suggestions, list))
        except ImportError as e:
            self.fail(f"Failed to import self-improvement modules: {e}")
        except Exception as e:
            self.fail(f"Error in self-improvement modules: {e}")

    def test_core_lyra_imports(self):
        """Test if the core Lyra components can be imported"""
        try:
            from lyra import main
            # Test that the main module has a main function
            self.assertTrue(hasattr(main, 'main'))
        except ImportError:
            self.fail("Failed to import Lyra main module")
        except Exception as e:
            self.fail(f"Error importing Lyra: {e}")

if __name__ == '__main__':
    unittest.main()
