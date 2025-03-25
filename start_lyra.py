"""
Startup script for Lyra - handles dependency resolution and launches the assistant
"""
import os
import sys
import subprocess
import argparse
import platform

def check_python_version():
    """Check if Python version is compatible"""
    major, minor = sys.version_info[:2]
    if major != 3 or minor < 10:
        print(f"⚠️ Warning: Lyra works best with Python 3.10+. You're using {major}.{minor}")
        return False
    return True

def create_env():
    """Create a virtual environment with dependencies"""
    print("📦 Setting up Lyra environment...")
    try:
        # Run the dependency resolver
        subprocess.run([sys.executable, "resolve_dependencies.py", "--langchain"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to set up environment.")
        return False

def run_lyra():
    """Run Lyra using the virtual environment"""
    try:
        # Use the wrapper that automatically finds the virtual environment
        subprocess.run([sys.executable, "run_lyra_wrapper.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to run Lyra.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Start Lyra AI Assistant")
    parser.add_argument("--setup-only", action="store_true", help="Only set up environment, don't run Lyra")
    args = parser.parse_args()
    
    # Check Python version
    check_python_version()
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# Environment variables for Lyra\n")
            f.write("OPENAI_API_KEY=your_api_key_here\n")
        print("📄 Created .env file - please edit it to add your OpenAI API key")
        input("Press Enter after you've added your API key...")
    
    # Run resolver if needed
    env_exists = any(os.path.exists(name) for name in ["lyra_env", "venv", "env"])
    if not env_exists:
        if not create_env():
            return False
    
    if args.setup_only:
        print("✅ Setup complete. Run 'python start_lyra.py' to start Lyra.")
        return True
        
    # Run Lyra
    print("🚀 Starting Lyra...")
    return run_lyra()

if __name__ == "__main__":
    main()
