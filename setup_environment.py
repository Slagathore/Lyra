"""
Script to set up a clean Poetry environment for Lyra
"""
import os
import subprocess
import sys
import shutil
from pathlib import Path

def setup_environment():
    """Set up a clean Poetry environment"""
    print("🔧 Setting up Lyra's Poetry environment...")
    
    # Check if Poetry is installed
    try:
        subprocess.run(["poetry", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Poetry is not installed. Please install it from https://python-poetry.org/docs/#installation")
        return False
        
    # Create a clean environment by removing Poetry cache and lock file
    print("🧹 Cleaning up existing Poetry environment...")
    
    # Remove poetry.lock if it exists
    if os.path.exists("poetry.lock"):
        os.remove("poetry.lock")
        print("   Removed poetry.lock file")
    
    # Check if we need to create any missing directories
    for path in ["src/lyra/memory", "src/lyra/integration"]:
        Path(path).mkdir(parents=True, exist_ok=True)
        
    # Make sure all __init__.py files exist
    for path in ["src/lyra", "src/lyra/memory", "src/lyra/integration", "actions"]:
        init_file = os.path.join(path, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                f.write(f'"""\n{path} module\n"""\n')
            print(f"   Created {init_file}")
            
    # Install all dependencies
    print("\n📦 Installing dependencies with Poetry...")
    result = subprocess.run(["poetry", "install"], capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Error installing dependencies: {result.stderr}")
        return False
        
    print("✅ Poetry environment set up successfully!")
    
    # Install specific non-conflicting packages
    print("\n📦 Installing specific packages...")
    subprocess.run([
        "poetry", "add",
        "langchain-openai",
        "textblob",
        "sentence-transformers",
        "faiss-cpu"
    ], check=False)
    
    # Create a .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# Environment variables for Lyra\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
        print("📄 Created .env file - please add your OpenAI API key")
    
    # Print next steps
    print("\n🚀 Next steps:")
    print("1. Add your OpenAI API key to the .env file")
    print("2. Run 'poetry run python -m lyra.main' to start Lyra")
    print("3. If you encounter issues, try 'poetry run python check_dependencies.py'")
    
    return True

if __name__ == "__main__":
    setup_environment()
