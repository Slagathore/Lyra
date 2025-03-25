"""
Script to check if all required dependencies are installed correctly
"""
import importlib
import sys
import subprocess

def check_dependency(name, import_name=None):
    """Check if a dependency is installed and can be imported"""
    if import_name is None:
        import_name = name
    
    try:
        importlib.import_module(import_name)
        print(f"✅ {name} is installed")
        return True
    except ImportError as e:
        print(f"❌ {name} is NOT installed: {e}")
        return False

def check_command(command):
    """Check if a command is available"""
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        print(f"✅ '{' '.join(command)}' is available")
        return True
    except FileNotFoundError:
        print(f"❌ '{' '.join(command)}' is NOT available")
        return False

def main():
    """Check all dependencies"""
    print("Checking Lyra dependencies...\n")
    
    # Core libraries
    check_dependency("rasa")
    check_dependency("openai")
    check_dependency("langchain")
    check_dependency("langchain_openai")
    check_dependency("sqlalchemy")
    
    # Vector search
    try:
        check_dependency("faiss", "faiss")
    except:
        check_dependency("faiss-cpu", "faiss")
    
    # NLP libraries
    check_dependency("transformers")
    check_dependency("spacy")
    check_dependency("nltk")
    check_dependency("textblob")
    check_dependency("sentence_transformers")
    
    # Neural networks
    check_dependency("torch")
    check_dependency("tensorflow")
    
    # Check external commands
    check_command(["python", "--version"])
    check_command(["poetry", "--version"])
    
    print("\nDependency check complete!")

if __name__ == "__main__":
    main()
