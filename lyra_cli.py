"""
Command-line interface for Lyra
"""
import argparse
import os
import subprocess
import sys

def setup():
    """Set up Lyra dependencies"""
    print("Setting up Lyra dependencies...")
    
    try:
        # Try using Poetry
        if os.system("poetry --version") == 0:
            subprocess.run(["python", "setup_environment.py"], check=True)
        else:
            # Fall back to pip
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    except Exception as e:
        print(f"Error during setup: {e}")
        return False
        
    return True

def run():
    """Run Lyra"""
    print("Starting Lyra...")
    
    try:
        # Try using Poetry
        if os.system("poetry --version") == 0:
            subprocess.run(["poetry", "run", "python", "-m", "lyra.main"], check=True)
        else:
            # Fall back to direct execution
            subprocess.run([sys.executable, "run_minimal.py"], check=True)
    except Exception as e:
        print(f"Error running Lyra: {e}")
        return False
        
    return True

def check():
    """Check Lyra dependencies"""
    print("Checking Lyra dependencies...")
    
    try:
        # Try using Poetry
        if os.system("poetry --version") == 0:
            subprocess.run(["poetry", "run", "python", "check_dependencies.py"], check=True)
        else:
            # Fall back to direct execution
            subprocess.run([sys.executable, "check_dependencies.py"], check=True)
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        return False
        
    return True

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Lyra AI Assistant CLI")
    parser.add_argument("command", choices=["setup", "run", "check"], help="Command to run")
    
    args = parser.parse_args()
    
    if args.command == "setup":
        setup()
    elif args.command == "run":
        run()
    elif args.command == "check":
        check()

if __name__ == "__main__":
    main()
