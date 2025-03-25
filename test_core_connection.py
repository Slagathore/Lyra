"""
Test script to verify connection to the Lyra core system
Helps identify where the core is located and how to connect to it
"""

import os
import sys
import logging
import importlib
import json
from pathlib import Path
import traceback
import inspect
import time

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("core_test")

def find_core():
    """Find and connect to the Lyra core"""
    logger.info("Searching for Lyra core module...")

    # Try to load core location from config file first
    config_file = Path("config/core_location.json")
    if config_file.exists():
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
                core_path = config.get("core_path")
                if core_path:
                    logger.info(f"Found core location in config: {core_path}")
                    
                    # Add the configured path to sys.path
                    if os.path.isdir(core_path):
                        sys.path.insert(0, core_path)
                        logger.info(f"Added {core_path} to sys.path")
                    
                    # Try the specific module if specified
                    core_module = config.get("core_module")
                    if core_module:
                        try:
                            logger.info(f"Attempting to import configured module: {core_module}")
                            module = importlib.import_module(core_module)
                            if hasattr(module, 'LyraCore'):
                                logger.info(f"Found LyraCore in configured module {core_module}")
                                if hasattr(module.LyraCore, 'get_instance'):
                                    core = module.LyraCore.get_instance()
                                    logger.info(f"✓ Successfully connected using configured path")
                                    return core, core_module
                            
                            # Try get_instance directly
                            if hasattr(module, 'get_instance'):
                                logger.info(f"Found get_instance() in {core_module}")
                                core = module.get_instance()
                                logger.info(f"✓ Successfully connected using configured path")
                                return core, core_module
                        except Exception as e:
                            logger.warning(f"Failed to load from configured path: {e}")
        except Exception as e:
            logger.warning(f"Error reading config file: {e}")
    
    # Add the current directory and parent directory to the path
    current_dir = Path(__file__).parent.absolute()
    sys.path.insert(0, str(current_dir))
    
    # Add parent directories to path for broader searching
    parent_dir = current_dir.parent
    if parent_dir and parent_dir != current_dir:
        logger.info(f"Adding parent directory to path: {parent_dir}")
        sys.path.insert(0, str(parent_dir))

    # Look for any potential Lyra installation folders
    potential_lyra_dirs = []
    
    # Check standard locations on Windows
    if sys.platform == 'win32':
        # Check program files directories
        for program_dir in ["C:/Program Files", "C:/Program Files (x86)"]:
            for subdir in Path(program_dir).glob("*[Ll]yra*"):
                if subdir.is_dir():
                    potential_lyra_dirs.append(subdir)

        # Check user directories
        userprofile = os.environ.get('USERPROFILE', '')
        if userprofile:
            user_path = Path(userprofile)
            # Check documents, downloads, etc.
            for subdir in ['Documents', 'Downloads', 'Desktop', 'Projects']:
                search_dir = user_path / subdir
                if search_dir.exists():
                    for lyra_dir in search_dir.glob("*[Ll]yra*"):
                        if lyra_dir.is_dir():
                            potential_lyra_dirs.append(lyra_dir)
    
    # Add found directories to path
    for lyra_dir in potential_lyra_dirs:
        if str(lyra_dir) not in sys.path:
            logger.info(f"Adding potential Lyra directory to path: {lyra_dir}")
            sys.path.insert(0, str(lyra_dir))
    
    # Check if we can find any Lyra modules at all
    all_python_files = list(current_dir.glob("**/*.py"))
    lyra_files = [f for f in all_python_files if "lyra" in f.name.lower()]
    core_files = [f for f in all_python_files if "core" in f.name.lower()]
    
    core_candidates = [f for f in all_python_files if "lyra" in f.name.lower() and "core" in f.name.lower()]
    
    if core_candidates:
        logger.info(f"Found {len(core_candidates)} potential Lyra core files:")
        for i, file in enumerate(core_candidates[:10]):  # Show first 10
            logger.info(f"  {i+1}. {file.relative_to(current_dir)}")
        if len(core_candidates) > 10:
            logger.info(f"  ... and {len(core_candidates) - 10} more")
    
    # Common module paths where the core might be located
    possible_modules = [
        # Primary locations
        "lyra.core",
        "core.lyra_core",
        "modules.lyra_core",
        "lyra_core",
        "core",
        # Project specific paths - add the ones found
        *[f.stem for f in core_candidates],
        # Direct imports from found files (without .py extension)
        *[str(f.relative_to(current_dir)).replace('\\', '.').replace('/', '.')[:-3] 
         for f in core_candidates if f.is_file()],
        # Additional alternatives
        "lyra.lib.core",
        "lyra.engine.core",
        "engine.core",
        "main.core",
        "lyra.main.core",
        "lyra.core.main",
    ]
    
    core = None
    successful_path = None
    
    # Try each potential location
    for module_path in possible_modules:
        if '.__pycache__.' in module_path:
            continue  # Skip __pycache__ entries
            
        try:
            logger.info(f"Attempting import from: {module_path}")
            module = importlib.import_module(module_path)
            
            # Look for the LyraCore class
            if hasattr(module, 'LyraCore'):
                logger.info(f"Found LyraCore in {module_path}")
                
                # Check for specific attributes that would indicate this is the real core
                if hasattr(module.LyraCore, 'version') or hasattr(module.LyraCore, 'VERSION'):
                    logger.info("This appears to be the real Lyra core based on version attribute")
                
                # Try get_instance method
                if hasattr(module.LyraCore, 'get_instance'):
                    logger.info("Found get_instance method")
                    try:
                        core = module.LyraCore.get_instance()
                        logger.info(f"✓ Successfully connected to Lyra core via {module_path}")
                        successful_path = module_path
                        break
                    except Exception as e:
                        logger.warning(f"Error initializing core via get_instance: {e}")
                
                # If no get_instance, try direct instantiation
                if not core:
                    try:
                        logger.info("Trying direct instantiation of LyraCore")
                        init_params = inspect.signature(module.LyraCore.__init__).parameters
                        if len(init_params) == 1:  # Just 'self'
                            core = module.LyraCore()
                            logger.info(f"✓ Successfully instantiated Lyra core via {module_path}")
                            successful_path = module_path
                            break
                    except Exception as e:
                        logger.warning(f"Error directly instantiating core: {e}")
            
            # Alternative: look for get_instance function directly
            if hasattr(module, 'get_instance'):
                logger.info(f"Found get_instance() in {module_path}")
                try:
                    core = module.get_instance()
                    logger.info(f"✓ Successfully connected via {module_path}.get_instance()")
                    successful_path = module_path
                    break
                except Exception as e:
                    logger.warning(f"Error calling get_instance: {e}")
                
        except ImportError as e:
            logger.debug(f"Import error with {module_path}: {e}")
            continue
        except Exception as e:
            logger.debug(f"Error with {module_path}: {e}")
            continue
    
    if not core:
        logger.warning("Could not connect to Lyra core through any standard path")
        
        # Final attempt - try the dummy implementation
        try:
            from modules.lyra_core import LyraCore
            core = LyraCore.get_instance()
            logger.info("Connected to local dummy core implementation")
            successful_path = "modules.lyra_core"
        except ImportError:
            logger.error("Even local dummy core is not available")
    
    return core, successful_path

