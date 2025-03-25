"""
Update Lyra's dependencies to the latest compatible versions
"""
import sys
import subprocess
import importlib.metadata

def check_gradio_version():
    """Check and potentially update Gradio version"""
    try:
        current_version = importlib.metadata.version("gradio")
        print(f"Current Gradio version: {current_version}")
        
        # Attempt to get the latest version using pip
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", "gradio"],
            capture_output=True,
            text=True
        )
        
        # Parse output to find latest version
        output_lines = result.stdout.splitlines()
        latest_version = None
        for line in output_lines:
            if "Available versions:" in line:
                versions = line.split("Available versions:")[1].strip().split(", ")
                if versions:
                    latest_version = versions[0].strip()
                    break
        
        if not latest_version:
            print("Could not determine latest Gradio version. Using version 4.44.0")
            latest_version = "4.44.0"
        
        print(f"Latest Gradio version: {latest_version}")
        
        # Ask user if they want to update
        resp = input(f"Do you want to update Gradio to version {latest_version}? (y/n): ")
        if resp.lower() in ['y', 'yes']:
            print(f"Updating Gradio to version {latest_version}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", f"gradio=={latest_version}"
            ])
            print("Gradio updated successfully!")
        else:
            print("Keeping current Gradio version.")
            
    except Exception as e:
        print(f"Error checking/updating Gradio: {e}")
        print("You can manually update using: pip install -U gradio")

def update_all_dependencies():
    """Update all Lyra dependencies to latest compatible versions"""
    try:
        print("Checking for updates to all dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--upgrade"
        ])
        print("All dependencies updated successfully!")
    except Exception as e:
        print(f"Error updating dependencies: {e}")

if __name__ == "__main__":
    print("==== Lyra Dependency Update Tool ====")
    print("\n1. Update only Gradio (recommended for UI fixes)")
    print("2. Update all dependencies (may take longer)")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ")
    
    if choice == "1":
        check_gradio_version()
    elif choice == "2":
        update_all_dependencies()
    else:
        print("Exiting without changes.")
