"""
Setup script to prepare Lyra environment
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main setup function"""
    print("Setting up Lyra AI Assistant...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("Lyra requires Python 3.8 or higher.")
        sys.exit(1)
    
    # Install dependencies
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)
    
    # Create necessary directories
    print("Creating directory structure...")
    directories = [
        "docs", "memories", "notes", "bot_notes", "images", "voice",
        "video", "code", "config", "context", "attachments"
    ]
    
    for directory in directories:
        Path(f"G:/AI/Lyra/{directory}").mkdir(exist_ok=True, parents=True)
    
    print("Setup complete! Run 'python run_lyra.py' to start Lyra.")

if __name__ == "__main__":
    main()
