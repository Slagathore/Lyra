"""
Simple utility to identify the actual Lyra core file location
"""
import os
import sys
from pathlib import Path

def find_core_candidates():
    """Find all potential core files in the Lyra directory"""
    base_dir = Path(__file__).parent.absolute()
    print(f"Searching for core files in: {base_dir}")
    
    # Look for specific patterns that might indicate the real core
    core_candidates = []
    
    # Search all .py files in the directory tree
    for filepath in base_dir.glob("**/*.py"):
        # Skip the dummy core we created
        if "modules/lyra_core.py" in str(filepath) or "modules\\lyra_core.py" in str(filepath):
            continue
            
        # Skip common utility files
        if filepath.name in ["__init__.py", "__main__.py", "setup.py"]:
            continue
            
        # Read the file content
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Look for patterns that suggest this might be the core
                core_indicators = [
                    # Class indicators
                    "class LyraCore",
                    "class Core",
                    # Core functionality indicators
                    "def process_message",
                    "def get_instance",
                    # Comment indicators 
                    "# Core implementation",
                    "# Lyra core"
                ]
                
                # Check if any indicator is in the content
                matches = [indicator for indicator in core_indicators if indicator in content]
                
                if matches:
                    # This file might be a core candidate
                    relative_path = filepath.relative_to(base_dir)
                    core_candidates.append({
                        "path": str(relative_path),
                        "full_path": str(filepath),
                        "indicators": matches,
                        "match_count": len(matches)
                    })
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    # Sort by number of indicators (most likely first)
    core_candidates.sort(key=lambda x: x["match_count"], reverse=True)
    return core_candidates

def main():
    """Main function"""
    print("Lyra Core Finder")
    print("===============")
    print("This utility will search your Lyra installation to find the actual core file.")
    print("")
    
    candidates = find_core_candidates()
    
    if not candidates:
        print("No core candidates found! This is unexpected.")
        return
    
    print(f"Found {len(candidates)} potential core files:")
    print("")
    
    for i, candidate in enumerate(candidates[:10]):  # Show top 10
        print(f"{i+1}. {candidate['path']}")
        print(f"   Indicators: {', '.join(candidate['indicators'])}")
        print(f"   Full path: {candidate['full_path']}")
        print("")
    
    if len(candidates) > 10:
        print(f"... and {len(candidates) - 10} more candidates")
    
    print("\nPlease check these files to identify your real Lyra core.")
    print("Once identified, you can configure the connection by running:")
    print("    python find_real_core.bat")
    
    # If we have high confidence in the top candidate, suggest it
    if candidates and candidates[0]["match_count"] >= 3:
        print(f"\nMost likely core file: {candidates[0]['path']}")
        print("Would you like to try connecting to this file now? (y/n)")
        choice = input().strip().lower()
        
        if choice == 'y':
            # Create a temporary config file
            import json
            import importlib
            
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            # Get module name from file path
            module_path = candidates[0]['path']
            if module_path.endswith(".py"):
                module_path = module_path[:-3]  # Remove .py extension
            module_path = module_path.replace("/", ".").replace("\\", ".")
            
            config = {
                "core_path": str(Path(__file__).parent),
                "core_module": module_path,
                "manual_setup": True,
                "setup_date": "auto-detected"
            }
            
            with open(config_dir / "core_location.json", "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"Testing connection to {module_path}...")
            
            # Try importing the module
            try:
                if module_path not in sys.path:
                    sys.path.insert(0, str(Path(__file__).parent))
                
                module = importlib.import_module(module_path)
                
                if hasattr(module, 'LyraCore'):
                    print("✓ Found LyraCore class")
                    if hasattr(module.LyraCore, 'get_instance'):
                        print("✓ Found get_instance method")
                        core = module.LyraCore.get_instance()
                        print("✓ Successfully instantiated core!")
                        print(f"\nReal core location confirmed: {module_path}")
                        print("Configuration saved. Your tray app should now connect to this core.")
                        return
                
                if hasattr(module, 'get_instance'):
                    print("✓ Found get_instance() function")
                    core = module.get_instance()
                    print("✓ Successfully instantiated core!")
                    print(f"\nReal core location confirmed: {module_path}")
                    print("Configuration saved. Your tray app should now connect to this core.")
                    return
                
                print("Could not find core interfaces in this module.")
            except Exception as e:
                print(f"Error connecting to core: {e}")
    
    print("\nRun python test_core_connection.py with your chosen core path to test the connection.")

if __name__ == "__main__":
    main()