def test_core(core):
    """Test the core's functionality"""
    if not core:
        logger.error("No core available to test")
        return False
    
    logger.info("Testing core functionality...")
    
    # Test 1: Basic attributes
    logger.info("Testing core attributes")
    try:
        # Print all attributes to help identify the core
        core_attrs = [attr for attr in dir(core) if not attr.startswith('__')]
        logger.info(f"Core has the following attributes: {', '.join(core_attrs[:20])}")
        if len(core_attrs) > 20:
            logger.info(f"...and {len(core_attrs) - 20} more attributes")
        
        # Test basic properties we expect the core to have
        if hasattr(core, 'process_message'):
            logger.info("✓ Core has process_message() method")
        else:
            logger.error("✗ Core is missing process_message() method")
            
            # Look for alternative message processing methods
            message_methods = [attr for attr in dir(core) if 'message' in attr.lower() or 'process' in attr.lower()]
            if message_methods:
                logger.info(f"Alternative message methods found: {message_methods}")
        
        if hasattr(core, 'model_manager'):
            logger.info("✓ Core has model_manager attribute")
            
            # Test model manager
            if hasattr(core.model_manager, 'get_active_model'):
                try:
                    active_model = core.model_manager.get_active_model()
                    logger.info(f"✓ Active model: {active_model.name if active_model else 'None'}")
                except Exception as e:
                    logger.warning(f"Error getting active model: {e}")
            else:
                logger.warning("✗ Model manager missing get_active_model() method")
        else:
            logger.warning("✗ Core is missing model_manager attribute")
            
            # Look for alternative model attributes
            model_attrs = [attr for attr in dir(core) if 'model' in attr.lower()]
            if model_attrs:
                logger.info(f"Alternative model attributes found: {model_attrs}")
    except Exception as e:
        logger.error(f"Error testing core attributes: {e}")
        traceback.print_exc()
        return False
    
    # Test 2: Process a message
    logger.info("Testing message processing")
    try:
        test_message = "Hello, this is a test message from the connection tester."
        
        if hasattr(core, 'process_message'):
            start_time = time.time()
            response = core.process_message(test_message)
            end_time = time.time()
            
            logger.info(f"✓ Received response in {end_time - start_time:.2f} seconds: {response}")
            return True
        else:
            # Try to find alternative message methods
            for method_name in dir(core):
                if 'message' in method_name.lower() or 'process' in method_name.lower():
                    if callable(getattr(core, method_name)):
                        try:
                            logger.info(f"Trying alternative method: {method_name}")
                            method = getattr(core, method_name)
                            result = method(test_message)
                            logger.info(f"✓ Got response from {method_name}: {result}")
                            return True
                        except Exception as method_e:
                            logger.warning(f"Error calling {method_name}: {method_e}")
            
            logger.error("No working message processing method found")
            return False
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        traceback.print_exc()
        return False

