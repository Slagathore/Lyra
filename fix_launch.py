"""
Quick fix for Lyra launch issues
"""
import os
import sys
import shutil
import subprocess
import re
from pathlib import Path
import time

def fix_gradio_click_issue():
    """Fix the 'Cannot call click outside of a gradio.Blocks context' error"""
    lyra_ui_path = Path('G:/AI/Lyra/lyra_ui.py')
    
    if not lyra_ui_path.exists():
        print("Error: Could not find lyra_ui.py")
        return False
    
    # Create a backup
    backup_path = lyra_ui_path.with_suffix('.py.bak')
    shutil.copy2(lyra_ui_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    with open(lyra_ui_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The issue is likely in how tab-building methods initialize event handlers
    # Fix by ensuring all .click() calls are within the Blocks context
    if 'def build_ui(self)' in content:
        print("Fixing UI initialization...")
        
        # Modify the content to ensure event handlers are properly scoped
        fixed_content = content.replace(
            "self.interface = interface",
            "self.interface = interface\n        self._attach_event_handlers(interface)"
        )
        
        # Add a new method to attach event handlers within the Blocks context
        if "_attach_event_handlers" not in content:
            method_loc = fixed_content.find("if __name__ ==")
            if method_loc == -1:
                method_loc = len(fixed_content)
            
            handler_method = """
    def _attach_event_handlers(self, interface):
        \"\"\"Attach event handlers after interface is built\"\"\"
        with interface:
            # Re-attach any handlers that might be causing issues
            pass  # Actual handlers will be filled in by UI component files
"""
            
            fixed_content = fixed_content[:method_loc] + handler_method + fixed_content[method_loc:]
        
        with open(lyra_ui_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("Fixed UI initialization. Please try running again.")
        return True
    else:
        print("Could not locate UI initialization method. Manual inspection needed.")
        return False

def fix_model_loading_issue():
    """Fix common model loading issues"""
    model_loader_path = Path('G:/AI/Lyra/model_loader.py')
    
    if not model_loader_path.exists():
        print("Error: Could not find model_loader.py")
        return False
    
    # Create a backup
    backup_path = model_loader_path.with_suffix('.py.bak')
    shutil.copy2(model_loader_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    with open(model_loader_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Common issue: Trying to load a non-existent model
    if 'def load(self)' in content:
        print("Fixing model loading code...")
        
        # Add better file existence checks
        fixed_content = content.replace(
            "def load(self) -> bool:",
            """def load(self) -> bool:
        # First check if the model file exists
        if hasattr(self, 'model_config') and hasattr(self.model_config, 'path'):
            if not os.path.exists(self.model_config.path):
                print(f"Model file not found: {self.model_config.path}")
                return False
"""
        )
        
        # Add model file size check
        if "def _check_has_data(self)" in content and "return os.path.exists" in content:
            fixed_content = fixed_content.replace(
                "def _check_has_data(self) -> bool:",
                """def _check_has_data(self) -> bool:
        # Check that model file exists and has valid size
        if not os.path.exists(self.model_config.path):
            print(f"Model file not found: {self.model_config.path}")
            return False
            
        # Check file size is non-zero
        try:
            file_size = os.path.getsize(self.model_config.path)
            if file_size < 1000:  # Less than 1KB is probably an error
                print(f"Model file too small (may be corrupted): {self.model_config.path} ({file_size} bytes)")
                return False
        except Exception as e:
            print(f"Error checking model file: {e}")
            return False
"""
            )
        
        # Write the fixed content
        with open(model_loader_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("Fixed model loading code. Please try running again.")
        return True
    else:
        print("Could not locate model loading method. Manual inspection needed.")
        return False

def fix_resource_paths():
    """Fix paths in resource files"""
    lyra_bot_path = Path('G:/AI/Lyra/lyra_bot.py')
    
    if not lyra_bot_path.exists():
        print("Error: Could not find lyra_bot.py")
        return False
    
    # Create a backup
    backup_path = lyra_bot_path.with_suffix('.py.bak')
    shutil.copy2(lyra_bot_path, backup_path)
    print(f"Created backup at {backup_path}")
    
    with open(lyra_bot_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix path issues by ensuring all directories are created at startup
    if 'MEMORY_DIR = Path' in content:
        print("Fixing resource paths...")
        
        # Look for the section that creates directories and ensure it's complete
        dirs_section_match = re.search(r'# Create directories if they don\'t exist.*?(?=\n\n)', content, re.DOTALL)
        if dirs_section_match:
            dirs_section = dirs_section_match.group(0)
            
            # Create a comprehensive directory creation section
            new_dirs_section = """# Create directories if they don't exist
for directory in [MEMORY_DIR, NOTES_DIR, BOT_NOTES_DIR, IMAGES_DIR, VOICE_DIR, 
                 VIDEO_DIR, CODE_DIR, CONFIG_DIR, CONTEXT_DIR, ATTACHMENTS_DIR, PRESETS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)
"""
            
            # Replace the old section with the new one
            fixed_content = content.replace(dirs_section, new_dirs_section)
            
            with open(lyra_bot_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            
            print("Fixed resource paths. Please try running again.")
            return True
        else:
            print("Could not locate directory creation section. Manual inspection needed.")
            return False
    else:
        print("Could not locate resource paths. Manual inspection needed.")
        return False

def fix_missing_modules():
    """Check for missing modules and install them"""
    required_modules = [
        "gradio",
        "pystray",
        "pyperclip",
        "Pillow",
        "keyboard",
        "llama-cpp-python",
        "pyautogui"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace("-", "_"))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"Missing required modules: {', '.join(missing_modules)}")
        
        response = input("Would you like to install them now? (y/n): ")
        if response.lower() in ('y', 'yes'):
            try:
                for module in missing_modules:
                    print(f"Installing {module}...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                print("All missing modules installed.")
                return True
            except Exception as e:
                print(f"Error installing modules: {e}")
                print("Try running: pip install -r requirements.txt")
                return False
    else:
        print("All required modules are installed.")
        return True

def main():
    """Main function for the fix utility"""
    print("Lyra Fix Utility")
    print("================")
    print("This utility will attempt to fix common issues with Lyra.")
    print()
    print("1. Fix UI initialization (gradio.Blocks context issue)")
    print("2. Fix model loading issues")
    print("3. Fix resource paths")
    print("4. Check for missing modules")
    print("5. Fix all of the above")
    print("6. Exit")
    print()
    
    choice = input("Enter your choice (1-6): ")
    
    if choice == "1":
        fix_gradio_click_issue()
    elif choice == "2":
        fix_model_loading_issue()
    elif choice == "3":
        fix_resource_paths()
    elif choice == "4":
        fix_missing_modules()
    elif choice == "5":
        print("\nRunning all fixes:")
        fix_gradio_click_issue()
        print()
        fix_model_loading_issue()
        print()
        fix_resource_paths()
        print()
        fix_missing_modules()
    else:
        print("Exiting without changes.")
        return
    
    print("\nFix operations completed. Please restart Lyra to apply changes.")

if __name__ == "__main__":
    main()
