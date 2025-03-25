import sys
import argparse
import tkinter as tk
from PIL import Image, ImageTk
import threading
import time
import os
import random

class FloatingWindow:
    def __init__(self, x=100, y=100, width=300, height=400, opacity=0.9):
        self.root = tk.Tk()
        self.root.title("Lyra Assistant")
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.attributes("-alpha", opacity)
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)  # Remove window decorations
        
        # Set up window dragging
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add close button
        self.close_btn = tk.Button(self.main_frame, text="×", font=("Arial", 12), 
                                  bg="#f0f0f0", fg="#555555", bd=0,
                                  command=self.close)
        self.close_btn.pack(side=tk.TOP, anchor=tk.NE, padx=5, pady=5)
        
        # Load character image if available
        self.image_label = None
        self.load_character_image()
        
        # Add message display area
        self.messages = tk.Text(self.main_frame, bg="#f0f0f0", wrap=tk.WORD, padx=10, pady=10,
                              font=("Arial", 10), bd=0)
        self.messages.pack(fill=tk.BOTH, expand=True)
        self.messages.config(state=tk.DISABLED)
        
        # Add some demo messages
        self.add_message("Hey there! I'm your friendly assistant.")
        self.add_message("I'm here if you need anything.")
        self.add_message("You can drag me around by clicking and dragging anywhere on the window.")
        
        # Configure mouse events for dragging
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<ButtonRelease-1>", self.stop_drag)
        self.root.bind("<B1-Motion>", self.on_drag)
        
        # Set up animation thread
        self.animation_thread = threading.Thread(target=self.animate, daemon=True)
        self.animation_thread.start()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.close)
    
    def load_character_image(self):
        """Load character image for the assistant"""
        try:
            # Default image path
            image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                      "data", "images", "assistant.png")
            
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image = image.resize((100, 100), Image.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Create label to hold image if it doesn't exist
                if self.image_label is None:
                    self.image_label = tk.Label(self.main_frame, image=photo, bg="#f0f0f0")
                    self.image_label.image = photo
                    self.image_label.pack(padx=10, pady=10)
                else:
                    self.image_label.configure(image=photo)
                    self.image_label.image = photo
            else:
                print(f"Character image not found: {image_path}")
                # Create a placeholder image
                image = Image.new('RGBA', (100, 100), (200, 200, 255, 255))
                photo = ImageTk.PhotoImage(image)
                self.image_label = tk.Label(self.main_frame, image=photo, bg="#f0f0f0")
                self.image_label.image = photo
                self.image_label.pack(padx=10, pady=10)
                
        except Exception as e:
            print(f"Error loading character image: {str(e)}")
    
    def add_message(self, text):
        """Add a message to the display area"""
        self.messages.config(state=tk.NORMAL)
        self.messages.insert(tk.END, text + "\n\n")
        self.messages.config(state=tk.DISABLED)
        self.messages.see(tk.END)
    
    def start_drag(self, event):
        """Start window dragging"""
        self.dragging = True
        self.offset_x = event.x
        self.offset_y = event.y
    
    def stop_drag(self, event):
        """Stop window dragging"""
        self.dragging = False
    
    def on_drag(self, event):
        """Handle window dragging"""
        if self.dragging:
            x = self.root.winfo_x() + event.x - self.offset_x
            y = self.root.winfo_y() + event.y - self.offset_y
            self.root.geometry(f"+{x}+{y}")
    
    def animate(self):
        """Animate the assistant"""
        idle_messages = [
            "Just hanging out here...",
            "I wonder what we'll do next?",
            "Need any help with something?",
            "I'm here whenever you need me.",
            "Just watching the screen go by...",
            "Let me know if you need assistance!",
            "Taking in the view from here.",
            "I can help with various tasks!"
        ]
        
        while True:
            try:
                # Add occasional idle messages
                time.sleep(30)  # Wait 30 seconds between potential idle messages
                
                # 30% chance to add an idle message
                if random.random() < 0.3:
                    message = random.choice(idle_messages)
                    self.add_message(message)
                    
                    # Occasionally move the window slightly
                    if random.random() < 0.2:
                        x = self.root.winfo_x() + random.randint(-20, 20)
                        y = self.root.winfo_y() + random.randint(-10, 10)
                        self.root.geometry(f"+{x}+{y}")
                
            except Exception as e:
                print(f"Animation error: {str(e)}")
                time.sleep(5)  # Wait a bit before trying again
    
    def close(self):
        """Close the window"""
        try:
            if self.animation_thread and self.animation_thread.is_alive():
                # Can't really kill threads in Python, but we can exit
                pass
                
            self.root.destroy()
            sys.exit(0)
        except:
            sys.exit(0)

def main():
    """Main function to start the floating window"""
    parser = argparse.ArgumentParser(description="Floating Assistant Window")
    parser.add_argument("--x", type=int, default=100, help="Initial X position")
    parser.add_argument("--y", type=int, default=100, help="Initial Y position")
    parser.add_argument("--width", type=int, default=300, help="Window width")
    parser.add_argument("--height", type=int, default=400, help="Window height")
    parser.add_argument("--opacity", type=float, default=0.9, help="Window opacity (0.0-1.0)")
    
    args = parser.parse_args()
    
    # Create data/images directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                           "data", "images"), exist_ok=True)
    
    window = FloatingWindow(
        x=args.x,
        y=args.y,
        width=args.width,
        height=args.height,
        opacity=args.opacity
    )
    
    window.root.mainloop()

if __name__ == "__main__":
    main()