def save_core_location(module_path, suggested_import_code=None):
    """Save the core location for future use"""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    config = {
        "core_module": module_path,
        "last_successful_connection": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if suggested_import_code:
        config["import_code"] = suggested_import_code
    
    with open(config_dir / "core_location.json", "w") as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Saved core location to config/core_location.json")

def main():
    """Main function to find and test the core"""
    print("\nLyra Core Connection Tester")
    print("==========================\n")
    print("This script will attempt to find and connect to the Lyra core system.\n")
    
    # Find the core
    core, module_path = find_core()
    
    if core:
        print(f"\nSUCCESS: Connected to Lyra core via {module_path}\n")
        
        # Test the core
        success = test_core(core)
        
        if success:
            print("\nCore tests PASSED ✓")
            print("\nYour persistent_module.py should be able to connect to this core.")
            print(f"The successful import path was: {module_path}")
            
            # Save the successful path
            suggested_code = f"from {module_path} import LyraCore\ncore = LyraCore.get_instance()"
            save_core_location(module_path, suggested_code)
            
            print("\nThis location has been saved for future use. The persistent module")
            print("will now be able to automatically connect to this core.")
            
            if module_path == "modules.lyra_core":
                print("\nNOTE: You are currently using the dummy core implementation.")
                print("To connect to the real core, make sure your real Lyra installation")
                print("is properly set up and accessible in your Python path.")
                
                # Ask user for core location
                print("\nWould you like to manually specify the location of your Lyra installation?")
                choice = input("Enter Y to specify a path, or N to continue: ").strip().lower()
                
                if choice == 'y':
                    core_path = input("\nEnter the full path to your Lyra installation: ").strip()
                    if os.path.isdir(core_path):
                        # Save this to config
                        config = {
                            "core_path": core_path,
                            "manual_setup": True,
                            "setup_date": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        config_dir = Path("config")
                        config_dir.mkdir(exist_ok=True)
                        with open(config_dir / "core_location.json", "w") as f:
                            json.dump(config, f, indent=2)
                        
                        print(f"\nSaved path: {core_path}")
                        print("Please run this test again to check if the core can be found.")
                    else:
                        print(f"Path not found: {core_path}")
        else:
            print("\nCore tests FAILED ✗")
            print("The core was found but doesn't seem to be functioning properly.")
    else:
        print("\nFAILED: Could not connect to any Lyra core ✗")
        print("Make sure your Lyra installation is correct and the core is initialized.")
        
        # Offer option to manually specify the core location
        print("\nWould you like to manually specify the location of your Lyra installation?")
        choice = input("Enter Y to specify a path, or N to exit: ").strip().lower()
        
        if choice == 'y':
            core_path = input("\nEnter the full path to your Lyra installation: ").strip()
            if os.path.isdir(core_path):
                # Save this to config
                config = {
                    "core_path": core_path,
                    "manual_setup": True,
                    "setup_date": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                config_dir = Path("config")
                config_dir.mkdir(exist_ok=True)
                with open(config_dir / "core_location.json", "w") as f:
                    json.dump(config, f, indent=2)
                
                print(f"\nSaved path: {core_path}")
                print("Please run this test again to check if the core can be found.")
            else:
                print(f"Path not found: {core_path}")
    
    return 0 if core and success else 1

if __name__ == "__main__":
    sys.exit(main())
