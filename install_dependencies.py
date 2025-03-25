"""
Script to install all dependencies using Poetry
"""
import os
import subprocess
import sys

def install_dependencies():
    """Install all dependencies using Poetry"""
    print("Installing Lyra dependencies with Poetry...")
    
    try:
        # Check if Poetry is installed
        subprocess.run(["poetry", "--version"], check=True)
        
        # Install dependencies
        result = subprocess.run(["poetry", "install"], check=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
            
            # Update specific packages if needed
            print("Updating key dependencies...")
            subprocess.run(["poetry", "update", "openai", "langchain", "langchain-openai"], check=False)
            
            print("\nYou can now run Lyra using: poetry run python -m lyra.main")
        else:
            print("❌ Error installing dependencies")
            
    except subprocess.CalledProcessError:
        print("❌ Poetry is not installed or not in PATH")
        print("Please install Poetry: https://python-poetry.org/docs/#installation")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
if __name__ == "__main__":
    install_dependencies()
