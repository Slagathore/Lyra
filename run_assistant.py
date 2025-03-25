"""
Run the floating assistant window
"""
import sys
import os
import argparse
from pathlib import Path
import importlib.metadata
import threading
import time

# Add the project directory to the Python path
sys.path.append(str(Path(__file__).parent))

def main():
    """Main entry point for the floating assistant"""
    parser = argparse.ArgumentParser(description="Lyra Assistant Window")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode without connecting to the bot")
    parser.add_argument("--personality", type=str, default="default", help="Initial personality to use")
    args = parser.parse_args()
    
    try:
        # Create assets folder if it doesn't exist
        assets_dir = Path(__file__).parent / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Create a simple icon if none exists
        icon_path = assets_dir / "lyra_icon.png"
        if not icon_path.exists():
            try:
                from PIL import Image, ImageDraw
                
                # Create a simple icon
                img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                
                # Draw a circle
                draw.ellipse((20, 20, 236, 236), fill=(74, 134, 232, 255))
                
                # Draw an 'L' in the center
                draw.rectangle((90, 80, 120, 180), fill=(255, 255, 255, 255))
                draw.rectangle((90, 150, 170, 180), fill=(255, 255, 255, 255))
                
                img.save(icon_path)
                print(f"Created icon at {icon_path}")
            except ImportError:
                print("PIL not available, skipping icon creation")
            except Exception as e:
                print(f"Error creating icon: {e}")
        
        if args.demo:
            print("Running in demo mode (not connected to bot)")
            from assistant_window import AssistantWindow
            assistant = AssistantWindow(bot=None)
            
            # Set initial personality
            assistant.personality_var.set(args.personality)
            
            assistant.run()
        else:
            print("Connecting to bot...")
            # Import dependencies only when needed
            from assistant_window import AssistantWindow
            from lyra_bot import LyraBot
            
            # Create and initialize bot
            bot = LyraBot()
            
            # Start the assistant window
            assistant = AssistantWindow(bot=bot)
            
            # Set initial personality
            assistant.personality_var.set(args.personality)
            
            # Try to load personality
            try:
                if args.personality != "default":
                    bot.load_personality_preset(args.personality)
            except Exception as e:
                print(f"Error loading personality: {e}")
            
            assistant.run()
    except Exception as e:
        print(f"Error starting assistant: {e}")
        print("\nIf you're experiencing issues:")
        print("1. Try running with --demo flag")
        print("2. Make sure all dependencies are installed")
        print("3. Check if your model files exist and are not corrupted")
        sys.exit(1)

if __name__ == "__main__":
    main()
