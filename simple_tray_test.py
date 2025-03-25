"""
Simple test for system tray functionality
"""
import os
import sys
import time
import logging

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger("tray_test")

logger.info("Testing system tray functionality...")

# Test imports
try:
    logger.info("Checking for PIL/Pillow...")
    from PIL import Image
    logger.info("PIL/Pillow is available")
except ImportError as e:
    logger.error(f"PIL/Pillow import error: {e}")
    logger.error("Please install Pillow: pip install pillow")
    sys.exit(1)

try:
    logger.info("Checking for pystray...")
    import pystray
    logger.info("pystray is available")
except ImportError as e:
    logger.error(f"pystray import error: {e}")
    logger.error("Please install pystray: pip install pystray")
    sys.exit(1)

try:
    logger.info("Checking for tkinter...")
    import tkinter as tk
    logger.info("tkinter is available")
except ImportError as e:
    logger.error(f"tkinter import error: {e}")
    logger.error("Please install tkinter or use your system package manager")
    # Continue anyway as we test pystray independently

# Create a simple image for the icon
def create_image():
    # Generate a plain color square with PIL
    logger.info("Creating test icon image...")
    img = Image.new('RGB', (64, 64), color='blue')
    return img

def exit_action(icon):
    logger.info("Exit requested through menu")
    icon.stop()

def test_tkinter():
    """Test if tkinter can create a window"""
    logger.info("Testing tkinter window creation...")
    try:
        root = tk.Tk()
        root.title("Tkinter Test")
        root.geometry("300x200")
        
        label = tk.Label(root, text="Tkinter is working!")
        label.pack(padx=20, pady=20)
        
        # Auto-close after 2 seconds
        root.after(2000, root.destroy)
        
        logger.info("Showing tkinter window for 2 seconds...")
        root.mainloop()
        logger.info("Tkinter window closed successfully")
        return True
    except Exception as e:
        logger.error(f"Tkinter window error: {e}")
        return False

def main():
    logger.info("Starting tray icon test...")
    
    # First test tkinter
    tk_result = test_tkinter()
    global tk_test_passed  # Global variable to track tkinter test result
    tk_test_passed = tk_result
    
    # Now test system tray icon
    try:
        logger.info("Creating tray icon...")
        image = create_image()
        menu = pystray.Menu(
            pystray.MenuItem("Exit", exit_action)
        )
        
        icon = pystray.Icon("test_icon", image, "Test Icon", menu)
        
        logger.info("Starting tray icon - look for a blue square in your system tray!")
        logger.info("The icon will automatically exit after 10 seconds")
        logger.info("You can also exit by selecting 'Exit' from the icon's menu")
        
        # Run the icon in a separate thread so we can time it
        import threading
        icon_thread = threading.Thread(target=icon.run, daemon=True)
        icon_thread.start()
        
        # Wait for a bit, then stop
        time.sleep(10)
        logger.info("Test complete, stopping icon")
        icon.stop()
        
        logger.info("System tray test complete - PASSED!")
        return True
    except Exception as e:
        logger.error(f"System tray test error: {e}")
        logger.error("System tray test FAILED")
        return False

if __name__ == "__main__":
    # Define a global variable to track the tkinter test
    tk_test_passed = False
    
    success = main()
    print("\nResults:")
    print("-" * 40)
    print(f"Tkinter GUI: {'WORKING' if tk_test_passed else 'FAILED'}")
    print(f"System Tray: {'WORKING' if success else 'FAILED'}")
    print("\nIf any test failed, check the logs above for details on what went wrong.")
    input("\nPress Enter to exit...")
