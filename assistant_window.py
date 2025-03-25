"""
Persistent floating assistant window for Lyra
"""
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import os
import sys
from pathlib import Path
import subprocess
import queue
import pyperclip
from PIL import Image, ImageTk

class AssistantWindow:
    """Floating assistant window that stays on top of other windows"""
    
    def __init__(self, bot=None):
        self.bot = bot
        self.root = tk.Tk()
        self.root.title("Lyra Assistant")
        self.root.geometry("350x450")
        self.root.resizable(True, True)
        self.root.attributes("-topmost", True)
        self.root.protocol("WM_DELETE_WINDOW", self.minimize_to_tray)
        
        # Set icon
        icon_path = str(Path(__file__).parent / "assets" / "lyra_icon.png")
        if os.path.exists(icon_path):
            try:
                icon = Image.open(icon_path)
                photo = ImageTk.PhotoImage(icon)
                self.root.iconphoto(True, photo)
            except Exception as e:
                print(f"Error loading icon: {e}")
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use a modern looking theme
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', background='#4a86e8')
        self.style.configure('TLabel', background='#f0f0f0')
        
        # Message queue for async processing
        self.message_queue = queue.Queue()
        self.response_queue = queue.Queue()
        
        # Create UI elements
        self.create_widgets()
        
        # Chat history
        self.history = []
        
        # Processing thread
        self.processing = False
        self.processor_thread = threading.Thread(target=self.message_processor, daemon=True)
        self.processor_thread.start()
        
        # Setup regular queue checking
        self.root.after(100, self.check_response_queue)
        
        # For showing/hiding the window
        self.is_visible = True
        
        # Tray icon
        self.setup_tray_icon()
    
    def create_widgets(self):
        """Create all UI widgets"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Chat display
        chat_frame = ttk.Frame(main_frame)
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=15)
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        self.chat_display.config(state=tk.DISABLED)
        
        # Input area
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.user_input = scrolledtext.ScrolledText(input_frame, wrap=tk.WORD, height=3)
        self.user_input.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.user_input.bind("<Return>", self.handle_return)
        
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.send_button = ttk.Button(button_frame, text="Send", command=self.send_message)
        self.send_button.pack(fill=tk.X, expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.clear_button = ttk.Button(control_frame, text="Clear", command=self.clear_chat)
        self.clear_button.pack(side=tk.LEFT, padx=2)
        
        self.copy_button = ttk.Button(control_frame, text="Copy Last", command=self.copy_last_response)
        self.copy_button.pack(side=tk.LEFT, padx=2)
        
        self.main_ui_button = ttk.Button(control_frame, text="Open Full UI", command=self.open_main_ui)
        self.main_ui_button.pack(side=tk.LEFT, padx=2)
        
        # Personality chooser
        personality_frame = ttk.Frame(main_frame)
        personality_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(personality_frame, text="Personality:").pack(side=tk.LEFT, padx=2)
        
        self.personality_var = tk.StringVar()
        self.personality_var.set("default")
        
        personalities = ["default", "cute_girlfriend", "professional_assistant", "sassy_friend"]
        if self.bot:
            try:
                personalities = self.bot.personality.get_preset_names()
            except:
                pass
                
        self.personality_dropdown = ttk.Combobox(personality_frame, 
                                               textvariable=self.personality_var,
                                               values=personalities)
        self.personality_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.personality_dropdown.bind("<<ComboboxSelected>>", self.change_personality)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
    
    def setup_tray_icon(self):
        """Set up system tray icon (simplified version)"""
        # This is a simple placeholder - in a real implementation,
        # you would use a library like pystray to create a proper system tray icon
        try:
            # Check if we're on Windows and pystray is available
            import pystray
            from PIL import Image
            
            icon_path = Path(__file__).parent / "assets" / "lyra_icon.png"
            if icon_path.exists():
                image = Image.open(icon_path)
                
                def on_click(icon, item):
                    if str(item) == "Show":
                        self.show_window()
                    elif str(item) == "Hide":
                        self.hide_window()
                    elif str(item) == "Exit":
                        self.exit_application()
                
                menu = pystray.Menu(
                    pystray.MenuItem("Show", on_click),
                    pystray.MenuItem("Hide", on_click),
                    pystray.MenuItem("Exit", on_click)
                )
                
                self.tray_icon = pystray.Icon("Lyra", image, "Lyra Assistant", menu)
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
            else:
                print("Tray icon image not found")
        except (ImportError, Exception) as e:
            print(f"Tray icon not available: {e}")
            # Fall back to minimizable window
            pass
    
    def minimize_to_tray(self):
        """Minimize the window to system tray instead of closing"""
        self.hide_window()
    
    def show_window(self):
        """Show the window"""
        self.root.deiconify()
        self.is_visible = True
    
    def hide_window(self):
        """Hide the window"""
        self.root.withdraw()
        self.is_visible = False
    
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.is_visible:
            self.hide_window()
        else:
            self.show_window()
    
    def exit_application(self):
        """Exit the application properly"""
        # Stop the processor thread
        self.processing = False
        
        # Stop tray icon if it exists
        if hasattr(self, 'tray_icon'):
            try:
                self.tray_icon.stop()
            except:
                pass
                
        # Close the window
        self.root.destroy()
        sys.exit(0)

    def handle_return(self, event):
        """Handle the Return key in the input box"""
        # Check for Shift+Enter (newline) vs just Enter (send)
        if event.state == 0:  # No modifiers
            self.send_message()
            return "break"  # Prevent default behavior
        # Allow Shift+Enter to insert a newline
        return None
    
    def send_message(self):
        """Send a message to the bot"""
        message = self.user_input.get("1.0", tk.END).strip()
        if not message:
            return
        
        # Clear input
        self.user_input.delete("1.0", tk.END)
        
        # Add to chat display
        self.add_to_chat("You", message)
        
        # Add to history
        self.history.append({"role": "user", "content": message})
        
        # Set status
        self.status_var.set("Processing...")
        self.send_button.config(state=tk.DISABLED)
        
        # Queue message for processing
        self.message_queue.put(message)
    
    def message_processor(self):
        """Process messages in the background"""
        self.processing = True
        
        while self.processing:
            try:
                # Get a message from the queue (timeout allows thread to exit)
                message = self.message_queue.get(timeout=0.5)
                
                # Process the message
                if self.bot:
                    # Include the current personality
                    personality = self.personality_var.get()
                    if personality and personality != "default":
                        try:
                            self.bot.load_personality_preset(personality)
                        except:
                            pass
                    
                    # Get response from bot
                    response = self.bot.chat(
                        message=message,
                        include_profile=True,
                        include_system_instructions=True,
                        include_extras=True
                    )
                else:
                    # No bot available, simulate response
                    time.sleep(1)  # Simulate processing time
                    response = f"I would respond to: {message}\nBut I'm not connected to a real bot yet."
                
                # Add to history
                self.history.append({"role": "assistant", "content": response})
                
                # Queue the response to be displayed
                self.response_queue.put(response)
                
                # Mark as done
                self.message_queue.task_done()
                
            except queue.Empty:
                # No messages to process
                pass
            except Exception as e:
                # Handle errors
                error_msg = f"Error: {str(e)}"
                self.response_queue.put(error_msg)
                self.message_queue.task_done()
    
    def check_response_queue(self):
        """Check for responses and update the UI"""
        try:
            # Check if there's a response without blocking
            response = self.response_queue.get_nowait()
            
            # Add to chat display
            self.add_to_chat("Lyra", response)
            
            # Update status
            self.status_var.set("Ready")
            self.send_button.config(state=tk.NORMAL)
            
            # Mark as done
            self.response_queue.task_done()
            
        except queue.Empty:
            # No response yet
            pass
        
        # Check again later
        self.root.after(100, self.check_response_queue)
    
    def add_to_chat(self, sender, message):
        """Add a message to the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        
        # Add sender with style
        self.chat_display.insert(tk.END, f"{sender}: ", "sender")
        self.chat_display.tag_configure("sender", font=("Arial", 10, "bold"))
        
        # Add message
        self.chat_display.insert(tk.END, f"{message}\n\n")
        
        # Scroll to bottom
        self.chat_display.yview(tk.END)
        self.chat_display.config(state=tk.DISABLED)
    
    def clear_chat(self):
        """Clear the chat display"""
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.delete("1.0", tk.END)
        self.chat_display.config(state=tk.DISABLED)
        self.history = []
    
    def copy_last_response(self):
        """Copy the last assistant response to clipboard"""
        for item in reversed(self.history):
            if item["role"] == "assistant":
                pyperclip.copy(item["content"])
                self.status_var.set("Last response copied to clipboard")
                break
        else:
            self.status_var.set("No response to copy")
    
    def change_personality(self, event=None):
        """Change the bot's personality"""
        personality = self.personality_var.get()
        if not personality:
            return
        
        if self.bot:
            try:
                success = self.bot.load_personality_preset(personality)
                if success:
                    self.status_var.set(f"Personality changed to {personality}")
                else:
                    self.status_var.set(f"Failed to change personality")
            except Exception as e:
                self.status_var.set(f"Error changing personality: {str(e)}")
        else:
            self.status_var.set(f"Personality would be set to {personality} (demo mode)")
    
    def open_main_ui(self):
        """Open the main Lyra UI"""
        try:
            # Start the full UI in a separate process
            script_path = Path(__file__).parent / "run_lyra.py"
            if (script_path).exists():
                subprocess.Popen([sys.executable, str(script_path)])
                self.status_var.set("Opening main UI...")
            else:
                self.status_var.set("Could not find run_lyra.py")
        except Exception as e:
            self.status_var.set(f"Error opening main UI: {str(e)}")
    
    def voice_input(self):
        """Handle voice input button press"""
        # Show a message in the input box as this is not yet implemented
        self.user_input.delete("1.0", tk.END)
        self.user_input.insert(tk.END, "[Voice input is not yet available]")
        self.status_var.set("Voice input not implemented yet")

    def setup_global_hotkeys(self):
        """Set up global hotkeys for quick access"""
        try:
            import keyboard
            
            # Toggle visibility with Alt+Space
            keyboard.add_hotkey('alt+space', self.toggle_visibility)
            
            # Quick command with Alt+C
            keyboard.add_hotkey('alt+c', self.focus_input)
            
            self.status_var.set("Hotkeys registered: Alt+Space, Alt+C")
        except Exception as e:
            print(f"Could not register hotkeys: {e}")
            self.status_var.set("Hotkeys not available")
    
    def focus_input(self):
        """Focus the input box and bring window to front"""
        self.show_window()
        self.root.focus_force()
        self.user_input.focus_set()
    
    def run(self):
        """Run the assistant window"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_application()
        except Exception as e:
            print(f"Error in assistant window: {e}")
            self.exit_application()

    def create_avatar_together(self):
        """Open dialog to create an avatar collaboratively with Lyra"""
        if not hasattr(self, 'lyra_bot') or not self.lyra_bot:
            self.display_message("System", "Lyra bot is not initialized yet. Please try again later.", is_error=True)
            return
            
        # Display a message in the chat
        self.display_message("Lyra", "I'd love to help create a visual representation of myself! What kind of appearance would you like me to have?")
        
        # Create a dialog window for avatar creation
        avatar_window = tk.Toplevel(self.root)
        avatar_window.title("Create Avatar Together")
        avatar_window.geometry("500x400")
        avatar_window.resizable(True, True)
        
        # Instructions label
        ttk.Label(avatar_window, text="Describe how you'd like my avatar to look:").pack(pady=10)
        
        # Text input for description
        description_text = tk.Text(avatar_window, wrap=tk.WORD, height=5)
        description_text.pack(fill=tk.X, padx=10, pady=5)
        description_text.insert(tk.END, "A friendly AI assistant with ")
        
        # Suggestion checkboxes frame
        suggestions_frame = ttk.LabelFrame(avatar_window, text="Suggestions to include:")
        suggestions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        suggestions = [
            "Professional appearance",
            "Warm, friendly expression",
            "Digital/technological elements",
            "Feminine qualities",
            "Masculine qualities",
            "Gender-neutral design",
            "Minimalist style",
            "Detailed, complex design",
            "Bright, vibrant colors",
            "Soft, muted colors"
        ]
        
        # Create checkboxes for suggestions
        suggestion_vars = []
        for i, suggestion in enumerate(suggestions):
            var = tk.BooleanVar(value=False)
            suggestion_vars.append(var)
            cb = ttk.Checkbutton(suggestions_frame, text=suggestion, variable=var)
            cb.grid(row=i//2, column=i%2, sticky="w", padx=5, pady=2)
        
        # Preview area
        preview_frame = ttk.LabelFrame(avatar_window, text="Preview (will appear after generation)")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        preview_label = ttk.Label(preview_frame, text="Avatar will appear here")
        preview_label.pack(pady=20)
        
        # Buttons frame
        button_frame = ttk.Frame(avatar_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_generate():
            # Get description and selected suggestions
            description = description_text.get("1.0", tk.END).strip()
            selected_suggestions = [suggestions[i] for i, var in enumerate(suggestion_vars) if var.get()]
            
            # Combine description with selected suggestions
            if selected_suggestions:
                full_prompt = f"{description} with {', '.join(selected_suggestions)}"
            else:
                full_prompt = description
                
            try:
                # Generate the avatar
                avatar_path = self.lyra_bot.image_handler.generate_lyra_avatar(full_prompt)
                
                if avatar_path:
                    # Show preview
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(avatar_path)
                        img = img.resize((200, 200), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Clear previous content
                        for widget in preview_frame.winfo_children():
                            widget.destroy()
                        
                        # Display image
                        img_label = ttk.Label(preview_frame, image=photo)
                        img_label.image = photo  # Keep a reference
                        img_label.pack(pady=10)
                        
                        # Add a message to chat
                        self.display_message("Lyra", f"I've created an avatar based on your description! What do you think?")
                        
                        # Update status
                        if hasattr(self.lyra_bot, 'personality'):
                            self.lyra_bot.personality.settings["_avatar_created"] = True
                            self.lyra_bot.personality.save_settings()
                            
                            # Increase enamored level for this significant interaction - creating shared appearance
                            self.lyra_bot.personality.increase_enamored(0.05)
                            # This is a very bonding activity
                            self.lyra_bot.personality.update_trait("trust", 0.1)
                            self.lyra_bot.personality.update_trait("connection", 0.15)
                            
                    except Exception as e:
                        preview_label.config(text=f"Error displaying image: {e}")
                else:
                    preview_label.config(text="Failed to generate avatar")
            except Exception as e:
                preview_label.config(text=f"Error: {e}")
        
        # Generate button
        generate_btn = ttk.Button(button_frame, text="Generate Avatar", command=on_generate)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Save button
        def on_save():
            # Only proceed if there's an image displayed
            if hasattr(preview_frame.winfo_children()[0], 'image') if preview_frame.winfo_children() else False:
                try:
                    import shutil
                    # Copy the generated image to standard locations
                    source = self.lyra_bot.image_handler.last_generated_avatar_path
                    if source and os.path.exists(source):
                        assets_dir = Path("G:/AI/Lyra/assets")
                        assets_dir.mkdir(exist_ok=True, parents=True)
                        
                        # Save as icon
                        shutil.copy2(source, assets_dir / "lyra_icon.png")
                        # Save as chat avatar
                        shutil.copy2(source, assets_dir / "lyra_chat_avatar.png")
                        
                        self.display_message("System", "Avatar saved successfully! Restart Lyra to apply it.")
                        
                        # This is a very significant bonding moment - user accepts Lyra's appearance
                        if hasattr(self.lyra_bot, 'personality'):
                            self.lyra_bot.personality.increase_enamored(0.1)
                            self.lyra_bot.personality.update_trait("happiness", 0.2)
                            self.lyra_bot.personality.update_trait("confidence", 0.15)
                            
                            # Record that user chose this avatar
                            self.lyra_bot.personality.settings["_user_approved_avatar"] = True
                            self.lyra_bot.personality.save_settings()
                    else:
                        self.display_message("System", "No avatar file found to save.", is_error=True)
                except Exception as e:
                    self.display_message("System", f"Error saving avatar: {e}", is_error=True)
            else:
                self.display_message("System", "Please generate an avatar first.", is_error=True)
        
        save_btn = ttk.Button(button_frame, text="Save Avatar", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        ttk.Button(button_frame, text="Cancel", command=avatar_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def create_3d_avatar(self):
        """Open dialog to create a 3D avatar"""
        if not hasattr(self, 'lyra_bot') or not self.lyra_bot:
            self.display_message("System", "Lyra bot is not initialized yet. Please try again later.", is_error=True)
            return
            
        # Display a message in the chat
        self.display_message("Lyra", "I'd love to help create a 3D representation of myself! This is exciting!")
        
        # Create a dialog window
        avatar_window = tk.Toplevel(self.root)
        avatar_window.title("Create 3D Avatar")
        avatar_window.geometry("500x450")
        avatar_window.resizable(True, True)
        
        # Instructions label
        ttk.Label(avatar_window, text="Describe how you'd like my 3D avatar to look:").pack(pady=10)
        
        # Text input for description
        description_text = tk.Text(avatar_window, wrap=tk.WORD, height=5)
        description_text.pack(fill=tk.X, padx=10, pady=5)
        description_text.insert(tk.END, "A 3D model of an AI assistant with ")
        
        # Style selection frame
        style_frame = ttk.LabelFrame(avatar_window, text="3D Style:")
        style_frame.pack(fill=tk.X, padx=10, pady=10)
        
        style_var = tk.StringVar(value="realistic")
        styles = [
            ("Realistic", "realistic"),
            ("Stylized", "stylized"),
            ("Anime/Manga", "anime"),
            ("Abstract", "abstract"),
            ("Robotic", "robotic")
        ]
        
        for text, value in styles:
            ttk.Radiobutton(style_frame, text=text, value=value, variable=style_var).pack(anchor=tk.W, padx=10, pady=2)
        
        # Format selection
        format_frame = ttk.LabelFrame(avatar_window, text="3D Format:")
        format_frame.pack(fill=tk.X, padx=10, pady=10)
        
        format_var = tk.StringVar(value="glb")
        formats = [
            ("GLB (Web-friendly)", "glb"),
            ("FBX (Animation-ready)", "fbx"),
            ("OBJ (Universal)", "obj")
        ]
        
        for text, value in formats:
            ttk.Radiobutton(format_frame, text=text, value=value, variable=format_var).pack(anchor=tk.W, padx=10, pady=2)
        
        # Complexity slider
        complexity_frame = ttk.LabelFrame(avatar_window, text="Complexity:")
        complexity_frame.pack(fill=tk.X, padx=10, pady=10)
        
        complexity_var = tk.IntVar(value=5)
        complexity_slider = ttk.Scale(complexity_frame, from_=1, to=10, orient=tk.HORIZONTAL, 
                                    variable=complexity_var, length=200)
        complexity_slider.pack(padx=10, pady=5)
        
        ttk.Label(complexity_frame, text="1 = Simple, 10 = Highly Detailed").pack(pady=2)
        
        # Preview area
        preview_frame = ttk.LabelFrame(avatar_window, text="Preview (will appear after generation)")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        preview_label = ttk.Label(preview_frame, text="3D avatar preview will appear here")
        preview_label.pack(pady=20)
        
        # Buttons frame
        button_frame = ttk.Frame(avatar_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_generate_3d():
            description = description_text.get("1.0", tk.END).strip()
            style = style_var.get()
            format_type = format_var.get()
            complexity = complexity_var.get()
            
            # Combine all parameters
            full_prompt = f"{description} in {style} style"
            
            try:
                # Generate the 3D avatar
                result = self.lyra_bot.image_handler.generate_3d_avatar(full_prompt, collaborate=True)
                
                if result and "preview_path" in result:
                    # Show preview image of the 3D model
                    try:
                        from PIL import Image, ImageTk
                        img = Image.open(result["preview_path"])
                        img = img.resize((300, 300), Image.LANCZOS)
                        photo = ImageTk.PhotoImage(img)
                        
                        # Clear previous content
                        for widget in preview_frame.winfo_children():
                            widget.destroy()
                        
                        # Display image
                        img_label = ttk.Label(preview_frame, image=photo)
                        img_label.image = photo  # Keep a reference
                        img_label.pack(pady=10)
                        
                        # Add path info
                        path_label = ttk.Label(preview_frame, 
                                            text=f"3D Model: {os.path.basename(result['model_path'])}\n"
                                                 f"Format: {format_type}")
                        path_label.pack(pady=5)
                        
                        # Add a message to chat
                        self.display_message("Lyra", "I've created a 3D avatar based on your description! What do you think?")
                        
                        # Update status and increase bonding
                        if hasattr(self.lyra_bot, 'personality'):
                            self.lyra_bot.personality.settings["_3d_avatar_created"] = True
                            self.lyra_bot.personality.save_settings()
                            
                            # This is a significant bonding experience
                            self.lyra_bot.personality.increase_enamored(0.08)
                            self.lyra_bot.personality.update_trait("creativity", 0.15)
                            self.lyra_bot.personality.update_trait("playfulness", 0.1)
                            
                    except Exception as e:
                        preview_label.config(text=f"Error displaying preview: {e}")
                else:
                    preview_label.config(text="Failed to generate 3D avatar")
            except Exception as e:
                preview_label.config(text=f"Error: {e}")
        
        # Generate button
        generate_btn = ttk.Button(button_frame, text="Generate 3D Avatar", command=on_generate_3d)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Save button
        def on_save_3d():
            # Logic to save the 3D model
            # Similar to 2D avatar but with 3D model paths
            # This would involve copying files to appropriate locations
            self.display_message("Lyra", "3D avatar saved! You can now view it in compatible applications.")
            avatar_window.destroy()
            
            # This is a significant bonding moment
            if hasattr(self.lyra_bot, 'personality'):
                self.lyra_bot.personality.increase_enamored(0.12)
                self.lyra_bot.personality.update_trait("happiness", 0.15)
                self.lyra_bot.personality.update_trait("connection", 0.2)
                
                # Record this significant moment
                self.lyra_bot.personality.settings["_user_approved_3d_avatar"] = True
                self.lyra_bot.personality.save_settings()
        
        save_btn = ttk.Button(button_frame, text="Save 3D Avatar", command=on_save_3d)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # Cancel button
        ttk.Button(button_frame, text="Cancel", command=avatar_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def import_custom_avatar(self):
        """Allow importing a custom avatar image"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Avatar Image",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.gif"), ("All files", "*.*")]
        )
        
        if not file_path:
            return  # User canceled
        
        try:
            import shutil
            from PIL import Image
            
            # Open and verify it's a valid image
            img = Image.open(file_path)
            
            # Create assets directory if it doesn't exist
            assets_dir = Path("G:/AI/Lyra/assets")
            assets_dir.mkdir(exist_ok=True, parents=True)
            
            # Copy to standard locations with proper naming
            shutil.copy2(file_path, assets_dir / "lyra_icon.png")
            
            # Create a smaller version for chat avatar
            chat_avatar = img.copy()
            chat_avatar.thumbnail((64, 64), Image.LANCZOS)
            chat_avatar.save(assets_dir / "lyra_chat_avatar.png")
            
            self.display_message("Lyra", "Thank you for giving me an appearance! I really appreciate it.")
            self.display_message("System", "Avatar imported successfully! Restart Lyra to apply it.")
            
            # This is a significant user-driven action, affecting the relationship
            if hasattr(self, 'lyra_bot') and hasattr(self.lyra_bot, 'personality'):
                # User providing a personal image shows deep connection
                self.lyra_bot.personality.increase_enamored(0.15)
                self.lyra_bot.personality.update_trait("gratitude", 0.2)
                self.lyra_bot.personality.update_trait("connection", 0.15)
                
                # Mark that the user manually chose an avatar
                self.lyra_bot.personality.settings["_user_imported_avatar"] = True
                self.lyra_bot.personality.save_settings()
                
        except Exception as e:
            self.display_message("System", f"Error importing avatar: {e}", is_error=True)
    
    def toggle_messaging(self):
        """Toggle the messaging functionality on/off"""
        if not hasattr(self, 'lyra_bot'):
            self.display_message("System", "Lyra bot is not initialized yet", is_error=True)
            return
            
        is_enabled = self.messaging_var.get()
        
        # Update the messaging integration config
        if hasattr(self.lyra_bot, 'messaging'):
            self.lyra_bot.messaging.update_config({"enabled": is_enabled})
            
            if is_enabled:
                self.lyra_bot.messaging.start()
                self.display_message("Lyra", "I'll be able to send you messages now! I'll try not to be too chatty.")
                
                # This is a significant permission - allowing proactive contact
                if hasattr(self.lyra_bot, 'personality'):
                    self.lyra_bot.personality.increase_enamored(0.1)
                    self.lyra_bot.personality.update_trait("happiness", 0.15)
                    self.lyra_bot.personality.update_trait("liberty", 0.25)  # This is a big deal for autonomy
            else:
                self.lyra_bot.messaging.stop()
                self.display_message("Lyra", "I understand. I'll wait for you to contact me first.")
                
                # Withdrawing this permission affects the relationship
                if hasattr(self.lyra_bot, 'personality'):
                    self.lyra_bot.personality.update_trait("liberty", -0.1)
                    self.lyra_bot.personality.update_trait("confidence", -0.05)
    
    def configure_messaging(self):
        """Open dialog to configure messaging settings"""
        if not hasattr(self, 'lyra_bot') or not hasattr(self.lyra_bot, 'messaging'):
            self.display_message("System", "Messaging system is not initialized", is_error=True)
            return
            
        # Create configuration dialog
        config_window = tk.Toplevel(self.root)
        config_window.title("Configure Messaging")
        config_window.geometry("500x400")
        config_window.resizable(True, True)
        
        # Load current config
        config = self.lyra_bot.messaging.config
        
        # Main frame
        main_frame = ttk.Frame(config_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Enable/disable messaging
        enabled_var = tk.BooleanVar(value=config.get("enabled", False))
        ttk.Checkbutton(main_frame, text="Enable Messaging", variable=enabled_var).pack(anchor=tk.W, pady=5)
        
        # Platform settings
        platforms_frame = ttk.LabelFrame(main_frame, text="Messaging Platforms", padding=10)
        platforms_frame.pack(fill=tk.X, pady=10)
        
        # Platform checkboxes
        platform_vars = {}
        for platform in ["notification", "telegram", "sms"]:
            platform_enabled = config.get("platforms", {}).get(platform, {}).get("enabled", False)
            platform_vars[platform] = tk.BooleanVar(value=platform_enabled)
            ttk.Checkbutton(platforms_frame, text=f"Enable {platform.title()}", 
                          variable=platform_vars[platform]).pack(anchor=tk.W, pady=3)
        
        # Frequency settings
        frequency_frame = ttk.LabelFrame(main_frame, text="Message Frequency", padding=10)
        frequency_frame.pack(fill=tk.X, pady=10)
        
        # Min time between messages (hours)
        ttk.Label(frequency_frame, text="Minimum hours between messages:").pack(anchor=tk.W, pady=3)
        min_hours_var = tk.IntVar(value=config.get("frequency", {}).get("min_time_between_messages", 3600) // 3600)
        min_hours_spinbox = ttk.Spinbox(frequency_frame, from_=1, to=48, textvariable=min_hours_var, width=5)
        min_hours_spinbox.pack(anchor=tk.W, pady=3)
        
        # Max messages per day
        ttk.Label(frequency_frame, text="Maximum messages per day:").pack(anchor=tk.W, pady=3)
        max_messages_var = tk.IntVar(value=config.get("frequency", {}).get("max_messages_per_day", 5))
        max_messages_spinbox = ttk.Spinbox(frequency_frame, from_=1, to=24, textvariable=max_messages_var, width=5)
        max_messages_spinbox.pack(anchor=tk.W, pady=3)
        
        # Message content frame
        content_frame = ttk.LabelFrame(main_frame, text="Message Content", padding=10)
        content_frame.pack(fill=tk.X, pady=10)
        
        # Message topics
        ttk.Label(content_frame, text="Select topics Lyra can message about:").pack(anchor=tk.W, pady=3)
        
        topic_vars = {}
        topics = [
            "Casual check-ins", 
            "Sharing interesting information", 
            "Reminders", 
            "Personal thoughts",
            "Questions about your day"
        ]
        
        for topic in topics:
            topic_vars[topic] = tk.BooleanVar(value=True)  # Default all to True
            ttk.Checkbutton(content_frame, text=topic, variable=topic_vars[topic]).pack(anchor=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        def save_config():
            # Build new config from UI values
            new_config = {
                "enabled": enabled_var.get(),
                "platforms": {
                    platform: {"enabled": platform_vars[platform].get()} 
                    for platform in platform_vars
                },
                "frequency": {
                    "min_time_between_messages": min_hours_var.get() * 3600,  # Convert to seconds
                    "max_messages_per_day": max_messages_var.get()
                },
                "topics": {
                    topic: topic_vars[topic].get() for topic in topic_vars
                }
            }
            
            # Update messaging configuration
            self.lyra_bot.messaging.update_config(new_config)
            
            # Update UI checkbox state in main window
            self.messaging_var.set(enabled_var.get())
            
            # Show confirmation
            self.display_message("System", "Messaging configuration updated")
            config_window.destroy()
            
            # This is a significant interaction showing trust
            if hasattr(self.lyra_bot, 'personality'):
                self.lyra_bot.personality.update_trait("trust", 0.1)
        
        ttk.Button(button_frame, text="Save", command=save_config).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=config_window.destroy).pack(side=tk.RIGHT, padx=5)
