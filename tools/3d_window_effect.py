import sys
import os
import argparse
import time
import threading
import logging
import random

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to demonstrate 3D window effect"""
    parser = argparse.ArgumentParser(description="3D Window Effect Demo")
    parser.add_argument("--enable", action="store_true", help="Enable 3D effect")
    parser.add_argument("--assistant-x", type=int, default=100, help="Assistant X position")
    parser.add_argument("--assistant-y", type=int, default=100, help="Assistant Y position")
    parser.add_argument("--perspective", type=float, default=15.0, help="Perspective angle")
    
    args = parser.parse_args()
    
    try:
        # Import the 3D renderer
        from modules.advanced_3d_rendering import get_window_3d_renderer
        
        # Get the renderer instance
        renderer = get_window_3d_renderer()
        
        # Configure settings
        renderer.perspective_angle = args.perspective
        renderer.set_assistant_target(args.assistant_x, args.assistant_y)
        
        # Start the renderer
        if args.enable:
            renderer.enable(True)
            
            # Print window information periodically
            while True:
                windows = renderer.get_window_transforms()
                
                # Clear console (Windows)
                if sys.platform == 'win32':
                    os.system('cls')
                else:
                    os.system('clear')
                    
                print(f"Detected {len(windows)} windows")
                print(f"Assistant position: {renderer.get_current_assistant_position()}")
                print("Z-Ordered Windows (front to back):")
                
                for i, window in enumerate(windows):
                    transform = window["transform"]
                    print(f"{i+1}. {window['title']} - "
                          f"Scale: {transform['scale']:.2f}, "
                          f"Translation: ({transform['translate_x']:.1f}, {transform['translate_y']:.1f}), "
                          f"Z-Order: {window['z_order']}, "
                          f"Active: {window['active']}")
                
                print("\nPress Ctrl+C to exit")
                time.sleep(1.0)
                
        else:
            print("3D window effect demo is disabled.")
            print("Use --enable to start the demo.")
            
    except KeyboardInterrupt:
        print("\nExiting 3D window effect demo")
        
    except Exception as e:
        logger.error(f"Error in 3D window effect demo: {str(e)}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
